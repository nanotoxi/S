import { useState, useEffect, useRef, useCallback } from "react";

export function useChat(autoSelectRole = null) {
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState("idle");
  const [isTyping, setIsTyping] = useState(false);
  const wsRef = useRef(null);
  const sessionIdRef = useRef(null);
  const autoSelectRef = useRef(autoSelectRole);

  const addMessage = useCallback((msg) => {
    setMessages((prev) => [...prev, { ...msg, id: Date.now() + Math.random() }]);
  }, []);

  useEffect(() => {
    let active = true;

    async function init() {
      setStatus("connecting");
      try {
        const res = await fetch("/api/sessions", { method: "POST" });
        if (!active) return;

        const { session_id } = await res.json();
        if (!active) return;
        sessionIdRef.current = session_id;

        const proto = window.location.protocol === "https:" ? "wss" : "ws";
        const ws = new WebSocket(`${proto}://${window.location.host}/ws/${session_id}`);
        wsRef.current = ws;

        ws.onopen = () => { if (active) setStatus("connected"); };

        ws.onmessage = (event) => {
          if (!active) return;
          const data = JSON.parse(event.data);
          setIsTyping(false);

          // Silently auto-answer role selection if pre-selected from landing page
          if (autoSelectRef.current && data.type === "options") {
            const roleVal = autoSelectRef.current;
            if (data.choices?.some(c => c.value === roleVal)) {
              autoSelectRef.current = null;
              const roleLabel = roleVal === "employer"
                ? "I'm Hiring (Employer)"
                : "I'm Looking for Work (Job Seeker)";
              setIsTyping(true);
              ws.send(JSON.stringify({ type: "option", value: roleVal, content: roleLabel }));
              return;
            }
          }

          if (data.type === "done") {
            setStatus("done");
          } else {
            addMessage({ from: "bot", ...data });
          }
        };

        ws.onerror = () => { if (active) setStatus("error"); };
        ws.onclose = () => {
          if (active) setStatus((s) => (s === "done" ? s : "idle"));
        };
      } catch {
        if (active) setStatus("error");
      }
    }

    init();

    return () => {
      active = false;
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [addMessage]);

  const send = useCallback((payload) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      addMessage({ from: "user", type: "text", content: payload.content || payload.value || "" });
      setIsTyping(true);
      wsRef.current.send(JSON.stringify(payload));
    }
  }, [addMessage]);

  const uploadFile = useCallback(async (file) => {
    const sessionId = sessionIdRef.current;
    if (!sessionId) return;

    const form = new FormData();
    form.append("file", file);
    addMessage({ from: "user", type: "text", content: `📎 ${file.name}` });
    setIsTyping(true);

    try {
      const res = await fetch(`/api/upload/${sessionId}`, { method: "POST", body: form });
      if (!res.ok) throw new Error("Upload failed");
      const { upload_id } = await res.json();
      wsRef.current?.send(JSON.stringify({ type: "file_ready", upload_id }));
    } catch {
      setIsTyping(false);
      addMessage({ from: "bot", type: "bot_message", content: "Upload failed. Please try again." });
    }
  }, [addMessage]);

  return { messages, status, isTyping, send, uploadFile };
}
