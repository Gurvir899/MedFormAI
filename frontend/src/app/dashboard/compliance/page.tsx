"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ComplianceDashboardView } from "@/components/ComplianceDashboardView";

export default function CompliancePage() {
  return (
    <ProtectedRoute roles={["doctor", "admin"]}>
      <div>
        <h2 style={{ marginBottom: "0.25rem" }}>Compliance Dashboard</h2>
        <p style={{ color: "var(--textMuted)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
          PHIPA / PIPEDA posture — real-time audit trail
        </p>
        <ComplianceDashboardView />
      </div>
    </ProtectedRoute>
  );
}
