import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAuthHeader } from "../lib/supabase";

type Project = {
  id: string;
  raw_input: string;
  status: string;
  created_at: string;
  requirements?: { project_name?: string; domain?: string };
  plan?: {
    architecture?: { pattern?: string };
    estimation?: { mvp_weeks?: number };
  };
};

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  drafting:   { label: "Drafting",   cls: "text-gray-400 bg-gray-800/60 border-gray-700" },
  clarifying: { label: "Clarifying", cls: "text-yellow-400 bg-yellow-900/30 border-yellow-800" },
  planning:   { label: "Planning",   cls: "text-blue-400 bg-blue-900/30 border-blue-800" },
  reviewing:  { label: "Reviewing",  cls: "text-purple-400 bg-purple-900/30 border-purple-800" },
  complete:   { label: "Complete",   cls: "text-green-400 bg-green-900/30 border-green-800" },
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const authHeader = await getAuthHeader();
        const res = await fetch(`${API_BASE}/api/projects/`, {
          headers: { Authorization: authHeader },
        });
        if (!res.ok) throw new Error(`Failed to load projects (${res.status})`);
        setProjects(await res.json());
      } catch (err: unknown) {
        setFetchError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Projects</h1>
            <p className="text-sm text-gray-500 mt-0.5">Your idea-to-plan history</p>
          </div>
          <Link
            to="/new"
            className="px-4 py-2 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 transition-colors"
          >
            + New Project
          </Link>
        </div>

        {fetchError ? (
          <div className="rounded-xl border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300">
            {fetchError}
          </div>
        ) : loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="rounded-xl border border-gray-800 bg-gray-900 px-5 py-4 animate-pulse">
                <div className="flex justify-between items-start">
                  <div className="space-y-2 flex-1">
                    <div className="h-4 bg-gray-800 rounded w-48" />
                    <div className="h-3 bg-gray-800 rounded w-72" />
                  </div>
                  <div className="h-5 bg-gray-800 rounded-full w-16" />
                </div>
              </div>
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-gray-800 bg-gray-900/50 p-16 text-center space-y-4">
            <div className="text-4xl text-gray-700">⬡</div>
            <div className="space-y-1">
              <p className="text-gray-300 font-medium">No projects yet</p>
              <p className="text-sm text-gray-600">Describe your idea and let agents build your plan</p>
            </div>
            <Link
              to="/new"
              className="inline-block mt-2 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
            >
              Start your first plan →
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {projects.map((p: Project) => {
              const badge = STATUS_BADGE[p.status] ?? STATUS_BADGE.drafting;
              const mvpWeeks = p.plan?.estimation?.mvp_weeks;
              const pattern = p.plan?.architecture?.pattern;
              const domain = p.requirements?.domain;

              return (
                <Link
                  key={p.id}
                  to={`/projects/${p.id}`}
                  className="block rounded-xl border border-gray-800 bg-gray-900 px-5 py-4 hover:border-gray-600 hover:bg-gray-800/50 transition-all"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-semibold text-white truncate">
                          {p.requirements?.project_name ?? "Untitled Project"}
                        </p>
                        {domain && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-500 border border-gray-700">
                            {domain}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 line-clamp-1">{p.raw_input}</p>
                      <div className="flex items-center gap-3 text-xs text-gray-600">
                        {pattern && <span>⬡ {pattern}</span>}
                        {mvpWeeks && <span>⏱ {mvpWeeks}w MVP</span>}
                        <span>{timeAgo(p.created_at)}</span>
                      </div>
                    </div>
                    <span className={`shrink-0 text-xs font-medium px-2.5 py-1 rounded-full border ${badge.cls}`}>
                      {badge.label}
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
