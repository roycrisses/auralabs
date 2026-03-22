import { getCurrentWindow } from "@tauri-apps/api/window";
import type { CSSProperties } from "react";
import { useChatStore } from "../stores/chatStore";

const appWindow = getCurrentWindow();

interface Props {
  collapsed: boolean;
  onToggle: () => void;
  onSettingsClick: () => void;
  onConnectorsClick: () => void;
}

const sidebarStyle: CSSProperties = {
  width: "260px",
  display: "flex",
  flexDirection: "column",
  background: "var(--bg-secondary)",
  borderRight: "1px solid var(--border-primary)",
  transition: "width var(--transition)",
  overflow: "hidden",
  flexShrink: 0,
};

const collapsedStyle: CSSProperties = {
  ...sidebarStyle,
  width: "0px",
  borderRight: "none",
};

const headerStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "12px 14px",
  height: "52px",
  borderBottom: "1px solid var(--border-subtle)",
};

const newChatBtnStyle: CSSProperties = {
  padding: "10px 14px",
  margin: "10px 12px",
  background: "transparent",
  border: "1px solid var(--border-primary)",
  borderRadius: "var(--radius-md)",
  color: "var(--text-primary)",
  fontSize: "13px",
  fontWeight: 500,
  fontFamily: "inherit",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  gap: "8px",
  transition: "background var(--transition)",
  width: "calc(100% - 24px)",
};

const bottomStyle: CSSProperties = {
  borderTop: "1px solid var(--border-subtle)",
  padding: "8px",
  display: "flex",
  flexDirection: "column",
  gap: "2px",
};

const bottomBtnStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "10px",
  padding: "10px 12px",
  background: "transparent",
  border: "none",
  borderRadius: "var(--radius-sm)",
  color: "var(--text-secondary)",
  fontSize: "13px",
  fontFamily: "inherit",
  cursor: "pointer",
  transition: "background var(--transition), color var(--transition)",
  width: "100%",
  textAlign: "left",
};

const statusDotStyle = (connected: boolean): CSSProperties => ({
  width: "8px",
  height: "8px",
  borderRadius: "50%",
  background: connected ? "var(--success)" : "var(--error)",
  flexShrink: 0,
});

const windowBtnStyle: CSSProperties = {
  width: "14px",
  height: "14px",
  borderRadius: "50%",
  border: "none",
  cursor: "pointer",
  transition: "opacity var(--transition)",
  flexShrink: 0,
};

export function Sidebar({ collapsed, onToggle, onSettingsClick, onConnectorsClick }: Props) {
  const isConnected = useChatStore((s) => s.isConnected);
  const clearChat = useChatStore((s) => s.clearChat);
  const hw = useChatStore((s) => s.hardwareStats);
  const showThinking = useChatStore((s) => s.showThinking);
  const toggleThinking = useChatStore((s) => s.toggleThinking);

  if (collapsed) {
    return (
      <div style={{ width: "48px", background: "var(--bg-secondary)", borderRight: "1px solid var(--border-primary)", display: "flex", flexDirection: "column", alignItems: "center", paddingTop: "12px" }}>
        <button
          onClick={onToggle}
          style={{ ...bottomBtnStyle, padding: "8px", justifyContent: "center", width: "auto" }}
          title="Expand sidebar"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
        </button>
      </div>
    );
  }

  return (
    <div className="titlebar-drag" style={sidebarStyle}>
      {/* Header with window controls + collapse */}
      <div style={headerStyle}>
        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
          <button onClick={() => appWindow.close()} style={{ ...windowBtnStyle, background: "#ff5f57" }} title="Close" />
          <button onClick={() => appWindow.minimize()} style={{ ...windowBtnStyle, background: "#ffbd2e" }} title="Minimize" />
        </div>
        <button
          onClick={onToggle}
          style={{ ...bottomBtnStyle, padding: "4px 6px", width: "auto" }}
          title="Collapse sidebar"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
        </button>
      </div>

      {/* New Chat */}
      <button
        onClick={clearChat}
        style={newChatBtnStyle}
        onMouseEnter={(e) => { (e.target as HTMLElement).style.background = "var(--bg-hover)"; }}
        onMouseLeave={(e) => { (e.target as HTMLElement).style.background = "transparent"; }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        New chat
      </button>

      {/* Spacer */}
      <div style={{ flex: 1, padding: "8px 12px", overflowY: "auto" }}>
        <div style={{ fontSize: "11px", fontWeight: 600, textTransform: "uppercase", color: "var(--text-tertiary)", letterSpacing: "0.05em", padding: "8px 4px" }}>
          System Status
        </div>
        {hw && (
          <div style={{ display: "flex", flexDirection: "column", gap: "6px", padding: "4px" }}>
            <StatusItem label="CPU" value={`${hw.cpu_percent.toFixed(0)}%`} percent={hw.cpu_percent} color="var(--kernel)" />
            <StatusItem label="RAM" value={`${hw.ram_used_gb}/${hw.ram_total_gb}GB`} percent={hw.ram_percent} color="var(--accent)" />
            {hw.gpu_load_percent != null && (
              <StatusItem label="GPU" value={`${hw.gpu_load_percent.toFixed(0)}%`} percent={hw.gpu_load_percent} color="var(--creator)" />
            )}
          </div>
        )}
      </div>

      {/* Bottom actions */}
      <div style={bottomStyle}>
        <button
          onClick={() => (window as any).toggleBlob?.(true)}
          style={bottomBtnStyle}
          onMouseEnter={(e) => { (e.target as HTMLElement).style.background = "var(--bg-hover)"; }}
          onMouseLeave={(e) => { (e.target as HTMLElement).style.background = "transparent"; }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>
          Minimized
        </button>
        <button
          onClick={toggleThinking}
          style={bottomBtnStyle}
          onMouseEnter={(e) => { (e.target as HTMLElement).style.background = "var(--bg-hover)"; }}
          onMouseLeave={(e) => { (e.target as HTMLElement).style.background = "transparent"; }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v6M12 17v6M4.22 4.22l4.24 4.24M15.54 15.54l4.24 4.24M1 12h6M17 12h6M4.22 19.78l4.24-4.24M15.54 8.46l4.24-4.24"/></svg>
          {showThinking ? "Hide thinking" : "Show thinking"}
        </button>
        <button
          onClick={onConnectorsClick}
          style={bottomBtnStyle}
          onMouseEnter={(e) => { (e.target as HTMLElement).style.background = "var(--bg-hover)"; }}
          onMouseLeave={(e) => { (e.target as HTMLElement).style.background = "transparent"; }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
          Connectors
        </button>
        <button
          onClick={onSettingsClick}
          style={bottomBtnStyle}
          onMouseEnter={(e) => { (e.target as HTMLElement).style.background = "var(--bg-hover)"; }}
          onMouseLeave={(e) => { (e.target as HTMLElement).style.background = "transparent"; }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          Settings
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 12px", fontSize: "12px", color: "var(--text-tertiary)" }}>
          <span style={statusDotStyle(isConnected)} />
          {isConnected ? "Connected" : "Disconnected"}
        </div>
      </div>
    </div>
  );
}

function StatusItem({ label, value, percent, color }: { label: string; value: string; percent: number; color: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "var(--text-secondary)" }}>
      <span style={{ width: "32px", flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, height: "4px", background: "rgba(255,255,255,0.06)", borderRadius: "2px", overflow: "hidden" }}>
        <div style={{ width: `${Math.min(percent, 100)}%`, height: "100%", background: percent > 85 ? "var(--error)" : color, borderRadius: "2px", transition: "width 0.5s ease" }} />
      </div>
      <span style={{ width: "60px", textAlign: "right", fontSize: "11px", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-tertiary)" }}>{value}</span>
    </div>
  );
}
