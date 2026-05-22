import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getAuthHeader } from "../lib/supabase";
import { useAgentStream } from "../hooks/useAgentStream";
import { AgentPanel } from "../components/AgentPanel/AgentPanel";
import { CheckpointModal } from "../components/Checkpoint/CheckpointModal";
import { PlanOutput } from "../components/PlanOutput/PlanOutput";

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

export default function NewProject() {
  const navigate = useNavigate();
  const [rawInput, setRawInput] = useState("");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadedFilename, setUploadedFilename] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { agents, checkpoint, planData, isStreaming, isDone, error, startStream, clearCheckpoint } =
    useAgentStream();

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

  // Checkpoint 1: truly blocks server — approve/edit unblocks Phase 2 agents
  async function handleCheckpoint1Decision(action: "approve" | "edit" | "reject", edited?: object) {
    clearCheckpoint();                          // dismiss modal immediately
    await postCheckpoint("checkpoint_1", action, edited);
    if (action === "reject") navigate("/");
    // approve/edit: graph resumes, Phase 2 agents stream in
  }

  // Checkpoint 2: truly blocks server — approve triggers DB save then "done" fires
  async function handleApprovePlan() {
    await postCheckpoint("checkpoint_2", "approve");
    // isDone useEffect above handles navigation
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

  const showForm = !isStreaming && !isDone && Object.keys(agents).length === 0;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
        {/* Header */}
        {showForm && (
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight">What are you building?</h1>
            <p className="text-gray-400">
              Describe your idea — agents will extract requirements, design architecture, and estimate costs.
            </p>
          </div>
        )}

        {/* Input form */}
        {showForm && (
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

            {uploadError && (
              <p className="text-xs text-red-400">{uploadError}</p>
            )}

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
        )}

        {/* Agent pipeline */}
        <AgentPanel agents={agents} isStreaming={isStreaming} />

        {/* Error */}
        {error && (
          <div className="rounded-xl border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Plan review — shown when checkpoint_2 event fires (stream paused) */}
        {planData && (
          <div className="space-y-4">
            <PlanOutput
              requirements={planData.requirements as any}
              architecture={planData.architecture as any}
              tech_stack={planData.tech_stack as any}
              estimation={planData.estimation as any}
              onSave={handleApprovePlan}
              reviewMode={true}
            />
            <div className="flex justify-end">
              <button
                onClick={handleRejectPlan}
                className="text-sm text-red-400 border border-red-900 px-4 py-2 rounded-lg hover:bg-red-900/20 transition-colors"
              >
                Reject & Restart
              </button>
            </div>
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
