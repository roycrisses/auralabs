import { useState, useEffect, type CSSProperties } from "react";
import { invoke } from "@tauri-apps/api/core";

interface MCPServer {
  name: string;
  transport: string;
  args: string[];
  status: string;
}

const overlayStyle: CSSProperties = {
  position: "fixed",
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  background: "rgba(0,0,0,0.7)",
  backdropFilter: "blur(12px)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 1000,
};

const panelStyle: CSSProperties = {
  width: "600px",
  maxHeight: "85vh",
  background: "linear-gradient(135deg, rgba(30, 30, 35, 0.95), rgba(20, 20, 25, 0.98))",
  borderRadius: "24px",
  border: "1px solid rgba(255, 255, 255, 0.1)",
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
  boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
};

const headerStyle: CSSProperties = {
  padding: "24px 32px",
  borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
};

const contentStyle: CSSProperties = {
  padding: "32px",
  overflowY: "auto",
  display: "flex",
  flexDirection: "column",
  gap: "28px",
};

const inputStyle: CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  background: "rgba(255, 255, 255, 0.05)",
  border: "1px solid rgba(255, 255, 255, 0.1)",
  borderRadius: "12px",
  color: "#fff",
  fontSize: "14px",
  outline: "none",
  fontFamily: "inherit",
};

const sectionTitleStyle: CSSProperties = {
  fontSize: "12px",
  fontWeight: 700,
  color: "rgba(255, 255, 255, 0.4)",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  marginBottom: "12px",
};

const templateCardStyle: CSSProperties = {
  padding: "16px",
  background: "rgba(255, 255, 255, 0.03)",
  borderRadius: "16px",
  border: "1px solid rgba(255, 255, 255, 0.05)",
  cursor: "pointer",
  transition: "all 0.2s ease",
  display: "flex",
  flexDirection: "column",
  gap: "4px",
  textAlign: "left" as const,
};

const API_BASE = "http://127.0.0.1:8420/api/mcp/servers";

export function ConnectorsPanel({ onClose }: { onClose: () => void }) {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [newName, setNewName] = useState("");
  const [newCommand, setNewCommand] = useState("");
  const [newArgs, setNewArgs] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchServers = async () => {
    try {
      const res = await fetch(API_BASE);
      if (res.ok) {
        setServers(await res.json());
      }
    } catch (err) {
      console.error("Failed to list MCP servers:", err);
    }
  };

  useEffect(() => {
    fetchServers();
  }, []);

  const addServer = async (name: string, command: string, args: string) => {
    setLoading(true);
    try {
      const res = await fetch(API_BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          name, 
          command, 
          args: args.split(",").map(a => a.trim()).filter(a => a) 
        })
      });
      if (res.ok) {
        setNewName("");
        setNewCommand("");
        setNewArgs("");
        await fetchServers();
      }
    } catch (err) {
      console.error("Failed to add MCP server:", err);
    } finally {
      setLoading(false);
    }
  };

  const removeServer = async (name: string) => {
    try {
      const res = await fetch(`${API_BASE}/${name}`, { method: "DELETE" });
      if (res.ok) {
        await fetchServers();
      }
    } catch (err) {
      console.error("Failed to remove MCP server:", err);
    }
  };

  const templates = [
    { name: "Filesystem", cmd: "npx", args: "-y @modelcontextprotocol/server-filesystem D:\\automation", desc: "Access local files" },
    { name: "Google Maps", cmd: "npx", args: "-y @modelcontextprotocol/server-google-maps", desc: "Lookup places and distance" },
    { name: "Memory", cmd: "npx", args: "-y @modelcontextprotocol/server-memory", desc: "Graph-based memory storage" }
  ];

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={panelStyle} onClick={(e) => e.stopPropagation()}>
        <div style={headerStyle}>
          <div>
            <h2 style={{ fontSize: "20px", fontWeight: 750, color: "#fff", margin: 0 }}>Omni Connectors</h2>
            <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.5)", marginTop: "4px" }}>Extend Aura with any MCP server.</p>
          </div>
          <button onClick={onClose} style={{ background: "rgba(255,255,255,0.05)", border: "none", color: "#fff", cursor: "pointer", width: "36px", height: "36px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        <div style={contentStyle}>
          {/* Quick Add Templates */}
          <div>
            <h3 style={sectionTitleStyle}>Recommended</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px" }}>
              {templates.map(t => (
                <button 
                  key={t.name}
                  style={templateCardStyle}
                  onClick={() => addServer(t.name.toLowerCase().replace(" ", "-"), t.cmd, t.args)}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = "rgba(255, 255, 255, 0.06)";
                    e.currentTarget.style.borderColor = "var(--accent)";
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)";
                    e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.05)";
                  }}
                >
                  <span style={{ fontWeight: 600, fontSize: "14px", color: "#fff" }}>{t.name}</span>
                  <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)" }}>{t.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Active List */}
          <div>
            <h3 style={sectionTitleStyle}>Active Connectors</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {servers.length === 0 ? (
                <div style={{ padding: "32px", textAlign: "center", color: "rgba(255,255,255,0.3)", borderRadius: "16px", border: "1px dashed rgba(255,255,255,0.1)" }}>
                  <p style={{ fontSize: "14px" }}>No connectors active at the moment.</p>
                </div>
              ) : (
                servers.map(s => (
                  <div key={s.name} style={{
                    padding: "16px 20px",
                    background: "rgba(255, 255, 255, 0.02)",
                    borderRadius: "16px",
                    border: "1px solid rgba(255, 255, 255, 0.05)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between"
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                      <div style={{
                        width: "8px", height: "8px", borderRadius: "50%",
                        background: (s as any).connected ? "#4ade80" : "#fb7185",
                        boxShadow: (s as any).connected ? "0 0 12px rgba(74, 222, 128, 0.4)" : "none"
                      }} />
                      <div style={{ display: "flex", flexDirection: "column" }}>
                        <span style={{ fontWeight: 600, color: "#fff", fontSize: "15px" }}>{s.name}</span>
                        <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "1px" }}>{s.transport}</span>
                      </div>
                    </div>
                    <button 
                      onClick={() => removeServer(s.name)}
                      style={{ background: "transparent", border: "none", color: "rgba(251, 113, 133, 0.6)", cursor: "pointer", padding: "8px" }}
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Manual Form */}
          <div style={{ 
            marginTop: "auto", 
            padding: "24px", 
            background: "rgba(255,255,255,0.03)", 
            borderRadius: "20px",
            border: "1px solid rgba(255,255,255,0.05)"
          }}>
            <h3 style={{ ...sectionTitleStyle, marginBottom: "16px" }}>Custom Connection</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
              <input 
                placeholder="ID" 
                style={{ ...inputStyle, padding: "12px 16px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.1)" }} 
                value={newName} 
                onChange={e => setNewName(e.target.value)}
              />
              <input 
                placeholder="Command (e.g. npx)" 
                style={{ ...inputStyle, padding: "12px 16px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.1)" }} 
                value={newCommand} 
                onChange={e => setNewCommand(e.target.value)}
              />
            </div>
            <input 
              placeholder="Arguments (e.g. -y @mcp/server-github)" 
              style={{ ...inputStyle, padding: "12px 16px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.1)", marginBottom: "16px" }} 
              value={newArgs} 
              onChange={e => setNewArgs(e.target.value)}
            />
            <button 
              onClick={() => addServer(newName, newCommand, newArgs)} 
              disabled={loading || !newName || !newCommand}
              style={{ 
                width: "100%", 
                padding: "14px", 
                borderRadius: "14px", 
                border: "none", 
                background: "linear-gradient(to right, var(--accent, #6366f1), #8b5cf6)", 
                color: "#fff", 
                fontWeight: 700, 
                cursor: "pointer",
                boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.3)",
                opacity: loading ? 0.7 : 1,
                transition: "all 0.2s ease"
              }}
            >
              {loading ? "Connecting..." : "Initialize Connection"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
