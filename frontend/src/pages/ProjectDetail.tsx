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
  const [generatingPrototype, setGeneratingPrototype] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);

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

  async function openGeneratedHtml(endpoint: string, errorLabel: string, setLoading: (v: boolean) => void) {
    if (!id) return;
    setLoading(true);
    try {
      const authHeader = await getAuthHeader();
      const res = await fetch(`${API_BASE}/api/projects/${id}/${endpoint}`, {
        method: "POST",
        headers: { Authorization: authHeader },
      });
      if (!res.ok) throw new Error(`${errorLabel} failed (${res.status})`);
      const html = await res.text();
      const blob = new Blob([html], { type: "text/html" });
      window.open(URL.createObjectURL(blob), "_blank");
    } catch (err: any) {
      alert(`${errorLabel}: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  const handleGenerateReport = () =>
    openGeneratedHtml("report", "Report generation", setGeneratingReport);

  const handleGeneratePrototype = () =>
    openGeneratedHtml("prototype", "Prototype generation", setGeneratingPrototype);

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
            {/* Action bar */}
            <div className="rounded-xl border border-gray-800 bg-gray-900/60 px-4 py-3 flex flex-wrap items-center gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-500">Generate deliverables from this plan</p>
              </div>

              {/* Full planning report */}
              <button
                onClick={handleGenerateReport}
                disabled={generatingReport || generatingPrototype}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {generatingReport ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Generating report…
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Download Full Report (PDF)
                  </>
                )}
              </button>

              {/* App prototype */}
              <button
                onClick={handleGeneratePrototype}
                disabled={generatingPrototype || generatingReport}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-purple-300 border border-purple-800 bg-purple-950/40 hover:bg-purple-900/40 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {generatingPrototype ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Generating…
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    App Prototype
                  </>
                )}
              </button>

              {isReviewing && (
                <button
                  onClick={handleReject}
                  disabled={saving}
                  className="text-sm text-red-400 border border-red-900 px-4 py-2 rounded-lg hover:bg-red-900/20 transition-colors disabled:opacity-40"
                >
                  Reject & Discard
                </button>
              )}
            </div>
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
