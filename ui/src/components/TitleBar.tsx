import { getCurrentWindow } from "@tauri-apps/api/window";
import type { CSSProperties } from "react";

const appWindow = getCurrentWindow();

const barStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "8px 12px",
  borderBottom: "1px solid var(--glass-border)",
  userSelect: "none",
  height: "40px",
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

const btnGroupStyle: any = {
  display: "flex",
  gap: "6px",
  zIndex: 1000,
  WebkitAppRegion: "no-drag",
};

const controlBtn: any = {
  width: "12px",
  height: "12px",
  borderRadius: "50%",
  border: "none",
  cursor: "pointer",
  transition: "opacity 0.15s",
  WebkitAppRegion: "no-drag",
  position: "relative",
};

interface Props {
  onSettingsClick?: () => void;
}

export function TitleBar({ onSettingsClick }: Props) {
  const minimize = () => {
    appWindow.minimize();
  };

  const close = () => {
    appWindow.close();
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
            onClick={(e) => {
              e.stopPropagation();
              onSettingsClick();
            }}
            style={{ 
              ...controlBtn, 
              background: "#8b5cf6", 
              width: "auto", 
              borderRadius: "4px", 
              padding: "0 8px", 
              height: "20px",
              fontSize: "10px", 
              color: "#fff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700
            }}
            title="Settings"
          >
            SETTINGS
          </button>
        )}
        <button
          onClick={(e) => {
            e.stopPropagation();
            minimize();
          }}
          style={{ ...controlBtn, background: "#f59e0b" }}
          title="Minimize"
        />
        <button
          onClick={(e) => {
            e.stopPropagation();
            close();
          }}
          style={{ ...controlBtn, background: "#ef4444" }}
          title="Close"
        />
      </div>
    </div>
  );
}
