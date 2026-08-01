"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";
import type { FormPreviewResult } from "@/lib/types";

export function FormAutomation() {
  const [patientId, setPatientId] = useState("demo-patient-001");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FormPreviewResult | null>(null);
  const [error, setError] = useState("");

  const runPipeline = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await apiFetch<FormPreviewResult>("/api/v1/forms/dtc/preview", {
        method: "POST",
        body: JSON.stringify({ patientId }),
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pipeline failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>Multi-Agent Form Automation Pipeline</h3>
      <p style={{ color: "var(--textMuted)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
        Disability Tax Credit (T2201) — Canada&apos;s #1 most burdensome form
      </p>

      <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <div style={{ flex: 1 }}>
          <label>Patient ID (EMR)</label>
          <input
            type="text"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            placeholder="Enter patient ID from EMR"
          />
        </div>
        <div style={{ display: "flex", alignItems: "flex-end" }}>
          <button className="primary" onClick={runPipeline} disabled={loading || !patientId}>
            {loading ? <span className="spinner" /> : "Run Pipeline"}
          </button>
        </div>
      </div>

      {error && (
        <div className="badge badgeDanger" style={{ padding: "0.75rem", marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      {result && (
        <div className="animateIn">
          {/* Pipeline Steps */}
          <PipelineSteps steps={result.pipelineSteps} />

          {/* PII Compliance Scan */}
          <PiiScanResult scan={result.piiScan} />

          {/* Form Data Preview */}
          <div style={{ marginTop: "1.5rem" }}>
            <h4>Auto-Populated Form Data</h4>
            {result.requiresReview && (
              <div className="badge badgeWarning" style={{ marginBottom: "0.75rem" }}>
                Requires Physician Review
              </div>
            )}
            <div
              style={{
                background: "var(--code)",
                borderRadius: "8px",
                padding: "1rem",
                maxHeight: "300px",
                overflowY: "auto",
                fontSize: "0.8125rem",
              }}
            >
              <FormDataDisplay
                formData={result.formData}
                confidence={result.confidence}
              />
            </div>
          </div>

          {/* Redacted Preview */}
          <div style={{ marginTop: "1.5rem" }}>
            <h4>PII-Redacted Preview (Safe for Logging)</h4>
            <pre
              style={{
                maxHeight: "200px",
                overflowY: "auto",
                fontSize: "0.75rem",
                background: "#1e1e1e",
                color: "#a5d6ff",
              }}
            >
              {result.redactedPreview}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

function PipelineSteps({ steps }: { steps: FormPreviewResult["pipelineSteps"] }) {
  const agentLabels: Record<string, string> = {
    dataExtractor: "Agent 1: Data Extractor",
    formFiller: "Agent 2: Form Filler",
    piiGuardian: "Agent 3: PII Guardian",
  };

  return (
    <div style={{ marginBottom: "1.5rem" }}>
      <h4>Pipeline Execution</h4>
      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
        {steps.map((step, idx) => (
          <div
            key={idx}
            style={{
              flex: 1,
              background: "var(--code)",
              borderRadius: "8px",
              padding: "0.75rem",
              textAlign: "center",
              border: "1px solid var(--border)",
            }}
          >
            <div style={{ fontSize: "0.75rem", color: "var(--textMuted)" }}>
              {agentLabels[step.agent] || step.agent}
            </div>
            <div style={{ marginTop: "0.25rem" }}>
              <span className="badge badgeSuccess">✓ {step.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PiiScanResult({ scan }: { scan: FormPreviewResult["piiScan"] }) {
  const scorePercent = Math.round(scan.score * 100);
  const badgeClass = scan.passed ? "badgeSuccess" : "badgeDanger";

  return (
    <div
      style={{
        marginTop: "1.5rem",
        padding: "1rem",
        borderRadius: "8px",
        background: scan.passed ? "#f0fdf4" : "#fef2f2",
        border: `1px solid ${scan.passed ? "#86efac" : "#fca5a5"}`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h4 style={{ margin: 0 }}>PII Compliance Scan</h4>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <span className={`badge ${badgeClass}`}>
            {scan.passed ? "PASSED" : "BLOCKED"}
          </span>
          <span className="badge badgeInfo">{scorePercent}% score</span>
        </div>
      </div>

      {scan.findings.length > 0 && (
        <div style={{ marginTop: "0.75rem" }}>
          {scan.findings.map((finding, idx) => (
            <div
              key={idx}
              style={{
                display: "flex",
                gap: "0.5rem",
                padding: "0.375rem 0",
                fontSize: "0.8125rem",
                borderBottom: idx < scan.findings.length - 1 ? "1px solid rgba(0,0,0,0.05)" : "none",
              }}
            >
              <span
                className={`badge ${
                  finding.severity === "critical"
                    ? "badgeDanger"
                    : finding.severity === "warning"
                    ? "badgeWarning"
                    : "badgeInfo"
                }`}
                style={{ flexShrink: 0 }}
              >
                {finding.severity}
              </span>
              <span>{finding.message}</span>
            </div>
          ))}
        </div>
      )}

      {scan.findings.length === 0 && (
        <p style={{ fontSize: "0.875rem", color: "var(--success)", marginTop: "0.5rem" }}>
          No PII findings — all fields comply with minimum-necessary principle.
        </p>
      )}
    </div>
  );
}

function FormDataDisplay({
  formData,
  confidence,
}: {
  formData: Record<string, unknown>;
  confidence: Record<string, number>;
}) {
  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <tbody>
        {Object.entries(formData).map(([key, value]) => {
          const conf = confidence[key] ?? 0;
          const confColor = conf >= 0.9 ? "var(--success)" : conf >= 0.7 ? "var(--warning)" : "var(--danger)";
          return (
            <tr key={key}>
              <td style={{ padding: "0.375rem 0", fontWeight: 500, width: "40%", verticalAlign: "top" }}>
                {key}
              </td>
              <td style={{ padding: "0.375rem 0", color: "var(--textMuted)" }}>
                {typeof value === "object" ? JSON.stringify(value) : String(value ?? "")}
              </td>
              <td style={{ padding: "0.375rem 0", textAlign: "right", width: "60px" }}>
                <span style={{ color: confColor, fontWeight: 600, fontSize: "0.75rem" }}>
                  {Math.round(conf * 100)}%
                </span>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
