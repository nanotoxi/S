import React from "react";

const s = {
  row: (isBot) => ({
    display: "flex",
    justifyContent: isBot ? "flex-start" : "flex-end",
    marginBottom: 4,
  }),
  bubble: (isBot) => ({
    maxWidth: "72%",
    padding: "10px 14px",
    borderRadius: isBot ? "4px 18px 18px 18px" : "18px 4px 18px 18px",
    background: isBot ? "#1e2535" : "#4f46e5",
    color: "#e2e8f0",
    fontSize: 14,
    lineHeight: 1.6,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
  }),
};

function renderMarkdown(text) {
  // Basic bold + newline support without a full library
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}

export default function MessageBubble({ message }) {
  const isBot = message.from === "bot";
  return (
    <div style={s.row(isBot)}>
      {isBot && (
        <div style={{ width: 28, height: 28, borderRadius: "50%", background: "#4f46e5", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, marginRight: 8, flexShrink: 0, alignSelf: "flex-end" }}>
          🤖
        </div>
      )}
      <div style={s.bubble(isBot)}>{renderMarkdown(message.content)}</div>
    </div>
  );
}
