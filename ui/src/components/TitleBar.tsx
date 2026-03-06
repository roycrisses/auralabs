import type { CSSProperties } from "react";

const barStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "8px 12px",
  borderBottom: "1px solid var(--glass-border)",
  userSelect: "none",
};

const titleStyle: CSSProperties = {
  fontSize: "13px",
  fontWeight: 600,
  color: "var(--text-secondary)",
  letterSpacing: "0.05em",
  display: "flex",
  alignItems: "center",
  gap: "8px",
};

const btnGroupStyle: CSSProperties = {
  display: "flex",
  gap: "6px",
};

const controlBtn: CSSProperties = {
  width: "12px",
  height: "12px",
  borderRadius: "50%",
  border: "none",
  cursor: "pointer",
  transition: "opacity 0.15s",
};

interface Props {
  onSettingsClick?: () => void;
}

export function TitleBar({ onSettingsClick }: Props) {
  const minimize = async () => {
    const { getCurrentWindow } = await import("@tauri-apps/api/window");
    getCurrentWindow().minimize();
  };

  const close = async () => {
    const { getCurrentWindow } = await import("@tauri-apps/api/window");
    getCurrentWindow().close();
  };

  return (
    <div className="titlebar-drag" style={barStyle}>
      <div style={titleStyle}>
        <span style={{ color: "var(--accent)", fontSize: "16px" }}>&#10024;</span>
        AURA
      </div>
      <div style={btnGroupStyle}>
        {onSettingsClick && (
          <button
            onClick={onSettingsClick}
            style={{ ...controlBtn, background: "#8b5cf6", width: "auto", borderRadius: "4px", padding: "0 6px", fontSize: "10px", color: "#fff" }}
            title="Settings"
          >
            SET
          </button>
        )}
        <button
          onClick={minimize}
          style={{ ...controlBtn, background: "#f59e0b" }}
          title="Minimize"
        />
        <button
          onClick={close}
          style={{ ...controlBtn, background: "#ef4444" }}
          title="Close"
        />
      </div>
    </div>
  );
}
