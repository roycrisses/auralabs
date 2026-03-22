import { useState, type CSSProperties } from "react";

interface Props {
  onExpand: () => void;
  onHover: (hovered: boolean) => void;
  status: "idle" | "listening" | "thinking";
}

const blobContainerStyle: CSSProperties = {
  width: "100%",
  height: "100%",
  display: "flex",
  alignItems: "flex-end",
  justifyContent: "center",
  background: "transparent",
  position: "relative",
  paddingBottom: "20px",
};

export function BlobView({ onExpand, onHover, status }: Props) {
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseEnter = () => {
    setIsHovered(true);
    onHover(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    onHover(false);
  };

  return (
    <div 
      style={blobContainerStyle} 
      className="titlebar-drag"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <button 
        className={`blob-button ${status === "listening" ? "blob-listening" : ""} ${status === "thinking" ? "thinking-shimmer" : ""}`}
        onClick={onExpand}
        title="Click to expand Aura"
      >
        {/* Layered Luminous Orb */}
        <div style={{ 
          position: "absolute",
          width: "100%", 
          height: "100%", 
          background: "radial-gradient(circle at 30% 30%, rgba(255,255,255,0.4) 0%, transparent 70%)",
          zIndex: 2
        }} />
        <div style={{ 
          width: "28px", 
          height: "28px", 
          background: "#fff", 
          borderRadius: "50%", 
          filter: "blur(6px)",
          opacity: 0.6,
          boxShadow: "0 0 20px rgba(255, 255, 255, 0.8)",
          zIndex: 1,
          animation: "aura-flow 3s infinite alternate ease-in-out"
        }} />
        
        {/* Internal Flowing Elements */}
        <div style={{
          position: "absolute",
          width: "120%",
          height: "120%",
          background: "conic-gradient(from 0deg, transparent, var(--aura-purple), transparent, var(--aura-cyan), transparent)",
          opacity: 0.3,
          animation: "rotate 8s infinite linear",
          filter: "blur(4px)"
        }} />
      </button>

      {/* Mini Chat Panel on Hover */}
      {isHovered && (
        <div className="mini-chat-hover" style={{ 
          textAlign: "center",
          border: "1px solid rgba(167, 139, 250, 0.3)",
          boxShadow: "0 15px 40px rgba(0,0,0,0.4), 0 0 20px rgba(167, 139, 250, 0.1)"
        }}>
          <div style={{ 
            fontSize: "11px", 
            textTransform: "uppercase", 
            letterSpacing: "0.1em",
            color: "var(--accent)", 
            marginBottom: "12px",
            opacity: 0.8
          }}>
            Aura Neural Link
          </div>
          <div style={{ 
            fontSize: "15px", 
            fontWeight: 500,
            lineHeight: 1.4,
            color: "#fff"
          }}>
            Systems synchronized.<br/>
            <span style={{ opacity: 0.6, fontSize: "13px" }}>Awaiting instruction.</span>
          </div>
          <div style={{ marginTop: "16px", display: "flex", gap: "10px", justifyContent: "center" }}>
             <div style={{ width: "4px", height: "4px", borderRadius: "50%", background: "var(--aura-purple)", boxShadow: "0 0 8px var(--aura-purple)" }} />
             <div style={{ width: "4px", height: "4px", borderRadius: "50%", background: "var(--aura-blue)", boxShadow: "0 0 8px var(--aura-blue)" }} />
             <div style={{ width: "4px", height: "4px", borderRadius: "50%", background: "var(--aura-cyan)", boxShadow: "0 0 8px var(--aura-cyan)" }} />
          </div>
        </div>
      )}

      {status !== "idle" && (
         <div style={{
           position: "absolute",
           bottom: "10px",
           right: "10px",
           width: "8px",
           height: "8px",
           borderRadius: "50%",
           background: status === "listening" ? "var(--success)" : "var(--accent)",
           boxShadow: `0 0 10px ${status === "listening" ? "var(--success)" : "var(--accent)"}`,
           animation: "pulse-dot 1s infinite"
         }} />
      )}
    </div>
  );
}
