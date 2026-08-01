"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { useToast } from "@/components/Toast";

export default function SettingsPage() {
  const { user, updateProfile } = useAuth();
  const { showToast } = useToast();
  const [firstName, setFirstName] = useState(user?.firstName || "");
  const [lastName, setLastName] = useState(user?.lastName || "");
  const [specialty, setSpecialty] = useState(user?.specialty || "");
  const [licenseNumber, setLicenseNumber] = useState(user?.licenseNumber || "");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");

    const data: Record<string, unknown> = { firstName, lastName };
    if (user?.role === "doctor") {
      data.specialty = specialty;
      data.licenseNumber = licenseNumber;
    }
    if (newPassword) {
      if (newPassword.length < 8) {
        setError("Password must be at least 8 characters");
        setLoading(false);
        return;
      }
      data.password = newPassword;
    }

    try {
      await updateProfile(data);
      showToast("Profile updated successfully", "success");
      setNewPassword("");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Update failed";
      setError(msg);
      showToast(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div>
      <h2 style={{ marginBottom: "0.25rem" }}>Settings</h2>
      <p style={{ color: "var(--textMuted)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
        Manage your profile and account
      </p>

      <div className="card" style={{ maxWidth: "560px" }}>
        <form onSubmit={handleSave}>
          {/* Account info (read-only) */}
          <div style={{ marginBottom: "1.5rem" }}>
            <label>Email</label>
            <input type="email" value={user.email} disabled style={{ opacity: 0.6 }} />
          </div>

          <div className="grid grid2" style={{ marginBottom: "1rem" }}>
            <div>
              <label>First Name</label>
              <input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
            </div>
            <div>
              <label>Last Name</label>
              <input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} required />
            </div>
          </div>

          {user.role === "doctor" && (
            <div className="grid grid2" style={{ marginBottom: "1rem" }}>
              <div>
                <label>License Number</label>
                <input type="text" value={licenseNumber} onChange={(e) => setLicenseNumber(e.target.value)} />
              </div>
              <div>
                <label>Specialty</label>
                <input type="text" value={specialty} onChange={(e) => setSpecialty(e.target.value)} placeholder="Family Medicine" />
              </div>
            </div>
          )}

          {user.clinic && (
            <div style={{ marginBottom: "1.5rem" }}>
              <label>Clinic</label>
              <input type="text" value={user.clinic.name} disabled style={{ opacity: 0.6 }} />
            </div>
          )}

          {/* Password change */}
          <div style={{ marginBottom: "1.5rem" }}>
            <label>New Password (leave blank to keep current)</label>
            <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="••••••••" />
          </div>

          {error && (
            <div className="badge badgeDanger" style={{ display: "block", padding: "0.625rem", marginBottom: "1rem" }}>
              {error}
            </div>
          )}
          {message && (
            <div className="badge badgeSuccess" style={{ display: "block", padding: "0.625rem", marginBottom: "1rem" }}>
              ✓ {message}
            </div>
          )}

          <button type="submit" className="primary" disabled={loading} style={{ padding: "0.75rem 2rem" }}>
            {loading ? <><span className="spinner" /> Saving...</> : "Save Changes"}
          </button>
        </form>
      </div>
    </div>
  );
}
