import { useState } from "react";

type Feature = { feature: string; priority: "must-have" | "nice-to-have" };

type Requirements = {
  project_name?: string;
  problem_statement?: string;
  target_users?: string[];
  core_features?: Feature[];
  integrations?: string[];
  scale?: string;
  domain?: string;
};

type Props = {
  checkpoint: {
    title: string;
    requirements?: Requirements;
    clarification_questions?: string[];
  };
  onDecision: (action: "approve" | "edit" | "reject", edited?: object) => void;
};

const SCALE_COLORS: Record<string, string> = {
  MVP: "bg-green-900/40 text-green-300 border-green-800",
  small: "bg-blue-900/40 text-blue-300 border-blue-800",
  medium: "bg-yellow-900/40 text-yellow-300 border-yellow-800",
  large: "bg-red-900/40 text-red-300 border-red-800",
};

export function CheckpointModal({ checkpoint, onDecision }: Props) {
  const [editing, setEditing] = useState(false);
  const [editedText, setEditedText] = useState(
    JSON.stringify(checkpoint.requirements ?? {}, null, 2)
  );

  const req = checkpoint.requirements as Requirements | undefined;

  function handleApprove() {
    onDecision("approve");
  }

  function handleEdit() {
    if (editing) {
      try {
        const parsed = JSON.parse(editedText);
        onDecision("edit", parsed);
      } catch {
        alert("Invalid JSON — fix before submitting.");
      }
    } else {
      setEditing(true);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-800 shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-blue-400 font-mono">①</span>
            <div>
              <h2 className="text-base font-semibold text-white">{checkpoint.title}</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Review extracted requirements before architecture planning begins
              </p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 px-6 py-5 space-y-5">
          {editing ? (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                Edit Requirements JSON
              </p>
              <textarea
                className="w-full bg-gray-950 border border-gray-700 rounded-lg p-3 text-sm font-mono text-gray-200 resize-none h-64 focus:outline-none focus:border-blue-500"
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
              />
            </div>
          ) : (
            <>
              {/* Project name + meta */}
              {req && (
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center gap-2">
                    {req.project_name && (
                      <h3 className="text-lg font-bold text-white">{req.project_name}</h3>
                    )}
                    {req.domain && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-gray-400 border border-gray-700">
                        {req.domain}
                      </span>
                    )}
                    {req.scale && (
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${SCALE_COLORS[req.scale] ?? "bg-gray-800 text-gray-400 border-gray-700"}`}>
                        {req.scale}
                      </span>
                    )}
                  </div>

                  {req.problem_statement && (
                    <p className="text-sm text-gray-300 leading-relaxed">
                      {req.problem_statement}
                    </p>
                  )}

                  {req.target_users && req.target_users.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                        Target Users
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {req.target_users.map((u, i) => (
                          <span
                            key={i}
                            className="text-xs px-2.5 py-1 rounded-full bg-gray-800 text-gray-300 border border-gray-700"
                          >
                            {u}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {req.core_features && req.core_features.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                        Core Features
                      </p>
                      <div className="space-y-2">
                        {req.core_features.map((f, i) => (
                          <div key={i} className="flex items-center gap-2">
                            <span
                              className={`shrink-0 text-xs px-1.5 py-0.5 rounded font-medium ${
                                f.priority === "must-have"
                                  ? "bg-blue-900/50 text-blue-300"
                                  : "bg-gray-800 text-gray-500"
                              }`}
                            >
                              {f.priority === "must-have" ? "must" : "nice"}
                            </span>
                            <span className="text-sm text-gray-300">{f.feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {req.integrations && req.integrations.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                        Integrations
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {req.integrations.map((int, i) => (
                          <span
                            key={i}
                            className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400 font-mono"
                          >
                            {int}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {checkpoint.clarification_questions && checkpoint.clarification_questions.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                    Open Questions
                  </p>
                  <ul className="space-y-2">
                    {checkpoint.clarification_questions.map((q, i) => (
                      <li key={i} className="flex gap-2 text-sm text-gray-400">
                        <span className="text-blue-500 font-mono shrink-0">{i + 1}.</span>
                        {q}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-800 flex gap-3 justify-between shrink-0">
          <button
            onClick={() => onDecision("reject")}
            className="px-4 py-2 rounded-lg text-sm text-red-400 border border-red-900 hover:bg-red-900/20 transition-colors"
          >
            Start Over
          </button>
          <div className="flex gap-2">
            <button
              onClick={handleEdit}
              className="px-4 py-2 rounded-lg text-sm text-yellow-400 border border-yellow-900 hover:bg-yellow-900/20 transition-colors"
            >
              {editing ? "Submit Edits" : "Edit"}
            </button>
            <button
              onClick={handleApprove}
              className="px-5 py-2 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 transition-colors"
            >
              Approve & Continue →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
