"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { CopilotChat } from "@/components/CopilotChat";

export default function CopilotPage() {
  return (
    <ProtectedRoute roles={["doctor", "admin"]}>
      <div style={{ height: "100%" }}>
        <h2 style={{ marginBottom: "0.25rem", color: "var(--primary)" }}>Clinical Copilot</h2>
        <p style={{ color: "var(--textMuted)", fontSize: "0.875rem", marginBottom: "1rem" }}>
          AI assistant with PII-safe patient matching — type a name (even misspelled) and ask anything
        </p>
        <CopilotChat />
      </div>
    </ProtectedRoute>
  );
}
