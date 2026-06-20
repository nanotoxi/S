import React from "react";

const TYPE_STYLE = {
  "Full-time": { bg: "#4f46e518", color: "#818cf8", border: "#4f46e533" },
  "Hybrid":    { bg: "#f59e0b18", color: "#fbbf24", border: "#f59e0b33" },
  "Remote":    { bg: "#22c55e18", color: "#4ade80", border: "#22c55e33" },
  "Contract":  { bg: "#ec489918", color: "#f472b6", border: "#ec489933" },
};

export default function JobCard({ job, isApplied, isSaved, onApply, onSave }) {
  const scoreColor =
    job.score >= 85 ? "#22c55e" :
    job.score >= 70 ? "#f59e0b" : "#94a3b8";
  const tc = TYPE_STYLE[job.type] || TYPE_STYLE["Full-time"];

  return (
    <div style={{
      background: "#161b27",
      border: `1px solid ${isApplied ? "#4f46e533" : "#1e2535"}`,
      borderRadius: 14,
      padding: "20px",
      display: "flex",
      flexDirection: "column",
      gap: 12,
      transition: "border-color 0.2s",
    }}>
      {/* Logo + title + score */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 13 }}>
        <div style={{
          width: 46, height: 46, borderRadius: 12,
          background: job.logoColor + "22",
          border: `1px solid ${job.logoColor}44`,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 13, fontWeight: 700, color: job.logoColor, flexShrink: 0,
        }}>
          {job.logo}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: 15, color: "#e2e8f0" }}>{job.title}</div>
          <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 2 }}>{job.company}</div>
        </div>
        <div style={{
          width: 44, height: 44, borderRadius: "50%",
          border: `2.5px solid ${scoreColor}`,
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          flexShrink: 0,
        }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: scoreColor, lineHeight: 1 }}>
            {job.score}
          </span>
          <span style={{ fontSize: 9, color: "#64748b" }}>fit</span>
        </div>
      </div>

      {/* Meta */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
        <span style={{
          background: tc.bg, border: `1px solid ${tc.border}`,
          color: tc.color, borderRadius: 20, padding: "3px 10px", fontSize: 11,
        }}>
          {job.type}
        </span>
        <span style={{ fontSize: 12, color: "#64748b" }}>📍 {job.location}</span>
        <span style={{ fontSize: 12, color: "#64748b" }}>💼 {job.experience}</span>
        <span style={{ fontSize: 12, color: "#64748b" }}>💰 {job.salary}</span>
      </div>

      {/* Skills */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {job.skills.map(s => (
          <span key={s} style={{
            background: "#1e2535", border: "1px solid #334155",
            borderRadius: 20, padding: "3px 10px", fontSize: 12, color: "#94a3b8",
          }}>
            {s}
          </span>
        ))}
      </div>

      {/* Footer */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 2,
      }}>
        <span style={{ fontSize: 11, color: "#64748b" }}>Posted {job.posted}</span>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => onSave(job.id)}
            title={isSaved ? "Saved" : "Save job"}
            style={{
              width: 32, height: 32, borderRadius: 8,
              border: `1px solid ${isSaved ? "#4f46e5" : "#334155"}`,
              background: isSaved ? "#4f46e522" : "transparent",
              color: isSaved ? "#818cf8" : "#64748b",
              cursor: "pointer", fontSize: 15,
              display: "flex", alignItems: "center", justifyContent: "center",
              transition: "all 0.15s",
            }}
          >
            🔖
          </button>
          <button
            onClick={() => !isApplied && onApply(job.id)}
            disabled={isApplied}
            style={{
              padding: "6px 18px", borderRadius: 8, border: "none",
              background: isApplied ? "#22c55e22" : "#4f46e5",
              color: isApplied ? "#22c55e" : "#fff",
              cursor: isApplied ? "default" : "pointer",
              fontSize: 13, fontWeight: 500,
              transition: "all 0.2s",
            }}
          >
            {isApplied ? "✓ Applied" : "Apply"}
          </button>
        </div>
      </div>
    </div>
  );
}
