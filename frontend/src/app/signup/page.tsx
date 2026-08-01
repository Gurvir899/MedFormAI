"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth, type RegisterData } from "@/lib/auth";

export default function SignupPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [licenseNumber, setLicenseNumber] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [clinicName, setClinicName] = useState("");
  const [clinicAddress, setClinicAddress] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      setLoading(false);
      return;
    }

    if (!licenseNumber) {
      setError("Medical license number is required");
      setLoading(false);
      return;
    }

    const data: RegisterData = {
      email, password, role: "doctor", firstName, lastName,
      licenseNumber, specialty, clinicName, clinicAddress,
    };

    try {
      await register(data);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ maxWidth: "560px", margin: "3rem auto", padding: "0 1rem" }}>
      <div style={{ textAlign: "center", marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2rem", marginBottom: "0.25rem" }}>
          <Link href="/" style={{ color: "inherit", textDecoration: "none" }}>Paean</Link>
        </h1>
        <p style={{ fontFamily: "var(--fontSerif)", fontSize: "1.125rem", color: "var(--textMuted)", fontStyle: "italic" }}>
          Physician registration
        </p>
      </div>

      <div className="card">
        <div style={{
          padding: "0.75rem 1rem", background: "#e6f0fa", borderRadius: "8px",
          marginBottom: "1.5rem", fontSize: "0.8125rem", color: "var(--primary)",
          border: "1px solid #93c5fd",
        }}>
          🩺 Paean is for licensed physicians and clinic staff. Patients are managed by their physicians — no patient self-registration.
        </div>

        <form onSubmit={handleSubmit}>
          <div className="grid grid2" style={{ marginBottom: "1rem" }}>
            <div>
              <label htmlFor="firstName">First Name</label>
              <input id="firstName" type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} required autoFocus />
            </div>
            <div>
              <label htmlFor="lastName">Last Name</label>
              <input id="lastName" type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} required />
            </div>
          </div>

          <div style={{ marginBottom: "1rem" }}>
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="dr.smith@clinic.ca" required />
          </div>

          <div style={{ marginBottom: "1.5rem" }}>
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min 8 characters" required />
          </div>

          <div className="grid grid2" style={{ marginBottom: "1rem" }}>
            <div>
              <label htmlFor="license">License Number</label>
              <input id="license" type="text" value={licenseNumber} onChange={(e) => setLicenseNumber(e.target.value)} placeholder="CPSO-12345" required />
            </div>
            <div>
              <label htmlFor="specialty">Specialty (optional)</label>
              <input id="specialty" type="text" value={specialty} onChange={(e) => setSpecialty(e.target.value)} placeholder="Family Medicine" />
            </div>
          </div>
          <div style={{ marginBottom: "1rem" }}>
            <label htmlFor="clinicName">Clinic Name</label>
            <input id="clinicName" type="text" value={clinicName} onChange={(e) => setClinicName(e.target.value)} placeholder="Toronto Family Health" required />
          </div>
          <div style={{ marginBottom: "1.5rem" }}>
            <label htmlFor="clinicAddress">Clinic Address</label>
            <input id="clinicAddress" type="text" value={clinicAddress} onChange={(e) => setClinicAddress(e.target.value)} placeholder="100 Yonge St, Toronto, ON" required />
          </div>

          {error && (
            <div className="badge badgeDanger" style={{ display: "block", padding: "0.625rem", marginBottom: "1rem", textAlign: "center" }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            className="primary"
            disabled={loading || !email || !password || !firstName || !lastName || !licenseNumber || !clinicName}
            style={{ width: "100%", padding: "0.75rem", fontSize: "1rem" }}
          >
            {loading ? <><span className="spinner" /> Creating account...</> : "Register as Physician"}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.875rem", color: "var(--textMuted)" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "var(--primaryLight)", fontWeight: 500 }}>
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
