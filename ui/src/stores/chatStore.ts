import { create } from "zustand";
import type {
  Attachment,
  HardwareStats,
  Message,
  ThinkingEvent,
  ToolCallEvent,
  ToolResultEvent,
} from "../types";

interface ChatState {
  messages: Message[];
  thinkingLog: ThinkingEvent[];
  toolEvents: (ToolCallEvent | ToolResultEvent)[];
  currentAgent: string | null;
  isProcessing: boolean;
  isConnected: boolean;
  hardwareStats: HardwareStats | null;
  showThinking: boolean;
  pendingAttachments: Attachment[];

  addUserMessage: (content: string) => void;
  addAttachment: (attachment: Attachment) => void;
  removeAttachment: (path: string) => void;
  clearAttachments: () => void;
  addAssistantMessage: (content: string, agent: string) => void;
  addThinking: (agent: string, content: string) => void;
  addToolEvent: (event: ToolCallEvent | ToolResultEvent) => void;
  setCurrentAgent: (agent: string | null) => void;
  setProcessing: (v: boolean) => void;
  setConnected: (v: boolean) => void;
  setHardwareStats: (stats: HardwareStats) => void;
  toggleThinking: () => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  thinkingLog: [],
  toolEvents: [],
  currentAgent: null,
  isProcessing: false,
  isConnected: false,
  hardwareStats: null,
  showThinking: true,
  pendingAttachments: [],

  addAttachment: (attachment) =>
    set((s) => ({ pendingAttachments: [...s.pendingAttachments, attachment] })),
  removeAttachment: (path) =>
    set((s) => ({
      pendingAttachments: s.pendingAttachments.filter((a) => a.path !== path),
    })),
  clearAttachments: () => set({ pendingAttachments: [] }),

  addUserMessage: (content) =>
    set((s) => ({
      messages: [
        ...s.messages,
        {
          role: "user",
          content,
          timestamp: new Date().toISOString(),
        },
      ],
    })),

  addAssistantMessage: (content, agent) =>
    set((s) => ({
      messages: [
        ...s.messages,
        {
          role: "assistant",
          content,
          agent,
          timestamp: new Date().toISOString(),
        },
      ],
    })),

  addThinking: (agent, content) =>
    set((s) => ({
      thinkingLog: [
        ...s.thinkingLog,
        { agent, content, timestamp: new Date().toISOString() },
      ],
    })),

  addToolEvent: (event) =>
    set((s) => ({ toolEvents: [...s.toolEvents, event] })),

  setCurrentAgent: (agent) => set({ currentAgent: agent }),
  setProcessing: (v) => set({ isProcessing: v }),
  setConnected: (v) => set({ isConnected: v }),
  setHardwareStats: (stats) => set({ hardwareStats: stats }),
  toggleThinking: () => set((s) => ({ showThinking: !s.showThinking })),
  clearChat: () =>
    set({ messages: [], thinkingLog: [], toolEvents: [], currentAgent: null }),
}));
