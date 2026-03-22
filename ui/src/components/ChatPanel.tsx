import { useEffect, useRef } from "react";
import Markdown from "react-markdown";
import { useChatStore } from "../stores/chatStore";
import type { Message } from "../types";
import type { CSSProperties } from "react";

const containerStyle: CSSProperties = {
  flex: 1,
  overflowY: "auto",
  display: "flex",
  flexDirection: "column",
};

const messageListStyle: CSSProperties = {
  maxWidth: "var(--max-chat-width)",
  width: "100%",
  margin: "0 auto",
  padding: "20px 24px",
  display: "flex",
  flexDirection: "column",
};

/* ─── Empty state (centered like Claude.ai) ─── */
const emptyStateStyle: CSSProperties = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  gap: "16px",
  paddingBottom: "80px",
};

const logoStyle: CSSProperties = {
  width: "48px",
  height: "48px",
  borderRadius: "50%",
  background: "linear-gradient(135deg, #8b5cf6, #6d28d9)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: "24px",
  boxShadow: "0 0 40px rgba(139, 92, 246, 0.2)",
};

const greetingStyle: CSSProperties = {
  fontSize: "28px",
  fontWeight: 600,
  color: "var(--text-primary)",
  letterSpacing: "-0.02em",
};

const subtitleStyle: CSSProperties = {
  fontSize: "15px",
  color: "var(--text-tertiary)",
  maxWidth: "400px",
  textAlign: "center",
  lineHeight: 1.5,
};

/* ─── Suggestion chips ─── */
const suggestionsStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: "8px",
  justifyContent: "center",
  marginTop: "12px",
};

const chipStyle: CSSProperties = {
  padding: "8px 16px",
  background: "var(--bg-tertiary)",
  border: "1px solid var(--border-primary)",
  borderRadius: "var(--radius-pill)",
  color: "var(--text-secondary)",
  fontSize: "13px",
  cursor: "pointer",
  transition: "background var(--transition), color var(--transition), border-color var(--transition)",
  fontFamily: "inherit",
};

/* ─── Message rows ─── */
const messageRowStyle = (isUser: boolean): CSSProperties => ({
  display: "flex",
  gap: "14px",
  padding: "20px 0",
  borderBottom: isUser ? "none" : "1px solid var(--border-subtle)",
  animation: "fade-in 0.2s ease-out",
});

const avatarStyle = (isUser: boolean): CSSProperties => ({
  width: "28px",
  height: "28px",
  borderRadius: "50%",
  background: isUser
    ? "var(--bg-message-user)"
    : "linear-gradient(135deg, #8b5cf6, #6d28d9)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: "13px",
  fontWeight: 600,
  color: isUser ? "var(--text-secondary)" : "#fff",
  flexShrink: 0,
  marginTop: "2px",
});

const messageContentStyle: CSSProperties = {
  flex: 1,
  minWidth: 0,
};

const agentLabelStyle = (color: string): CSSProperties => ({
  fontSize: "13px",
  fontWeight: 600,
  color,
  marginBottom: "4px",
  display: "flex",
  alignItems: "center",
  gap: "6px",
});

const userLabelStyle: CSSProperties = {
  fontSize: "13px",
  fontWeight: 600,
  color: "var(--text-primary)",
  marginBottom: "4px",
};

const AGENT_DISPLAY: Record<string, { label: string; color: string }> = {
  kernel: { label: "Kernel", color: "#3b82f6" },
  researcher: { label: "Researcher", color: "#10b981" },
  creator: { label: "Creator", color: "#f59e0b" },
  router: { label: "Aura", color: "#8b5cf6" },
};

/* ─── Thinking indicator ─── */
const thinkingStyle: CSSProperties = {
  display: "flex",
  gap: "14px",
  padding: "20px 0",
  animation: "fade-in 0.2s ease-out",
};

const dotContainerStyle: CSSProperties = {
  display: "flex",
  gap: "4px",
  alignItems: "center",
  padding: "4px 0",
};

const dotStyle = (delay: number): CSSProperties => ({
  width: "6px",
  height: "6px",
  borderRadius: "50%",
  background: "var(--text-tertiary)",
  animation: `typing-bounce 1.2s ease-in-out ${delay}s infinite`,
});

/* ─── Suggestions ─── */
const SUGGESTIONS = [
  "Open Notepad",
  "What's my CPU usage?",
  "Search the web for latest tech news",
  "Write me a professional email",
];

function MessageRow({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  const agentInfo = msg.agent ? AGENT_DISPLAY[msg.agent] : null;

  return (
    <div style={messageRowStyle(isUser)}>
      <div style={avatarStyle(isUser)}>
        {isUser ? "Y" : "A"}
      </div>
      <div style={messageContentStyle}>
        <div style={isUser ? userLabelStyle : agentLabelStyle(agentInfo?.color ?? "var(--accent)")}>
          {isUser ? "You" : (agentInfo?.label ?? "Aura")}
        </div>
        <div className="markdown-content">
          {isUser ? (
            <span style={{ color: "var(--text-primary)", lineHeight: 1.7 }}>{msg.content}</span>
          ) : (
            <Markdown>{msg.content}</Markdown>
          )}
        </div>
      </div>
    </div>
  );
}

export function ChatPanel() {
  const messages = useChatStore((s) => s.messages);
  const isProcessing = useChatStore((s) => s.isProcessing);
  const currentAgent = useChatStore((s) => s.currentAgent);
  const thinkingLog = useChatStore((s) => s.thinkingLog);
  const showThinking = useChatStore((s) => s.showThinking);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing, thinkingLog]);

  const agentInfo = currentAgent ? AGENT_DISPLAY[currentAgent] : null;

  return (
    <div style={containerStyle}>
      {messages.length === 0 ? (
        <div style={{ ...messageListStyle, flex: 1 }}>
          <div style={emptyStateStyle}>
            <div style={logoStyle}>✦</div>
            <div style={greetingStyle}>How can I help you?</div>
            <div style={subtitleStyle}>
              I can run commands, search the web, create content, and manage your system.
            </div>
            <div style={suggestionsStyle}>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  style={chipStyle}
                  onMouseEnter={(e) => {
                    (e.target as HTMLElement).style.background = "var(--bg-hover)";
                    (e.target as HTMLElement).style.borderColor = "var(--border-focus)";
                    (e.target as HTMLElement).style.color = "var(--text-primary)";
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLElement).style.background = "var(--bg-tertiary)";
                    (e.target as HTMLElement).style.borderColor = "var(--border-primary)";
                    (e.target as HTMLElement).style.color = "var(--text-secondary)";
                  }}
                  onClick={() => {
                    // Trigger send via the store
                    useChatStore.getState().addUserMessage(s);
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div style={messageListStyle}>
          {messages.map((msg, i) => (
            <MessageRow key={i} msg={msg} />
          ))}

          {/* Thinking log inline (like Claude's thinking blocks) */}
          {showThinking && isProcessing && thinkingLog.length > 0 && (
            <div style={{ padding: "12px 0 0 42px" }}>
              <details open style={{ fontSize: "12px", color: "var(--text-tertiary)" }}>
                <summary style={{ cursor: "pointer", fontWeight: 500, marginBottom: "6px", color: "var(--text-secondary)" }}>
                  Thinking...
                </summary>
                <div style={{ paddingLeft: "8px", borderLeft: "2px solid var(--border-primary)", display: "flex", flexDirection: "column", gap: "4px" }}>
                  {thinkingLog.slice(-5).map((entry, i) => (
                    <div key={i} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", lineHeight: 1.5 }}>
                      <span style={{ color: AGENT_DISPLAY[entry.agent]?.color ?? "var(--text-tertiary)", fontWeight: 600 }}>
                        [{entry.agent}]
                      </span>{" "}
                      {entry.content}
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )}

          {/* Typing indicator */}
          {isProcessing && (
            <div style={thinkingStyle}>
              <div style={avatarStyle(false)}>A</div>
              <div style={messageContentStyle}>
                <div style={agentLabelStyle(agentInfo?.color ?? "var(--accent)")}>
                  {agentInfo?.label ?? "Aura"}
                </div>
                <div style={dotContainerStyle}>
                  <div style={dotStyle(0)} />
                  <div style={dotStyle(0.15)} />
                  <div style={dotStyle(0.3)} />
                </div>
              </div>
            </div>
          )}

          <div ref={endRef} />
        </div>
      )}
    </div>
  );
}
