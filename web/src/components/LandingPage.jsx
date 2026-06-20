import React from "react";

function RoleCard({ icon, title, description, cta, accentColor, onClick }) {
  const [hovered, setHovered] = React.useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        flex: "1 1 280px",
        maxWidth: 320,
        background: hovered ? "#1a2030" : "#161b27",
        border: `1px solid ${hovered ? accentColor : "#1e2535"}`,
        borderRadius: 16,
        padding: "32px 28px",
        textAlign: "left",
        cursor: "pointer",
        transform: hovered ? "translateY(-3px)" : "translateY(0)",
        transition: "all 0.2s",
        color: "inherit",
        boxShadow: hovered ? `0 8px 32px ${accentColor}22` : "none",
      }}
    >
      <div style={{
        width: 52, height: 52, borderRadius: 14,
        background: accentColor + "22",
        border: `1px solid ${accentColor}44`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 26, marginBottom: 20,
      }}>
        {icon}
      </div>
      <h2 style={{ fontSize: 18, fontWeight: 600, color: "#e2e8f0", margin: "0 0 10px" }}>
        {title}
      </h2>
      <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.65, margin: 0 }}>
        {description}
      </p>
      <div style={{
        marginTop: 24, display: "flex", alignItems: "center", gap: 6,
        color: accentColor, fontSize: 14, fontWeight: 500,
      }}>
        {cta} <span style={{ transition: "transform 0.15s", transform: hovered ? "translateX(4px)" : "translateX(0)", display: "inline-block" }}>→</span>
      </div>
    </button>
  );
}

export default function LandingPage({ onSelect }) {
  return (
    <div style={{
      width: "100%",
      minHeight: "100dvh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      background: "#0f1117",
      padding: "24px",
    }}>
      {/* Brand header */}
      <div style={{ textAlign: "center", marginBottom: 52 }}>
        <div style={{
          width: 60, height: 60, borderRadius: 18, background: "#4f46e5",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 30, margin: "0 auto 18px",
          boxShadow: "0 0 40px #4f46e544",
        }}>
          🤖
        </div>
        <h1 style={{ fontSize: 30, fontWeight: 700, color: "#e2e8f0", margin: "0 0 10px" }}>
          Sath Bot
        </h1>
        <p style={{ color: "#64748b", fontSize: 15, margin: 0, maxWidth: 340 }}>
          AI-powered recruitment — from job description to offer letter.
        </p>
      </div>

      {/* Role cards */}
      <div style={{
        display: "flex",
        gap: 20,
        flexWrap: "wrap",
        justifyContent: "center",
        width: "100%",
        maxWidth: 700,
      }}>
        <RoleCard
          icon="💼"
          title="I'm Hiring"
          description="Post a role, define your requirements conversationally, and get matched with pre-screened candidates instantly."
          cta="Start hiring"
          accentColor="#4f46e5"
          onClick={() => onSelect("employer")}
        />
        <RoleCard
          icon="🎯"
          title="Find a Job"
          description="Upload your resume, get AI-ranked job recommendations tailored to your skills, and apply with one click."
          cta="Explore jobs"
          accentColor="#7c3aed"
          onClick={() => onSelect("candidate")}
        />
      </div>

      <p style={{ color: "#334155", fontSize: 12, marginTop: 40 }}>
        Powered by Groq · llama-3.3-70b
      </p>
    </div>
  );
}
