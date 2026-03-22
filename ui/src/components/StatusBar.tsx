import { useChatStore } from "../stores/chatStore";
import type { CSSProperties } from "react";

const barStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "16px",
  padding: "6px 16px",
  borderTop: "1px solid var(--glass-border)",
  fontSize: "11px",
  color: "var(--text-dim)",
  fontFamily: "'JetBrains Mono', monospace",
};

const statStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "4px",
};

function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div
      style={{
        width: "40px",
        height: "4px",
        background: "rgba(255,255,255,0.06)",
        borderRadius: "2px",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: `${pct}%`,
          height: "100%",
          background: pct > 80 ? "var(--error)" : color,
          borderRadius: "2px",
          transition: "width 0.5s ease",
        }}
      />
    </div>
  );
}

export function StatusBar() {
  const hw = useChatStore((s) => s.hardwareStats);
  const isConnected = useChatStore((s) => s.isConnected);
  const showThinking = useChatStore((s) => s.showThinking);
  const toggleThinking = useChatStore((s) => s.toggleThinking);

  return (
    <div style={barStyle}>
      {/* Connection indicator */}
      <span style={statStyle}>
        <span
          style={{
            width: "6px",
            height: "6px",
            borderRadius: "50%",
            background: isConnected ? "#10b981" : "#ef4444",
          }}
        />
        {isConnected ? "Connected" : "Disconnected"}
      </span>

      {hw && (
        <>
          <span style={statStyle}>
            CPU {hw.cpu_percent.toFixed(0)}%
            <MiniBar value={hw.cpu_percent} max={100} color="var(--kernel)" />
          </span>

          <span style={statStyle}>
            RAM {hw.ram_used_gb}/{hw.ram_total_gb}GB
            <MiniBar value={hw.ram_percent} max={100} color="var(--accent)" />
          </span>

          {hw.gpu_load_percent != null && (
            <span style={statStyle}>
              GPU {hw.gpu_load_percent.toFixed(0)}%
              <MiniBar value={hw.gpu_load_percent} max={100} color="var(--creator)" />
            </span>
          )}
        </>
      )}

      <div style={{ flex: 1 }} />

      {!showThinking && (
        <button
          onClick={toggleThinking}
          style={{
            background: "none",
            border: "1px solid var(--glass-border)",
            borderRadius: "4px",
            color: "var(--text-dim)",
            cursor: "pointer",
            padding: "1px 8px",
            fontSize: "10px",
          }}
        >
          Show Thinking
        </button>
      )}

      <span style={{ color: "var(--text-dim)" }}>Aura v0.1.0</span>
    </div>
  );
}
