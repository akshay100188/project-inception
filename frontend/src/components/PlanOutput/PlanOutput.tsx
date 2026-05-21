type Architecture = {
  pattern: string;
  description: string;
  components: { name: string; role: string; tech_hint: string }[];
  data_flow: string;
  key_decisions: string[];
  future_evolution: string;
};

type TechStack = {
  layers: {
    frontend?: { name: string; rationale: string; key_libs?: string[] };
    backend?: { name: string; rationale: string; key_libs?: string[] };
    database?: { name: string; rationale: string; schema_hint?: string };
    auth?: { name: string; rationale: string };
    infrastructure?: { name: string; rationale: string };
    mobile?: { name: string; rationale: string } | null;
  };
  alternatives?: { layer: string; name: string; tradeoff: string }[];
};

type Estimation = {
  mvp_weeks: number;
  full_product_weeks: number;
  recommended_team: { size: number; roles: string[] };
  phases: { name: string; weeks: number; deliverables: string[] }[];
  cost_range: { mvp_low: number; mvp_high: number; currency: string; basis: string };
  confidence: string;
  risks: string[];
};

type Props = {
  requirements?: Record<string, unknown>;
  architecture?: Architecture;
  tech_stack?: TechStack;
  estimation?: Estimation;
  onSave?: () => void;
  reviewMode?: boolean;
};

const PATTERN_COLORS: Record<string, string> = {
  monolith: "bg-blue-900/40 text-blue-300 border-blue-800",
  microservices: "bg-purple-900/40 text-purple-300 border-purple-800",
  serverless: "bg-green-900/40 text-green-300 border-green-800",
  jamstack: "bg-yellow-900/40 text-yellow-300 border-yellow-800",
  "event-driven": "bg-orange-900/40 text-orange-300 border-orange-800",
};

const CONFIDENCE_COLORS: Record<string, string> = {
  low: "text-red-400",
  medium: "text-yellow-400",
  high: "text-green-400",
};

const STACK_LAYER_ICONS: Record<string, string> = {
  frontend: "◈",
  backend: "⬡",
  database: "◉",
  auth: "◎",
  infrastructure: "△",
  mobile: "◻",
};

function fmt(n: number) {
  return n >= 1000 ? `$${(n / 1000).toFixed(0)}k` : `$${n}`;
}

function buildMarkdown(
  requirements: Record<string, unknown> | undefined,
  architecture: Architecture | undefined,
  tech_stack: TechStack | undefined,
  estimation: Estimation | undefined,
): string {
  const req = requirements as any;
  const lines: string[] = [];

  lines.push(`# ${req?.project_name ?? "Project Plan"}`);
  if (req?.domain) lines.push(`**Domain:** ${req.domain}  |  **Scale:** ${req?.scale ?? "—"}`);
  lines.push("");

  if (req?.problem_statement) {
    lines.push("## Problem Statement");
    lines.push(req.problem_statement);
    lines.push("");
  }

  if (architecture) {
    lines.push("## Architecture");
    lines.push(`**Pattern:** ${architecture.pattern}`);
    lines.push(architecture.description ?? "");
    lines.push("");
    if (architecture.components?.length) {
      lines.push("### Components");
      architecture.components.forEach((c) => lines.push(`- **${c.name}** (${c.tech_hint}): ${c.role}`));
      lines.push("");
    }
    if (architecture.data_flow) {
      lines.push(`**Data Flow:** ${architecture.data_flow}`);
      lines.push("");
    }
  }

  if (tech_stack?.layers) {
    lines.push("## Tech Stack");
    Object.entries(tech_stack.layers).filter(([, v]) => v).forEach(([layer, info]: [string, any]) => {
      lines.push(`- **${layer}:** ${info.name} — ${info.rationale}`);
    });
    lines.push("");
  }

  if (estimation) {
    lines.push("## Estimation");
    lines.push(`- **MVP:** ${estimation.mvp_weeks} weeks`);
    lines.push(`- **Full product:** ${estimation.full_product_weeks} weeks`);
    lines.push(`- **Team:** ${estimation.recommended_team.size} engineers`);
    lines.push(`- **Cost range:** ${fmt(estimation.cost_range.mvp_low)}–${fmt(estimation.cost_range.mvp_high)} ${estimation.cost_range.currency}`);
    lines.push("");
    if (estimation.phases?.length) {
      lines.push("### Phases");
      estimation.phases.forEach((p) => lines.push(`- **${p.name}** (${p.weeks}w): ${p.deliverables.join(", ")}`));
      lines.push("");
    }
    if (estimation.risks?.length) {
      lines.push("### Risks");
      estimation.risks.forEach((r) => lines.push(`- ⚠ ${r}`));
    }
  }

  return lines.join("\n");
}

export function PlanOutput({ requirements, architecture, tech_stack, estimation, onSave, reviewMode }: Props) {
  const projectName = (requirements as any)?.project_name ?? "Your Project";
  const domain = (requirements as any)?.domain ?? "";

  function handleCopyMarkdown() {
    const md = buildMarkdown(requirements, architecture, tech_stack, estimation);
    navigator.clipboard.writeText(md).then(() => {
      alert("Plan copied as Markdown!");
    });
  }

  function handlePrint() {
    window.print();
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-2xl border border-gray-800 bg-gray-900 px-6 py-5 no-print">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="space-y-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-xl font-bold text-white">{projectName}</h2>
              {domain && (
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-800 text-gray-400 border border-gray-700">
                  {domain}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-400">
              {reviewMode ? "Review your plan before saving" : "Your project plan"}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={handleCopyMarkdown}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 border border-gray-700 hover:border-gray-500 hover:text-gray-200 transition-colors"
            >
              Copy Markdown
            </button>
            <button
              onClick={handlePrint}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 border border-gray-700 hover:border-gray-500 hover:text-gray-200 transition-colors"
            >
              Print / PDF
            </button>
            {onSave && (
              <button
                onClick={onSave}
                className="px-5 py-1.5 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 transition-colors"
              >
                {reviewMode ? "Approve & Save →" : "Save Plan →"}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Architecture */}
      {architecture && (
        <section className="rounded-2xl border border-gray-800 bg-gray-900 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
              Architecture
            </h3>
            {architecture.pattern && (
              <span
                className={`text-xs font-medium px-2 py-0.5 rounded-full border ${
                  PATTERN_COLORS[architecture.pattern] ?? "bg-gray-800 text-gray-400 border-gray-700"
                }`}
              >
                {architecture.pattern}
              </span>
            )}
          </div>
          <div className="px-6 py-5 space-y-5">
            {architecture.description && (
              <p className="text-sm text-gray-300">{architecture.description}</p>
            )}
            {architecture.components?.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                  Components
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {architecture.components.map((c, i) => (
                    <div
                      key={i}
                      className="rounded-lg bg-gray-950 border border-gray-800 px-3 py-2.5 space-y-0.5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-white">{c.name}</span>
                        {c.tech_hint && (
                          <span className="text-xs text-blue-400 font-mono">{c.tech_hint}</span>
                        )}
                      </div>
                      <p className="text-xs text-gray-500">{c.role}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {architecture.data_flow && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                  Data Flow
                </p>
                <p className="text-sm text-gray-400">{architecture.data_flow}</p>
              </div>
            )}
            {architecture.key_decisions?.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                  Key Decisions
                </p>
                <ul className="space-y-1">
                  {architecture.key_decisions.map((d, i) => (
                    <li key={i} className="flex gap-2 text-sm text-gray-400">
                      <span className="text-blue-500 mt-0.5">›</span>
                      {d}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Tech Stack */}
      {tech_stack && (
        <section className="rounded-2xl border border-gray-800 bg-gray-900 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-800">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
              Tech Stack
            </h3>
          </div>
          <div className="px-6 py-5 space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {Object.entries(tech_stack.layers ?? {})
                .filter(([, v]) => v !== null && v !== undefined)
                .map(([layer, info]: [string, any]) => (
                  <div
                    key={layer}
                    className="rounded-lg bg-gray-950 border border-gray-800 px-3 py-3 space-y-1.5"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600 font-mono text-sm">
                        {STACK_LAYER_ICONS[layer] ?? "◆"}
                      </span>
                      <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                        {layer}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-white">{info.name}</p>
                    <p className="text-xs text-gray-500">{info.rationale}</p>
                    {info.key_libs?.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-0.5">
                        {info.key_libs.map((lib: string) => (
                          <span
                            key={lib}
                            className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 font-mono"
                          >
                            {lib}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
            </div>
            {(tech_stack.alternatives?.length ?? 0) > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                  Alternatives Considered
                </p>
                <ul className="space-y-1.5">
                  {(tech_stack.alternatives ?? []).map((alt, i) => (
                    <li key={i} className="text-xs text-gray-500 flex gap-2">
                      <span className="text-gray-700 uppercase font-medium shrink-0">{alt.layer}:</span>
                      <span>
                        <span className="text-gray-400">{alt.name}</span> — {alt.tradeoff}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Estimation */}
      {estimation && (
        <section className="rounded-2xl border border-gray-800 bg-gray-900 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
              Estimation
            </h3>
            <span className={`text-xs font-medium ${CONFIDENCE_COLORS[estimation.confidence] ?? "text-gray-400"}`}>
              {estimation.confidence} confidence
            </span>
          </div>
          <div className="px-6 py-5 space-y-5">
            {/* Headline numbers */}
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg bg-gray-950 border border-gray-800 px-3 py-3 text-center">
                <p className="text-2xl font-bold text-white">{estimation.mvp_weeks}w</p>
                <p className="text-xs text-gray-500 mt-0.5">MVP</p>
              </div>
              <div className="rounded-lg bg-gray-950 border border-gray-800 px-3 py-3 text-center">
                <p className="text-2xl font-bold text-white">{estimation.full_product_weeks}w</p>
                <p className="text-xs text-gray-500 mt-0.5">Full Product</p>
              </div>
              <div className="rounded-lg bg-gray-950 border border-gray-800 px-3 py-3 text-center">
                <p className="text-2xl font-bold text-white">{estimation.recommended_team.size}</p>
                <p className="text-xs text-gray-500 mt-0.5">Engineers</p>
              </div>
            </div>

            {/* Cost range */}
            {estimation.cost_range && (
              <div className="rounded-lg bg-gray-950 border border-gray-800 px-4 py-3 space-y-1">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                    MVP Cost Range
                  </p>
                  <p className="text-lg font-bold text-white">
                    {fmt(estimation.cost_range.mvp_low)}–{fmt(estimation.cost_range.mvp_high)}
                    <span className="text-sm text-gray-500 font-normal ml-1">
                      {estimation.cost_range.currency}
                    </span>
                  </p>
                </div>
                <p className="text-xs text-gray-600">{estimation.cost_range.basis}</p>
              </div>
            )}

            {/* Phases */}
            {estimation.phases?.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                  Phases
                </p>
                <div className="space-y-2">
                  {estimation.phases.map((phase, i) => (
                    <div key={i} className="flex gap-3">
                      <div className="shrink-0 w-6 h-6 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-xs text-gray-400 font-mono mt-0.5">
                        {i + 1}
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-white">{phase.name}</span>
                          <span className="text-xs text-gray-600">{phase.weeks}w</span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {phase.deliverables?.map((d, j) => (
                            <span
                              key={j}
                              className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400"
                            >
                              {d}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Risks */}
            {estimation.risks?.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                  Risks
                </p>
                <ul className="space-y-1">
                  {estimation.risks.map((r, i) => (
                    <li key={i} className="flex gap-2 text-xs text-gray-500">
                      <span className="text-yellow-700 mt-0.5">⚠</span>
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
