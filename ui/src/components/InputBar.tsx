import { useRef, useState } from "react";
import { useChatStore } from "../stores/chatStore";
import type { Attachment } from "../types";
import type { CSSProperties, DragEvent, KeyboardEvent } from "react";

interface Props {
  onSend: (message: string, attachments?: string[]) => void;
}

const barStyle: CSSProperties = {
  padding: "12px 16px",
  borderTop: "1px solid var(--glass-border)",
  display: "flex",
  flexDirection: "column",
  gap: "8px",
};

const inputRowStyle: CSSProperties = {
  display: "flex",
  gap: "10px",
  alignItems: "flex-end",
};

const inputStyle: CSSProperties = {
  flex: 1,
  padding: "10px 14px",
  background: "rgba(255, 255, 255, 0.04)",
  border: "1px solid var(--glass-border)",
  borderRadius: "var(--radius)",
  color: "var(--text-primary)",
  fontFamily: "inherit",
  fontSize: "14px",
  lineHeight: 1.5,
  resize: "none",
  outline: "none",
  minHeight: "42px",
  maxHeight: "120px",
  transition: "border-color 0.2s",
};

const btnStyle: CSSProperties = {
  padding: "10px 20px",
  background: "var(--accent)",
  border: "none",
  borderRadius: "var(--radius)",
  color: "#fff",
  fontWeight: 600,
  fontSize: "13px",
  cursor: "pointer",
  transition: "opacity 0.2s, transform 0.1s",
  whiteSpace: "nowrap",
};

const iconBtnStyle: CSSProperties = {
  padding: "10px",
  background: "rgba(255, 255, 255, 0.04)",
  border: "1px solid var(--glass-border)",
  borderRadius: "var(--radius)",
  color: "var(--text-secondary)",
  cursor: "pointer",
  fontSize: "16px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  transition: "background 0.2s, color 0.2s",
};

const attachmentBarStyle: CSSProperties = {
  display: "flex",
  gap: "6px",
  flexWrap: "wrap",
  padding: "0 4px",
};

const attachmentChipStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "4px",
  padding: "4px 8px",
  background: "rgba(255, 255, 255, 0.06)",
  border: "1px solid var(--glass-border)",
  borderRadius: "12px",
  fontSize: "12px",
  color: "var(--text-secondary)",
};

const dropOverlayStyle: CSSProperties = {
  position: "absolute",
  inset: 0,
  background: "rgba(59, 130, 246, 0.1)",
  border: "2px dashed var(--accent)",
  borderRadius: "var(--radius)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "var(--accent)",
  fontSize: "14px",
  fontWeight: 600,
  zIndex: 10,
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
  const [isDragging, setIsDragging] = useState(false);
  const isProcessing = useChatStore((s) => s.isProcessing);
  const attachments = useChatStore((s) => s.pendingAttachments);
  const addAttachment = useChatStore((s) => s.addAttachment);
  const removeAttachment = useChatStore((s) => s.removeAttachment);
  const ref = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const send = () => {
    const trimmed = text.trim();
    if (!trimmed || isProcessing) return;
    const paths = attachments.map((a) => a.path);
    onSend(trimmed, paths.length > 0 ? paths : undefined);
    setText("");
    if (ref.current) {
      ref.current.style.height = "42px";
    }
  };

  const handleKey = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const handleInput = () => {
    if (ref.current) {
      ref.current.style.height = "42px";
      ref.current.style.height = `${Math.min(ref.current.scrollHeight, 120)}px`;
    }
  };

  const handleFiles = async (files: FileList | File[]) => {
    for (const file of Array.from(files)) {
      const result = await uploadFile(file);
      if (result) addAttachment(result);
    }
  };

  const onDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div style={{ ...barStyle, position: "relative" }} onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}>
      {isDragging && <div style={dropOverlayStyle}>Drop files here</div>}

      {attachments.length > 0 && (
        <div style={attachmentBarStyle}>
          {attachments.map((a) => (
            <span key={a.path} style={attachmentChipStyle}>
              {a.type === "image" ? "\uD83D\uDDBC" : "\uD83D\uDCC4"} {a.filename}
              <button
                onClick={() => removeAttachment(a.path)}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--text-secondary)",
                  cursor: "pointer",
                  padding: "0 2px",
                  fontSize: "14px",
                }}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <div style={inputRowStyle}>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".png,.jpg,.jpeg,.gif,.webp,.pdf,.txt,.md,.csv,.json,.yaml,.yml"
          style={{ display: "none" }}
          onChange={(e) => {
            if (e.target.files) handleFiles(e.target.files);
            e.target.value = "";
          }}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          style={iconBtnStyle}
          title="Attach files"
          disabled={isProcessing}
        >
          📎
        </button>
        <textarea
          ref={ref}
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            handleInput();
          }}
          onKeyDown={handleKey}
          placeholder="Ask Aura anything..."
          rows={1}
          style={{
            ...inputStyle,
            borderColor: text ? "var(--glass-border-light)" : "var(--glass-border)",
          }}
          disabled={isProcessing}
        />
        <button
          onClick={send}
          disabled={!text.trim() || isProcessing}
          style={{
            ...btnStyle,
            opacity: !text.trim() || isProcessing ? 0.4 : 1,
          }}
        >
          {isProcessing ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
