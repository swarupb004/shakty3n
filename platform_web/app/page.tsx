"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Terminal, Activity, Cpu, Box, Play } from "lucide-react";
import { motion } from "framer-motion";
import { api, cn } from "@/lib/utils";

interface Agent {
  id: string;
  name: string;
  status: string;
  provider: string;
  model: string;
  workspace: {
    artifact_count: number;
    approval_count: number;
  };
}

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  // Creation Form State
  const [newAgentName, setNewAgentName] = useState("");
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("gpt-4");

  const refresh = async () => {
    try {
      const data = await api.get("/api/dashboard");
      setAgents(data.agents || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  const createAgent = async () => {
    if (!newAgentName) return;
    try {
      await api.post("/api/agents", {
        name: newAgentName,
        provider: provider,
        model: model
      });
      setNewAgentName("");
      setShowModal(false);
      refresh();
    } catch (e) {
      alert("Failed to create agent. Ensure backend is running and keys are set.");
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-200 font-sans selection:bg-cyan-500/30">
      {/* Header */}
      <header className="border-b border-white/10 bg-neutral-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <Box className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-neutral-400">
              Shakty3n Platform
            </h1>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-white text-black rounded-full text-sm font-medium hover:bg-neutral-200 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Agent
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-semibold">Active Agents</h2>
          <div className="flex gap-2">
            <div className="px-3 py-1 rounded-full bg-green-500/10 text-green-400 text-xs border border-green-500/20 flex items-center gap-1">
              <Activity className="w-3 h-3" />
              System Online
            </div>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 rounded-xl bg-neutral-900/50 animate-pulse border border-white/5" />
            ))}
          </div>
        ) : agents.length === 0 ? (
          <div className="text-center py-20 border border-dashed border-white/10 rounded-2xl bg-neutral-900/20">
            <Cpu className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-400">No active agents</h3>
            <p className="text-neutral-500 mb-6">Spawn an autonomous agent to get started.</p>
            <button
              onClick={() => setShowModal(true)}
              className="text-cyan-400 hover:underline"
            >
              Create your first agent
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map((agent) => (
              <Link href={`/agent/${agent.id}`} key={agent.id}>
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="group relative p-6 rounded-2xl bg-neutral-900 border border-white/10 hover:border-cyan-500/50 transition-colors overflow-hidden"
                >
                  <div className="absolute top-0 right-0 p-4 opacity-50 group-hover:opacity-100 transition-opacity">
                    <Terminal className="w-5 h-5 text-neutral-500 group-hover:text-cyan-400" />
                  </div>

                  <div className="mb-4">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-lg font-semibold text-white">{agent.name}</h3>
                      <span className={cn(
                        "w-2 h-2 rounded-full",
                        agent.status === 'running' ? "bg-green-500 animate-pulse" :
                          agent.status === 'failed' ? "bg-red-500" : "bg-neutral-500"
                      )} />
                    </div>
                    <p className="text-xs text-neutral-500 uppercase tracking-wider font-mono">
                      {agent.provider} • {agent.model || "Default"}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mt-6">
                    <div className="bg-black/20 rounded-lg p-3">
                      <div className="text-2xl font-mono text-white">{agent.workspace.artifact_count}</div>
                      <div className="text-xs text-neutral-500">Artifacts</div>
                    </div>
                    <div className="bg-black/20 rounded-lg p-3">
                      <div className="text-2xl font-mono text-white">{agent.workspace.approval_count}</div>
                      <div className="text-xs text-neutral-500">Decisions</div>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center text-xs text-cyan-500 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                    Open Workspace <Play className="w-3 h-3 ml-1 fill-current" />
                  </div>
                </motion.div>
              </Link>
            ))}
          </div>
        )}
      </main>

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-neutral-900 border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl"
          >
            <h2 className="text-xl font-bold mb-4">Spawn New Agent</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-400 mb-1">Agent Name</label>
                <input
                  type="text"
                  value={newAgentName}
                  onChange={(e) => setNewAgentName(e.target.value)}
                  placeholder="e.g., Payment Service Builder"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-400 mb-1">AI Provider</label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="google">Google Gemini</option>
                  <option value="ollama">Ollama (Local)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-400 mb-1">Model</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500"
                >
                  {provider === 'openai' && (
                    <>
                      <option value="gpt-4">GPT-4</option>
                      <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                    </>
                  )}
                  {provider === 'anthropic' && (
                    <>
                      <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                      <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                    </>
                  )}
                  {provider === 'google' && (
                    <>
                      <option value="gemini-pro">Gemini Pro</option>
                      <option value="gemini-ultra">Gemini Ultra</option>
                    </>
                  )}
                  {provider === 'ollama' && (
                    <>
                      <option value="llama3">Llama 3</option>
                      <option value="qwen2.5-coder">Qwen 2.5 Coder</option>
                      <option value="deepseek-coder">DeepSeek Coder</option>
                    </>
                  )}
                </select>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm text-neutral-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={createAgent}
                  disabled={!newAgentName}
                  className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Spawn Agent
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
