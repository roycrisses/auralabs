import { useState, type CSSProperties } from "react";
import { ChatPanel } from "./components/ChatPanel";
import { InputBar } from "./components/InputBar";
import { SettingsPanel } from "./components/SettingsPanel";
import { StatusBar } from "./components/StatusBar";
import { ThinkingLog } from "./components/ThinkingLog";
import { TitleBar } from "./components/TitleBar";
import { useHardware } from "./hooks/useHardware";
import { useWebSocket } from "./hooks/useWebSocket";

const shellStyle: CSSProperties = {
  height: "100vh",
  width: "100vw",
  display: "flex",
  flexDirection: "column",
  background: "var(--bg-card)",
  borderRadius: "var(--radius-lg)",
  border: "1px solid var(--glass-border)",
  overflow: "hidden",
  backdropFilter: "blur(var(--glass-blur))",
  WebkitBackdropFilter: "blur(var(--glass-blur))",
};

const bodyStyle: CSSProperties = {
  flex: 1,
  display: "flex",
  overflow: "hidden",
};

export default function App() {
  const { sendMessage } = useWebSocket();
  useHardware();
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div style={shellStyle}>
      <TitleBar onSettingsClick={() => setShowSettings((v) => !v)} />
      <div style={bodyStyle}>
        <ChatPanel />
        <ThinkingLog />
        {showSettings && <SettingsPanel onClose={() => setShowSettings(false)} />}
      </div>
      <InputBar onSend={sendMessage} />
      <StatusBar />
    </div>
  );
}
