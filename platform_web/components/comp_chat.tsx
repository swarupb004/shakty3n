"use client";

import { useState, useEffect, useRef } from "react";
import { Send, Bot, User, Play, Loader2 } from "lucide-react";
import { api, cn } from "@/lib/utils";

interface Message {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    timestamp: number;
}

interface AgentChatProps {
    agentId: string;
}

export function AgentChat({ agentId }: AgentChatProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const sendMessage = async () => {
        if (!input.trim() || isProcessing) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: "user",
            content: input,
            timestamp: Date.now(),
        };

        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsProcessing(true);

        try {
            // Trigger workflow
            await api.post(`/api/agents/${agentId}/workflow`, {
                description: userMsg.content,
                project_type: "web-react", // TODO: make dynamic?
                requirements: {}
            });

            // Add system ack
            const sysMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: "system",
                content: "Task started. Monitoring execution...",
                timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, sysMsg]);

        } catch (e) {
            console.error(e);
            setMessages((prev) => [
                ...prev,
                {
                    id: Date.now().toString(),
                    role: "system",
                    content: "Error: Failed to send command to agent.",
                    timestamp: Date.now(),
                },
            ]);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-neutral-900 border-l border-white/10">
            <div className="p-3 border-b border-white/10 font-medium text-sm flex items-center gap-2">
                <Bot className="w-4 h-4 text-cyan-400" />
                Agent Communication
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 text-sm" ref={scrollRef}>
                <div className="text-center text-neutral-500 text-xs py-4">
                    Session Started
                </div>

                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={cn(
                            "flex gap-3 max-w-[90%]",
                            msg.role === "user" ? "ml-auto flex-row-reverse" : ""
                        )}
                    >
                        <div
                            className={cn(
                                "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                                msg.role === "user" ? "bg-neutral-700" : "bg-cyan-600/20 text-cyan-400"
                            )}
                        >
                            {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                        </div>
                        <div
                            className={cn(
                                "p-3 rounded-lg",
                                msg.role === "user"
                                    ? "bg-blue-600 text-white"
                                    : msg.role === "system"
                                        ? "bg-neutral-800 text-neutral-400 text-xs italic border border-white/5"
                                        : "bg-neutral-800 text-white"
                            )}
                        >
                            {msg.content}
                        </div>
                    </div>
                ))}

                {isProcessing && (
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-cyan-600/20 flex items-center justify-center shrink-0">
                            <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                        </div>
                        <div className="text-neutral-500 text-xs flex items-center">
                            Thinking...
                        </div>
                    </div>
                )}
            </div>

            <div className="p-3 border-t border-white/10 bg-neutral-900">
                <div className="relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                        placeholder="Instruct the agent..."
                        className="w-full bg-black/50 border border-white/10 rounded-lg pl-4 pr-10 py-3 text-sm focus:outline-none focus:border-cyan-500"
                    />
                    <button
                        onClick={sendMessage}
                        disabled={!input.trim() || isProcessing}
                        className="absolute right-2 top-2 p-1 text-neutral-400 hover:text-white disabled:opacity-50"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
