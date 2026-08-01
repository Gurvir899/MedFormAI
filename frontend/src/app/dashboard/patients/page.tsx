"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useToast } from "@/components/Toast";

interface Patient {
  id: number;
  patientName: string;
  dateOfBirth: string;
  healthCardNumber: string;
  diagnosis: string;
  createdAt: string;
}

interface PatientsResponse {
  patients: Patient[];
  total: number;
}

export default function PatientsPage() {
  const { showToast } = useToast();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [error, setError] = useState("");

  // Add form state
  const [name, setName] = useState("");
  const [dob, setDob] = useState("");
  const [healthCard, setHealthCard] = useState("");
  const [diagnosis, setDiagnosis] = useState("");

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<PatientsResponse>("/api/v1/doctor/patients");
      setPatients(data.patients || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load patients");
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await apiFetch("/api/v1/doctor/patients", {
        method: "POST",
        body: JSON.stringify({
          patientName: name,
          dateOfBirth: dob,
          healthCardNumber: healthCard,
          diagnosis,
        }),
      });
      setShowAdd(false);
      setName(""); setDob(""); setHealthCard(""); setDiagnosis("");
      loadPatients();
      showToast("Patient added successfully", "success");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to add patient";
      setError(msg);
      showToast(msg, "error");
    }
  };

  return (
    <ProtectedRoute roles={["doctor", "admin"]}>
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
          <div>
            <h2 style={{ marginBottom: "0.25rem" }}>Patients</h2>
            <p style={{ color: "var(--textMuted)", fontSize: "0.875rem" }}>
              {patients.length} patient{patients.length !== 1 ? "s" : ""} in your practice
            </p>
          </div>
          <button className="primary" onClick={() => setShowAdd(!showAdd)}>
            {showAdd ? "Cancel" : "+ Add Patient"}
          </button>
        </div>

        {error && (
          <div className="badge badgeDanger" style={{ display: "block", padding: "0.625rem", marginBottom: "1rem" }}>
            {error}
          </div>
        )}

        {showAdd && (
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <h4 style={{ marginBottom: "1rem" }}>Add New Patient</h4>
            <form onSubmit={handleAdd}>
              <div className="grid grid2" style={{ marginBottom: "1rem" }}>
                <div>
                  <label>Full Name</label>
                  <input type="text" value={name} onChange={(e) => setName(e.target.value)} required autoFocus />
                </div>
                <div>
                  <label>Date of Birth</label>
                  <input type="date" value={dob} onChange={(e) => setDob(e.target.value)} required />
                </div>
              </div>
              <div style={{ marginBottom: "1rem" }}>
                <label>Health Card Number</label>
                <input type="text" value={healthCard} onChange={(e) => setHealthCard(e.target.value)} placeholder="1234 567 890" />
              </div>
              <div style={{ marginBottom: "1.5rem" }}>
                <label>Diagnosis</label>
                <textarea value={diagnosis} onChange={(e) => setDiagnosis(e.target.value)} rows={2} />
              </div>
              <button type="submit" className="primary" disabled={!name || !dob}>
                Save Patient
              </button>
            </form>
          </div>
        )}

        {loading ? (
          <div style={{ padding: "2rem" }}><span className="spinner" style={{ borderTopColor: "var(--primary)" }} /> Loading...</div>
        ) : patients.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "2rem" }}>
            <p style={{ color: "var(--textMuted)" }}>No patients yet. Click &quot;Add Patient&quot; to get started.</p>
          </div>
        ) : (
          <div className="card" style={{ padding: 0 }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--border)" }}>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Name</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>DOB</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Health Card</th>
                  <th style={{ textAlign: "left", padding: "0.75rem" }}>Diagnosis</th>
                </tr>
              </thead>
              <tbody>
                {patients.map((p) => (
                  <tr key={p.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "0.75rem", fontWeight: 500 }}>{p.patientName}</td>
                    <td style={{ padding: "0.75rem", color: "var(--textMuted)" }}>{p.dateOfBirth || "—"}</td>
                    <td style={{ padding: "0.75rem", fontFamily: "var(--fontMono)", fontSize: "0.75rem" }}>{p.healthCardNumber || "—"}</td>
                    <td style={{ padding: "0.75rem", color: "var(--textMuted)", maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis" }}>{p.diagnosis || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
