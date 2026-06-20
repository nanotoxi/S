import React from "react";

const ACTION_META = {
  shortlisted: { icon: "✓", label: "Shortlist", color: "#22c55e" },
  hold:        { icon: "⏸", label: "Hold",      color: "#f59e0b" },
  rejected:    { icon: "✕", label: "Reject",    color: "#ef4444" },
};

const STATUS_LABEL = { available: "Available", employed: "Employed", freelance: "Freelancing" };

export default function CandidateCard({ candidate, currentAction, onAction }) {
  const scoreColor =
    candidate.score >= 85 ? "#22c55e" :
    candidate.score >= 70 ? "#f59e0b" : "#94a3b8";

  const borderColor =
    currentAction === "shortlisted" ? "#22c55e55" :
    currentAction === "hold"        ? "#f59e0b55" :
    currentAction === "rejected"    ? "#ef444455" :
    "#1e2535";

  return (
    <div style={{
      background: "#161b27",
      border: `1px solid ${borderColor}`,
      borderRadius: 14,
      padding: "20px",
      display: "flex",
      flexDirection: "column",
      gap: 12,
      transition: "border-color 0.2s, opacity 0.2s",
      opacity: currentAction === "rejected" ? 0.55 : 1,
    }}>
      {/* Avatar + info + score */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 13 }}>
        <div style={{
          width: 44, height: 44, borderRadius: "50%",
          background: candidate.color,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 15, fontWeight: 700, color: "#fff", flexShrink: 0,
        }}>
          {candidate.initials}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: 15, color: "#e2e8f0" }}>{candidate.name}</div>
          <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 2 }}>{candidate.title}</div>
          <div style={{ fontSize: 12, color: "#64748b", marginTop: 3 }}>
            {candidate.experience} yrs · {candidate.location}
          </div>
        </div>
        <div style={{
          width: 44, height: 44, borderRadius: "50%",
          border: `2.5px solid ${scoreColor}`,
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          flexShrink: 0,
        }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: scoreColor, lineHeight: 1 }}>
            {candidate.score}
          </span>
          <span style={{ fontSize: 9, color: "#64748b" }}>match</span>
        </div>
      </div>

      {/* Skills */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {candidate.skills.slice(0, 4).map(s => (
          <span key={s} style={{
            background: "#1e2535", border: "1px solid #334155",
            borderRadius: 20, padding: "3px 10px", fontSize: 12, color: "#94a3b8",
          }}>
            {s}
          </span>
        ))}
        {candidate.skills.length > 4 && (
          <span style={{ fontSize: 12, color: "#64748b", padding: "3px 4px" }}>
            +{candidate.skills.length - 4}
          </span>
        )}
      </div>

      {/* Status + action buttons */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{
          fontSize: 11, padding: "3px 9px", borderRadius: 20,
          background: candidate.status === "available" ? "#22c55e18" : "#1e2535",
          color: candidate.status === "available" ? "#22c55e" : "#64748b",
          border: `1px solid ${candidate.status === "available" ? "#22c55e33" : "#334155"}`,
        }}>
          {STATUS_LABEL[candidate.status] || candidate.status}
        </span>

        <div style={{ display: "flex", gap: 6 }}>
          {Object.entries(ACTION_META).map(([key, meta]) => {
            const active = currentAction === key;
            return (
              <button
                key={key}
                onClick={() => onAction(candidate.id, active ? "none" : key)}
                title={meta.label}
                style={{
                  width: 30, height: 30, borderRadius: "50%",
                  border: `1px solid ${active ? meta.color : "#334155"}`,
                  background: active ? meta.color + "22" : "transparent",
                  color: active ? meta.color : "#64748b",
                  cursor: "pointer", fontSize: 14,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  transition: "all 0.15s",
                }}
              >
                {meta.icon}
              </button>
            );
          })}
        </div>
      </div>

      {/* Contact reveal when shortlisted */}
      {currentAction === "shortlisted" && (
        <div style={{
          padding: "10px 12px",
          background: "#22c55e0d",
          border: "1px solid #22c55e22",
          borderRadius: 8,
          fontSize: 12, color: "#94a3b8",
          display: "flex", flexDirection: "column", gap: 5,
          animation: "fadeIn 0.2s ease",
        }}>
          <span>📧 {candidate.email}</span>
          <span>📱 {candidate.phone}</span>
        </div>
      )}
    </div>
  );
}
