import React, { useState } from "react";
import JobCard from "./JobCard";
import { MOCK_JOBS } from "../data/mockData";

const PIPELINE_STAGES = ["Applied", "Shortlisted", "Interview", "Offer"];

export default function CandidateResults({ onReset }) {
  const [appliedIds, setAppliedIds] = useState(new Set());
  const [savedIds, setSavedIds] = useState(new Set());
  const [activeTab, setActiveTab] = useState("All Jobs");

  const handleApply = (id) => setAppliedIds(prev => new Set([...prev, id]));
  const handleSave  = (id) => setSavedIds(prev => {
    const next = new Set(prev);
    next.has(id) ? next.delete(id) : next.add(id);
    return next;
  });

  const allJobs    = MOCK_JOBS;
  const bestMatch  = MOCK_JOBS.filter(j => j.score >= 85);
  const appliedJobs = MOCK_JOBS.filter(j => appliedIds.has(j.id));
  const savedJobs   = MOCK_JOBS.filter(j => savedIds.has(j.id));

  const tabJobs = {
    "All Jobs":   allJobs,
    "Best Match": bestMatch,
    "Applied":    appliedJobs,
    "Saved":      savedJobs,
  };

  const tabs = [
    { key: "All Jobs",   count: allJobs.length },
    { key: "Best Match", count: bestMatch.length },
    { key: "Applied",    count: appliedIds.size },
    { key: "Saved",      count: savedIds.size },
  ];

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
            width: 36, height: 36, borderRadius: "50%", background: "#7c3aed",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
          }}>🎯</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15 }}>Matching Jobs</div>
            <div style={{ fontSize: 12, color: "#64748b" }}>
              {MOCK_JOBS.length} opportunities found for your profile
            </div>
          </div>
        </div>
        <button
          onClick={onReset}
          style={{
            background: "transparent", border: "1px solid #334155", borderRadius: 8,
            padding: "8px 14px", color: "#94a3b8", fontSize: 13, cursor: "pointer",
          }}
        >
          Update Profile
        </button>
      </div>

      {/* Tabs */}
      <div style={{
        display: "flex", gap: 0, padding: "0 24px",
        borderBottom: "1px solid #1e2535",
      }}>
        {tabs.map(({ key, count }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            style={{
              background: "none", border: "none",
              borderBottom: `2px solid ${activeTab === key ? "#7c3aed" : "transparent"}`,
              color: activeTab === key ? "#e2e8f0" : "#64748b",
              padding: "12px 16px", fontSize: 13,
              fontWeight: activeTab === key ? 600 : 400,
              cursor: "pointer", transition: "all 0.15s",
              display: "flex", alignItems: "center", gap: 7,
            }}
          >
            {key}
            {count > 0 && (
              <span style={{
                background: activeTab === key ? "#7c3aed" : "#1e2535",
                color: activeTab === key ? "#fff" : "#64748b",
                borderRadius: 20, padding: "1px 7px", fontSize: 11,
              }}>
                {count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Job grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
        gap: 16,
        padding: 24,
        maxWidth: 1200,
        margin: "0 auto",
      }}>
        {tabJobs[activeTab].length === 0 ? (
          <div style={{
            gridColumn: "1 / -1", textAlign: "center",
            color: "#64748b", padding: "56px 0", fontSize: 14,
          }}>
            {activeTab === "Applied" ? "You haven't applied to any jobs yet." :
             activeTab === "Saved"   ? "No saved jobs yet." :
             "No jobs match this filter."}
          </div>
        ) : (
          tabJobs[activeTab].map(job => (
            <JobCard
              key={job.id}
              job={job}
              isApplied={appliedIds.has(job.id)}
              isSaved={savedIds.has(job.id)}
              onApply={handleApply}
              onSave={handleSave}
            />
          ))
        )}
      </div>

      {/* Application tracker — only show if applied to something */}
      {appliedIds.size > 0 && (
        <div style={{
          maxWidth: 1200, margin: "0 auto",
          padding: "0 24px 40px",
        }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "#94a3b8", marginBottom: 16, letterSpacing: "0.04em" }}>
            APPLICATION TRACKER
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {MOCK_JOBS.filter(j => appliedIds.has(j.id)).map(job => (
              <div key={job.id} style={{
                background: "#161b27", border: "1px solid #1e2535", borderRadius: 12,
                padding: "14px 18px",
                display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap",
              }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 9,
                  background: job.logoColor + "22",
                  border: `1px solid ${job.logoColor}44`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 11, fontWeight: 700, color: job.logoColor, flexShrink: 0,
                }}>
                  {job.logo}
                </div>
                <div style={{ minWidth: 150 }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{job.title}</div>
                  <div style={{ fontSize: 12, color: "#64748b" }}>{job.company}</div>
                </div>
                {/* Pipeline stages */}
                <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 0, minWidth: 240 }}>
                  {PIPELINE_STAGES.map((stage, i) => {
                    const active = i === 0; // "Applied" is always the first stage
                    return (
                      <React.Fragment key={stage}>
                        <div style={{
                          display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
                        }}>
                          <div style={{
                            width: 28, height: 28, borderRadius: "50%",
                            background: active ? "#4f46e5" : "#1e2535",
                            border: `2px solid ${active ? "#4f46e5" : "#334155"}`,
                            display: "flex", alignItems: "center", justifyContent: "center",
                            fontSize: 12, color: active ? "#fff" : "#64748b",
                          }}>
                            {active ? "✓" : i + 1}
                          </div>
                          <span style={{ fontSize: 10, color: active ? "#818cf8" : "#64748b", whiteSpace: "nowrap" }}>
                            {stage}
                          </span>
                        </div>
                        {i < PIPELINE_STAGES.length - 1 && (
                          <div style={{
                            flex: 1, height: 2, marginBottom: 18,
                            background: "#1e2535",
                            minWidth: 20,
                          }} />
                        )}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
