import { useEffect, useRef } from "react";
import Markdown from "react-markdown";
import { useChatStore } from "../stores/chatStore";
import type { Message } from "../types";
import { AgentBadge } from "./AgentBadge";
import type { CSSProperties } from "react";

const containerStyle: CSSProperties = {
  flex: 1,
  overflowY: "auto",
  padding: "16px",
  display: "flex",
  flexDirection: "column",
  gap: "12px",
};

const userBubble: CSSProperties = {
  alignSelf: "flex-end",
  maxWidth: "75%",
  padding: "10px 14px",
  background: "var(--accent-dim)",
  border: "1px solid rgba(124, 92, 252, 0.2)",
  borderRadius: "var(--radius) var(--radius) 4px var(--radius)",
  animation: "fade-in 0.2s ease-out",
};

const assistantBubble: CSSProperties = {
  alignSelf: "flex-start",
  maxWidth: "85%",
  padding: "10px 14px",
  background: "var(--glass-bg)",
  border: "1px solid var(--glass-border)",
  borderRadius: "var(--radius) var(--radius) var(--radius) 4px",
  animation: "fade-in 0.2s ease-out",
};

const timeStyle: CSSProperties = {
  fontSize: "10px",
  color: "var(--text-dim)",
  marginTop: "4px",
};

function ChatBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  const time = new Date(msg.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div style={isUser ? userBubble : assistantBubble}>
      {!isUser && msg.agent && (
        <div style={{ marginBottom: "6px" }}>
          <AgentBadge agent={msg.agent} />
        </div>
      )}
      <div className="markdown-content">
        {isUser ? msg.content : <Markdown>{msg.content}</Markdown>}
      </div>
      <div style={timeStyle}>{time}</div>
    </div>
  );
}

export function ChatPanel() {
  const messages = useChatStore((s) => s.messages);
  const isProcessing = useChatStore((s) => s.isProcessing);
  const currentAgent = useChatStore((s) => s.currentAgent);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  return (
    <div style={containerStyle}>
      {messages.length === 0 && (
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "12px",
            color: "var(--text-dim)",
          }}
        >
          <div style={{ fontSize: "36px", opacity: 0.5 }}>&#10024;</div>
          <div style={{ fontSize: "18px", fontWeight: 500, color: "var(--text-secondary)" }}>
            Aura
          </div>
          <div style={{ fontSize: "13px" }}>Ask me anything. I'll route to the right agent.</div>
        </div>
      )}

      {messages.map((msg, i) => (
        <ChatBubble key={i} msg={msg} />
      ))}

      {isProcessing && (
        <div style={{ ...assistantBubble, display: "flex", alignItems: "center", gap: "8px" }}>
          {currentAgent && <AgentBadge agent={currentAgent} pulse />}
          <span
            style={{
              color: "var(--text-secondary)",
              fontSize: "13px",
              background: "linear-gradient(90deg, var(--text-secondary), var(--text-dim), var(--text-secondary))",
              backgroundSize: "200% 100%",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              animation: "shimmer 2s linear infinite",
            }}
          >
            Thinking...
          </span>
        </div>
      )}

      <div ref={endRef} />
    </div>
  );
}
