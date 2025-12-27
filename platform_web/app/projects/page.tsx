"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Loader2, RefreshCw, Calendar, CheckCircle, XCircle, Clock, Zap } from "lucide-react";
import { motion } from "framer-motion";
import { api, cn } from "@/lib/utils";

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

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = async () => {
    try {
      setError(null);
      const data = await api.get("/api/projects");
      setProjects(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch projects");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
    // Poll every 5 seconds for updates
    const interval = setInterval(fetchProjects, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "done":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-red-500" />;
      case "planning":
      case "generating":
      case "validating":
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              Projects
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Manage and monitor your autonomous code generation projects
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={fetchProjects}
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors border border-gray-200 dark:border-gray-700"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <Link href="/projects/new">
              <button className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl">
                <Plus className="w-5 h-5" />
                New Project
              </button>
            </Link>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && projects.length === 0 && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          </div>
        )}

        {/* Empty State */}
        {!loading && projects.length === 0 && (
          <div className="text-center py-20">
            <Zap className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              No projects yet
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Create your first autonomous coding project to get started
            </p>
            <Link href="/projects/new">
              <button className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg">
                Create Project
              </button>
            </Link>
          </div>
        )}

        {/* Projects Grid */}
        {projects.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project, index) => (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Link href={`/projects/${project.id}`}>
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md hover:shadow-xl transition-all p-6 border border-gray-200 dark:border-gray-700 cursor-pointer group">
                    {/* Status Badge */}
                    <div className="flex items-center justify-between mb-4">
                      <span
                        className={cn(
                          "px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5",
                          getStatusColor(project.status)
                        )}
                      >
                        {getStatusIcon(project.status)}
                        {project.status}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {project.project_type}
                      </span>
                    </div>

                    {/* Description */}
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {project.description}
                    </h3>

                    {/* Metadata */}
                    <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        {new Date(project.created_at).toLocaleDateString()}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                          {project.provider}
                        </span>
                        {project.with_tests && (
                          <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
                            + tests
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Error Message */}
                    {project.error_message && (
                      <div className="mt-3 p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs text-red-600 dark:text-red-400 line-clamp-2">
                        {project.error_message}
                      </div>
                    )}
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
