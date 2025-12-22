"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Editor from "@monaco-editor/react";
import dynamic from 'next/dynamic';
import { Folder, FileCode, Save, ChevronRight, RefreshCw, FolderPlus } from "lucide-react";
import { api, cn } from "@/lib/utils";
import { AgentChat } from "@/components/comp_chat";

// Dynamic import for Terminal (no SSR)
const AgentTerminal = dynamic(() => import("@/components/comp_terminal"), {
    ssr: false,
    loading: () => <div className="p-4 text-xs text-neutral-500">Initializing Terminal...</div>
});

// --- Types ---
interface FileNode {
    name: string;
    type: "file" | "directory";
    path: string;
}

type DashboardAgent = {
    id: string;
    name?: string;
};

type RecentAgent = {
    id: string;
    name: string;
    lastOpened: number;
};

const RECENT_AGENT_KEY = "shakty3n_recent_agents";

const loadRecentAgents = (): RecentAgent[] => {
    if (typeof window === "undefined") return [];
    try {
        const raw = localStorage.getItem(RECENT_AGENT_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch {
        return [];
    }
};

const persistRecentAgents = (agents: RecentAgent[]) => {
    if (typeof window === "undefined") return;
    localStorage.setItem(RECENT_AGENT_KEY, JSON.stringify(agents.slice(0, 5)));
};

// --- Icons ---
const FileIcon = ({ name }: { name: string }) => {
    if (name.endsWith(".py")) return <span className="text-yellow-400">🐍</span>;
    if (name.endsWith(".tsx")) return <span className="text-cyan-400">⚛️</span>;
    if (name.endsWith(".ts")) return <span className="text-blue-400">TS</span>;
    if (name.endsWith(".json")) return <span className="text-orange-400">{ }</span>;
    return <FileCode className="w-4 h-4 text-neutral-400" />;
};

export default function AgentWorkspace() {
    const { id } = useParams();
    const router = useRouter();
    const [agentName, setAgentName] = useState<string>("");
    const [files, setFiles] = useState<FileNode[]>([]);
    const [currentFile, setCurrentFile] = useState<string | null>(null);
    const [fileContent, setFileContent] = useState("");
    const [recentAgents, setRecentAgents] = useState<RecentAgent[]>([]);

    const recordRecentAgent = (name: string) => {
        const agentId = String(id);
        setRecentAgents((current) => {
            const updated: RecentAgent[] = [
                { id: agentId, name, lastOpened: Date.now() },
                ...current.filter((item) => item.id !== agentId),
            ].slice(0, 5);
            persistRecentAgents(updated);
            return updated;
        });
    };

    // Load Files
    const loadFiles = async () => {
        try {
            const data = await api.get(`/api/agents/${id}/workspace/files`);
            setFiles(Array.isArray(data) ? data : [data]);
        } catch (e) {
            console.error("Failed to load files", e);
        }
    };

    useEffect(() => {
        if (id) {
            loadFiles();
            const interval = setInterval(loadFiles, 10000);
            return () => clearInterval(interval);
        }
    }, [id]);

    useEffect(() => {
        if (!id) return;
        setRecentAgents(loadRecentAgents());
        const fetchName = async () => {
            try {
                const dashboard = await api.get("/api/dashboard");
                const match = (dashboard?.agents as DashboardAgent[] || []).find(
                    (agent) => String(agent.id) === String(id)
                );
                const resolvedName = match?.name || `Agent ${String(id).slice(0, 8)}`;
                setAgentName(resolvedName);
                recordRecentAgent(resolvedName);
            } catch {
                const fallback = `Agent ${String(id).slice(0, 8)}`;
                setAgentName(fallback);
                recordRecentAgent(fallback);
            }
        };
        fetchName();
    }, [id]);

    // Handlers
    const handleFileClick = async (file: FileNode) => {
        if (file.type === "directory") {
            return;
        }
        try {
            const data = await api.get(`/api/agents/${id}/workspace/content?path=${file.path}`);
            setFileContent(data.content);
            setCurrentFile(file.path);
        } catch (e) {
            console.error(e);
        }
    };

    const saveFile = async () => {
        if (!currentFile) return;
        try {
            await api.post(`/api/agents/${id}/workspace/content?path=${currentFile}`, {
                content: fileContent
            });
            alert("Saved!");
        } catch (e) {
            alert("Error saving file");
        }
    };

    const createFolder = async () => {
        const name = prompt("Folder name:");
        if (!name) return;
        try {
            await api.post(`/api/agents/${id}/workspace/directory`, {
                path: name
            });
            loadFiles();
        } catch (e) { alert("Failed to create folder"); }
    };

    return (
        <div className="flex flex-col h-screen bg-black text-neutral-300 overflow-hidden font-sans">
            <div className="h-12 border-b border-white/10 bg-neutral-900/70 px-3 flex items-center gap-2 overflow-x-auto">
                <span className="text-[11px] uppercase text-neutral-500 font-semibold tracking-wide">Recent Projects</span>
                {recentAgents.map((agent) => (
                    <button
                        key={agent.id}
                        onClick={() => router.push(`/agent/${agent.id}`)}
                        className={cn(
                            "px-3 py-1 rounded-full text-xs border transition-colors whitespace-nowrap",
                            String(agent.id) === String(id)
                                ? "border-cyan-500 text-cyan-300 bg-cyan-500/10"
                                : "border-white/10 text-neutral-300 hover:border-cyan-500/60 hover:text-cyan-200"
                        )}
                        title={agent.name}
                    >
                        {agent.name}
                    </button>
                ))}
                {recentAgents.length === 0 && (
                    <span className="text-xs text-neutral-600">Open a project to pin it here</span>
                )}
            </div>
            <div className="flex flex-1 overflow-hidden">
                {/* Sidebar: File Explorer */}
                <div className="w-64 border-r border-white/10 flex flex-col bg-neutral-900/50 flex-shrink-0">
                    <div className="h-10 border-b border-white/10 flex items-center justify-between px-3 font-semibold text-xs tracking-wide bg-neutral-900">
                        <span>EXPLORER</span>
                        <div className="flex gap-1">
                            <button onClick={createFolder} className="p-1 hover:bg-white/10 rounded" title="New Folder">
                                <FolderPlus className="w-3.5 h-3.5" />
                            </button>
                            <button onClick={loadFiles} className="p-1 hover:bg-white/10 rounded" title="Refresh">
                                <RefreshCw className="w-3.5 h-3.5" />
                            </button>
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-1">
                        {files.map((file, idx) => (
                            <div
                                key={idx}
                                className={cn(
                                    "flex items-center gap-2 px-2 py-1 rounded cursor-pointer text-sm select-none transition-colors truncate",
                                    currentFile === file.path ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30" : "hover:bg-white/5",
                                    file.type === "directory" ? "font-bold text-neutral-400" : "text-neutral-300"
                                )}
                                style={{ paddingLeft: `${(file.path.split('/').length - 1) * 12 + 8}px` }}
                                onClick={() => handleFileClick(file)}
                            >
                                {file.type === "directory" ? (
                                    <Folder className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                                ) : (
                                    <FileIcon name={file.name} />
                                )}
                                <span className="truncate">{file.name}</span>
                            </div>
                        ))}
                        {files.length === 0 && (
                            <div className="text-xs text-neutral-500 text-center mt-4">Empty Workspace</div>
                        )}
                    </div>
                </div>

                {/* Main Center Area: Editor + Terminal */}
                <div className="flex-1 flex flex-col min-w-0 bg-neutral-900">

                    {/* Editor Toolbar */}
                    <div className="h-10 border-b border-white/10 flex items-center justify-between px-4 bg-neutral-900">
                        <div className="flex items-center gap-2 text-xs">
                            <span className="text-neutral-500">{currentFile ? 'Editing' : 'Workspace'}</span>
                            <ChevronRight className="w-3 h-3 text-neutral-700" />
                            <span className="text-white font-mono">
                                {currentFile || (agentName ? `${agentName} - No file open` : "No file open")}
                            </span>
                        </div>
                        <div>
                            <button
                                onClick={saveFile}
                                disabled={!currentFile}
                                className="flex items-center gap-2 px-3 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 text-xs rounded border border-white/10 disabled:opacity-50 transition-colors"
                            >
                                <Save className="w-3 h-3" /> Save Changes
                            </button>
                        </div>
                    </div>

                    {/* Editor */}
                    <div className="flex-1 relative">
                        {currentFile ? (
                            <Editor
                                height="100%"
                                theme="vs-dark"
                                path={currentFile}
                                defaultLanguage={currentFile.endsWith("py") ? "python" : "javascript"}
                                value={fileContent}
                                onChange={(val) => setFileContent(val || "")}
                                options={{
                                    minimap: { enabled: false },
                                    fontSize: 13,
                                    padding: { top: 10 },
                                    scrollBeyondLastLine: false
                                }}
                            />
                        ) : (
                            <div className="absolute inset-0 flex items-center justify-center text-neutral-700 bg-[#1e1e1e]">
                                <div className="text-center">
                                    <FileCode className="w-12 h-12 mx-auto mb-4 opacity-20" />
                                    <p className="text-sm">Select a file from the explorer</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Terminal Panel */}
                    <div className="h-[250px] bg-black border-t border-white/10 flex flex-col">
                        <div className="flex items-center justify-between px-3 py-1 bg-neutral-900/50 border-b border-white/5">
                            <span className="text-[10px] uppercase font-bold text-neutral-500 tracking-wider">Terminal Output</span>
                        </div>
                        <div className="flex-1 p-2 overflow-hidden">
                            <AgentTerminal agentId={String(id)} />
                        </div>
                    </div>
                </div>

                {/* Right Sidebar: Chat */}
                <div className="w-[350px] border-l border-white/10 bg-neutral-900 flex-shrink-0">
                    <AgentChat agentId={String(id)} />
                </div>
            </div>
        </div>
    );
}
