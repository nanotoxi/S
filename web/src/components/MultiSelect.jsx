import React, { useState, useRef } from "react";

export default function MultiSelect({ field, suggestions, onDone, disabled }) {
  const [selected, setSelected] = useState(new Set());
  const [custom, setCustom] = useState("");
  const [extras, setExtras] = useState([]);
  const inputRef = useRef(null);

  const toggle = (item) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(item)) next.delete(item);
      else next.add(item);
      return next;
    });
  };

  const addCustom = () => {
    const val = custom.trim();
    if (!val || extras.includes(val) || suggestions.includes(val)) return;
    setExtras((prev) => [...prev, val]);
    setSelected((prev) => new Set([...prev, val]));
    setCustom("");
    inputRef.current?.focus();
  };

  const handleKey = (e) => {
    if (e.key === "Enter") { e.preventDefault(); addCustom(); }
  };

  const handleDone = () => {
    if (selected.size === 0) return;
    onDone(JSON.stringify([...selected]));
  };

  const allItems = [...suggestions, ...extras];

  return (
    <div style={{ marginLeft: 36, marginTop: 8, marginBottom: 12 }}>
      {/* Chip grid */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
        {allItems.map((item) => {
          const active = selected.has(item);
          return (
            <button
              key={item}
              onClick={() => !disabled && toggle(item)}
              disabled={disabled}
              style={{
                padding: "6px 12px",
                borderRadius: 20,
                border: `1px solid ${active ? "#4f46e5" : "#334155"}`,
                background: active ? "#4f46e5" : "#1e2535",
                color: active ? "#fff" : "#94a3b8",
                fontSize: 13,
                cursor: disabled ? "not-allowed" : "pointer",
                transition: "all 0.15s",
                display: "flex",
                alignItems: "center",
                gap: 4,
              }}
            >
              {active && <span style={{ fontSize: 11 }}>✓</span>}
              {item}
            </button>
          );
        })}
      </div>

      {/* Add custom */}
      {!disabled && (
        <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
          <input
            ref={inputRef}
            value={custom}
            onChange={(e) => setCustom(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Add a custom item..."
            style={{
              flex: 1,
              background: "#1e2535",
              border: "1px solid #334155",
              borderRadius: 8,
              padding: "7px 12px",
              color: "#e2e8f0",
              fontSize: 13,
              outline: "none",
              fontFamily: "inherit",
            }}
          />
          <button
            onClick={addCustom}
            style={{
              padding: "7px 14px",
              borderRadius: 8,
              border: "1px solid #334155",
              background: "#1e2535",
              color: "#94a3b8",
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            + Add
          </button>
        </div>
      )}

      {/* Done button */}
      {!disabled && (
        <button
          onClick={handleDone}
          disabled={selected.size === 0}
          style={{
            padding: "8px 20px",
            borderRadius: 8,
            border: "none",
            background: selected.size === 0 ? "#334155" : "#4f46e5",
            color: "#fff",
            fontSize: 13,
            fontWeight: 600,
            cursor: selected.size === 0 ? "not-allowed" : "pointer",
            transition: "background 0.15s",
          }}
        >
          Done ({selected.size} selected)
        </button>
      )}
    </div>
  );
}
