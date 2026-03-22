import type { CSSProperties, ReactNode } from "react";

interface Props {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  padding?: string;
}

const baseStyle: CSSProperties = {
  background: "var(--glass-bg)",
  backdropFilter: "blur(var(--glass-blur))",
  WebkitBackdropFilter: "blur(var(--glass-blur))",
  border: "1px solid var(--glass-border)",
  borderRadius: "var(--radius)",
  boxShadow: "var(--glass-shadow)",
};

export function GlassCard({ children, className, style, padding = "16px" }: Props) {
  return (
    <div className={className} style={{ ...baseStyle, padding, ...style }}>
      {children}
    </div>
  );
}
