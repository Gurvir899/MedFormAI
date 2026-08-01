"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import type { ComplianceDashboard } from "@/lib/types";

export function ComplianceDashboardView() {
  const [dashboard, setDashboard] = useState<ComplianceDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<ComplianceDashboard>("/api/v1/compliance/dashboard");
      setDashboard(data);
    } catch {
      // Silent fail — dashboard is secondary view
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <h3>Compliance Dashboard</h3>
        <p style={{ color: "var(--textMuted)" }}>Loading...</p>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="card">
        <h3>Compliance Dashboard</h3>
        <p style={{ color: "var(--textMuted)" }}>Unable to load. Is backend running?</p>
      </div>
    );
  }

  const posture = dashboard.compliancePosture;

  return (
    <div className="card">
      <h3>Compliance Dashboard</h3>
      <p style={{ color: "var(--textMuted)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
        PHIPA / PIPEDA posture — real-time audit trail
      </p>

      {/* Compliance Posture */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h4>Privacy Posture</h4>
        <div className="grid grid3" style={{ marginTop: "0.75rem" }}>
          <PostureCard label="Encryption at Rest" enabled={posture.encryptionAtRest} />
          <PostureCard label="Encryption in Transit" enabled={posture.encryptionInTransit} />
          <PostureCard label="PII Redaction (LLM)" enabled={posture.piiRedactionBeforeLlm} />
          <PostureCard label="Audit Trail" enabled={posture.auditTrailEnabled} />
          <PostureCard label="Minimum Necessary" enabled={posture.minimumNecessaryEnforced} />
          <PostureCard label="Retention Policy" enabled={true} subValue={`${posture.retentionPolicyDays} days`} />
        </div>
      </div>

      {/* Submission Stats */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h4>Submission Statistics</h4>
        <div className="grid grid4" style={{ marginTop: "0.75rem" }}>
          <StatBox label="Total" value={dashboard.submissionStats.total} />
          <StatBox label="Passed" value={dashboard.submissionStats.passed} color="var(--success)" />
          <StatBox label="Blocked" value={dashboard.submissionStats.blocked} color="var(--danger)" />
          <StatBox label="Pass Rate" value={`${dashboard.submissionStats.passRate}%`} />
        </div>
      </div>

      {/* Audit Log */}
      <div>
        <h4>Recent Audit Trail</h4>
        {dashboard.auditLogs.length === 0 ? (
          <p style={{ fontSize: "0.875rem", color: "var(--textMuted)", marginTop: "0.5rem" }}>
            No audit entries yet. Run the form automation pipeline to generate audit logs.
          </p>
        ) : (
          <div style={{ overflowX: "auto", marginTop: "0.75rem" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--border)" }}>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>User</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Action</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>PII Fields</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Endpoint</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Time</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.auditLogs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "0.5rem" }}>{log.userId}</td>
                    <td style={{ padding: "0.5rem" }}>
                      <span className={`badge ${log.action === "blocked_excess_pii" ? "badgeDanger" : "badgeInfo"}`}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ padding: "0.5rem", fontFamily: "var(--fontMono)", fontSize: "0.75rem" }}>
                      {log.piiFields.join(", ")}
                    </td>
                    <td style={{ padding: "0.5rem", fontFamily: "var(--fontMono)", fontSize: "0.75rem" }}>
                      {log.endpoint}
                    </td>
                    <td style={{ padding: "0.5rem", color: "var(--textMuted)" }}>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function PostureCard({ label, enabled, subValue }: { label: string; enabled: boolean; subValue?: string }) {
  return (
    <div
      style={{
        background: enabled ? "#f0fdf4" : "#fef2f2",
        border: `1px solid ${enabled ? "#86efac" : "#fca5a5"}`,
        borderRadius: "8px",
        padding: "0.75rem",
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
      }}
    >
      <span style={{ fontSize: "1.25rem" }}>{enabled ? "✓" : "✗"}</span>
      <div>
        <div style={{ fontSize: "0.8125rem", fontWeight: 500 }}>{label}</div>
        {subValue && <div style={{ fontSize: "0.75rem", color: "var(--textMuted)" }}>{subValue}</div>}
      </div>
    </div>
  );
}

function StatBox({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div
      style={{
        background: "var(--code)",
        borderRadius: "8px",
        padding: "0.75rem",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: color || "var(--primary)", fontFamily: "var(--fontSerif)" }}>
        {value}
      </div>
      <div style={{ fontSize: "0.75rem", color: "var(--textMuted)" }}>{label}</div>
    </div>
  );
}
