"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { ProtectedRoute } from "@/components/ProtectedRoute";

interface FormRecord {
  id: number;
  formType: string;
  patientId: number;
  physicianId: string;
  status: string;
  piiScanPassed: boolean;
  createdAt: string;
  submittedAt: string | null;
}

interface FormsResponse {
  forms: FormRecord[];
  total: number;
  pages: number;
  currentPage: number;
}

export default function HistoryPage() {
  const [forms, setForms] = useState<FormRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState("");

  useEffect(() => {
    loadForms();
  }, [page, filterType]);

  const loadForms = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), perPage: "20" });
      if (filterType) params.set("formType", filterType);
      const data = await apiFetch<FormsResponse>(`/api/v1/doctor/forms?${params}`);
      setForms(data.forms || []);
      setTotal(data.total);
      setPages(data.pages);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute roles={["doctor", "admin"]}>
      <div>
        <h2 style={{ marginBottom: "0.25rem" }}>Form History</h2>
        <p style={{ color: "var(--textMuted)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
          {total} form submission{total !== 1 ? "s" : ""}
        </p>

        {/* Filter */}
        <div style={{ marginBottom: "1rem", display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <label style={{ marginBottom: 0 }}>Filter by type:</label>
          <select value={filterType} onChange={(e) => { setFilterType(e.target.value); setPage(1); }} style={{ width: "auto" }}>
            <option value="">All types</option>
            <option value="dtc">DTC (T2201)</option>
            <option value="sickNote">Sick Note</option>
            <option value="insurance">Insurance</option>
            <option value="cpp">CPP Disability</option>
          </select>
        </div>

        {loading ? (
          <div style={{ padding: "2rem" }}><span className="spinner" style={{ borderTopColor: "var(--primary)" }} /> Loading...</div>
        ) : forms.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "2rem" }}>
            <p style={{ color: "var(--textMuted)" }}>No form submissions yet.</p>
          </div>
        ) : (
          <div className="card" style={{ padding: 0 }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--border)" }}>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>ID</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Type</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Patient ID</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Status</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>PII Scan</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Date</th>
                </tr>
              </thead>
              <tbody>
                {forms.map((f) => (
                  <tr key={f.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "0.75rem" }}>#{f.id}</td>
                    <td style={{ padding: "0.75rem" }}>{f.formType}</td>
                    <td style={{ padding: "0.75rem" }}>{f.patientId || "—"}</td>
                    <td style={{ padding: "0.75rem" }}>
                      <span className="badge badgeInfo">{f.status}</span>
                    </td>
                    <td style={{ padding: "0.75rem" }}>
                      <span className={`badge ${f.piiScanPassed ? "badgeSuccess" : "badgeDanger"}`}>
                        {f.piiScanPassed ? "Passed" : "Blocked"}
                      </span>
                    </td>
                    <td style={{ padding: "0.75rem", color: "var(--textMuted)" }}>
                      {new Date(f.createdAt).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {pages > 1 && (
              <div style={{ display: "flex", justifyContent: "center", gap: "0.5rem", padding: "1rem" }}>
                <button className="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                  ← Prev
                </button>
                <span style={{ padding: "0.5rem 0.75rem", fontSize: "0.875rem", color: "var(--textMuted)" }}>
                  Page {page} of {pages}
                </span>
                <button className="secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>
                  Next →
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
