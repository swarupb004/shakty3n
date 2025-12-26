"use client";

import { useEffect, useRef } from "react";
import { Terminal as XTerm } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import "xterm/css/xterm.css";

interface AgentTerminalProps {
    agentId: string;
}

export default function AgentTerminal({ agentId }: AgentTerminalProps) {
    const terminalRef = useRef<HTMLDivElement>(null);
    const instanceRef = useRef<XTerm | null>(null);

    useEffect(() => {
        if (!terminalRef.current) return;

        // Prevent double init
        if (terminalRef.current.childElementCount > 0) return;

        const term = new XTerm({
            theme: {
                background: "#0a0a0a",
                foreground: "#d4d4d4",
            },
            fontSize: 14,
            fontFamily: "Menlo, Monaco, 'Courier New', monospace",
            cursorBlink: true,
            rows: 15
        });

        const fitAddon = new FitAddon();
        term.loadAddon(fitAddon);
        term.open(terminalRef.current);
        fitAddon.fit();

        term.writeln("\x1b[1;36mShakty3n Agent Terminal\x1b[0m");
        term.writeln("Connected to agent environment...");
        term.writeln("$ ");

        instanceRef.current = term;

        const resizeObserver = new ResizeObserver(() => fitAddon.fit());
        resizeObserver.observe(terminalRef.current);

        // Initial socket connection
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
            resizeObserver.disconnect();
            term.dispose();
            ws.close();
        };
    }, [agentId]);

    return <div className="h-full w-full" ref={terminalRef} />;
}
