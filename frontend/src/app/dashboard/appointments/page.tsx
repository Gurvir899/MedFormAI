"use client";

import { useState, useEffect } from "react";
import { getAuthToken } from "@/lib/auth";

interface Patient {
  id: number;
  patientName?: string;
  name?: string;
  dateOfBirth?: string;
  dob?: string;
  diagnosis: string;
}

interface FieldUpdates {
  diagnosis?: string;
  medications?: string;
  allergies?: string;
  notes?: string;
  disabilityWalking?: boolean;
  disabilityDressing?: boolean;
  disabilityFeeding?: boolean;
  disabilitySpeaking?: boolean;
  disabilityHearing?: boolean;
  disabilityVision?: boolean;
  disabilityEliminating?: boolean;
  disabilityMental?: boolean;
  disabilityIndependentLiving?: boolean;
  disabilityTherapy?: boolean;
  yearImpaired?: number;
  devicesTherapy?: string;
}

interface AppointmentResult {
  appointment: {
    id: number;
    patientId: number;
    clinicalNote: string;
    aiSummary: string;
    status: string;
    createdAt: string;
  };
  fieldUpdates: FieldUpdates;
  aiSummary: string;
  llmUsed: boolean;
  redactionPreview: string;
}

export default function AppointmentsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [clinicalNote, setClinicalNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AppointmentResult | null>(null);
  const [error, setError] = useState("");
  const [patientSearch, setPatientSearch] = useState("");
  const [showPatientDropdown, setShowPatientDropdown] = useState(false);
  const [applied, setApplied] = useState<Record<string, { old: string; new: string }> | null>(null);

  // Load patients
  useEffect(() => {
    const loadPatients = async () => {
      try {
        const token = getAuthToken();
        const res = await fetch("/api/v1/doctor/patients", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setPatients(data.patients || []);
        }
      } catch { /* silent */ }
    };
    loadPatients();
  }, []);

  // Filter patients by search
  const filteredPatients = patientSearch.length >= 2
    ? patients.filter(p =>
        (p.patientName || p.name || "").toLowerCase().includes(patientSearch.toLowerCase()) ||
        (p.diagnosis || "").toLowerCase().includes(patientSearch.toLowerCase())
      ).slice(0, 5)
    : [];

  const handleSubmit = async () => {
    if (!selectedPatient || !clinicalNote.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    setApplied(null);

    try {
      const token = getAuthToken();
      const res = await fetch("/api/v1/appointments", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          patientId: selectedPatient.id,
          clinicalNote: clinicalNote.trim(),
        }),
      });

      if (!res.ok) throw new Error("Failed to create appointment");
      const data = await res.json();

      if (data.status === "success") {
        setResult(data);
      } else {
        throw new Error(data.message || "Failed");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create appointment");
    } finally {
      setLoading(false);
    }
  };

  const handleApplyUpdates = async () => {
    if (!result) return;
    setLoading(true);
    try {
      const token = getAuthToken();
      const res = await fetch(`/api/v1/appointments/${result.appointment.id}/apply`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to apply updates");
      const data = await res.json();
      if (data.status === "success") {
        setApplied(data.applied);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to apply updates");
    } finally {
      setLoading(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: "100%", background: "var(--code)", border: "1px solid var(--border)",
    borderRadius: "8px", padding: "0.625rem 0.75rem", color: "var(--text)",
    fontSize: "0.875rem", fontFamily: "var(--fontSans)", outline: "none",
  };

  const labelStyle: React.CSSProperties = {
    fontSize: "0.75rem", fontWeight: 600, color: "var(--textMuted)",
    textTransform: "uppercase" as const, letterSpacing: "0.05em", marginBottom: "0.375rem",
    display: "block",
  };

  return (
    <div>
      <h2 style={{ marginBottom: "0.25rem", color: "var(--primary)" }}>Appointments</h2>
      <p style={{ color: "var(--textMuted)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
        Write a clinical note after each visit. AI extracts diagnosis, medications, and disability
        checkmarks to keep patient records up to date.
      </p>

      {/* Patient selector */}
      <div className="card" style={{ marginBottom: "1rem" }}>
        <label style={labelStyle}>Patient</label>
        <input
          type="text"
          value={patientSearch}
          onChange={(e) => {
            setPatientSearch(e.target.value);
            setShowPatientDropdown(true);
          }}
          onFocus={() => setShowPatientDropdown(true)}
          placeholder="Type a patient name..."
          style={inputStyle}
        />
        {showPatientDropdown && filteredPatients.length > 0 && (
          <div style={{ marginTop: "0.25rem", border: "1px solid var(--border)", borderRadius: "8px", overflow: "hidden" }}>
            {filteredPatients.map((p) => (
              <button
                key={p.id}
                onClick={() => {
                  setSelectedPatient(p);
                  setPatientSearch(p.patientName || p.name || "");
                  setShowPatientDropdown(false);
                }}
                style={{
                  display: "flex", width: "100%", padding: "0.5rem 0.75rem",
                  background: "transparent", border: "none", borderBottom: "1px solid var(--border)",
                  cursor: "pointer", textAlign: "left", gap: "0.75rem",
                }}
              >
                <span style={{ fontWeight: 600, fontSize: "0.8125rem", color: "var(--text)" }}>{p.patientName || p.name}</span>
                <span style={{ fontSize: "0.75rem", color: "var(--textMuted)" }}>{p.dateOfBirth || p.dob}</span>
                <span style={{ fontSize: "0.75rem", color: "var(--textMuted)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.diagnosis}</span>
              </button>
            ))}
          </div>
        )}
        {selectedPatient && (
          <div style={{ marginTop: "0.5rem", padding: "0.5rem 0.75rem", background: "#e6f0fa", borderRadius: "8px", fontSize: "0.8125rem", color: "var(--primary)" }}>
            📋 {selectedPatient.patientName || selectedPatient.name} — {selectedPatient.diagnosis}
          </div>
        )}
      </div>

      {/* Clinical note */}
      <div className="card" style={{ marginBottom: "1rem" }}>
        <label style={labelStyle}>Clinical Note</label>
        <textarea
          value={clinicalNote}
          onChange={(e) => setClinicalNote(e.target.value)}
          placeholder="Write your clinical note here... e.g., 'Patient presents with worsening knee pain. Difficulty walking more than 30 meters. Uses cane. Prescribed celecoxib. Diagnosis: severe osteoarthritis bilateral knees. Condition started in 2019.'"
          style={{ ...inputStyle, minHeight: "200px", resize: "vertical" }}
        />
        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
          <button
            className="primary"
            onClick={handleSubmit}
            disabled={loading || !selectedPatient || !clinicalNote.trim()}
            style={{ padding: "0.625rem 1.5rem", fontSize: "0.875rem" }}
          >
            {loading ? <><span className="spinner" /> Processing...</> : "Process Note with AI →"}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="badge badgeDanger" style={{ display: "block", padding: "0.625rem", marginBottom: "1rem", textAlign: "center" }}>
          {error}
        </div>
      )}

      {/* AI Result */}
      {result && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <h3 style={{ fontSize: "1rem", marginBottom: "0.75rem", color: "var(--primary)" }}>
            AI Summary
          </h3>
          <p style={{ fontSize: "0.875rem", color: "var(--text)", lineHeight: 1.6, marginBottom: "1rem" }}>
            {result.aiSummary}
          </p>

          {Object.keys(result.fieldUpdates).length > 0 && (
            <>
              <h4 style={{ fontSize: "0.8125rem", marginBottom: "0.5rem", color: "var(--textMuted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Extracted Field Updates ({Object.keys(result.fieldUpdates).length})
              </h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginBottom: "1rem" }}>
                {Object.entries(result.fieldUpdates).map(([field, value]) => (
                  <div key={field} style={{
                    display: "flex", gap: "0.75rem", alignItems: "center",
                    padding: "0.5rem 0.75rem", background: "var(--code)",
                    borderRadius: "8px", border: "1px solid var(--border)",
                  }}>
                    <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--textMuted)", minWidth: "180px" }}>
                      {field}
                    </span>
                    <span style={{ fontSize: "0.8125rem", color: "var(--text)", flex: 1 }}>
                      {typeof value === "boolean" ? (value ? "✅ Yes" : "❌ No") : String(value)}
                    </span>
                  </div>
                ))}
              </div>

              {!applied ? (
                <button
                  className="primary"
                  onClick={handleApplyUpdates}
                  disabled={loading}
                  style={{ padding: "0.5rem 1.5rem", fontSize: "0.8125rem" }}
                >
                  ✓ Apply Updates to Patient Record
                </button>
              ) : (
                <div style={{
                  padding: "0.625rem 0.75rem", background: "#e6f0fa", borderRadius: "8px",
                  fontSize: "0.8125rem", color: "var(--success)",
                }}>
                  ✅ {Object.keys(applied).length} fields updated on patient record
                </div>
              )}
            </>
          )}

          {result.redactionPreview && (
            <details style={{ marginTop: "1rem" }}>
              <summary style={{ fontSize: "0.75rem", color: "var(--textMuted)", cursor: "pointer" }}>
                🔒 What the LLM received (PII redacted)
              </summary>
              <pre style={{
                marginTop: "0.5rem", padding: "0.75rem", fontSize: "0.75rem",
                fontFamily: "var(--fontMono)",
                background: "#1e1e1e", color: "#a5d6ff", borderRadius: "8px",
                whiteSpace: "pre-wrap", wordBreak: "break-word", maxHeight: "200px", overflowY: "auto",
              }}>
                {result.redactionPreview}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
