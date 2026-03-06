import { useRef, useState } from "react";
import { useChatStore } from "../stores/chatStore";
import type { Attachment } from "../types";
import type { CSSProperties, DragEvent, KeyboardEvent } from "react";

interface Props {
  onSend: (message: string, attachments?: string[]) => void;
}

const wrapperStyle: CSSProperties = {
  padding: "0 24px 20px",
  display: "flex",
  justifyContent: "center",
};

const barStyle: CSSProperties = {
  maxWidth: "var(--max-chat-width)",
  width: "100%",
  position: "relative",
};

const inputContainerStyle: CSSProperties = {
  background: "var(--bg-input)",
  border: "1px solid var(--border-primary)",
  borderRadius: "var(--radius-lg)",
  padding: "4px",
  display: "flex",
  flexDirection: "column",
  transition: "border-color var(--transition), box-shadow var(--transition)",
};

const inputContainerFocusStyle: CSSProperties = {
  ...inputContainerStyle,
  borderColor: "var(--border-focus)",
  boxShadow: "0 0 0 2px rgba(139, 92, 246, 0.1)",
};

const textareaStyle: CSSProperties = {
  width: "100%",
  padding: "12px 16px 8px",
  background: "transparent",
  border: "none",
  color: "var(--text-primary)",
  fontFamily: "inherit",
  fontSize: "15px",
  lineHeight: 1.5,
  resize: "none",
  outline: "none",
  minHeight: "44px",
  maxHeight: "200px",
};

const actionsRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "4px 8px 6px",
};

const leftActionsStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "2px",
};

const iconBtnStyle: CSSProperties = {
  width: "32px",
  height: "32px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  background: "transparent",
  border: "none",
  borderRadius: "var(--radius-sm)",
  color: "var(--text-tertiary)",
  cursor: "pointer",
  transition: "background var(--transition), color var(--transition)",
};

const sendBtnStyle = (active: boolean): CSSProperties => ({
  width: "32px",
  height: "32px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  background: active ? "var(--accent)" : "var(--bg-tertiary)",
  border: "none",
  borderRadius: "var(--radius-sm)",
  color: active ? "#fff" : "var(--text-tertiary)",
  cursor: active ? "pointer" : "default",
  transition: "background var(--transition), color var(--transition)",
});

const attachmentBarStyle: CSSProperties = {
  display: "flex",
  gap: "6px",
  flexWrap: "wrap",
  padding: "6px 12px 0",
};

const chipStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "6px",
  padding: "4px 10px",
  background: "rgba(255, 255, 255, 0.05)",
  border: "1px solid var(--border-primary)",
  borderRadius: "var(--radius-pill)",
  fontSize: "12px",
  color: "var(--text-secondary)",
};

const dropOverlayStyle: CSSProperties = {
  position: "absolute",
  inset: 0,
  background: "rgba(139, 92, 246, 0.08)",
  border: "2px dashed var(--accent)",
  borderRadius: "var(--radius-lg)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "var(--accent)",
  fontSize: "14px",
  fontWeight: 500,
  zIndex: 10,
};

const hintStyle: CSSProperties = {
  textAlign: "center",
  fontSize: "11px",
  color: "var(--text-tertiary)",
  padding: "6px 0 0",
};

const API_BASE = "http://127.0.0.1:8420/api";

async function uploadFile(file: File): Promise<Attachment | null> {
  const formData = new FormData();
  formData.append("file", file);
  try {
    const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export function InputBar({ onSend }: Props) {
  const [text, setText] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const isProcessing = useChatStore((s) => s.isProcessing);
  const attachments = useChatStore((s) => s.pendingAttachments);
  const addAttachment = useChatStore((s) => s.addAttachment);
  const removeAttachment = useChatStore((s) => s.removeAttachment);
  const ref = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const canSend = text.trim().length > 0 && !isProcessing;

  const send = () => {
    const trimmed = text.trim();
    if (!trimmed || isProcessing) return;
    const paths = attachments.map((a) => a.path);
    onSend(trimmed, paths.length > 0 ? paths : undefined);
    setText("");
    if (ref.current) ref.current.style.height = "44px";
  };

  const handleKey = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const handleInput = () => {
    if (ref.current) {
      ref.current.style.height = "44px";
      ref.current.style.height = `${Math.min(ref.current.scrollHeight, 200)}px`;
    }
  };

  const handleFiles = async (files: FileList | File[]) => {
    for (const file of Array.from(files)) {
      const result = await uploadFile(file);
      if (result) addAttachment(result);
    }
  };

  const onDragOver = (e: DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const onDragLeave = (e: DragEvent) => { e.preventDefault(); setIsDragging(false); };
  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files.length > 0) handleFiles(e.dataTransfer.files);
  };

  return (
    <div style={wrapperStyle}>
      <div style={barStyle} onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}>
        {isDragging && <div style={dropOverlayStyle}>Drop files here</div>}

        <div style={isFocused ? inputContainerFocusStyle : inputContainerStyle}>
          {/* Attachments */}
          {attachments.length > 0 && (
            <div style={attachmentBarStyle}>
              {attachments.map((a) => (
                <span key={a.path} style={chipStyle}>
                  {a.type === "image" ? "🖼" : "📄"} {a.filename}
                  <button
                    onClick={() => removeAttachment(a.path)}
                    style={{ background: "none", border: "none", color: "var(--text-tertiary)", cursor: "pointer", padding: 0, fontSize: "14px", lineHeight: 1 }}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Textarea */}
          <textarea
            ref={ref}
            value={text}
            onChange={(e) => { setText(e.target.value); handleInput(); }}
            onKeyDown={handleKey}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Message Aura..."
            rows={1}
            style={textareaStyle}
            disabled={isProcessing}
          />

          {/* Action row */}
          <div style={actionsRowStyle}>
            <div style={leftActionsStyle}>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".png,.jpg,.jpeg,.gif,.webp,.pdf,.txt,.md,.csv,.json,.yaml,.yml"
                style={{ display: "none" }}
                onChange={(e) => { if (e.target.files) handleFiles(e.target.files); e.target.value = ""; }}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                style={iconBtnStyle}
                title="Attach files"
                disabled={isProcessing}
                onMouseEnter={(e) => { (e.target as HTMLElement).style.background = "var(--bg-hover)"; (e.target as HTMLElement).style.color = "var(--text-secondary)"; }}
                onMouseLeave={(e) => { (e.target as HTMLElement).style.background = "transparent"; (e.target as HTMLElement).style.color = "var(--text-tertiary)"; }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                </svg>
              </button>
            </div>
            <button
              onClick={send}
              disabled={!canSend}
              style={sendBtnStyle(canSend)}
              title="Send message"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z"/>
              </svg>
            </button>
          </div>
        </div>

        <div style={hintStyle}>
          Aura can make mistakes. Verify important information.
        </div>
      </div>
    </div>
  );
}
