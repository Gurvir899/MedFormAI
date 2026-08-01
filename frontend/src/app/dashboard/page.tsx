"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface DoctorStats {
  totalForms: number;
  passedForms: number;
  blockedForms: number;
  patientCount: number;
  recentForms: Array<{
    id: number;
    formType: string;
    status: string;
    piiScanPassed: boolean;
    createdAt: string;
  }>;
}

export default function DashboardOverview() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DoctorStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await apiFetch<DoctorStats>("/api/v1/doctor/stats");
      setStats(data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ padding: "2rem" }}><span className="spinner" style={{ borderTopColor: "var(--primary)" }} /> Loading...</div>;
  }

  const firstName = user?.firstName || "there";

  return (
    <div>
      <h2 style={{ marginBottom: "0.25rem" }}>Welcome, {firstName}</h2>
      <p style={{ color: "var(--textMuted)", fontSize: "0.875rem", marginBottom: "2rem" }}>
        Here&apos;s your practice overview
      </p>

      {/* Stats grid */}
      <div className="grid grid4" style={{ marginBottom: "2rem" }}>
        <StatCard label="Total Forms" value={stats?.totalForms ?? 0} />
        <StatCard label="Passed PII Scan" value={stats?.passedForms ?? 0} color="var(--success)" />
        <StatCard label="Blocked" value={stats?.blockedForms ?? 0} color="var(--danger)" />
        <StatCard label="Patients" value={stats?.patientCount ?? 0} />
      </div>

      {/* Quick actions */}
      <div style={{ marginBottom: "2rem" }}>
        <h3 style={{ marginBottom: "1rem" }}>Quick Actions</h3>
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          <Link href="/dashboard/forms" className="primary" style={{
            display: "inline-block", padding: "0.75rem 1.25rem", borderRadius: "8px",
            color: "white", fontSize: "0.9375rem", textDecoration: "none",
          }}>
            📝 New Form
          </Link>
          <Link href="/dashboard/patients" className="secondary" style={{
            display: "inline-block", padding: "0.75rem 1.25rem", borderRadius: "8px",
            fontSize: "0.9375rem", textDecoration: "none",
          }}>
            👥 View Patients
          </Link>
          <Link href="/dashboard/roi" className="secondary" style={{
            display: "inline-block", padding: "0.75rem 1.25rem", borderRadius: "8px",
            fontSize: "0.9375rem", textDecoration: "none",
          }}>
            💰 ROI Calculator
          </Link>
        </div>
      </div>

      {/* Recent forms */}
      <div>
        <h3 style={{ marginBottom: "1rem" }}>Recent Forms</h3>
        {!stats?.recentForms || stats.recentForms.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "2rem" }}>
            <p style={{ color: "var(--textMuted)", fontSize: "0.875rem" }}>
              No forms yet. Click &quot;New Form&quot; to get started.
            </p>
          </div>
        ) : (
          <div className="card" style={{ padding: 0 }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--border)" }}>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>ID</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Type</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Status</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>PII Scan</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Date</th>
                </tr>
              </thead>
              <tbody>
                {stats.recentForms.map((form) => (
                  <tr key={form.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "0.75rem" }}>#{form.id}</td>
                    <td style={{ padding: "0.75rem" }}>{form.formType}</td>
                    <td style={{ padding: "0.75rem" }}>
                      <span className="badge badgeInfo">{form.status}</span>
                    </td>
                    <td style={{ padding: "0.75rem" }}>
                      <span className={`badge ${form.piiScanPassed ? "badgeSuccess" : "badgeDanger"}`}>
                        {form.piiScanPassed ? "Passed" : "Blocked"}
                      </span>
                    </td>
                    <td style={{ padding: "0.75rem", color: "var(--textMuted)" }}>
                      {new Date(form.createdAt).toLocaleDateString()}
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

function StatCard({ label, value, color }: { label: string; value: number | string; color?: string }) {
  return (
    <div className="card" style={{ textAlign: "center" }}>
      <div style={{
        fontSize: "2rem", fontWeight: 700,
        fontFamily: "var(--fontSerif)",
        color: color || "var(--primary)",
      }}>
        {value}
      </div>
      <div style={{ fontSize: "0.75rem", color: "var(--textMuted)", marginTop: "0.25rem" }}>{label}</div>
    </div>
  );
}
