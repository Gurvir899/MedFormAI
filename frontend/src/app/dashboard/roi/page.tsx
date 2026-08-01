"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { RoiCalculator } from "@/components/RoiCalculator";

export default function RoiPage() {
  return (
    <ProtectedRoute>
      <div>
        <h2 style={{ marginBottom: "0.25rem" }}>ROI Calculator</h2>
        <p style={{ color: "var(--textMuted)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
          Based on real data from the CMA/CFIB 2026 Report
        </p>
        <RoiCalculator />
      </div>
    </ProtectedRoute>
  );
}
