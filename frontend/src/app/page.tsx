"use client";

import Link from "next/link";
import { Navbar } from "@/components/Navbar";

export default function Home() {

  return (
    <div>
      <Navbar />
      <main style={{ margin: 0, padding: 0 }}>
        {/* ─── Hero ───────────────────────────────────── */}
        <section style={{
          minHeight: "100vh", display: "flex", flexDirection: "column",
          justifyContent: "center", alignItems: "center",
          padding: "4rem 1.5rem", textAlign: "center",
          background: "linear-gradient(180deg, var(--bg) 0%, var(--surface) 100%)",
        }}>
          <div style={{
            display: "inline-block", padding: "0.25rem 0.75rem",
            background: "#e6f0fa", color: "var(--primary)",
            borderRadius: "999px", fontSize: "0.75rem", fontWeight: 600,
            textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "1.5rem",
          }}>
            PHIPA / PIPEDA Compliant · Real AI · Built for Canadian Physicians
          </div>
          <h1 style={{ fontSize: "clamp(3rem, 8vw, 5rem)", marginBottom: "0.5rem", letterSpacing: "-0.03em" }}>
            Paean
          </h1>
          <p style={{
            fontFamily: "var(--fontSerif)", fontSize: "clamp(1.1rem, 2.5vw, 1.5rem)",
            color: "var(--textMuted)", fontStyle: "italic",
            maxWidth: "700px", margin: "0 auto 2rem", lineHeight: 1.4,
          }}>
            The clinical copilot that fills forms, drafts sick notes,
            and completes DTC applications — while keeping patient data private.
          </p>
          <div style={{ display: "flex", justifyContent: "center", gap: "1rem", flexWrap: "wrap" }}>
            <Link href="/dashboard/copilot" className="primary" style={{
              display: "inline-block", padding: "0.75rem 2rem", borderRadius: "8px",
              color: "white", fontSize: "1rem", textDecoration: "none",
            }}>
              Try the Copilot →
            </Link>
            <Link href="/signup" className="secondary" style={{
              display: "inline-block", padding: "0.75rem 2rem", borderRadius: "8px",
              fontSize: "1rem", textDecoration: "none",
            }}>
              Register Clinic
            </Link>
          </div>
          <div style={{ marginTop: "3rem", color: "var(--textMuted)", fontSize: "0.875rem" }}>
            ↓ scroll to explore
          </div>
        </section>

        {/* ─── The Problem ─────────────────────────────── */}
        <Section>
          <SectionLabel>The Problem</SectionLabel>
          <h2 style={{ fontSize: "clamp(1.75rem, 4vw, 2.5rem)", marginBottom: "1.5rem", textAlign: "center" }}>
            19.8 million hours. Wasted. Every year.
          </h2>
          <p style={{ fontFamily: "var(--fontSerif)", fontSize: "1.15rem", color: "var(--textMuted)",
            fontStyle: "italic", textAlign: "center", maxWidth: "650px", margin: "0 auto 2rem" }}>
            That's 47% of all physician admin time — work the CMA calls "unnecessary."
            It's equivalent to losing 9,093 full-time physicians. 9% of Canada's entire workforce.
          </p>
          <div style={{ display: "flex", gap: "2.5rem", flexWrap: "wrap", justifyContent: "center", marginBottom: "2rem" }}>
            <Stat label="DTC form time" value="36.6 min" source="per form, 32×/year" />
            <Stat label="Sick notes/physician" value="136" source="10.4 min each, 25% paid" />
            <Stat label="Hours lost/physician" value="199" source="per year — 1 full month" />
            <Stat label="Privacy barrier" value="49%" source="#1 reason AI not adopted" />
          </div>
          <div style={{
            maxWidth: "600px", margin: "0 auto", padding: "1.25rem 1.5rem",
            background: "var(--code)", borderRadius: "var(--radius)",
            border: "1px solid var(--border)",
          }}>
            <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--primary)", marginBottom: "0.5rem" }}>
              The cost is human
            </div>
            <div style={{ fontSize: "0.875rem", color: "var(--textMuted)", lineHeight: 1.7 }}>
              <strong>93%</strong> of physicians say admin disrupts their work-life balance.
              <strong> 95%</strong> say unnecessary paperwork reduces professional fulfillment.
              <strong> 1 in 4</strong> are considering leaving medicine or retiring early.
              <strong> 54%</strong> plan to cut clinical hours — because of paperwork.
            </div>
          </div>
          <p style={{ fontFamily: "var(--fontSerif)", fontSize: "1.05rem", color: "var(--textMuted)",
            fontStyle: "italic", textAlign: "center", maxWidth: "550px", margin: "2rem auto 0" }}>
            The CMA says AI could save 64 minutes per day for physicians who adopt it.
            But 49% won't — because of privacy fear.
          </p>
        </Section>

        {/* ─── The Copilot ─────────────────────────────── */}
        <Section dark>
          <SectionLabel light>The Copilot</SectionLabel>
          <h2 style={{ fontSize: "clamp(1.75rem, 4vw, 2.5rem)", marginBottom: "1rem", textAlign: "center", color: "white" }}>
            Talk to your patients' data
          </h2>
          <p style={{ fontFamily: "var(--fontSerif)", fontSize: "1.15rem", color: "rgba(255,255,255,0.8)",
            fontStyle: "italic", textAlign: "center", maxWidth: "600px", margin: "0 auto 2rem" }}>
            Type a patient name. Ask a question. Get an answer — with every identifier
            redacted before it reaches the AI.
          </p>

          {/* Mock copilot chat */}
          <div style={{ maxWidth: "700px", margin: "0 auto", borderRadius: "var(--radius)",
            background: "var(--surface)", overflow: "hidden",
            boxShadow: "var(--shadowLg)", border: "1px solid var(--border)" }}>
            {/* Chat header */}
            <div style={{ padding: "0.75rem 1rem", borderBottom: "1px solid var(--border)",
              background: "#e6f0fa", fontSize: "0.75rem", fontWeight: 600,
              color: "var(--primary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              🩺 Clinical Copilot
            </div>
            {/* Chat messages */}
            <div style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
              <ChatMock role="user" text="Draft a sick note for Jon Doe" badge="📋 Jon Doe (100% match)" />
              <ChatMock role="assistant" text="## Sick Note — Medical Certificate of Illness

**Date:** August 1, 2026

**To Whom It May Concern:**

This is to confirm that **Jon Doe** was assessed on August 1, 2026 and has been diagnosed with **acute gastroenteritis**.

Mr. Doe is medically advised to refrain from work for a period of **three (3) days**, from August 1 to August 3, 2026.

**Physician:** Dr. Doctor Doctor, MD, CCFP
**Clinic:** Toronto Family Health" sickNote />
              <RedactionMock />
            </div>
          </div>
        </Section>

        {/* ─── PII Safety ──────────────────────────────── */}
        <Section>
          <SectionLabel>The Solution: Privacy-First AI</SectionLabel>
          <h2 style={{ fontSize: "clamp(1.75rem, 4vw, 2.5rem)", marginBottom: "0.5rem", textAlign: "center" }}>
            49% of physicians won't adopt AI
          </h2>
          <p style={{ fontFamily: "var(--fontSerif)", fontSize: "1.15rem", color: "var(--textMuted)",
            fontStyle: "italic", textAlign: "center", maxWidth: "500px", margin: "0 auto 2rem" }}>
            The #1 barrier? Privacy and medico-legal risk. Paean removes it.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", maxWidth: "600px", margin: "0 auto" }}>
            <LayerCard num="1" title="Field-Level Encryption at Rest" desc="Every PII field — names, DOBs, SINs, health cards, diagnoses, medications — encrypted individually with AES-256 (Fernet). A stolen database reveals ciphertext only." />
            <LayerCard num="2" title="Three-Tier Redaction Before LLM" desc="Tier 1: identifiers (name → [PATIENT_NAME_1]). Tier 2: quasi-identifiers (meds → [MEDICATION_1]). Tier 3: context minimization — only sends fields relevant to the task. The LLM never sees real patient data." />
            <LayerCard num="3" title="Pre-Send Confirmation" desc="Before every LLM call, the doctor sees exactly what data will be sent — task type, fields included/excluded, token counts, and the redacted context. Nothing goes to the AI without explicit physician approval." />
            <LayerCard num="4" title="PII Gateway Middleware" desc="Every API request is classified, checked against a per-endpoint minimum-necessary allowlist, and audit-logged. Excess PII fields are blocked with 403. Physician ID comes from JWT — never the request body." />
            <LayerCard num="5" title="Immutable Audit Trail" desc="Every PII access — who, what fields, which patient, when, from what IP — logged in an append-only table. No UPDATE or DELETE allowed. PHIPA/PIPEDA Principle 4.9 (Accountability) compliant." />
          </div>
        </Section>

        {/* ─── Forms ──────────────────────────────────── */}
        <Section dark>
          <SectionLabel light>Forms</SectionLabel>
          <h2 style={{ fontSize: "clamp(1.75rem, 4vw, 2.5rem)", marginBottom: "1rem", textAlign: "center", color: "white" }}>
            Sick notes → PDFs in seconds
          </h2>
          <p style={{ fontFamily: "var(--fontSerif)", fontSize: "1.15rem", color: "rgba(255,255,255,0.8)",
            fontStyle: "italic", textAlign: "center", maxWidth: "600px", margin: "0 auto 2rem" }}>
            Ask the copilot to draft a sick note or complete a DTC T2201.
            The narrative goes straight to a professional PDF on clinic letterhead.
          </p>
          <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap", justifyContent: "center" }}>
            <FormCard icon="📝" title="Sick Notes" desc="Medical certificate of illness — one LLM call, narrative → PDF" />
            <FormCard icon="📋" title="DTC T2201" desc="Disability Tax Credit — full 16-page CRA form, generated as narrative" />
            <FormCard icon="💊" title="Medication Review" desc="Check interactions, summarize prescriptions" />
            <FormCard icon="🩺" title="Clinical Summary" desc="Full patient history overview in seconds" />
          </div>
        </Section>

        {/* ─── How It Works ───────────────────────────── */}
        <Section>
          <SectionLabel>How It Works</SectionLabel>
          <h2 style={{ fontSize: "clamp(1.75rem, 4vw, 2.5rem)", marginBottom: "1.5rem", textAlign: "center" }}>
            From clinical notes to completed forms
          </h2>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center",
            gap: "0.5rem", flexWrap: "wrap", maxWidth: "900px", margin: "0 auto" }}>
            <PipelineNode title="1. Type patient name" subtitle="Fuzzy match handles misspellings" />
            <Arrow />
            <PipelineNode title="2. Confirm what AI sees" subtitle="Redaction preview before send" highlighted />
            <Arrow />
            <PipelineNode title="3. AI generates narrative" subtitle="Sick note, DTC, summary — streaming" highlighted />
            <Arrow />
            <PipelineNode title="4. Download PDF" subtitle="Clinic letterhead, compliance footer" />
          </div>
        </Section>

        {/* ─── CTA ────────────────────────────────────── */}
        <section style={{
          minHeight: "60vh", display: "flex", flexDirection: "column",
          justifyContent: "center", alignItems: "center",
          padding: "4rem 1.5rem", textAlign: "center",
          background: "linear-gradient(180deg, var(--surface) 0%, var(--bg) 100%)",
        }}>
          <h2 style={{ fontSize: "clamp(2rem, 5vw, 3rem)", marginBottom: "1rem" }}>
            Give 199 hours back to every physician
          </h2>
          <p style={{ fontFamily: "var(--fontSerif)", fontSize: "1.25rem", color: "var(--textMuted)",
            fontStyle: "italic", maxWidth: "550px", margin: "0 auto 2rem" }}>
            One month of working time, per physician, per year.
            That's 9,093 full-time physicians recovered nationally.
          </p>
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", justifyContent: "center" }}>
            <Link href="/dashboard/copilot" className="primary" style={{
              display: "inline-block", padding: "0.875rem 2.5rem", borderRadius: "8px",
              color: "white", fontSize: "1.1rem", textDecoration: "none",
            }}>
              Try the Copilot →
            </Link>
          </div>
        </section>

        {/* ─── Footer ─────────────────────────────────── */}
        <footer style={{
          textAlign: "center", padding: "2rem 1rem",
          borderTop: "1px solid var(--border)", color: "var(--textMuted)", fontSize: "0.8125rem",
        }}>
          <p style={{ fontFamily: "var(--fontSerif)", fontSize: "1rem", marginBottom: "0.5rem" }}>
            Paean — Built for Canadian Physicians
          </p>
          <p>
            Data source: CMA/CFIB (2026). &ldquo;Losing doctors to desk work: Canadian physicians
            lose 20 million hours each year to red tape.&rdquo;
          </p>
          <p style={{ marginTop: "0.5rem", opacity: 0.7 }}>
            AES-256 encryption · PII Gateway · LLM redaction · Immutable audit trail · PHIPA/PIPEDA
          </p>
        </footer>
      </main>
    </div>
  );
}

// ─── Components ──────────────────────────────────────────────────────

function Section({ children, dark }: { children: React.ReactNode; dark?: boolean }) {
  return (
    <section style={{
      minHeight: "100vh", display: "flex", flexDirection: "column",
      justifyContent: "center", padding: "4rem 1.5rem",
      background: dark ? "linear-gradient(135deg, var(--primary) 0%, var(--primaryLight) 100%)" : "var(--surface)",
    }}>
      <div style={{ maxWidth: "1000px", margin: "0 auto", width: "100%" }}>
        {children}
      </div>
    </section>
  );
}

function SectionLabel({ children, light }: { children: React.ReactNode; light?: boolean }) {
  return (
    <div style={{
      textAlign: "center", fontSize: "0.75rem", fontWeight: 600,
      color: light ? "rgba(255,255,255,0.6)" : "var(--textMuted)",
      textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "0.75rem",
    }}>
      {children}
    </div>
  );
}

function Stat({ label, value, source }: { label: string; value: string; source: string }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontFamily: "var(--fontSerif)", fontSize: "2.5rem", fontWeight: 700, color: "var(--primary)" }}>
        {value}
      </div>
      <div style={{ fontSize: "0.875rem", color: "var(--textMuted)" }}>{label}</div>
      <div style={{ fontSize: "0.6875rem", color: "var(--textMuted)", opacity: 0.7 }}>{source}</div>
    </div>
  );
}

function ChatMock({ role, text, badge, sickNote }: { role: "user" | "assistant"; text: string; badge?: string; sickNote?: boolean }) {
  const isUser = role === "user";
  return (
    <div>
      <div style={{ fontSize: "0.75rem", fontWeight: 600, marginBottom: "0.25rem",
        color: isUser ? "var(--primaryLight)" : "var(--success)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
        {isUser ? "▸ YOU" : "🩺 COPILOT"}
        {badge && <span style={{ marginLeft: "0.5rem", background: "#e6f0fa", border: "1px solid #93c5fd",
          borderRadius: "999px", padding: "0.125rem 0.5rem", fontSize: "0.6875rem", color: "var(--primary)" }}>
          {badge}
        </span>}
      </div>
      <div style={{
        fontSize: "0.875rem", lineHeight: 1.7, paddingLeft: "0.75rem",
        borderLeft: `3px solid ${isUser ? "var(--primaryLight)" : "var(--primary)"}`,
        whiteSpace: "pre-wrap", color: "var(--text)",
      }}>
        {text}
      </div>
      {sickNote && (
        <div style={{ marginTop: "0.5rem", paddingLeft: "0.75rem" }}>
          <span style={{
            display: "inline-block", padding: "0.375rem 0.875rem", borderRadius: "8px",
            background: "var(--primary)", color: "white", fontSize: "0.75rem", fontWeight: 600,
          }}>
            📄 Generate Sick Note PDF
          </span>
        </div>
      )}
    </div>
  );
}

function RedactionMock() {
  return (
    <div style={{
      marginTop: "0.5rem", background: "var(--code)", border: "1px solid var(--border)",
      borderRadius: "8px", overflow: "hidden",
    }}>
      <div style={{
        padding: "0.5rem 0.75rem", fontSize: "0.75rem", fontWeight: 600, color: "var(--primary)",
        background: "#e6f0fa", borderBottom: "1px solid var(--border)",
      }}>
        🔒 What the LLM received (PII redacted + context minimized)
      </div>
      <div style={{ padding: "0.5rem 0.75rem", display: "flex", flexWrap: "wrap", gap: "0.375rem" }}>
        <span style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "999px",
          padding: "0.125rem 0.5rem", fontSize: "0.6875rem", color: "var(--text)" }}>
          Task: <strong>sickNote</strong>
        </span>
        <span style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "999px",
          padding: "0.125rem 0.5rem", fontSize: "0.6875rem", color: "var(--text)" }}>
          ✓ Included: diagnosis, notes
        </span>
        <span style={{ background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: "999px",
          padding: "0.125rem 0.5rem", fontSize: "0.6875rem", color: "var(--danger)" }}>
          ✗ Excluded: medications, allergies
        </span>
      </div>
      <pre style={{
        padding: "0.5rem 0.75rem", fontSize: "0.75rem", fontFamily: "var(--fontMono)",
        color: "var(--textMuted)", whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0,
      }}>
{`Patient: [PATIENT_NAME_1]
DOB: [DOB_1]
Diagnosis: Acute gastroenteritis with dehydration
Clinical Notes: Presented with severe nausea...`}</pre>
    </div>
  );
}

function LayerCard({ num, title, desc }: { num: string; title: string; desc: string }) {
  return (
    <div style={{
      display: "flex", gap: "1rem", alignItems: "flex-start",
      padding: "1rem 1.25rem", background: "var(--surface)",
      border: "1px solid var(--border)", borderRadius: "var(--radius)",
      boxShadow: "var(--shadow)",
    }}>
      <div style={{
        flexShrink: 0, width: "32px", height: "32px", borderRadius: "50%",
        background: "var(--primary)", color: "white", fontSize: "0.875rem", fontWeight: 700,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>{num}</div>
      <div>
        <div style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text)", marginBottom: "0.25rem" }}>{title}</div>
        <div style={{ fontSize: "0.8125rem", color: "var(--textMuted)", lineHeight: 1.5 }}>{desc}</div>
      </div>
    </div>
  );
}

function FormCard({ icon, title, desc }: { icon: string; title: string; desc: string }) {
  return (
    <div style={{
      width: "220px", padding: "1.25rem", borderRadius: "var(--radius)",
      background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.2)",
    }}>
      <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>{icon}</div>
      <div style={{ fontSize: "1rem", fontWeight: 600, color: "white", marginBottom: "0.25rem" }}>{title}</div>
      <div style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.7)", lineHeight: 1.5 }}>{desc}</div>
    </div>
  );
}

function PipelineNode({ title, subtitle, highlighted }: { title: string; subtitle: string; highlighted?: boolean }) {
  return (
    <div style={{
      background: highlighted ? "#e6f0fa" : "var(--code)",
      border: highlighted ? "1px solid #93c5fd" : "1px solid var(--border)",
      borderRadius: "10px", padding: "0.75rem 1rem", textAlign: "center", minWidth: "140px",
    }}>
      <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text)" }}>{title}</div>
      <div style={{ fontSize: "0.75rem", color: "var(--textMuted)" }}>{subtitle}</div>
    </div>
  );
}

function Arrow() {
  return <span style={{ color: "var(--textMuted)", fontSize: "1.25rem" }}>→</span>;
}
