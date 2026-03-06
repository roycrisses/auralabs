import { useEffect, useState, type CSSProperties } from "react";

interface Settings {
  models: Record<string, string>;
  confirmation_enabled: boolean;
  tool_risk_levels: Record<string, string>;
  allowed_roots: string[];
}

const API = "http://localhost:8420/api";

const overlayStyle: CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0, 0, 0, 0.5)",
  zIndex: 200,
  display: "flex",
  justifyContent: "flex-end",
};

const panelStyle: CSSProperties = {
  width: "400px",
  height: "100vh",
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
  background: "var(--bg-secondary)",
  borderLeft: "1px solid var(--border-primary)",
  animation: "fade-in 0.15s ease-out",
};

const headerStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "16px 20px",
  borderBottom: "1px solid var(--border-primary)",
};

const bodyStyle: CSSProperties = {
  flex: 1,
  overflowY: "auto",
  padding: "16px 20px",
  display: "flex",
  flexDirection: "column",
  gap: "20px",
};

const sectionTitleStyle: CSSProperties = {
  fontSize: "11px",
  textTransform: "uppercase",
  fontWeight: 600,
  color: "var(--text-tertiary)",
  letterSpacing: "0.06em",
  marginBottom: "10px",
};

const cardStyle: CSSProperties = {
  background: "var(--bg-tertiary)",
  border: "1px solid var(--border-primary)",
  borderRadius: "var(--radius-md)",
  padding: "14px",
};

const inputStyle: CSSProperties = {
  width: "100%",
  padding: "8px 12px",
  background: "var(--bg-primary)",
  border: "1px solid var(--border-primary)",
  borderRadius: "var(--radius-sm)",
  color: "var(--text-primary)",
  fontSize: "13px",
  fontFamily: "'JetBrains Mono', monospace",
  outline: "none",
  transition: "border-color var(--transition)",
};

const closeBtnStyle: CSSProperties = {
  background: "none",
  border: "none",
  color: "var(--text-secondary)",
  cursor: "pointer",
  fontSize: "18px",
  padding: "4px 8px",
  borderRadius: "var(--radius-sm)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  transition: "background var(--transition)",
};

const toggleStyle = (active: boolean): CSSProperties => ({
  width: "40px",
  height: "22px",
  borderRadius: "11px",
  background: active ? "var(--accent)" : "var(--bg-hover)",
  border: "1px solid var(--border-primary)",
  cursor: "pointer",
  position: "relative",
  transition: "background var(--transition)",
  flexShrink: 0,
});

const toggleDotStyle = (active: boolean): CSSProperties => ({
  width: "16px",
  height: "16px",
  borderRadius: "50%",
  background: "#fff",
  position: "absolute",
  top: "2px",
  left: active ? "20px" : "2px",
  transition: "left var(--transition)",
});

interface Props {
  onClose: () => void;
}

export function SettingsPanel({ onClose }: Props) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/settings`)
      .then((r) => r.json())
      .then(setSettings)
      .catch((e) => setError(e.message));
  }, []);

  const updateModel = async (role: string, model: string) => {
    const res = await fetch(`${API}/settings/models`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ models: { [role]: model } }),
    });
    const data = await res.json();
    if (settings) setSettings({ ...settings, models: data.models });
  };

  const toggleConfirmation = async () => {
    if (!settings) return;
    const res = await fetch(`${API}/settings/confirmation`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !settings.confirmation_enabled }),
    });
    const data = await res.json();
    setSettings({ ...settings, confirmation_enabled: data.confirmation_enabled });
  };

  return (
    <div style={overlayStyle} onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={panelStyle}>
        <div style={headerStyle}>
          <span style={{ fontSize: "16px", fontWeight: 600 }}>Settings</span>
          <button
            onClick={onClose}
            style={closeBtnStyle}
            onMouseEnter={(e) => { (e.target as HTMLElement).style.background = "var(--bg-hover)"; }}
            onMouseLeave={(e) => { (e.target as HTMLElement).style.background = "none"; }}
          >
            ✕
          </button>
        </div>

        <div style={bodyStyle}>
          {error && (
            <div style={{ ...cardStyle, borderColor: "var(--error)", color: "var(--error)" }}>
              Failed to load settings: {error}
            </div>
          )}

          {!settings && !error && (
            <div style={{ padding: "40px", textAlign: "center", color: "var(--text-tertiary)" }}>Loading...</div>
          )}

          {settings && (
            <>
              {/* Models */}
              <div>
                <div style={sectionTitleStyle}>Agent Models</div>
                <div style={{ ...cardStyle, display: "flex", flexDirection: "column", gap: "12px" }}>
                  {Object.entries(settings.models).map(([role, model]) => (
                    <div key={role}>
                      <div style={{ fontSize: "12px", fontWeight: 600, marginBottom: "6px", textTransform: "capitalize", color: "var(--text-secondary)" }}>
                        {role}
                      </div>
                      <input
                        style={inputStyle}
                        value={model}
                        onChange={(e) => setSettings({ ...settings, models: { ...settings.models, [role]: e.target.value } })}
                        onBlur={(e) => updateModel(role, e.target.value)}
                        onFocus={(e) => { (e.target as HTMLElement).style.borderColor = "var(--border-focus)"; }}
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Safety */}
              <div>
                <div style={sectionTitleStyle}>Safety</div>
                <div style={cardStyle}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                      Require confirmation for dangerous tools
                    </span>
                    <button
                      onClick={toggleConfirmation}
                      style={toggleStyle(settings.confirmation_enabled)}
                    >
                      <div style={toggleDotStyle(settings.confirmation_enabled)} />
                    </button>
                  </div>
                </div>
              </div>

              {/* Allowed roots */}
              <div>
                <div style={sectionTitleStyle}>Allowed File Roots</div>
                <div style={cardStyle}>
                  {settings.allowed_roots.map((root, i) => (
                    <div key={i} style={{ fontSize: "12px", padding: "4px 0", color: "var(--text-secondary)", fontFamily: "'JetBrains Mono', monospace" }}>
                      {root}
                    </div>
                  ))}
                </div>
              </div>

              {/* Tool risk levels */}
              <div>
                <div style={sectionTitleStyle}>Tool Risk Levels</div>
                <div style={{ ...cardStyle, maxHeight: "200px", overflowY: "auto" }}>
                  {Object.entries(settings.tool_risk_levels).map(([tool, level]) => (
                    <div key={tool} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px", padding: "4px 0" }}>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", color: "var(--text-secondary)" }}>{tool}</span>
                      <span style={{
                        color: level === "safe" ? "var(--success)" : level === "blocked" ? "var(--error)" : "var(--creator)",
                        fontWeight: 600,
                        fontSize: "11px",
                        textTransform: "uppercase",
                      }}>{level}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Omni Connectors Shortcut */}
              <div>
                <div style={sectionTitleStyle}>Extensions</div>
                <div style={cardStyle}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                      Manage MCP servers and external tools.
                    </div>
                    <button
                      onClick={() => {
                        onClose();
                        (window as any).showConnectors?.();
                      }}
                      style={{
                        padding: "10px",
                        background: "var(--accent)",
                        border: "none",
                        borderRadius: "var(--radius-md)",
                        color: "#fff",
                        fontWeight: 600,
                        cursor: "pointer",
                        fontSize: "13px",
                      }}
                    >
                      Open Omni Connectors
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
