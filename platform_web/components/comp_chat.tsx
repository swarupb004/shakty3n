"use client";

import { useState, useEffect, useRef } from "react";
import { Send, Bot, User, Loader2, Settings2, ChevronDown } from "lucide-react";
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

const AI_PROVIDERS = [
    { value: "ollama", label: "Ollama (Local)", defaultModel: "devstral:latest" },
    { value: "docker", label: "Docker (Desktop Models)", defaultModel: "ai/qwen3-coder:latest" },
    { value: "openai", label: "OpenAI", defaultModel: "gpt-4" },
    { value: "anthropic", label: "Anthropic", defaultModel: "claude-3-sonnet-20240229" },
    { value: "google", label: "Google", defaultModel: "gemini-pro" },
];

interface ProjectConfig {
    description: string;
    type: string;
    requirements: Record<string, unknown>;
}

export function AgentChat({ agentId }: AgentChatProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [isLoadingHistory, setIsLoadingHistory] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Model switching state
    const [showSettings, setShowSettings] = useState(false);
    const [provider, setProvider] = useState("ollama");
    const [model, setModel] = useState("devstral:latest");
    const [availableModels, setAvailableModels] = useState<string[]>([]);

    // Confirmation state for project creation
    const [pendingProject, setPendingProject] = useState<ProjectConfig | null>(null);

    // Load chat history on mount
    useEffect(() => {
        async function loadHistory() {
            try {
                const res = await api.get(`/api/agents/${agentId}/chat`);
                if (res.history && res.history.length > 0) {
                    const loaded = res.history.map((msg: any) => ({
                        id: String(msg.id),
                        role: msg.role as "user" | "assistant" | "system",
                        content: msg.content,
                        timestamp: new Date(msg.created_at).getTime()
                    }));
                    setMessages(loaded);
                }
            } catch (e) {
                console.warn("Failed to load chat history", e);
            } finally {
                setIsLoadingHistory(false);
            }
        }
        loadHistory();
    }, [agentId]);

    // Save message to backend
    const saveMessage = async (role: string, content: string) => {
        try {
            await api.post(`/api/agents/${agentId}/chat`, { role, content });
        } catch (e) {
            console.warn("Failed to save message", e);
        }
    };

    // Fetch models when provider changes
    useEffect(() => {
        async function fetchModels() {
            // Try dynamic fetch for Ollama
            if (provider === 'ollama') {
                try {
                    const res = await api.get(`/api/providers/${provider}/models`);
                    if (res.models && res.models.length > 0) {
                        setAvailableModels(res.models);
                        // Set first model if current isn't in list
                        if (!res.models.includes(model)) {
                            setModel(res.models[0]);
                        }
                        return;
                    }
                } catch (e) {
                    // API not available or failed - fall back to defaults
                    console.warn("Dynamic model fetch failed, using defaults", e);
                }
            }
            // Fallback to defaults
            const defaults: Record<string, string[]> = {
                openai: ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                anthropic: ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                google: ["gemini-pro", "gemini-3.0-pro"],
                ollama: ["devstral:latest", "codestral:22b", "deepseek-coder:6.7b", "llama3.1:latest"],
                docker: ["ai/qwen3-coder:latest"]
            };
            setAvailableModels(defaults[provider] || []);
            const list = defaults[provider] || [];
            if (list.length > 0 && !list.includes(model)) {
                setModel(list[0]);
            }
        }
        fetchModels();
    }, [provider]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    // Listen for events from backend
    useEffect(() => {
        const ws = new WebSocket(`ws://localhost:8000/ws/events`);

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                // Handle different event types
                if (data.kind === 'workflow_finished') {
                    const status = data.message; // 'completed' or 'failed'
                    const extra = data.extra || {};
                    const progress = extra.progress || {};
                    let content = "";

                    if (status === 'completed') {
                        const tasksInfo = progress.completed && progress.total
                            ? `${progress.completed}/${progress.total} tasks`
                            : '';
                        content = `✅ **Project Created Successfully!**\n\nYour code has been generated and is ready in the workspace. Check the file explorer on the left to see your new files.\n\n${tasksInfo ? `📊 ${tasksInfo} completed` : ''}`;
                    } else {
                        // Check for partial success (code generated but low task completion)
                        const hasProgress = progress.completed > 0;
                        if (hasProgress) {
                            content = `⚠️ **Workflow Completed with Issues**\n\nCompleted ${progress.completed}/${progress.total} tasks (${progress.percentage?.toFixed(0) || 0}%)\n\nCheck the file explorer - some files may have been generated. You can try running the workflow again or modify the request.`;
                        } else {
                            const errorMsg = extra.error || extra.message || "Unknown error";
                            content = `❌ **Workflow Failed**\n\n${errorMsg}\n\nTry rephrasing your request or check that the AI model is responding correctly.`;
                        }
                    }

                    setMessages(prev => [...prev, {
                        id: crypto.randomUUID(),
                        role: "assistant",
                        content: content,
                        timestamp: Date.now()
                    }]);
                    saveMessage("assistant", content);
                    setIsProcessing(false);
                }
            } catch (e) {
                console.error("Chat WebSocket error", e);
            }
        };

        return () => {
            ws.close();
        };
    }, [agentId]);

    const sendMessage = async () => {
        if (!input.trim() || isProcessing) return;

        const userMsg: Message = {
            id: crypto.randomUUID(),
            role: "user",
            content: input,
            timestamp: Date.now(),
        };

        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsProcessing(true);
        saveMessage("user", userMsg.content);

        try {
            // First, process the message to classify intent
            const processResult = await api.post(`/api/agents/${agentId}/process`, {
                content: userMsg.content,
                provider: provider,
                model: model
            });

            const { intent, response, action, requires_confirmation, project_config } = processResult;

            // Add AI response message
            const aiMsg: Message = {
                id: crypto.randomUUID(),
                role: "assistant",
                content: response,
                timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, aiMsg]);
            saveMessage("assistant", response);

            // Handle different intents
            if (intent === "greeting" || intent === "question" || intent === "clarification") {
                // Just show the response, no action needed
                setIsProcessing(false);
            } else if (intent === "project_creation" && requires_confirmation) {
                // Store pending project for confirmation
                setPendingProject(project_config);
                setIsProcessing(false);
            } else if (intent === "command" && action === "run_code") {
                // Execute command - for now just acknowledge
                const cmdMsg: Message = {
                    id: crypto.randomUUID(),
                    role: "system",
                    content: "Preparing to execute command...",
                    timestamp: Date.now(),
                };
                setMessages((prev) => [...prev, cmdMsg]);
                setIsProcessing(false);
            } else if (action === "create_project" && !requires_confirmation) {
                // Direct project creation (if user confirms via intent)
                await startWorkflow(project_config || { description: userMsg.content, type: "web-react", requirements: {} });
            } else {
                setIsProcessing(false);
            }

        } catch (e) {
            console.error(e);
            setMessages((prev) => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: "system",
                    content: "Error: Failed to process message. Please try again.",
                    timestamp: Date.now(),
                },
            ]);
            setIsProcessing(false);
        }
    };

    const inferProjectType = (description: string): string => {
        const descLower = description.toLowerCase();
        const staticHints = ["html", "static", "landing page", "single page", "simple page", "plain page"];
        if (staticHints.some((hint) => descLower.includes(hint))) {
            return "html";
        }
        return "web-react";
    };

    const startWorkflow = async (config: ProjectConfig) => {
        try {
            setIsProcessing(true);

            // Determine project type with smart defaults
            let projectType = config.type;
            if (!projectType || projectType.trim() === "") {
                projectType = inferProjectType(config.description);
            }

            await api.post(`/api/agents/${agentId}/workflow`, {
                description: config.description || "Create a new project",
                project_type: projectType,
                requirements: config.requirements || {},
            });

            const sysMsg: Message = {
                id: crypto.randomUUID(),
                role: "system",
                content: `✨ Project creation started! Building: ${config.description}`,
                timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, sysMsg]);
            setPendingProject(null);
        } catch (e) {
            console.error(e);
            setMessages((prev) => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: "system",
                    content: "Error: Failed to start project workflow.",
                    timestamp: Date.now(),
                },
            ]);
            setIsProcessing(false);
        }
    };

    const confirmProject = () => {
        if (pendingProject) {
            startWorkflow(pendingProject);
        }
    };

    const cancelProject = () => {
        setPendingProject(null);
        const cancelMsg: Message = {
            id: crypto.randomUUID(),
            role: "system",
            content: "Project creation cancelled. Let me know if you need anything else!",
            timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, cancelMsg]);
    };

    const currentProviderLabel = AI_PROVIDERS.find(p => p.value === provider)?.label || provider;

    return (
        <div className="flex flex-col h-full bg-neutral-900 border-l border-white/10">
            {/* Header with model switcher */}
            <div className="p-3 border-b border-white/10 font-medium text-sm">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Bot className="w-4 h-4 text-cyan-400" />
                        Agent Communication
                    </div>
                    <button
                        onClick={() => setShowSettings(!showSettings)}
                        className={cn(
                            "p-1.5 rounded hover:bg-white/10 transition-colors",
                            showSettings && "bg-white/10"
                        )}
                        title="Model Settings"
                    >
                        <Settings2 className="w-4 h-4" />
                    </button>
                </div>

                {/* Model settings panel */}
                {showSettings && (
                    <div className="mt-3 p-3 bg-black/30 rounded-lg border border-white/10 space-y-3">
                        <div className="text-xs text-neutral-400 uppercase font-semibold">AI Model Settings</div>

                        <div className="space-y-2">
                            <label className="text-xs text-neutral-500">Provider</label>
                            <select
                                value={provider}
                                onChange={(e) => {
                                    setProvider(e.target.value);
                                    const prov = AI_PROVIDERS.find(p => p.value === e.target.value);
                                    if (prov) setModel(prov.defaultModel);
                                }}
                                className="w-full bg-black/50 border border-white/10 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-cyan-500"
                            >
                                {AI_PROVIDERS.map((p) => (
                                    <option key={p.value} value={p.value}>{p.label}</option>
                                ))}
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs text-neutral-500">Model</label>
                            <select
                                value={model}
                                onChange={(e) => setModel(e.target.value)}
                                className="w-full bg-black/50 border border-white/10 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-cyan-500"
                            >
                                {availableModels.map((m) => (
                                    <option key={m} value={m}>{m}</option>
                                ))}
                            </select>
                        </div>

                        <div className="text-[10px] text-neutral-600 pt-1">
                            Active: <span className="text-cyan-400">{currentProviderLabel} / {model}</span>
                        </div>
                    </div>
                )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 text-sm" ref={scrollRef}>
                {isLoadingHistory ? (
                    <div className="text-center text-neutral-500 text-xs py-4">
                        Loading chat history...
                    </div>
                ) : messages.length === 0 ? (
                    <div className="text-center text-neutral-500 text-xs py-4">
                        New Session - Start chatting!
                    </div>
                ) : (
                    <div className="text-center text-neutral-500 text-xs py-4">
                        Chat history loaded ({messages.length} messages)
                    </div>
                )}

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
                {/* Confirmation dialog for project creation */}
                {pendingProject && (
                    <div className="mb-3 p-3 bg-cyan-900/20 border border-cyan-500/30 rounded-lg">
                        <div className="text-xs text-cyan-400 font-semibold mb-2">
                            🚀 Confirm Project Creation
                        </div>
                        <div className="text-sm text-neutral-300 mb-2">
                            <strong>Description:</strong> {pendingProject.description}
                        </div>
                        <div className="text-xs text-neutral-500 mb-3">
                            <strong>Type:</strong> {pendingProject.type}
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={confirmProject}
                                className="flex-1 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium rounded transition-colors"
                            >
                                ✓ Yes, Create It
                            </button>
                            <button
                                onClick={cancelProject}
                                className="flex-1 px-3 py-1.5 bg-neutral-700 hover:bg-neutral-600 text-neutral-300 text-xs font-medium rounded transition-colors"
                            >
                                ✗ Cancel
                            </button>
                        </div>
                    </div>
                )}

                {/* Current model indicator */}
                <div className="text-[10px] text-neutral-600 mb-2 flex items-center gap-1">
                    <span>Using:</span>
                    <span className="text-cyan-500">{currentProviderLabel}</span>
                    <ChevronDown className="w-3 h-3" />
                    <span className="text-cyan-400">{model}</span>
                </div>
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
