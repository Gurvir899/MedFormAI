"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";
import type { RoiResult } from "@/lib/types";

const provinces = [
  { value: "ontario", label: "Ontario" },
  { value: "quebec", label: "Quebec" },
  { value: "britishColumbia", label: "British Columbia" },
  { value: "alberta", label: "Alberta" },
  { value: "manitoba", label: "Manitoba" },
  { value: "novaScotia", label: "Nova Scotia" },
  { value: "territories", label: "Territories" },
];

const formOptions = [
  { value: "dtc", label: "Disability Tax Credit (T2201)" },
  { value: "privateInsurance", label: "Private Insurance Forms" },
  { value: "cppDisability", label: "CPP Disability Benefits" },
  { value: "sickNotes", label: "Sick Notes" },
];

export function RoiCalculator() {
  const [physicianCount, setPhysicianCount] = useState(10);
  const [province, setProvince] = useState("ontario");
  const [selectedForms, setSelectedForms] = useState<string[]>(["dtc", "privateInsurance", "cppDisability"]);
  const [useAiScribe, setUseAiScribe] = useState(true);
  const [result, setResult] = useState<RoiResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFormToggle = (formValue: string) => {
    setSelectedForms((prev) =>
      prev.includes(formValue)
        ? prev.filter((f) => f !== formValue)
        : [...prev, formValue]
    );
  };

  const calculate = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch<RoiResult>("/api/v1/roi/calculate", {
        method: "POST",
        body: JSON.stringify({
          physicianCount,
          province,
          formsAutomated: selectedForms,
          useAiScribe,
        }),
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to calculate ROI");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ animation: "fadeInUp 0.4s ease-out" }}>
      <h3>ROI Calculator</h3>
      <p style={{ color: "var(--textMuted)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
        Based on real data from the CMA/CFIB 2026 Report
      </p>

      <div className="grid grid2" style={{ marginBottom: "1rem" }}>
        <div>
          <label>Number of Physicians</label>
          <input
            type="number"
            min={1}
            value={physicianCount}
            onChange={(e) => setPhysicianCount(Number(e.target.value))}
          />
        </div>
        <div>
          <label>Province</label>
          <select value={province} onChange={(e) => setProvince(e.target.value)}>
            {provinces.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <label>Forms to Automate</label>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem" }}>
          {formOptions.map((form) => (
            <label
              key={form.value}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                cursor: "pointer",
                padding: "0.5rem 0.75rem",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                fontSize: "0.875rem",
                background: selectedForms.includes(form.value) ? "#e6f0fa" : "var(--surface)",
                color: "var(--text)",
              }}
            >
              <input
                type="checkbox"
                checked={selectedForms.includes(form.value)}
                onChange={() => handleFormToggle(form.value)}
                style={{ width: "auto" }}
              />
              {form.label}
            </label>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: "1.5rem" }}>
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <input
            type="checkbox"
            checked={useAiScribe}
            onChange={(e) => setUseAiScribe(e.target.checked)}
            style={{ width: "auto" }}
          />
          Include AI Scribe savings (64 min/day per physician)
        </label>
      </div>

      <button
        className="primary"
        onClick={calculate}
        disabled={loading || selectedForms.length === 0}
      >
        {loading ? <span className="spinner" /> : "Calculate ROI"}
      </button>

      {error && (
        <p style={{ color: "var(--danger)", marginTop: "1rem", fontSize: "0.875rem" }}>
          {error}
        </p>
      )}

      {result && (
        <div className="animateIn" style={{ marginTop: "2rem" }}>
          <div
            style={{
              background: "linear-gradient(135deg, var(--primary), var(--primaryLight))",
              color: "white",
              borderRadius: "var(--radius)",
              padding: "1.5rem",
              marginBottom: "1.5rem",
            }}
          >
            <p style={{ fontFamily: "var(--fontSerif)", fontSize: "1.5rem", lineHeight: 1.4 }}>
              {result.summary.headline}
            </p>
            <p style={{ fontSize: "0.75rem", opacity: 0.8, marginTop: "0.5rem" }}>
              Source: {result.summary.source}
            </p>
          </div>

          <div className="grid grid4">
            <StatCard label="Hours Saved/Year" value={result.hoursSavedPerYear.toLocaleString()} />
            <StatCard label="Cost Savings" value={`$${result.costSavingsPerYear.toLocaleString()}`} subValue="CAD/year" />
            <StatCard label="FTE Recovered" value={result.fteRecovered.toFixed(1)} />
            <StatCard label="Patient Visits" value={result.patientVisitsRecovered.toLocaleString()} subValue="recovered" />
          </div>

          <div className="grid grid2" style={{ marginTop: "1.5rem" }}>
            <div>
              <h4 style={{ marginBottom: "0.75rem" }}>Form Breakdown</h4>
              {Object.entries(result.formBreakdown).map(([key, form]) => (
                <div
                  key={key}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    padding: "0.5rem 0",
                    borderBottom: "1px solid var(--border)",
                    fontSize: "0.875rem",
                  }}
                >
                  <span>{form.formName}</span>
                  <span style={{ fontWeight: 600 }}>
                    {form.totalHoursSaved.toLocaleString()} hrs saved
                  </span>
                </div>
              ))}
            </div>

            <div>
              <h4 style={{ marginBottom: "0.75rem" }}>Per Physician Impact</h4>
              <div style={{ fontSize: "0.875rem", color: "var(--textMuted)" }}>
                <div style={{ marginBottom: "0.5rem" }}>
                  <strong style={{ color: "var(--text)" }}>
                    {result.hoursSavedPerPhysician.toLocaleString()} hours
                  </strong>
                  {" "}saved per physician/year
                </div>
                {result.useAiScribe && (
                  <div style={{ marginBottom: "0.5rem" }}>
                    <strong style={{ color: "var(--text)" }}>
                      {result.aiScribeBonusHours.toLocaleString()} hours
                    </strong>
                    {" "}from AI scribe alone
                  </div>
                )}
                <div>
                  <strong style={{ color: "var(--text)" }}>
                    {result.formAutomationHours.toLocaleString()} hours
                  </strong>
                  {" "}from form automation
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, subValue }: { label: string; value: string; subValue?: string }) {
  return (
    <div
      style={{
        background: "var(--code)",
        borderRadius: "8px",
        padding: "1rem",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--primary)", fontFamily: "var(--fontSerif)" }}>
        {value}
      </div>
      <div style={{ fontSize: "0.75rem", color: "var(--textMuted)", marginTop: "0.25rem" }}>
        {label}{subValue ? ` (${subValue})` : ""}
      </div>
    </div>
  );
}
