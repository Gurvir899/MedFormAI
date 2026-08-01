"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ClinicalNotesDemo } from "@/components/ClinicalNotesDemo";

export default function FormsPage() {
  return (
    <ProtectedRoute roles={["doctor", "admin"]}>
      <div>
        <h2 style={{ marginBottom: "0.5rem" }}>Form Automation</h2>
        <p style={{ color: "var(--textMuted)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
          Paste clinical notes — AI fills the form. PII stays protected.
        </p>
        <ClinicalNotesDemo />
      </div>
    </ProtectedRoute>
  );
}
