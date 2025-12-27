"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Loader2, 
  Download, 
  RotateCcw, 
  Trash2, 
  CheckCircle, 
  XCircle, 
  Clock,
  Calendar,
  Cpu,
  FileCode
} from "lucide-react";
import { api, createEventSource, cn } from "@/lib/utils";

interface Project {
  id: string;
  description: string;
  project_type: string;
  provider: string;
  model: string | null;
  status: string;
  with_tests: boolean;
  validate_code: boolean;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  artifact_path: string | null;
  error_message: string | null;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  
  const [project, setProject] = useState<Project | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const logsEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Scroll to bottom of logs
  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  // Fetch project metadata
  const fetchProject = async () => {
    try {
      const data = await api.get(`/api/projects/${projectId}`);
      setProject(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch project");
    } finally {
      setLoading(false);
    }
  };

  // Set up SSE for logs
  useEffect(() => {
    fetchProject();

    // Set up log streaming
    const eventSource = createEventSource(`/api/projects/${projectId}/logs`);
    eventSourceRef.current = eventSource;

    eventSource.addEventListener("log", (event) => {
      setLogs((prev) => [...prev, event.data]);
    });

    eventSource.addEventListener("status", (event) => {
      // Final status received, close connection
      eventSource.close();
      fetchProject(); // Refresh project metadata
    });

    eventSource.addEventListener("error", (event: any) => {
      console.error("SSE error:", event);
      eventSource.close();
    });

    // Poll for project updates
    const interval = setInterval(fetchProject, 5000);

    return () => {
      eventSource.close();
      clearInterval(interval);
    };
  }, [projectId]);

  const handleDownload = () => {
    window.open(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/projects/${projectId}/artifact`, "_blank");
  };

  const handleRetry = async () => {
    try {
      await api.post(`/api/projects/${projectId}/retry`, {});
      setLogs([]);
      fetchProject();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to retry project");
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this project?")) return;
    
    try {
      await api.delete(`/api/projects/${projectId}`);
      router.push("/projects");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete project");
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "done":
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case "failed":
        return <XCircle className="w-6 h-6 text-red-500" />;
      case "planning":
      case "generating":
      case "validating":
        return <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-6 h-6 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "done":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "failed":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      case "planning":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200";
      case "generating":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "validating":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Project not found</h2>
          <Link href="/projects">
            <button className="text-blue-600 dark:text-blue-400 hover:underline">
              Back to Projects
            </button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/projects">
            <button className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-4">
              <ArrowLeft className="w-4 h-4" />
              Back to Projects
            </button>
          </Link>
          
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                {getStatusIcon(project.status)}
                <span
                  className={cn(
                    "px-3 py-1 rounded-full text-sm font-semibold",
                    getStatusColor(project.status)
                  )}
                >
                  {project.status}
                </span>
              </div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                {project.description}
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                {project.project_type} • {project.provider} {project.model ? `(${project.model})` : ""}
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              {project.status === "done" && project.artifact_path && (
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
              )}
              {project.status === "failed" && (
                <button
                  onClick={handleRetry}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <RotateCcw className="w-4 h-4" />
                  Retry
                </button>
              )}
              <button
                onClick={handleDelete}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Project Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3 mb-2">
              <Calendar className="w-5 h-5 text-gray-500" />
              <span className="text-sm font-semibold text-gray-900 dark:text-white">Created</span>
            </div>
            <p className="text-gray-600 dark:text-gray-400">
              {new Date(project.created_at).toLocaleString()}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3 mb-2">
              <Cpu className="w-5 h-5 text-gray-500" />
              <span className="text-sm font-semibold text-gray-900 dark:text-white">Provider</span>
            </div>
            <p className="text-gray-600 dark:text-gray-400">
              {project.provider} {project.model && `(${project.model})`}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3 mb-2">
              <FileCode className="w-5 h-5 text-gray-500" />
              <span className="text-sm font-semibold text-gray-900 dark:text-white">Options</span>
            </div>
            <div className="flex gap-2">
              {project.with_tests && (
                <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
                  Tests
                </span>
              )}
              {project.validate_code && (
                <span className="text-xs bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 px-2 py-1 rounded">
                  Validate
                </span>
              )}
              {!project.with_tests && !project.validate_code && (
                <span className="text-gray-500 dark:text-gray-400 text-sm">None</span>
              )}
            </div>
          </div>
        </div>

        {/* Logs */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="bg-gray-100 dark:bg-gray-900 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Execution Logs</h2>
          </div>
          <div className="p-6 h-96 overflow-y-auto bg-gray-50 dark:bg-gray-900 font-mono text-sm">
            {logs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                Waiting for logs...
              </div>
            ) : (
              <div className="space-y-1">
                {logs.map((log, index) => (
                  <div key={index} className="text-gray-800 dark:text-gray-200">
                    {log}
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Error Details */}
        {project.error_message && (
          <div className="mt-6 bg-red-50 dark:bg-red-900/20 rounded-lg p-6 border border-red-200 dark:border-red-800">
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-200 mb-2">Error Details</h3>
            <p className="text-red-800 dark:text-red-300 font-mono text-sm whitespace-pre-wrap">
              {project.error_message}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
