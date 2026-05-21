import { useState, useCallback } from "react";
import { getAuthHeader } from "../lib/supabase";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type AgentEvent = {
  event: "agent_start" | "token" | "agent_done" | "checkpoint" | "error" | "done";
  agent: string | null;
  data: string | object | null;
};

export type AgentState = {
  name: string;
  status: "idle" | "running" | "done" | "error";
  output: string;
};

export type CheckpointData = {
  title: string;
  requirements?: object;
  clarification_questions?: string[];
  architecture?: object;
  tech_stack?: object;
  estimation?: object;
  _agent: string;
};

export function useAgentStream() {
  const [agents, setAgents] = useState<Record<string, AgentState>>({});
  const [checkpoint, setCheckpoint] = useState<CheckpointData | null>(null);
  const [planData, setPlanData] = useState<CheckpointData | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startStream = useCallback(async (projectId: string, rawInput: string) => {
    setIsStreaming(true);
    setIsDone(false);
    setError(null);
    setAgents({});
    setCheckpoint(null);
    setPlanData(null);

    try {
      const authHeader = await getAuthHeader();
      const params = new URLSearchParams({ raw_input: rawInput });
      const url = `${API_BASE}/api/stream/run/${projectId}?${params}`;

      const response = await fetch(url, {
        method: "POST",
        headers: { Authorization: authHeader },
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() ?? "";

        for (const chunk of lines) {
          const line = chunk.replace(/^data: /, "").trim();
          if (!line) continue;
          try {
            const evt: AgentEvent = JSON.parse(line);
            handleEvent(evt);
          } catch {
            // skip malformed chunks
          }
        }
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsStreaming(false);
    }
  }, []);

  function handleEvent(evt: AgentEvent) {
    const agentName = evt.agent ?? "system";

    switch (evt.event) {
      case "agent_start":
        setAgents((prev) => ({
          ...prev,
          [agentName]: { name: agentName, status: "running", output: "" },
        }));
        break;

      case "token":
        setAgents((prev) => ({
          ...prev,
          [agentName]: {
            ...prev[agentName],
            output: (prev[agentName]?.output ?? "") + (evt.data as string),
          },
        }));
        break;

      case "agent_done":
        setAgents((prev) => ({
          ...prev,
          [agentName]: { ...prev[agentName], status: "done" },
        }));
        break;

      case "checkpoint": {
        const data = { ...(evt.data as object), _agent: agentName } as CheckpointData;
        if (agentName === "checkpoint_2") {
          setPlanData(data);
        } else {
          setCheckpoint(data);
        }
        break;
      }

      case "error":
        setError(evt.data as string);
        setAgents((prev) => ({
          ...prev,
          [agentName]: { ...prev[agentName], status: "error" },
        }));
        break;

      case "done":
        setIsDone(true);
        break;
    }
  }

  function clearCheckpoint() {
    setCheckpoint(null);
  }

  function reset() {
    setAgents({});
    setCheckpoint(null);
    setPlanData(null);
    setIsStreaming(false);
    setIsDone(false);
    setError(null);
  }

  return { agents, checkpoint, planData, isStreaming, isDone, error, startStream, clearCheckpoint, reset };
}
