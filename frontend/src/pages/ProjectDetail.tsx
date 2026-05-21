import { useEffect, useState, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
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
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
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
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // Poll every 5s while plan is still generating
  useEffect(() => {
    if (!project || project.status === "complete" || project.status === "reviewing") return;
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, [project, load]);

  async function handleApprove() {
    if (!id) return;
    setSaving(true);
    try {
      const authHeader = await getAuthHeader();
      await fetch(`${API_BASE}/api/projects/${id}/checkpoint`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: authHeader },
        body: JSON.stringify({ action: "approve", checkpoint_name: "checkpoint_2" }),
      });
      await load();
    } finally {
      setSaving(false);
    }
  }

  async function handleReject() {
    if (!id) return;
    const authHeader = await getAuthHeader();
    await fetch(`${API_BASE}/api/projects/${id}/checkpoint`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: authHeader },
      body: JSON.stringify({ action: "reject", checkpoint_name: "checkpoint_2" }),
    });
    navigate("/");
  }

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
  const isReviewing = project.status === "reviewing";
  const hasPlan = plan.architecture || plan.tech_stack || plan.estimation;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-sm text-gray-500 hover:text-gray-300 transition-colors">
            ← Dashboard
          </Link>
        </div>

        {hasPlan ? (
          <div className="space-y-4">
            <PlanOutput
              requirements={project.requirements}
              architecture={plan.architecture as any}
              tech_stack={plan.tech_stack as any}
              estimation={plan.estimation as any}
              onSave={isReviewing ? handleApprove : undefined}
              reviewMode={isReviewing}
            />
            {isReviewing && (
              <div className="flex justify-end">
                <button
                  onClick={handleReject}
                  disabled={saving}
                  className="text-sm text-red-400 border border-red-900 px-4 py-2 rounded-lg hover:bg-red-900/20 transition-colors disabled:opacity-40"
                >
                  Reject & Discard
                </button>
              </div>
            )}
          </div>
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
