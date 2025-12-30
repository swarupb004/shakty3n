"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Loader2, Sparkles } from "lucide-react";
import { api } from "@/lib/utils";

const PROJECT_TYPES = [
  { value: "web-react", label: "React Web App", description: "Modern web application with React" },
  { value: "web-vue", label: "Vue Web App", description: "Progressive web app with Vue.js" },
  { value: "web-angular", label: "Angular Web App", description: "Enterprise web app with Angular" },
  { value: "web-svelte", label: "Svelte Web App", description: "Lightweight web app with Svelte" },
  { value: "web-nextjs", label: "Next.js App", description: "Full-stack React framework" },
  { value: "android", label: "Android App", description: "Native Android application" },
  { value: "android-kotlin", label: "Android (Kotlin)", description: "Android app with Kotlin" },
  { value: "android-java", label: "Android (Java)", description: "Android app with Java" },
  { value: "ios", label: "iOS App", description: "Native iOS application with Swift" },
  { value: "flutter", label: "Flutter App", description: "Cross-platform mobile app" },
  { value: "desktop-electron", label: "Electron Desktop", description: "Desktop app with Electron" },
  { value: "desktop-python", label: "Python Desktop", description: "Desktop app with Python/tkinter" },
];

const AI_PROVIDERS = [
  { value: "openai", label: "OpenAI", models: ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"] },
  { value: "anthropic", label: "Anthropic", models: ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"] },
  { value: "google", label: "Google", models: ["gemini-3.0-pro", "gemini-pro"] },
  { value: "ollama", label: "Ollama (Local)", models: ["qwen3-coder", "qwen2.5-coder:7b", "deepseek-coder", "codellama", "llama3"] },
];

export default function NewProjectPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [description, setDescription] = useState("");
  const [projectType, setProjectType] = useState("web-react");
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("gpt-4");
  const [withTests, setWithTests] = useState(false);
  const [validate, setValidate] = useState(false);

  const selectedProvider = AI_PROVIDERS.find((p) => p.value === provider);
  const [availableModels, setAvailableModels] = useState<string[]>([]);

  // Fetch models dynamically
  useEffect(() => {
    async function fetchModels() {
      if (provider === 'ollama') {
        try {
          const res = await api.get(`/api/providers/${provider}/models`);
          if (res.models && res.models.length > 0) {
            setAvailableModels(res.models);
            if (!res.models.includes(model)) {
              setModel(res.models[0]);
            }
            return;
          }
        } catch (e) {
          console.error("Failed to fetch dynamic models", e);
        }
      }
      // Fallback to static list
      const staticList = AI_PROVIDERS.find(p => p.value === provider)?.models || [];
      setAvailableModels(staticList);
      if (staticList.length > 0 && !staticList.includes(model)) {
        setModel(staticList[0]);
      }
    }
    fetchModels();
  }, [provider]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const project = await api.post("/api/projects", {
        description,
        project_type: projectType,
        provider,
        model,
        with_tests: withTests,
        validate_code: validate,
      });

      // Redirect to project detail page
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/projects">
            <button className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-4">
              <ArrowLeft className="w-4 h-4" />
              Back to Projects
            </button>
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Create New Project
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Describe your project and let AI build it autonomously
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 border border-gray-200 dark:border-gray-700">
          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}

          {/* Description */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
              Project Description *
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="E.g., A todo list application with user authentication, categories, and priority levels"
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
              rows={4}
              required
            />
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              Be specific about features, functionality, and requirements
            </p>
          </div>

          {/* Project Type */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
              Project Type *
            </label>
            <select
              value={projectType}
              onChange={(e) => setProjectType(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
              required
            >
              {PROJECT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label} - {type.description}
                </option>
              ))}
            </select>
          </div>

          {/* AI Provider */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
              AI Provider *
            </label>
            <select
              value={provider}
              onChange={(e) => {
                setProvider(e.target.value);
                const newProvider = AI_PROVIDERS.find((p) => p.value === e.target.value);
                if (newProvider) {
                  setModel(newProvider.models[0]);
                }
              }}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
              required
            >
              {AI_PROVIDERS.map((prov) => (
                <option key={prov.value} value={prov.value}>
                  {prov.label}
                </option>
              ))}
            </select>
          </div>

          {/* Model */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
              Model
            </label>
            <div className="relative">
              <input
                type="text"
                list="model-options"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="Select or type model name..."
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
              />
              <datalist id="model-options">
                {availableModels.map((m) => (
                  <option key={m} value={m} />
                ))}
              </datalist>
            </div>
          </div>

          {/* Options */}
          <div className="mb-8 space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="with-tests"
                checked={withTests}
                onChange={(e) => setWithTests(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
              />
              <label htmlFor="with-tests" className="ml-3 text-sm text-gray-900 dark:text-white">
                Generate tests (unit and integration tests)
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="validate"
                checked={validate}
                onChange={(e) => setValidate(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
              />
              <label htmlFor="validate" className="ml-3 text-sm text-gray-900 dark:text-white">
                Validate generated code (syntax, structure, dependencies)
              </label>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !description}
            className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed text-lg font-semibold"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Creating Project...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Create Project
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
