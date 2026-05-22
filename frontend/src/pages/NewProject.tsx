import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getAuthHeader } from "../lib/supabase";
import { useAgentStream } from "../hooks/useAgentStream";
import { CheckpointModal } from "../components/Checkpoint/CheckpointModal";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const EXAMPLE_IDEAS = [
  "A food delivery app for college campuses with group ordering",
  "A SaaS tool that turns Loom recordings into Notion docs automatically",
  "A mobile app for gym-goers to track progressive overload with AI coaching",
];

const ACCEPTED_TYPES = ".pdf,.txt,.docx";
const ACCEPTED_MIME = new Set([
  "application/pdf",
  "text/plain",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]);

const GENERATION_STAGES = [
  "Extracting your project requirements…",
  "Asking clarifying questions…",
  "Designing system architecture…",
  "Selecting technology stack…",
  "Estimating timeline & budget…",
];

export default function NewProject() {
  const navigate = useNavigate();
  const [rawInput, setRawInput] = useState("");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadedFilename, setUploadedFilename] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [stageIdx, setStageIdx] = useState(0);
  const [saving, setSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { agents, checkpoint, planData, isStreaming, isDone, error, startStream, clearCheckpoint } =
    useAgentStream();

  // Stop showing loading screen once planData arrives (SSE stream stays open at checkpoint_2)
  const isGenerating = !planData && !isDone && (isStreaming || Object.keys(agents).length > 0);

  // Cycle through stage labels while loading
  useEffect(() => {
    if (!isGenerating) return;
    const timer = setInterval(() => setStageIdx(i => (i + 1) % GENERATION_STAGES.length), 9000);
    return () => clearInterval(timer);
  }, [isGenerating]);

  // Navigate only on clean completion — stay on page if there was an error
  useEffect(() => {
    if (isDone && projectId && !error) {
      navigate(`/projects/${projectId}`);
    }
  }, [isDone, projectId, navigate, error]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!rawInput.trim()) return;

    const authHeader = await getAuthHeader();
    const res = await fetch(`${API_BASE}/api/projects/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: authHeader },
      body: JSON.stringify({ raw_input: rawInput }),
    });
    const project = await res.json();
    setProjectId(project.id);

    await startStream(project.id, rawInput);
  }

  async function postCheckpoint(checkpointName: string, action: string, edited?: object) {
    if (!projectId) return;
    const authHeader = await getAuthHeader();
    await fetch(`${API_BASE}/api/projects/${projectId}/checkpoint`, {
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

  const parseFile = useCallback(async (file: File) => {
    if (!ACCEPTED_MIME.has(file.type) && !file.name.match(/\.(pdf|txt|docx)$/i)) {
      setUploadError("Unsupported file type. Please upload a PDF, TXT, or DOCX file.");
      return;
    }
    setUploading(true);
    setUploadError(null);
    setUploadedFilename(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/api/parse-document`, {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail ?? "Upload failed");
      setRawInput(json.text);
      setUploadedFilename(json.filename);
    } catch (err: any) {
      setUploadError(err.message ?? "Failed to parse file");
    } finally {
      setUploading(false);
    }
  }, []);

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) parseFile(file);
    e.target.value = "";
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) parseFile(file);
  }

  const showForm = !isGenerating && !planData && !isDone && !error;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">

        {/* Form */}
        {showForm && (
          <>
            <div className="space-y-1">
              <h1 className="text-3xl font-bold tracking-tight">What are you building?</h1>
              <p className="text-gray-400">
                Describe your idea — agents will extract requirements, design architecture, and estimate costs.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <textarea
                className="w-full bg-gray-900 border border-gray-700 rounded-xl p-4 text-base text-white placeholder-gray-600 resize-none h-36 focus:outline-none focus:border-blue-500 transition-colors"
                placeholder="e.g. A food delivery app for college campuses..."
                value={rawInput}
                onChange={(e) => setRawInput(e.target.value)}
              />

              {/* File upload zone */}
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl border border-dashed cursor-pointer transition-colors select-none
                  ${dragOver
                    ? "border-blue-500 bg-blue-950/30 text-blue-300"
                    : "border-gray-700 bg-gray-900/40 text-gray-500 hover:border-gray-500 hover:text-gray-400"
                  }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPTED_TYPES}
                  className="hidden"
                  onChange={handleFileInput}
                />
                {uploading ? (
                  <>
                    <svg className="animate-spin h-4 w-4 shrink-0 text-blue-400" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    <span className="text-sm text-blue-400">Parsing file…</span>
                  </>
                ) : uploadedFilename ? (
                  <>
                    <svg className="h-4 w-4 shrink-0 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-sm text-green-400">{uploadedFilename} — text extracted</span>
                    <span className="ml-auto text-xs text-gray-600">click to replace</span>
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    <span className="text-sm">Upload requirements doc — PDF, TXT, or Word</span>
                    <span className="ml-auto text-xs text-gray-600">or drag & drop</span>
                  </>
                )}
              </div>

              {uploadError && <p className="text-xs text-red-400">{uploadError}</p>}

              <div className="flex flex-wrap gap-2">
                {EXAMPLE_IDEAS.map((idea) => (
                  <button
                    key={idea}
                    type="button"
                    onClick={() => setRawInput(idea)}
                    className="text-xs text-gray-400 border border-gray-700 rounded-full px-3 py-1 hover:border-gray-500 hover:text-gray-200 transition-colors"
                  >
                    {idea.slice(0, 45)}…
                  </button>
                ))}
              </div>

              <button
                type="submit"
                disabled={!rawInput.trim() || uploading}
                className="w-full py-3 rounded-xl font-semibold text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Start Planning →
              </button>
            </form>
          </>
        )}

        {/* Loading screen while agents are working */}
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

        {/* Error */}
        {error && (
          <div className="rounded-xl border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Plan review — checkpoint_2: show only the save action, nothing else */}
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

        {/* Checkpoint 1 modal — blocks until user approves requirements */}
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
