"use client";

import { useEffect, useRef, useState } from "react";
import { Terminal as XTerm } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import "xterm/css/xterm.css";

interface AgentTerminalProps {
    agentId: string;
}

export default function AgentTerminal({ agentId }: AgentTerminalProps) {
    const terminalRef = useRef<HTMLDivElement>(null);
    const instanceRef = useRef<XTerm | null>(null);
    const fitAddonRef = useRef<FitAddon | null>(null);
    const [isReady, setIsReady] = useState(false);

    // Wait for container to have valid dimensions before initializing
    useEffect(() => {
        if (!terminalRef.current) return;

        const checkDimensions = () => {
            if (terminalRef.current &&
                terminalRef.current.clientWidth > 0 &&
                terminalRef.current.clientHeight > 0) {
                setIsReady(true);
                return true;
            }
            return false;
        };

        if (checkDimensions()) return;

        // Poll until dimensions are valid
        const interval = setInterval(() => {
            if (checkDimensions()) {
                clearInterval(interval);
            }
        }, 50);

        return () => clearInterval(interval);
    }, []);

    // Initialize terminal only when ready
    useEffect(() => {
        if (!isReady || !terminalRef.current) return;
        if (instanceRef.current) return; // Already initialized

        const term = new XTerm({
            theme: {
                background: "#0a0a0a",
                foreground: "#d4d4d4",
            },
            fontSize: 14,
            fontFamily: "Menlo, Monaco, 'Courier New', monospace",
            cursorBlink: true,
            rows: 10,
            cols: 80,
        });

        const fitAddon = new FitAddon();
        term.loadAddon(fitAddon);
        term.open(terminalRef.current);

        instanceRef.current = term;
        fitAddonRef.current = fitAddon;

        // Safe fit after open
        requestAnimationFrame(() => {
            try {
                if (terminalRef.current &&
                    terminalRef.current.clientWidth > 0 &&
                    terminalRef.current.clientHeight > 0) {
                    fitAddon.fit();
                }
            } catch (e) {
                console.warn("Initial fit error:", e);
            }
        });

        term.writeln("\x1b[1;36mShakty3n Agent Terminal\x1b[0m");
        term.writeln("Connected to agent environment...");
        term.writeln("$ ");

        // ResizeObserver with debounce and safety checks
        let resizeTimeout: NodeJS.Timeout;
        const resizeObserver = new ResizeObserver(() => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (!terminalRef.current) return;
                if (terminalRef.current.clientWidth === 0 || terminalRef.current.clientHeight === 0) return;
                if (!fitAddonRef.current) return;

                try {
                    fitAddonRef.current.fit();
                } catch (e) {
                    // Silently ignore - terminal may be in transition
                }
            }, 100);
        });
        resizeObserver.observe(terminalRef.current);

        // WebSocket connection
        const ws = new WebSocket(`ws://localhost:8000/ws/events`);
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.kind === 'terminal') {
                    term.writeln(data.message.replace(/\n/g, '\r\n'));
                } else if (data.kind === 'workflow_started') {
                    term.writeln(`\r\n\x1b[32m[Workflow Started]\x1b[0m ${data.message}\r\n`);
                }
            } catch {
                // ignore
            }
        };

        return () => {
            clearTimeout(resizeTimeout);
            resizeObserver.disconnect();
            term.dispose();
            ws.close();
            instanceRef.current = null;
            fitAddonRef.current = null;
        };
    }, [isReady, agentId]);

    return (
        <div
            className="h-full w-full min-h-[100px]"
            ref={terminalRef}
            style={{ minHeight: '100px', minWidth: '200px' }}
        />
    );
}
