import { useEffect, useRef } from "react";
import { useChatStore } from "../stores/chatStore";
import { AGENT_COLORS } from "../types";
import { GlassCard } from "./GlassCard";
import type { CSSProperties } from "react";

const panelStyle: CSSProperties = {
  width: "280px",
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
  borderLeft: "1px solid var(--glass-border)",
};

const headerStyle: CSSProperties = {
  padding: "12px 14px",
  fontSize: "12px",
  fontWeight: 600,
  textTransform: "uppercase",
  letterSpacing: "0.08em",
  color: "var(--text-secondary)",
  borderBottom: "1px solid var(--glass-border)",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
};

const listStyle: CSSProperties = {
  flex: 1,
  overflowY: "auto",
  padding: "8px",
  display: "flex",
  flexDirection: "column",
  gap: "6px",
};

const entryStyle: CSSProperties = {
  padding: "8px 10px",
  fontSize: "12px",
  fontFamily: "'JetBrains Mono', monospace",
  color: "var(--text-secondary)",
  background: "rgba(0, 0, 0, 0.2)",
  borderRadius: "var(--radius-sm)",
  lineHeight: 1.4,
  animation: "fade-in 0.15s ease-out",
};

export function ThinkingLog() {
  const thinkingLog = useChatStore((s) => s.thinkingLog);
  const showThinking = useChatStore((s) => s.showThinking);
  const toggleThinking = useChatStore((s) => s.toggleThinking);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thinkingLog]);

  if (!showThinking) return null;

  return (
    <div style={panelStyle}>
      <div style={headerStyle}>
        <span>Thinking Log</span>
        <button
          onClick={toggleThinking}
          style={{
            background: "none",
            border: "none",
            color: "var(--text-dim)",
            cursor: "pointer",
            fontSize: "14px",
            padding: "0 4px",
          }}
          title="Hide thinking log"
        >
          ✕
        </button>
      </div>

      <div style={listStyle}>
        {thinkingLog.length === 0 && (
          <div style={{ ...entryStyle, color: "var(--text-dim)", textAlign: "center" }}>
            Agent reasoning will appear here...
          </div>
        )}

        {thinkingLog.map((entry, i) => {
          const color = AGENT_COLORS[entry.agent] ?? "var(--text-secondary)";
          const time = new Date(entry.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          });

          return (
            <div key={i} style={entryStyle}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: "3px",
                }}
              >
                <span style={{ color, fontWeight: 500 }}>{entry.agent}</span>
                <span style={{ color: "var(--text-dim)", fontSize: "10px" }}>{time}</span>
              </div>
              <div>{entry.content}</div>
            </div>
          );
        })}
        <div ref={endRef} />
      </div>
    </div>
  );
}
