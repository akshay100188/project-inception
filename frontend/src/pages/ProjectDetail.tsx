import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getAuthHeader } from "../lib/supabase";
import { PlanOutput } from "../components/PlanOutput/PlanOutput";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    async function load() {
      const authHeader = await getAuthHeader();
      const res = await fetch(`${API_BASE}/api/projects/${id}`, {
        headers: { Authorization: authHeader },
      });
      setProject(await res.json());
      setLoading(false);
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
            architecture={plan.architecture}
            tech_stack={plan.tech_stack}
            estimation={plan.estimation}
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
