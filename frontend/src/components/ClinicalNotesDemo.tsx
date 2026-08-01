"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface FormResult {
  status: string;
  formType: string;
  formData: Record<string, unknown>;
  piiScan: {
    passed: boolean;
    score: number;
    findings: Array<{
      type: string;
      severity: string;
      field: string;
      message: string;
    }>;
    redactedPreview: string;
    summary: {
      criticalCount: number;
      warningCount: number;
      totalFindings: number;
    };
  };
  timeSavedMinutes: number;
  manualTimeMinutes: number;
  automatedTimeMinutes: number;
  originalNotes: string;
  redactedNotesPreview: string;
  llmUsed: boolean;
  timestamp: string;
}

export function ClinicalNotesDemo() {
  const { user } = useAuth();
  const [clinicalNotes, setClinicalNotes] = useState(sampleNotes.sickNote);
  const [formType, setFormType] = useState<"sickNote" | "dtc">("sickNote");
  const [physicianName, setPhysicianName] = useState("");
  const [physicianLicense, setPhysicianLicense] = useState("");
  const [clinicName, setClinicName] = useState("");
  const [clinicAddress, setClinicAddress] = useState("");
  const [result, setResult] = useState<FormResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Pre-fill physician info from authenticated user profile
  useEffect(() => {
    if (user) {
      const fullName = `${user.firstName || ""} ${user.lastName || ""}`.trim();
      if (fullName) setPhysicianName(fullName);
      if (user.licenseNumber) setPhysicianLicense(user.licenseNumber);
      if (user.clinic?.name) setClinicName(user.clinic.name);
      if (user.clinic?.address) setClinicAddress(user.clinic.address);
    }
  }, [user]);

  const process = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await apiFetch<FormResult>("/api/v1/forms/process", {
        method: "POST",
        body: JSON.stringify({
          clinicalNotes,
          formType,
          physicianName,
          physicianLicense,
          clinicName,
          clinicAddress,
        }),
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Processing failed");
    } finally {
      setLoading(false);
    }
  };

  const switchFormType = (type: "sickNote" | "dtc") => {
    setFormType(type);
    setClinicalNotes(type === "sickNote" ? sampleNotes.sickNote : sampleNotes.dtc);
  };

  return (
    <div className="card">
      <h3>Real Form Automation — Paste Clinical Notes</h3>
      <p style={{ color: "var(--textMuted)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
        Doctor writes clinical notes → AI fills form → PII compliance scan → time saved
      </p>

      {/* Form type selector */}
      <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <FormTypeButton
          active={formType === "sickNote"}
          onClick={() => switchFormType("sickNote")}
          title="Sick Leave Certificate"
          subtitle="10.4 min × 136/yr per physician"
        />
        <FormTypeButton
          active={formType === "dtc"}
          onClick={() => switchFormType("dtc")}
          title="Disability Tax Credit (T2201)"
          subtitle="36.6 min × 32.2/yr per physician"
        />
      </div>

      {/* Clinical notes input */}
      <div style={{ marginBottom: "1rem" }}>
        <label>Clinical Notes (what the doctor writes during the visit)</label>
        <textarea
          value={clinicalNotes}
          onChange={(e) => setClinicalNotes(e.target.value)}
          rows={6}
          style={{ fontFamily: "var(--fontMono)", fontSize: "0.8125rem" }}
          placeholder="Patient: John Doe, DOB 1985-03-15. Presented with..."
        />
      </div>

      {/* Physician details */}
      <div className="grid grid2" style={{ marginBottom: "1rem" }}>
        <div>
          <label>Physician Name</label>
          <input value={physicianName} onChange={(e) => setPhysicianName(e.target.value)} />
        </div>
        <div>
          <label>License Number</label>
          <input value={physicianLicense} onChange={(e) => setPhysicianLicense(e.target.value)} />
        </div>
        <div>
          <label>Clinic Name</label>
          <input value={clinicName} onChange={(e) => setClinicName(e.target.value)} />
        </div>
        <div>
          <label>Clinic Address</label>
          <input value={clinicAddress} onChange={(e) => setClinicAddress(e.target.value)} />
        </div>
      </div>

      <button
        className="primary"
        onClick={process}
        disabled={loading || !clinicalNotes.trim()}
        style={{ width: "100%", padding: "0.875rem", fontSize: "1rem" }}
      >
        {loading ? (
          <>
            <span className="spinner" /> Processing with AI...
          </>
        ) : (
          `Generate ${formType === "sickNote" ? "Sick Note" : "DTC Form"} from Notes`
        )}
      </button>

      {error && (
        <p style={{ color: "var(--danger)", marginTop: "1rem", fontSize: "0.875rem" }}>
          {error}
        </p>
      )}

      {result && <ResultDisplay result={result} />}
    </div>
  );
}

function ResultDisplay({ result }: { result: FormResult }) {
  const scorePercent = Math.round(result.piiScan.score * 100);
  const timeSavedPercent = Math.round((result.timeSavedMinutes / result.manualTimeMinutes) * 100);
  const [editableData, setEditableData] = useState<Record<string, unknown>>(result.formData);
  const [downloading, setDownloading] = useState(false);

  const updateField = (key: string, value: string) => {
    setEditableData((prev) => ({ ...prev, [key]: value }));
  };

  const downloadPdf = async () => {
    setDownloading(true);
    try {
      const token = localStorage.getItem("medformai_token");
      // Use the letter endpoint — the narrative IS the letter, rendered once
      const patientName = (editableData.patientName || "patient").toString();
      const res = await fetch("/api/v1/forms/sicknote/letter-pdf", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ content: editableData.fitnessForDuty || editableData.reasonForAbsence || "", patientName }),
      });
      if (!res.ok) throw new Error("PDF generation failed");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement("a");
      a.href = url;
      a.download = `sick_note_${patientName.replace(/\s/g, "_")}.pdf`;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="animateIn" style={{ marginTop: "2rem" }}>
      {/* Time saved banner */}
      <div
        style={{
          background: "linear-gradient(135deg, #2d7a4a, #1a5c36)",
          color: "white",
          borderRadius: "var(--radius)",
          padding: "1.5rem",
          marginBottom: "1.5rem",
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: "3rem", fontWeight: 700, fontFamily: "var(--fontSerif)" }}>
          {result.timeSavedMinutes} min
        </div>
        <div style={{ fontSize: "0.875rem", opacity: 0.9 }}>
          saved on this {result.formType === "sickNote" ? "sick note" : "DTC form"}
          {" "}({timeSavedPercent}% reduction from {result.manualTimeMinutes} min manual)
        </div>
        {result.llmUsed && (
          <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", opacity: 0.8 }}>
            ✅ Generated by AI · PII redacted before LLM call
          </div>
        )}
      </div>

      {/* Before/After */}
      <div className="grid grid2" style={{ marginBottom: "1.5rem" }}>
        <div>
          <h4 style={{ marginBottom: "0.5rem" }}>What the Doctor Wrote</h4>
          <div
            style={{
              background: "#fff5e6",
              borderRadius: "8px",
              padding: "0.75rem",
              fontSize: "0.8125rem",
              fontFamily: "var(--fontMono)",
              maxHeight: "200px",
              overflowY: "auto",
              border: "1px solid #ffe0b3",
            }}
          >
            {result.originalNotes}
          </div>
        </div>
        <div>
          <h4 style={{ marginBottom: "0.5rem" }}>What the LLM Saw (PII Redacted)</h4>
          <div
            style={{
              background: "#1e1e1e",
              color: "#a5d6ff",
              borderRadius: "8px",
              padding: "0.75rem",
              fontSize: "0.8125rem",
              fontFamily: "var(--fontMono)",
              maxHeight: "200px",
              overflowY: "auto",
            }}
          >
            {result.redactedNotesPreview}
          </div>
        </div>
      </div>

      {/* PII Scan */}
      <div
        style={{
          padding: "1rem",
          borderRadius: "8px",
          background: result.piiScan.passed ? "#f0fdf4" : "#fef2f2",
          border: `1px solid ${result.piiScan.passed ? "#86efac" : "#fca5a5"}`,
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h4 style={{ margin: 0 }}>PII Compliance Scan</h4>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <span className={`badge ${result.piiScan.passed ? "badgeSuccess" : "badgeDanger"}`}>
              {result.piiScan.passed ? "PASSED" : "BLOCKED"}
            </span>
            <span className="badge badgeInfo">{scorePercent}%</span>
          </div>
        </div>
        {result.piiScan.findings.length === 0 ? (
          <p style={{ fontSize: "0.875rem", color: "var(--success)", marginTop: "0.5rem" }}>
            ✓ No PII findings — all fields comply with minimum-necessary principle.
          </p>
        ) : (
          <div style={{ marginTop: "0.5rem" }}>
            {result.piiScan.findings.map((f, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  gap: "0.5rem",
                  padding: "0.25rem 0",
                  fontSize: "0.8125rem",
                }}
              >
                <span
                  className={`badge ${
                    f.severity === "critical" ? "badgeDanger" : "badgeWarning"
                  }`}
                  style={{ flexShrink: 0 }}
                >
                  {f.severity}
                </span>
                <span>{f.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Editable Form Data */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <h4 style={{ margin: 0 }}>Auto-Filled Form — Editable</h4>
          {result.formType === "sickNote" && (
            <button
              className="primary"
              onClick={downloadPdf}
              disabled={downloading}
              style={{ padding: "0.5rem 1.25rem", fontSize: "0.875rem" }}
            >
              {downloading ? <><span className="spinner" /> Generating PDF...</> : "📄 Download PDF"}
            </button>
          )}
        </div>
        <div
          style={{
            background: "var(--code)",
            borderRadius: "8px",
            padding: "1rem",
          }}
        >
          {Object.entries(editableData).map(([key, value]) => (
            <div key={key} style={{ marginBottom: "0.75rem" }}>
              <label style={{ fontSize: "0.75rem", fontWeight: 500, color: "var(--textMuted)", marginBottom: "0.25rem" }}>
                {key}
              </label>
              {key.toLowerCase().includes("fitness") || key.toLowerCase().includes("reason") || key.toLowerCase().includes("notes") ? (
                <textarea
                  value={typeof value === "object" ? JSON.stringify(value) : String(value || "")}
                  onChange={(e) => updateField(key, e.target.value)}
                  rows={3}
                  style={{ fontSize: "0.8125rem", fontFamily: "var(--fontSans)" }}
                />
              ) : (
                <input
                  type="text"
                  value={typeof value === "object" ? JSON.stringify(value) : String(value || "")}
                  onChange={(e) => updateField(key, e.target.value)}
                  style={{ fontSize: "0.8125rem", fontFamily: "var(--fontSans)" }}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function FormTypeButton({
  active,
  onClick,
  title,
  subtitle,
}: {
  active: boolean;
  onClick: () => void;
  title: string;
  subtitle: string;
}) {
  return (
    <button
      onClick={onClick}
      className={active ? "primary" : "secondary"}
      style={{
        flex: 1,
        textAlign: "left",
        padding: "0.875rem 1rem",
      }}
    >
      <div style={{ fontWeight: 600, fontSize: "0.9375rem" }}>{title}</div>
      <div style={{ fontSize: "0.75rem", opacity: active ? 0.9 : 0.7 }}>{subtitle}</div>
    </button>
  );
}

const sampleNotes = {
  sickNote: `Patient: John Doe, DOB 1985-03-15. Presented today with acute gastroenteritis. Severe nausea, vomiting, and diarrhea for 2 days. Unable to work. Dehydrated on exam. Recommend rest and fluids for 3 days. Expected return to work on Monday. Prescribed ondansetron for nausea.`,
  dtc: `Patient: Jane Smith, DOB 1962-04-15, SIN 123-456-789. Severe osteoarthritis of bilateral knees diagnosed June 2021. Marked difficulty walking more than 50 meters without rest. Unable to climb stairs without significant pain. Requires assistance with bathing and dressing on bad days. Prescribed celecoxib and acetaminophen with limited relief. Total knee replacement recommended but delayed due to surgical wait list. Condition is prolonged and expected to last 12+ months. No life-sustaining therapy required.`,
};
