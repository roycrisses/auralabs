import { useState, useCallback, useEffect, type CSSProperties } from "react";
import { LogicalSize, getCurrentWindow } from "@tauri-apps/api/window";
import { ChatPanel } from "./components/ChatPanel";
import { InputBar } from "./components/InputBar";
import { SettingsPanel } from "./components/SettingsPanel";
import { Sidebar } from "./components/Sidebar";
import { ConnectorsPanel } from "./components/ConnectorsPanel";
import { BlobView } from "./components/BlobView";
import { useHardware } from "./hooks/useHardware";
import { useWebSocket } from "./hooks/useWebSocket";

const appStyle: CSSProperties = {
  height: "100vh",
  width: "100vw",
  display: "flex",
  background: "var(--bg-primary)",
  overflow: "hidden",
};

const mainStyle: CSSProperties = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
  position: "relative",
};

export default function App() {
  const { sendMessage } = useWebSocket();
  useHardware();
  const [showSettings, setShowSettings] = useState(false);
  const [showConnectors, setShowConnectors] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isBlob, setIsBlob] = useState(false);

  const toggleBlob = useCallback(async (blob: boolean) => {
    setIsBlob(blob);
    const win = getCurrentWindow();
    if (blob) {
      await win.setSize(new LogicalSize(100, 100)); // Default blob size
      await win.setAlwaysOnTop(true);
      await win.setDecorations(false);
      await win.setShadow(false); // Important for floating feel
    } else {
      await win.setSize(new LogicalSize(1000, 750));
      await win.setAlwaysOnTop(false);
      await win.setDecorations(false); // Keep custom titlebar feel
      await win.setShadow(true);
      await win.center();
    }
  }, []);

  const handleBlobHover = useCallback(async (hovered: boolean) => {
    if (!isBlob) return;
    const win = getCurrentWindow();
    if (hovered) {
      // Expand to fit mini-chat
      await win.setSize(new LogicalSize(340, 450));
    } else {
      // Collapse back to blob
      await win.setSize(new LogicalSize(100, 100));
    }
  }, [isBlob]);

  useEffect(() => {
    (window as any).toggleBlob = toggleBlob;
    (window as any).showConnectors = () => setShowConnectors(true);
    return () => { 
      delete (window as any).toggleBlob; 
      delete (window as any).showConnectors;
    };
  }, [toggleBlob]);

  if (isBlob) {
    return (
      <div style={{ width: '100vw', height: '100vh', background: 'transparent', display: 'flex', alignItems: 'flex-end', justifyContent: 'center', paddingBottom: '20px' }}>
        <BlobView 
          status="idle" 
          onExpand={() => toggleBlob(false)} 
          onHover={handleBlobHover}
        />
      </div>
    );
  }

  return (
    <div style={appStyle}>
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((v) => !v)}
        onSettingsClick={() => setShowSettings((v) => !v)}
        onConnectorsClick={() => setShowConnectors((v) => !v)}
      />
      <div style={mainStyle}>
        <ChatPanel />
        <InputBar onSend={sendMessage} />
      </div>
      {showSettings && <SettingsPanel onClose={() => setShowSettings(false)} />}
      {showConnectors && <ConnectorsPanel onClose={() => setShowConnectors(false)} />}
    </div>
  );
}
