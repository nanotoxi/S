import React from "react";

export default function OptionButtons({ choices, onSelect, disabled }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginLeft: 36, marginTop: 6, marginBottom: 8 }}>
      {choices.map((choice) => (
        <button
          key={choice.value}
          onClick={() => !disabled && onSelect(choice)}
          disabled={disabled}
          style={{
            padding: "7px 16px",
            borderRadius: 20,
            border: "1px solid #4f46e5",
            background: disabled ? "#1e2535" : "transparent",
            color: disabled ? "#64748b" : "#a5b4fc",
            fontSize: 13,
            cursor: disabled ? "not-allowed" : "pointer",
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) => { if (!disabled) e.currentTarget.style.background = "#4f46e5"; e.currentTarget.style.color = "#fff"; }}
          onMouseLeave={(e) => { if (!disabled) { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#a5b4fc"; } }}
        >
          {choice.label}
        </button>
      ))}
    </div>
  );
}
