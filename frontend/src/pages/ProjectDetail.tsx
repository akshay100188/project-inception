import { useEffect, useState, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { getAuthHeader } from "../lib/supabase";
import { PlanOutput } from "../components/PlanOutput/PlanOutput";
import { CheckpointModal } from "../components/Checkpoint/CheckpointModal";
import { useAgentStream } from "../hooks/useAgentStream";
import { track } from "../lib/analytics";

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

const GENERATION_STAGES = [
  "Extracting your project requirements…",
  "Asking clarifying questions…",
  "Designing system architecture…",
  "Selecting technology stack…",
  "Estimating timeline & budget…",
];

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [generatingPrototype, setGeneratingPrototype] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [stageIdx, setStageIdx] = useState(0);
  const [streamActive, setStreamActive] = useState(false);
  const [retryError, setRetryError] = useState<string | null>(null);

  const { checkpoint, planData, isDone, error: streamError, startStream, clearCheckpoint } =
    useAgentStream();

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

  // After stream completes successfully, reload the project to get saved data
  useEffect(() => {
    if (isDone && !streamError) {
      load();
    }
  }, [isDone, streamError, load]);

  // Cycle through stage labels during generation
  useEffect(() => {
    if (!streamActive) return;
    const timer = setInterval(() => setStageIdx(i => (i + 1) % GENERATION_STAGES.length), 9000);
    return () => clearInterval(timer);
  }, [streamActive]);

  async function handleRetry() {
    if (!project) return;
    setRetryError(null);
    setStreamActive(true);
    try {
      await startStream(project.id, project.raw_input);
    } catch (err: any) {
      setRetryError(err.message ?? "Something went wrong. Please try again.");
      setStreamActive(false);
    }
  }

  async function postCheckpoint(checkpointName: string, action: string, edited?: object) {
    if (!id) return;
    const authHeader = await getAuthHeader();
    await fetch(`${API_BASE}/api/projects/${id}/checkpoint`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: authHeader },
      body: JSON.stringify({ action, checkpoint_name: checkpointName, edited_content: edited }),
    });
  }

  async function handleCheckpoint1Decision(action: "approve" | "edit" | "reject", edited?: object) {
    clearCheckpoint();
    await postCheckpoint("checkpoint_1", action, edited);
    if (action === "reject") navigate("/");
  }

  async function handleApprovePlan() {
    setSaving(true);
    try {
      await postCheckpoint("checkpoint_2", "approve");
    } finally {
      setSaving(false);
    }
  }

  async function handleRejectPlan() {
    await postCheckpoint("checkpoint_2", "reject");
    navigate("/");
  }

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

  async function downloadHtml(
    endpoint: string,
    filename: string,
    errorLabel: string,
    setLoad: (v: boolean) => void,
  ) {
    if (!id) return;
    setLoad(true);
    try {
      const authHeader = await getAuthHeader();
      const res = await fetch(`${API_BASE}/api/projects/${id}/${endpoint}`, {
        method: "POST",
        headers: { Authorization: authHeader },
      });
      if (!res.ok) throw new Error(`${errorLabel} failed (${res.status})`);
      const html = await res.text();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([html], { type: "text/html" }));
      a.download = filename;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 60_000);
    } catch (err: any) {
      alert(`${errorLabel}: ${err.message}`);
    } finally {
      setLoad(false);
    }
  }

  const handleGenerateReport = () => {
    track("report_downloaded", { project_id: id });
    downloadHtml("report", "project-plan-report.html", "Report generation", setGeneratingReport);
  };

  const handleGeneratePrototype = () => {
    track("prototype_downloaded", { project_id: id });
    downloadHtml("prototype", "app-prototype.html", "Prototype generation", setGeneratingPrototype);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <span className="text-gray-500 text-sm">Loading…</span>
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
  const isComplete = project.status === "complete";
  const hasPlan = !!(plan.architecture || plan.tech_stack || plan.estimation);

  // Only show the generating screen when we actively started a stream
  const isGenerating = streamActive && !planData && !isDone && !streamError;
  const displayError = streamError ?? retryError;

  // A draft/failed project that isn't currently streaming — show retry card
  const isDraft = !isReviewing && !isComplete && !streamActive;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
        <Link to="/" className="text-sm text-gray-500 hover:text-gray-300 transition-colors">
          ← Dashboard
        </Link>

        {/* Draft / failed project — show retry card */}
        {isDraft && (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Resume Project</h1>
              <p className="text-gray-400 text-sm mt-1">This project hasn't been fully planned yet. Generate the plan below.</p>
            </div>

            <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6 space-y-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Your Idea</p>
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{project.raw_input}</p>
            </div>

            {displayError && (
              <div className="rounded-xl border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300">
                {displayError}
              </div>
            )}

            <button
              onClick={handleRetry}
              className="w-full py-3 rounded-xl font-semibold text-white bg-blue-600 hover:bg-blue-500 transition-colors"
            >
              Generate Plan →
            </button>
          </div>
        )}

        {/* Generating — stream is active */}
        {isGenerating && (
          <div className="rounded-2xl border border-gray-800 bg-gray-900 p-16 text-center space-y-8">
            <div className="flex justify-center">
              <div className="w-24 h-24 rounded-3xl bg-indigo-950/60 border border-indigo-800/40 flex items-center justify-center">
                <svg className="h-12 w-12 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
                </svg>
              </div>
            </div>

            <div className="space-y-2">
              <h2 className="text-2xl font-semibold text-white">Generating your project plan</h2>
              <p className="text-gray-500 text-sm">This typically takes 3–5 minutes. Please keep this tab open.</p>
            </div>

            <div className="flex items-center justify-center gap-2 text-sm text-indigo-400 min-h-[1.5rem]">
              <svg className="animate-spin h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span>{GENERATION_STAGES[stageIdx]}</span>
            </div>

            <div className="flex justify-center gap-2">
              {GENERATION_STAGES.map((_, i) => (
                <div
                  key={i}
                  className={`h-1 rounded-full transition-all duration-500 ${
                    i === stageIdx ? "w-6 bg-indigo-500" : "w-2 bg-gray-700"
                  }`}
                />
              ))}
            </div>
          </div>
        )}

        {/* Stream error */}
        {streamActive && displayError && (
          <div className="space-y-4">
            <div className="rounded-xl border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300">
              {displayError}
            </div>
            <button
              onClick={() => { setStreamActive(false); setRetryError(null); }}
              className="text-sm text-gray-400 hover:text-gray-200 transition-colors"
            >
              ← Try again
            </button>
          </div>
        )}

        {/* Plan ready to save — from live stream reaching checkpoint_2 */}
        {planData && (
          <div className="rounded-2xl border border-amber-900/40 bg-amber-950/20 px-8 py-7 flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="h-2.5 w-2.5 rounded-full bg-amber-400 animate-pulse flex-shrink-0" />
              <p className="text-base font-semibold text-white">Your plan is ready to save</p>
            </div>
            <button
              onClick={handleRejectPlan}
              className="text-sm text-gray-500 border border-gray-700 px-4 py-2 rounded-lg hover:bg-gray-800/40 transition-colors"
            >
              Discard
            </button>
            <button
              onClick={handleApprovePlan}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Saving…
                </>
              ) : (
                "Save Plan & Continue →"
              )}
            </button>
          </div>
        )}

        {/* Reviewing — user navigated here before approving from NewProject */}
        {isReviewing && hasPlan && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
              <p className="text-sm text-amber-400 font-medium">Your plan is ready for review</p>
            </div>

            <PlanOutput
              requirements={project.requirements}
              architecture={plan.architecture as any}
              tech_stack={plan.tech_stack as any}
              estimation={plan.estimation as any}
              onSave={undefined}
              reviewMode={false}
            />

            <div className="rounded-xl border border-amber-900/40 bg-amber-950/20 px-4 py-4 flex flex-wrap items-center gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white">Ready to save this plan?</p>
                <p className="text-xs text-gray-500 mt-0.5">Saving unlocks report & prototype generation</p>
              </div>
              <button
                onClick={handleReject}
                className="text-sm text-gray-500 border border-gray-800 px-3 py-1.5 rounded-lg hover:bg-gray-800/40 transition-colors"
              >
                Discard
              </button>
              <button
                onClick={handleApprove}
                disabled={saving}
                className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {saving ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Saving…
                  </>
                ) : (
                  "Save Plan & Continue →"
                )}
              </button>
            </div>
          </div>
        )}

        {/* Complete — show plan + download deliverables */}
        {isComplete && hasPlan && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-emerald-400" />
              <p className="text-sm text-emerald-400 font-medium">Plan saved — generate your deliverables below</p>
            </div>

            <PlanOutput
              requirements={project.requirements}
              architecture={plan.architecture as any}
              tech_stack={plan.tech_stack as any}
              estimation={plan.estimation as any}
              onSave={undefined}
              reviewMode={false}
            />

            <div className="rounded-xl border border-gray-800 bg-gray-900/60 px-5 py-5 space-y-4">
              <div>
                <p className="text-sm font-semibold text-white">Generate deliverables</p>
                <p className="text-xs text-gray-500 mt-0.5">Download AI-generated outputs based on your approved plan</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  onClick={handleGenerateReport}
                  disabled={generatingReport || generatingPrototype}
                  className="flex flex-col items-start gap-2 p-4 rounded-xl border border-indigo-800/50 bg-indigo-950/40 hover:bg-indigo-950/60 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-left"
                >
                  <div className="flex items-center gap-2">
                    {generatingReport ? (
                      <svg className="animate-spin h-5 w-5 text-indigo-400" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    )}
                    <span className="text-sm font-semibold text-white">
                      {generatingReport ? "Generating report…" : "Download Planning Report"}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 leading-relaxed">
                    19-section HTML report — architecture, timelines, budget & risk analysis. Takes ~3–4 minutes to generate. Open in browser to print as PDF.
                  </p>
                </button>

                <button
                  onClick={handleGeneratePrototype}
                  disabled={generatingPrototype || generatingReport}
                  className="flex flex-col items-start gap-2 p-4 rounded-xl border border-purple-800/50 bg-purple-950/40 hover:bg-purple-950/60 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-left"
                >
                  <div className="flex items-center gap-2">
                    {generatingPrototype ? (
                      <svg className="animate-spin h-5 w-5 text-purple-400" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    )}
                    <span className="text-sm font-semibold text-white">
                      {generatingPrototype ? "Generating prototype…" : "Download App Prototype"}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 leading-relaxed">
                    5-screen wireframe document — all key app views with realistic sample data. Takes ~2–3 minutes to generate.
                  </p>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Checkpoint 1 modal */}
        {checkpoint && (
          <CheckpointModal
            checkpoint={checkpoint as any}
            onDecision={handleCheckpoint1Decision}
          />
        )}
      </div>
    </div>
  );
}
