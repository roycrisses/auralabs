import { useCallback, useEffect, useRef } from "react";
import { useChatStore } from "../stores/chatStore";
import type { WsEvent } from "../types";

const WS_URL = "ws://127.0.0.1:8420/api/chat/stream";
const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000];

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const store = useChatStore;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      store.getState().setConnected(true);
      retriesRef.current = 0;
    };

    ws.onclose = () => {
      store.getState().setConnected(false);
      wsRef.current = null;
      // Reconnect with backoff
      const delay =
        RECONNECT_DELAYS[
          Math.min(retriesRef.current, RECONNECT_DELAYS.length - 1)
        ];
      retriesRef.current++;
      setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };

    ws.onmessage = (ev) => {
      const event: WsEvent = JSON.parse(ev.data);
      const s = store.getState();

      switch (event.type) {
        case "thinking":
          s.addThinking(event.agent, event.content);
          s.setCurrentAgent(event.agent);
          break;
        case "tool_call":
          s.addToolEvent({ tool: event.tool, args: event.args });
          break;
        case "tool_result":
          s.addToolEvent({
            tool: event.tool,
            success: event.success,
            output: event.output,
          });
          break;
        case "response":
          s.addAssistantMessage(event.content, event.agent);
          s.setCurrentAgent(event.agent);
          break;
        case "done":
          s.setProcessing(false);
          break;
        case "error":
          s.addAssistantMessage(`Error: ${event.content}`, "system");
          s.setProcessing(false);
          break;
      }
    };
  }, []);

  const sendMessage = useCallback((message: string, attachments?: string[]) => {
    const s = store.getState();
    s.addUserMessage(message);
    s.setProcessing(true);
    s.clearAttachments();

    const payload: Record<string, unknown> = { type: "user_message", content: message };
    if (attachments && attachments.length > 0) {
      payload.attachments = attachments;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    } else {
      s.addAssistantMessage("Not connected to backend. Retrying...", "system");
      s.setProcessing(false);
      connect();
    }
  }, [connect]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { sendMessage };
}
