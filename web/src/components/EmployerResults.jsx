import React, { useState } from "react";
import CandidateCard from "./CandidateCard";
import { MOCK_CANDIDATES } from "../data/mockData";

const TABS = ["All", "Shortlisted", "On Hold", "Rejected"];

export default function EmployerResults({ onReset }) {
  const [actions, setActions] = useState({});
  const [activeTab, setActiveTab] = useState("All");
  const [outreachOpen, setOutreachOpen] = useState(false);
  const [notified, setNotified] = useState(false);

  const handleAction = (id, action) => {
    setActions(prev => ({ ...prev, [id]: action }));
  };

  const shortlisted = MOCK_CANDIDATES.filter(c => actions[c.id] === "shortlisted");
  const onHold      = MOCK_CANDIDATES.filter(c => actions[c.id] === "hold");
  const rejected    = MOCK_CANDIDATES.filter(c => actions[c.id] === "rejected");

  const tabCandidates = {
    "All":        MOCK_CANDIDATES,
    "Shortlisted": shortlisted,
    "On Hold":    onHold,
    "Rejected":   rejected,
  };
  const tabCounts = Object.fromEntries(
    Object.entries(tabCandidates).map(([k, v]) => [k, v.length])
  );

  return (
    <div style={{ width: "100%", minHeight: "100dvh", background: "#0f1117", color: "#e2e8f0" }}>

      {/* Sticky header */}
      <div style={{
        position: "sticky", top: 0, zIndex: 10,
        background: "#0f1117", borderBottom: "1px solid #1e2535",
        padding: "14px 24px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: "50%", background: "#4f46e5",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
          }}>🤖</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15 }}>Candidate Matches</div>
            <div style={{ fontSize: 12, color: "#64748b" }}>
              {MOCK_CANDIDATES.length} candidates · AI-ranked by fit
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {shortlisted.length > 0 && (
            <button
              onClick={() => { setOutreachOpen(true); setNotified(false); }}
              style={{
                background: "#4f46e5", border: "none", borderRadius: 8,
                padding: "8px 16px", color: "#fff", fontSize: 13, fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Notify {shortlisted.length} Shortlisted →
            </button>
          )}
          <button
            onClick={onReset}
            style={{
              background: "transparent", border: "1px solid #334155", borderRadius: 8,
              padding: "8px 14px", color: "#94a3b8", fontSize: 13, cursor: "pointer",
            }}
          >
            New JD
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: "flex", gap: 0, padding: "0 24px",
        borderBottom: "1px solid #1e2535",
      }}>
        {TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              background: "none", border: "none",
              borderBottom: `2px solid ${activeTab === tab ? "#4f46e5" : "transparent"}`,
              color: activeTab === tab ? "#e2e8f0" : "#64748b",
              padding: "12px 16px",
              fontSize: 13, fontWeight: activeTab === tab ? 600 : 400,
              cursor: "pointer", transition: "all 0.15s",
              display: "flex", alignItems: "center", gap: 7,
            }}
          >
            {tab}
            {(tab === "All" || tabCounts[tab] > 0) && (
              <span style={{
                background: activeTab === tab ? "#4f46e5" : "#1e2535",
                color: activeTab === tab ? "#fff" : "#64748b",
                borderRadius: 20, padding: "1px 7px", fontSize: 11,
              }}>
                {tabCounts[tab]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
        gap: 16,
        padding: 24,
        maxWidth: 1200,
        margin: "0 auto",
      }}>
        {tabCandidates[activeTab].length === 0 ? (
          <div style={{
            gridColumn: "1 / -1", textAlign: "center",
            color: "#64748b", padding: "56px 0", fontSize: 14,
          }}>
            No candidates here yet.
          </div>
        ) : (
          tabCandidates[activeTab].map(c => (
            <CandidateCard
              key={c.id}
              candidate={c}
              currentAction={actions[c.id] || "none"}
              onAction={handleAction}
            />
          ))
        )}
      </div>

      {/* Outreach modal */}
      {outreachOpen && (
        <div
          onClick={() => setOutreachOpen(false)}
          style={{
            position: "fixed", inset: 0,
            background: "rgba(0,0,0,0.75)",
            display: "flex", alignItems: "center", justifyContent: "center",
            zIndex: 100, padding: 24,
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: "#161b27", border: "1px solid #1e2535",
              borderRadius: 16, padding: "28px",
              width: "100%", maxWidth: 480,
            }}
          >
            {notified ? (
              <div style={{ textAlign: "center", padding: "16px 0" }}>
                <div style={{ fontSize: 40, marginBottom: 16 }}>✅</div>
                <h3 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 8px" }}>Invitations Sent!</h3>
                <p style={{ color: "#64748b", fontSize: 13, margin: "0 0 24px" }}>
                  {shortlisted.length} candidate{shortlisted.length > 1 ? "s" : ""} will be notified shortly.
                </p>
                <button
                  onClick={() => setOutreachOpen(false)}
                  style={{
                    padding: "10px 24px", borderRadius: 8, border: "none",
                    background: "#4f46e5", color: "#fff", cursor: "pointer", fontSize: 14,
                  }}
                >
                  Done
                </button>
              </div>
            ) : (
              <>
                <h3 style={{ fontWeight: 600, fontSize: 16, margin: "0 0 4px" }}>
                  Notify Shortlisted Candidates
                </h3>
                <p style={{ color: "#64748b", fontSize: 13, margin: "0 0 20px" }}>
                  Send interview invitations to {shortlisted.length} candidate{shortlisted.length > 1 ? "s" : ""}.
                </p>

                <div style={{ marginBottom: 20 }}>
                  <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 8, fontWeight: 600, letterSpacing: "0.05em" }}>
                    NOTIFY VIA
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    {[
                      { ch: "Email", icon: "📧" },
                      { ch: "WhatsApp", icon: "💬" },
                      { ch: "SMS", icon: "📱" },
                    ].map(({ ch, icon }) => (
                      <button key={ch} style={{
                        flex: 1, padding: "10px", borderRadius: 8,
                        border: "1px solid #334155", background: "#1e2535",
                        color: "#e2e8f0", cursor: "pointer", fontSize: 13,
                      }}>
                        {icon} {ch}
                      </button>
                    ))}
                  </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 24 }}>
                  {shortlisted.map(c => (
                    <div key={c.id} style={{
                      display: "flex", alignItems: "center", gap: 12,
                      padding: "10px 12px", background: "#1e2535", borderRadius: 8,
                    }}>
                      <div style={{
                        width: 32, height: 32, borderRadius: "50%", background: c.color,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: 12, fontWeight: 700, color: "#fff", flexShrink: 0,
                      }}>
                        {c.initials}
                      </div>
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 500 }}>{c.name}</div>
                        <div style={{ fontSize: 12, color: "#64748b" }}>{c.email}</div>
                      </div>
                    </div>
                  ))}
                </div>

                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    onClick={() => setOutreachOpen(false)}
                    style={{
                      flex: 1, padding: "10px", borderRadius: 8,
                      border: "1px solid #334155", background: "transparent",
                      color: "#94a3b8", cursor: "pointer", fontSize: 14,
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => setNotified(true)}
                    style={{
                      flex: 1, padding: "10px", borderRadius: 8,
                      border: "none", background: "#4f46e5",
                      color: "#fff", cursor: "pointer", fontSize: 14, fontWeight: 500,
                    }}
                  >
                    Send Invitations
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
