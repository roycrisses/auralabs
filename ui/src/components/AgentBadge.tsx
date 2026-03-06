import { AGENT_COLORS } from "../types";
import type { CSSProperties } from "react";

interface Props {
  agent: string;
  size?: "sm" | "md";
  pulse?: boolean;
}

export function AgentBadge({ agent, size = "sm", pulse = false }: Props) {
  const color = AGENT_COLORS[agent] ?? "#888";
  const fontSize = size === "sm" ? "11px" : "12px";
  const pad = size === "sm" ? "2px 8px" : "3px 10px";

  const style: CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: "5px",
    padding: pad,
    fontSize,
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    color,
    background: `${color}18`,
    border: `1px solid ${color}30`,
    borderRadius: "6px",
    whiteSpace: "nowrap",
  };

  const dotStyle: CSSProperties = {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    background: color,
    animation: pulse ? "pulse-dot 1.5s ease-in-out infinite" : "none",
  };

  return (
    <span style={style}>
      <span style={dotStyle} />
      {agent}
    </span>
  );
}
