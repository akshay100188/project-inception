import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getAuthHeader } from "../lib/supabase";
import { PlanOutput } from "../components/PlanOutput/PlanOutput";

type ProjectRecord = {
  id: string;
  status: string;
  raw_input: string;
  requirements?: Record<string, unknown>;
  plan?: {
    architecture?: Record<string, unknown>;
    tech_stack?: Record<string, unknown>;
    estimation?: Record<string, unknown>;
  };
};

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<ProjectRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    async function load() {
      try {
        const authHeader = await getAuthHeader();
        const res = await fetch(`${API_BASE}/api/projects/${id}`, {
          headers: { Authorization: authHeader },
        });
        if (!res.ok) throw new Error(`Failed to load project (${res.status})`);
        setProject(await res.json());
      } catch (err: unknown) {
        setFetchError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <span className="text-gray-500 text-sm">Loading plan...</span>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <span className="text-red-400 text-sm">{fetchError}</span>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <span className="text-red-400 text-sm">Project not found.</span>
      </div>
    );
  }

  const plan = project.plan ?? {};

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-sm text-gray-500 hover:text-gray-300 transition-colors">
            ← Dashboard
          </Link>
        </div>

        {plan.architecture || plan.tech_stack || plan.estimation ? (
          <PlanOutput
            requirements={project.requirements}
            architecture={plan.architecture as any}
            tech_stack={plan.tech_stack as any}
            estimation={plan.estimation as any}
          />
        ) : (
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-10 text-center space-y-2">
            <p className="text-gray-400">Plan is still being generated.</p>
            <p className="text-sm text-gray-600">Status: {project.status}</p>
          </div>
        )}
      </div>
    </div>
  );
}
