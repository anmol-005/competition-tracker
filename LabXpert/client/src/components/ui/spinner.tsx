import * as React from "react"

export function Spinner({ size = 20, color = "#999" }: { size?: number; color?: string }) {
  return (
    <div
      className="animate-spin inline-block"
      style={{
        width: size,
        height: size,
        border: `${size / 8}px solid ${color}33`,
        borderTop: `${size / 8}px solid ${color}`,
        borderRadius: "50%",
      }}
    />
  );
}
