import React, { useState, useRef } from "react";

export default function InputBar({ onSend, onFileUpload, disabled, awaitingFile, inputRef: externalRef }) {
  const [text, setText] = useState("");
  const fileRef = useRef(null);
  const internalRef = useRef(null);
  const textareaRef = externalRef || internalRef;

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend({ type: "text", content: trimmed });
    setText("");
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFile = (e) => {
    const file = e.target.files?.[0];
    if (file) onFileUpload(file);
    e.target.value = "";
  };

  return (
    <div style={{
      display: "flex",
      alignItems: "flex-end",
      gap: 8,
      padding: "12px 16px",
      borderTop: "1px solid #1e2535",
      background: "#0f1117",
    }}>
      <input type="file" ref={fileRef} style={{ display: "none" }} accept=".pdf,.docx" onChange={handleFile} />

      <button
        onClick={() => fileRef.current?.click()}
        disabled={disabled}
        title="Upload resume"
        style={{
          width: 38,
          height: 38,
          borderRadius: "50%",
          border: "1px solid #334155",
          background: awaitingFile ? "#4f46e5" : "transparent",
          color: awaitingFile ? "#fff" : "#94a3b8",
          cursor: disabled ? "not-allowed" : "pointer",
          fontSize: 16,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          transition: "all 0.15s",
        }}
      >
        📎
      </button>

      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKey}
        disabled={disabled}
        placeholder={awaitingFile ? "Upload your resume using 📎..." : "Type a message..."}
        rows={1}
        style={{
          flex: 1,
          resize: "none",
          background: "#1e2535",
          border: "1px solid #334155",
          borderRadius: 20,
          padding: "9px 14px",
          color: "#e2e8f0",
          fontSize: 14,
          outline: "none",
          fontFamily: "inherit",
          lineHeight: 1.5,
          maxHeight: 120,
          overflowY: "auto",
          opacity: disabled ? 0.5 : 1,
        }}
      />

      <button
        onClick={handleSend}
        disabled={disabled || !text.trim()}
        style={{
          width: 38,
          height: 38,
          borderRadius: "50%",
          border: "none",
          background: disabled || !text.trim() ? "#334155" : "#4f46e5",
          color: "#fff",
          cursor: disabled || !text.trim() ? "not-allowed" : "pointer",
          fontSize: 16,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          transition: "all 0.15s",
        }}
      >
        ➤
      </button>
    </div>
  );
}
