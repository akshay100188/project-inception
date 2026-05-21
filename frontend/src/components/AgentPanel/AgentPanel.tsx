import { AgentState } from "../../hooks/useAgentStream";

const AGENT_LABELS: Record<string, string> = {
  requirement: "Requirement Analyst",
  clarification: "Clarification Agent",
  checkpoint_1: "Requirements Review",
  architecture: "Architecture Architect",
  techstack: "Tech Stack Selector",
  estimation: "Estimation Analyst",
  checkpoint_2: "Plan Review",
};

const STATUS_COLORS: Record<string, string> = {
  idle: "text-gray-400",
  running: "text-blue-400",
  done: "text-green-400",
  error: "text-red-400",
};

const STATUS_ICONS: Record<string, string> = {
  idle: "○",
  running: "◉",
  done: "✓",
  error: "✗",
};

type Props = {
  agents: Record<string, AgentState>;
  isStreaming: boolean;
};

export function AgentPanel({ agents, isStreaming }: Props) {
  const agentList = Object.values(agents);

  if (!isStreaming && agentList.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-950 divide-y divide-gray-800">
      <div className="px-4 py-3 flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
          Agent Pipeline
        </span>
        {isStreaming && (
          <span className="inline-block h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
        )}
      </div>

      {agentList.map((agent) => (
        <div key={agent.name} className="px-4 py-3 space-y-2">
          <div className="flex items-center gap-2">
            <span className={`font-mono text-sm ${STATUS_COLORS[agent.status]}`}>
              {STATUS_ICONS[agent.status]}
            </span>
            <span className="text-sm font-medium text-gray-200">
              {AGENT_LABELS[agent.name] ?? agent.name}
            </span>
            {agent.status === "running" && (
              <span className="text-xs text-blue-400 ml-auto animate-pulse">
                thinking...
              </span>
            )}
          </div>

          {agent.output && (
            <pre className="text-xs text-gray-400 font-mono whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto bg-gray-900 rounded-lg p-3">
              {agent.output}
            </pre>
          )}
        </div>
      ))}
    </div>
  );
}
