import { useEffect, useState, type CSSProperties } from "react";
import { GlassCard } from "./GlassCard";

interface Settings {
  models: Record<string, string>;
  confirmation_enabled: boolean;
  tool_risk_levels: Record<string, string>;
  allowed_roots: string[];
}

const API = "http://localhost:8420/api";

const panelStyle: CSSProperties = {
  position: "fixed",
  top: 0,
  right: 0,
  width: "380px",
  height: "100vh",
  zIndex: 100,
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
  borderLeft: "1px solid var(--glass-border)",
  background: "var(--bg-card)",
};

const headerStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "12px 16px",
  borderBottom: "1px solid var(--glass-border)",
};

const bodyStyle: CSSProperties = {
  flex: 1,
  overflowY: "auto",
  padding: "12px 16px",
  display: "flex",
  flexDirection: "column",
  gap: "16px",
};

const labelStyle: CSSProperties = {
  fontSize: "11px",
  textTransform: "uppercase",
  opacity: 0.6,
  letterSpacing: "0.5px",
  marginBottom: "6px",
};

const inputStyle: CSSProperties = {
  width: "100%",
  padding: "6px 10px",
  background: "rgba(255,255,255,0.05)",
  border: "1px solid var(--glass-border)",
  borderRadius: "6px",
  color: "inherit",
  fontSize: "13px",
  fontFamily: "inherit",
};

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
    if (settings) {
      setSettings({ ...settings, models: data.models });
    }
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

  if (error) {
    return (
      <div style={panelStyle}>
        <div style={headerStyle}>
          <strong>Settings</strong>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "inherit", cursor: "pointer" }}>X</button>
        </div>
        <div style={bodyStyle}>
          <p style={{ color: "var(--accent-red, #f66)" }}>Failed to load settings: {error}</p>
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div style={panelStyle}>
        <div style={headerStyle}>
          <strong>Settings</strong>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "inherit", cursor: "pointer" }}>X</button>
        </div>
        <div style={bodyStyle}><p>Loading...</p></div>
      </div>
    );
  }

  return (
    <div style={panelStyle}>
      <div style={headerStyle}>
        <strong>Settings</strong>
        <button onClick={onClose} style={{ background: "none", border: "none", color: "inherit", cursor: "pointer", fontSize: "16px" }}>X</button>
      </div>
      <div style={bodyStyle}>
        {/* Model configuration */}
        <GlassCard padding="12px">
          <div style={labelStyle}>Agent Models</div>
          {Object.entries(settings.models).map(([role, model]) => (
            <div key={role} style={{ marginBottom: "8px" }}>
              <div style={{ fontSize: "12px", fontWeight: 600, marginBottom: "4px", textTransform: "capitalize" }}>{role}</div>
              <input
                style={inputStyle}
                value={model}
                onChange={(e) => {
                  setSettings({ ...settings, models: { ...settings.models, [role]: e.target.value } });
                }}
                onBlur={(e) => updateModel(role, e.target.value)}
              />
            </div>
          ))}
        </GlassCard>

        {/* Safety settings */}
        <GlassCard padding="12px">
          <div style={labelStyle}>Safety</div>
          <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={settings.confirmation_enabled}
              onChange={toggleConfirmation}
            />
            <span style={{ fontSize: "13px" }}>Require confirmation for dangerous tools</span>
          </label>
        </GlassCard>

        {/* Allowed roots */}
        <GlassCard padding="12px">
          <div style={labelStyle}>Allowed File Roots</div>
          {settings.allowed_roots.map((root, i) => (
            <div key={i} style={{ fontSize: "12px", padding: "4px 0", opacity: 0.8, fontFamily: "monospace" }}>{root}</div>
          ))}
        </GlassCard>

        {/* Tool risk levels */}
        <GlassCard padding="12px">
          <div style={labelStyle}>Tool Risk Levels</div>
          <div style={{ maxHeight: "200px", overflowY: "auto" }}>
            {Object.entries(settings.tool_risk_levels).map(([tool, level]) => (
              <div key={tool} style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", padding: "3px 0" }}>
                <span style={{ fontFamily: "monospace" }}>{tool}</span>
                <span style={{
                  color: level === "safe" ? "#4f4" : level === "blocked" ? "#f44" : "#ff4",
                  fontWeight: 600,
                  fontSize: "11px",
                }}>{level}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
