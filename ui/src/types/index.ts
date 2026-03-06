/** Type definitions matching Python Pydantic models. */

export interface Message {
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  agent?: string;
  thinking?: string;
  timestamp: string;
}

export interface ToolCallEvent {
  tool: string;
  args: Record<string, unknown>;
}

export interface ToolResultEvent {
  tool: string;
  success: boolean;
  output: string;
}

export interface ThinkingEvent {
  agent: string;
  content: string;
  timestamp: string;
}

export interface HardwareStats {
  cpu_percent: number;
  cpu_freq_mhz: number;
  ram_used_gb: number;
  ram_total_gb: number;
  ram_percent: number;
  gpu_load_percent: number | null;
  gpu_memory_used_mb: number | null;
  gpu_memory_total_mb: number | null;
  gpu_temperature_c: number | null;
  hardware_profile: {
    cpu: string;
    gpu: string;
    gpu_vram_mb: number;
  };
}

export interface AgentInfo {
  model: string;
  status: "ready" | "busy" | "error";
}

/** WebSocket event types from the Python backend. */
export type WsEvent =
  | { type: "thinking"; agent: string; content: string }
  | { type: "tool_call"; tool: string; args: Record<string, unknown> }
  | { type: "tool_result"; tool: string; success: boolean; output: string }
  | { type: "response"; agent: string; content: string }
  | { type: "token"; content: string }
  | { type: "done" }
  | { type: "error"; content: string };

/** File attachment. */
export interface Attachment {
  path: string;
  filename: string;
  type: "image" | "document";
  size: number;
}

/** Agent color mapping. */
export const AGENT_COLORS: Record<string, string> = {
  router: "#7c5cfc",
  kernel: "#3b82f6",
  researcher: "#10b981",
  creator: "#f59e0b",
};
