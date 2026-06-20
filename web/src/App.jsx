import React, { useEffect, useRef, useState } from "react";
import { useChat } from "./hooks/useChat";
import MessageBubble from "./components/MessageBubble";
import OptionButtons from "./components/OptionButtons";
import MultiSelect from "./components/MultiSelect";
import TypingIndicator from "./components/TypingIndicator";
import InputBar from "./components/InputBar";
import LandingPage from "./components/LandingPage";
import EmployerResults from "./components/EmployerResults";
import CandidateResults from "./components/CandidateResults";

function ChatView({ role, onDone }) {
  const { messages, status, isTyping, send, uploadFile } = useChat(role);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    if (!isTyping && status === "connected") {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isTyping, messages.length, status]);

  useEffect(() => {
    if (status === "done") {
      setTimeout(onDone, 1200);
    }
  }, [status, onDone]);

  const lastInteractiveIdx = (() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.from === "bot" && (m.type === "options" || m.type === "multi_select")) return i;
      if (m.from === "user") return -1;
    }
    return -1;
  })();

  const awaitingFile = messages.some(
    (m, i) =>
      m.from === "bot" &&
      m.type === "file_request" &&
      !messages.slice(i + 1).some((x) => x.from === "user")
  );

  const isInputDisabled =
    status === "done" || status === "connecting" || status === "error" || isTyping;

  const handleOptionSelect = (choice) => {
    send({ type: "option", value: choice.value, content: choice.label });
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const handleMultiSelectDone = (jsonStr) => {
    const items = JSON.parse(jsonStr);
    send({ type: "multi_select_done", value: jsonStr, content: items.join(", ") });
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  return (
    <div style={{
      width: "100%",
      maxWidth: 720,
      height: "100dvh",
      display: "flex",
      flexDirection: "column",
      background: "#0f1117",
    }}>
      {/* Header */}
      <div style={{
        padding: "14px 20px",
        borderBottom: "1px solid #1e2535",
        display: "flex",
        alignItems: "center",
        gap: 10,
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: "50%",
          background: role === "candidate" ? "#7c3aed" : "#4f46e5",
          display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
        }}>🤖</div>
        <div>
          <div style={{ fontWeight: 600, fontSize: 15 }}>Sath Bot</div>
          <div style={{
            fontSize: 12,
            color: status === "connected" || status === "done" ? "#22c55e" : "#64748b",
          }}>
            {status === "connecting" ? "Connecting..."
              : status === "connected" ? "Online"
              : status === "done" ? "Preparing your results..."
              : status === "error" ? "Connection error"
              : ""}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px 16px 8px" }}>
        {messages.map((msg, idx) => {
          if (msg.from === "bot" && msg.type === "options") {
            return (
              <div key={msg.id}>
                {msg.content && <MessageBubble message={{ ...msg, type: "bot_message" }} />}
                <OptionButtons
                  choices={msg.choices}
                  disabled={idx !== lastInteractiveIdx || isTyping}
                  onSelect={handleOptionSelect}
                />
              </div>
            );
          }
          if (msg.from === "bot" && msg.type === "multi_select") {
            return (
              <div key={msg.id}>
                {msg.content && <MessageBubble message={{ ...msg, type: "bot_message" }} />}
                <MultiSelect
                  field={msg.field}
                  suggestions={msg.suggestions || []}
                  disabled={idx !== lastInteractiveIdx || isTyping}
                  onDone={handleMultiSelectDone}
                />
              </div>
            );
          }
          if (msg.from === "bot" && (msg.type === "bot_message" || msg.type === "file_request")) {
            return <MessageBubble key={msg.id} message={{ ...msg, type: "bot_message" }} />;
          }
          if (msg.from === "user") {
            return <MessageBubble key={msg.id} message={msg} />;
          }
          return null;
        })}

        {isTyping && <TypingIndicator />}

        {status === "done" && (
          <div style={{ textAlign: "center", color: "#64748b", fontSize: 13, margin: "16px 0" }}>
            Loading your results...
          </div>
        )}
        {status === "error" && (
          <div style={{ textAlign: "center", color: "#ef4444", fontSize: 13, margin: "16px 0" }}>
            Connection error. Please refresh and try again.
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <InputBar
        inputRef={inputRef}
        onSend={send}
        onFileUpload={uploadFile}
        disabled={isInputDisabled}
        awaitingFile={awaitingFile}
      />
    </div>
  );
}

export default function App() {
  const [view, setView] = useState("landing"); // "landing" | "chat" | "results"
  const [role, setRole] = useState(null);

  const handleRoleSelect = (selectedRole) => {
    setRole(selectedRole);
    setView("chat");
  };

  const handleChatDone = () => setView("results");

  const handleReset = () => {
    setRole(null);
    setView("landing");
  };

  if (view === "landing") {
    return <LandingPage onSelect={handleRoleSelect} />;
  }

  if (view === "chat") {
    return (
      <div style={{
        width: "100%", height: "100dvh",
        display: "flex", alignItems: "center", justifyContent: "center",
        background: "#0f1117",
      }}>
        <ChatView role={role} onDone={handleChatDone} />
      </div>
    );
  }

  if (view === "results") {
    return role === "employer"
      ? <EmployerResults onReset={handleReset} />
      : <CandidateResults onReset={handleReset} />;
  }

  return null;
}
