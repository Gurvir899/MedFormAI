"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { getAuthToken } from "@/lib/auth";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  patientMatch?: {
    patientName: string;
    matchScore: number;
    matchType: string;
  };
  isStreaming?: boolean;
  isSickNote?: boolean;
  isDtc?: boolean;
  redactionPreview?: {
    taskType: string;
    fieldsIncluded: string[];
    fieldsExcluded: string[];
    redactedContext: string;
    tier1Count: number;
    tier2Count: number;
    totalTokensRedacted: number;
  };
}

interface PatientSuggestion {
  id: number;
  name: string;
  dob: string;
  diagnosis: string;
  score: number;
  matchType: string;
}

interface ConfirmationData {
  query: string;
  patient: PatientSuggestion | null;
  redactedContext: string;
  taskType: string;
  fieldsIncluded: string[];
  fieldsExcluded: string[];
  tier1Count: number;
  tier2Count: number;
}

const FORM_OPTIONS = [
  { id: "sickNote", label: "Sick Note", icon: "📝", desc: "Medical certificate of illness" },
  { id: "dtc", label: "DTC Form (T2201)", icon: "📋", desc: "Disability Tax Credit — full 16-page form" },
  { id: "medication_review", label: "Medication Review", icon: "💊", desc: "Review meds + interactions" },
  { id: "clinical_summary", label: "Clinical Summary", icon: "🩺", desc: "Full patient history overview" },
  { id: "general", label: "General Question", icon: "💬", desc: "Ask anything about this patient" },
];

export function CopilotChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [confirmLoading, setConfirmLoading] = useState(false);

  // Autocomplete state
  const [suggestions, setSuggestions] = useState<PatientSuggestion[]>([]);
  const [showPatientDropdown, setShowPatientDropdown] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<PatientSuggestion | null>(null);
  const [showFormOptions, setShowFormOptions] = useState(false);

  // Confirmation state
  const [confirmation, setConfirmation] = useState<ConfirmationData | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, confirmation, showPatientDropdown, showFormOptions]);

  // ─── Download sick note PDF ───────────────────────────────
  const downloadSickNotePdf = async (content: string, patientName?: string) => {
    try {
      const token = getAuthToken();
      const res = await fetch("/api/v1/forms/sicknote/letter-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ content, patientName: patientName || "patient" }),
      });
      if (!res.ok) throw new Error("PDF generation failed");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement("a");
      a.href = url;
      a.download = `sick_note_${(patientName || "patient").replace(/\s/g, "_")}.pdf`;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : "PDF download failed");
    }
  };

  // ─── Download DTC T2201 PDF ──────────────────────────────
  const downloadDtcPdf = async (content: string, patientName?: string) => {
    try {
      const token = getAuthToken();
      const res = await fetch("/api/v1/forms/dtc/letter-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ content, patientName: patientName || "patient" }),
      });
      if (!res.ok) throw new Error("DTC PDF generation failed");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement("a");
      a.href = url;
      a.download = `dtc_t2201_${(patientName || "patient").replace(/\s/g, "_")}.pdf`;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : "DTC PDF download failed");
    }
  };

  // ─── Patient search (debounced) ──────────────────────────
  const searchPatients = useCallback(async (query: string) => {
    const token = getAuthToken();
    if (!token || query.length < 2) {
      setSuggestions([]);
      return;
    }
    try {
      const res = await fetch(`/api/v1/copilot/patients?q=${encodeURIComponent(query)}&limit=5`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data.patients || []);
        setShowPatientDropdown(true);
        setShowFormOptions(false);
      }
    } catch { /* silent */ }
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setInput(val);

    // If user already selected a patient and is now typing again, reset
    if (selectedPatient) {
      setSelectedPatient(null);
      setShowFormOptions(false);
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const words = val.split(/\s+/);
      const lastWords = words.slice(-3).join(" ");
      if (lastWords.length >= 2) {
        searchPatients(lastWords);
      } else {
        setSuggestions([]);
        setShowPatientDropdown(false);
      }
    }, 300);
  };

  // ─── Patient selected → show form options ────────────────
  const handlePatientSelect = (patient: PatientSuggestion) => {
    setSelectedPatient(patient);
    setShowPatientDropdown(false);
    setShowFormOptions(true);
    setSuggestions([]);
    setInput("");
  };

  // ─── Form option selected → build query + show confirmation ─
  const handleFormSelect = async (formId: string) => {
    setShowFormOptions(false);
    if (!selectedPatient) return;

    // DTC flows through the normal copilot chat — narrative, not structured JSON
    const formOption = FORM_OPTIONS.find(f => f.id === formId);
    if (!formOption) return;

    let query = "";
    if (formId === "dtc") {
      query = `Complete the DTC T2201 form for ${selectedPatient.name}. Write it as a narrative document covering Part A (patient info), Part B (impairment categories — only those that apply), and Certification. Use the physician info for certification fields. If you need clarification on any impairment details, ask me before finalizing.`;
    } else if (formId === "sickNote") {
      query = `Draft a sick note for ${selectedPatient.name}`;
    } else if (formId === "medication_review") {
      query = `Review the medications for ${selectedPatient.name}, check for interactions`;
    } else if (formId === "clinical_summary") {
      query = `Provide a full clinical summary for ${selectedPatient.name}`;
    } else if (formId === "general") {
      setInput(`Tell me about ${selectedPatient.name}: `);
      setShowFormOptions(false);
      inputRef.current?.focus();
      return;
    }

    // Fetch redaction preview
    setConfirmLoading(true);
    try {
      const token = getAuthToken();
      const previewRes = await fetch("/api/v1/copilot/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ query }),
      });

      if (!previewRes.ok) throw new Error("Preview failed");
      const previewData = await previewRes.json();

      setConfirmation({
        query,
        patient: selectedPatient,
        redactedContext: "",
        taskType: formId,
        fieldsIncluded: [],
        fieldsExcluded: [],
        tier1Count: 0,
        tier2Count: 0,
      });

      // Fetch redaction preview from streaming endpoint
      if (previewData.patientFound) {
        const chatRes = await fetch("/api/v1/copilot/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({ query, history: [] }),
        });

        if (chatRes.ok && chatRes.body) {
          const reader = chatRes.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";
          let found = false;

          while (!found) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              try {
                const event = JSON.parse(line.slice(6));
                if (event.type === "redaction_preview") {
                  setConfirmation((prev) => prev ? {
                    ...prev,
                    redactedContext: event.data.redactedContext,
                    taskType: event.data.taskType,
                    fieldsIncluded: event.data.fieldsIncluded,
                    fieldsExcluded: event.data.fieldsExcluded,
                    tier1Count: event.data.tier1Count,
                    tier2Count: event.data.tier2Count,
                  } : prev);
                  found = true;
                  break;
                } else if (event.type === "thinking" || event.type === "chunk") {
                  found = true;
                  break;
                }
              } catch { /* skip */ }
            }
          }
          reader.cancel();
        }
      }
    } catch {
      // Fallback: show confirmation without redaction preview
    } finally {
      setConfirmLoading(false);
    }
  };

  // ─── Confirm and send ─────────────────────────────────────
  const confirmAndSend = () => {
    if (!confirmation) return;
    const query = confirmation.query;
    const patient = confirmation.patient;
    setConfirmation(null);
    setSelectedPatient(null);
    sendMessage(query, patient);
  };

  const cancelConfirmation = () => {
    setConfirmation(null);
    setSelectedPatient(null);
    inputRef.current?.focus();
  };

  // ─── Send message to copilot ─────────────────────────────
  const sendMessage = async (query: string, patient: PatientSuggestion | null) => {
    const userMessage: ChatMessage = {
      role: "user", content: query,
      patientMatch: patient ? {
        patientName: patient.name, matchScore: patient.score, matchType: patient.matchType,
      } : undefined,
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    const assistantIdx = messages.length + 1;
    setMessages((prev) => [...prev, { role: "assistant", content: "", isStreaming: true }]);

    try {
      const token = getAuthToken();
      const history = messages.map((m) => ({ role: m.role, content: m.content }));

      const response = await fetch("/api/v1/copilot/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ query, history }),
      });

      if (!response.ok) throw new Error("Copilot request failed");
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error("No response stream");

      let buffer = "";
      let fullContent = "";
      let patientMatch: ChatMessage["patientMatch"] | undefined;
      let redactionPreview: ChatMessage["redactionPreview"] | undefined;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === "patient_match") {
              patientMatch = { patientName: event.data.patientName, matchScore: event.data.matchScore, matchType: event.data.matchType };
            } else if (event.type === "redaction_preview") {
              redactionPreview = event.data;
            } else if (event.type === "chunk") {
              fullContent += event.data.content;
              setMessages((prev) => {
                const updated = [...prev];
                updated[assistantIdx] = { role: "assistant", content: fullContent, isStreaming: true, patientMatch };
                return updated;
              });
            } else if (event.type === "done") {
              fullContent = event.data.fullResponse || fullContent;
              const lc = fullContent.toLowerCase();
              const isSickNote = (lc.includes("sick") || lc.includes("unfit") || lc.includes("medically unfit") || lc.includes("sick leave") || lc.includes("absence")) && patientMatch !== undefined;
              const isDtc = (lc.includes("disability tax credit") || lc.includes("t2201") || lc.includes("part a") && lc.includes("part b") || lc.includes("marked restriction") || lc.includes("cumulative effect")) && patientMatch !== undefined;
              setMessages((prev) => {
                const updated = [...prev];
                updated[assistantIdx] = { role: "assistant", content: fullContent, isStreaming: false, patientMatch, isSickNote, isDtc, redactionPreview };
                return updated;
              });
            } else if (event.type === "error") {
              setMessages((prev) => {
                const updated = [...prev];
                updated[assistantIdx] = { role: "assistant", content: `Error: ${event.data.message}`, isStreaming: false };
                return updated;
              });
            }
          } catch { /* skip */ }
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[assistantIdx] = { role: "assistant", content: `Error: ${err instanceof Error ? err.message : "Request failed"}`, isStreaming: false };
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  // ─── Direct submit (for general queries without patient) ──
  const handleSubmit = async () => {
    if (!input.trim() || loading || confirmLoading) return;

    // If patient is selected, treat input as the query
    if (selectedPatient) {
      setConfirmLoading(true);
      const query = input.trim();
      try {
        const token = getAuthToken();
        const previewRes = await fetch("/api/v1/copilot/preview", {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({ query }),
        });
        if (previewRes.ok) {
          const previewData = await previewRes.json();
          setConfirmation({
            query,
            patient: selectedPatient,
            redactedContext: "",
            taskType: "general",
            fieldsIncluded: [],
            fieldsExcluded: [],
            tier1Count: 0,
            tier2Count: 0,
          });

          if (previewData.patientFound) {
            const chatRes = await fetch("/api/v1/copilot/chat", {
              method: "POST",
              headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
              body: JSON.stringify({ query, history: [] }),
            });
            if (chatRes.ok && chatRes.body) {
              const reader = chatRes.body.getReader();
              const decoder = new TextDecoder();
              let buffer = "";
              let found = false;
              while (!found) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";
                for (const line of lines) {
                  if (!line.startsWith("data: ")) continue;
                  try {
                    const event = JSON.parse(line.slice(6));
                    if (event.type === "redaction_preview") {
                      setConfirmation((prev) => prev ? { ...prev, redactedContext: event.data.redactedContext, taskType: event.data.taskType, fieldsIncluded: event.data.fieldsIncluded, fieldsExcluded: event.data.fieldsExcluded, tier1Count: event.data.tier1Count, tier2Count: event.data.tier2Count } : prev);
                      found = true; break;
                    } else if (event.type === "thinking" || event.type === "chunk") { found = true; break; }
                  } catch { /* skip */ }
                }
              }
              reader.cancel();
            }
          }
        }
      } catch { /* fallback */ }
      finally { setConfirmLoading(false); }
      return;
    }

    // No patient selected — try to match from the query
    setConfirmLoading(true);
    try {
      const token = getAuthToken();
      const previewRes = await fetch("/api/v1/copilot/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ query: input.trim() }),
      });
      if (previewRes.ok) {
        const previewData = await previewRes.json();
        if (previewData.patientFound) {
          const p = previewData.patient;
          setConfirmation({
            query: input.trim(),
            patient: { id: p.id, name: p.name, dob: p.dob, diagnosis: p.diagnosis || "", score: previewData.matchScore, matchType: previewData.matchType },
            redactedContext: "", taskType: "", fieldsIncluded: [], fieldsExcluded: [], tier1Count: 0, tier2Count: 0,
          });
          // Fetch redaction
          const chatRes = await fetch("/api/v1/copilot/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ query: input.trim(), history: [] }),
          });
          if (chatRes.ok && chatRes.body) {
            const reader = chatRes.body.getReader();
            const decoder = new TextDecoder();
            let buffer = ""; let found = false;
            while (!found) {
              const { done, value } = await reader.read();
              if (done) break;
              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n");
              buffer = lines.pop() || "";
              for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                try {
                  const event = JSON.parse(line.slice(6));
                  if (event.type === "redaction_preview") {
                    setConfirmation((prev) => prev ? { ...prev, redactedContext: event.data.redactedContext, taskType: event.data.taskType, fieldsIncluded: event.data.fieldsIncluded, fieldsExcluded: event.data.fieldsExcluded, tier1Count: event.data.tier1Count, tier2Count: event.data.tier2Count } : prev);
                    found = true; break;
                  } else if (event.type === "thinking" || event.type === "chunk") { found = true; break; }
                } catch { /* skip */ }
              }
            }
            reader.cancel();
          }
        } else {
          // No patient — send directly
          setInput("");
          sendMessage(input.trim(), null);
        }
      }
    } catch {
      setInput("");
      sendMessage(input.trim(), null);
    } finally {
      setConfirmLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (confirmation) confirmAndSend();
      else handleSubmit();
    }
  };

  const exampleQueries = [
    "Summarize the clinical history for Jon Doe",
    "What medications is Sarah J on?",
    "Draft a sick note for Mike Chen — gastroenteritis, 3 days off",
    "What are the allergies for Jhon Doe?",
    "Explain the treatment plan for Robert Williams",
  ];

  return (
    <div style={styles.container}>
      {/* Messages */}
      <div ref={scrollRef} style={styles.messages}>
        {messages.length === 0 && !confirmation && !showPatientDropdown && !showFormOptions && (
          <div style={styles.emptyState}>
            <div style={styles.logo}>🩺</div>
            <h3 style={styles.logoTitle}>Clinical Copilot</h3>
            <p style={styles.logoSubtitle}>
              Type a patient name to get started.
              <br />
              <span style={{ color: "var(--primary)" }}>PII-safe</span> — all patient data redacted before AI processing.
            </p>
            <div style={styles.examples}>
              {exampleQueries.map((q, i) => (
                <button key={i} style={styles.exampleBtn}
                  onClick={() => { setInput(q); inputRef.current?.focus(); }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={msg.role === "user" ? styles.userMsg : styles.assistantMsg}>
            <div style={styles.msgHeader}>
              <span style={msg.role === "user" ? styles.userLabel : styles.assistantLabel}>
                {msg.role === "user" ? "▸ YOU" : "🩺 COPILOT"}
              </span>
              {msg.patientMatch && (
                <span style={styles.patientBadge}>
                  📋 {msg.patientMatch.patientName}
                  <span style={styles.matchScore}> ({Math.round(msg.patientMatch.matchScore * 100)}% match)</span>
                </span>
              )}
            </div>
            {msg.redactionPreview && !msg.isStreaming && (
              <div style={styles.redactionPanel}>
                <div style={styles.redactionHeader}>🔒 What the LLM received (PII redacted + context minimized)</div>
                <div style={styles.redactionStats}>
                  <span style={styles.redactionBadge}>Task: <strong>{msg.redactionPreview.taskType}</strong></span>
                  <span style={styles.redactionBadge}>✓ Included: {msg.redactionPreview.fieldsIncluded.join(", ") || "none"}</span>
                  {msg.redactionPreview.fieldsExcluded.length > 0 && (
                    <span style={styles.redactionBadgeExcluded}>✗ Excluded: {msg.redactionPreview.fieldsExcluded.join(", ")}</span>
                  )}
                  <span style={styles.redactionBadge}>Tier 1: {msg.redactionPreview.tier1Count} redacted</span>
                  <span style={styles.redactionBadge}>Tier 2: {msg.redactionPreview.tier2Count} redacted</span>
                </div>
                <pre style={styles.redactedText}>{msg.redactionPreview.redactedContext}</pre>
              </div>
            )}
            <div style={styles.msgContent}>
              {msg.role === "assistant" ? <MarkdownRenderer content={msg.content} /> : msg.content}
              {msg.isStreaming && <span style={styles.cursor}>▊</span>}
            </div>
            {msg.isSickNote && !msg.isDtc && !msg.isStreaming && (
              <div style={{ marginTop: "0.75rem", paddingLeft: "0.75rem" }}>
                <button className="primary"
                  onClick={() => downloadSickNotePdf(msg.content, msg.patientMatch?.patientName)}
                  style={{ padding: "0.5rem 1rem", fontSize: "0.8125rem" }}>
                  📄 Generate Sick Note PDF
                </button>
              </div>
            )}
            {msg.isDtc && !msg.isStreaming && (
              <div style={{ marginTop: "0.75rem", paddingLeft: "0.75rem" }}>
                <button className="primary"
                  onClick={() => downloadDtcPdf(msg.content, msg.patientMatch?.patientName)}
                  style={{ padding: "0.5rem 1rem", fontSize: "0.8125rem" }}>
                  📋 Download T2201 PDF
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Dropdown area — above input, never covering it */}
      {/* Patient search results */}
      {showPatientDropdown && suggestions.length > 0 && (
        <div style={styles.dropdownArea}>
          <div style={styles.dropdownHeader}>Patients</div>
          {suggestions.map((s) => (
            <button key={s.id} style={styles.dropdownItem} onClick={() => handlePatientSelect(s)}>
              <span style={styles.dropdownItemName}>{s.name}</span>
              <span style={styles.dropdownItemDob}>{s.dob}</span>
              <span style={styles.dropdownItemDiagnosis}>{s.diagnosis}</span>
              <span style={styles.dropdownItemScore}>{Math.round(s.score * 100)}%</span>
            </button>
          ))}
        </div>
      )}

      {/* Form options after patient selected */}
      {showFormOptions && selectedPatient && (
        <div style={styles.dropdownArea}>
          <div style={styles.dropdownHeader}>
            {selectedPatient.name} <span style={styles.dropdownHeaderSub}>— select a form</span>
          </div>
          {FORM_OPTIONS.map((f) => (
            <button key={f.id} style={styles.formOption} onClick={() => handleFormSelect(f.id)}>
              <span style={styles.formOptionIcon}>{f.icon}</span>
              <div style={styles.formOptionText}>
                <div style={styles.formOptionLabel}>{f.label}</div>
                <div style={styles.formOptionDesc}>{f.desc}</div>
              </div>
            </button>
          ))}
          <button style={styles.dropdownCancel} onClick={() => { setShowFormOptions(false); setSelectedPatient(null); inputRef.current?.focus(); }}>
            ← Back to search
          </button>
        </div>
      )}

      {/* Confirmation panel */}
      {confirmation && (
        <div style={styles.confirmPanel}>
          <div style={styles.confirmHeader}>📋 Confirm before sending to AI</div>
          <div style={styles.confirmSection}>
            <div style={styles.confirmLabel}>1. Patient</div>
            {confirmation.patient ? (
              <div style={styles.confirmPatientCard}>
                <div style={styles.confirmPatientName}>
                  {confirmation.patient.name}
                  <span style={styles.confirmMatchScore}> ({Math.round(confirmation.patient.score * 100)}% — {confirmation.patient.matchType})</span>
                </div>
                {confirmation.patient.dob && <div style={styles.confirmPatientDob}>DOB: {confirmation.patient.dob}</div>}
                {confirmation.patient.diagnosis && <div style={styles.confirmPatientDiagnosis}>{confirmation.patient.diagnosis}</div>}
              </div>
            ) : (
              <div style={styles.confirmNoPatient}>No specific patient matched — general clinical question.</div>
            )}
          </div>
          <div style={styles.confirmSection}>
            <div style={styles.confirmLabel}>2. Your query</div>
            <div style={styles.confirmQuery}>{confirmation.query}</div>
          </div>
          {confirmation.patient && (
            <div style={styles.confirmSection}>
              <div style={styles.confirmLabel}>3. What the LLM will see (after PII redaction)</div>
              {confirmation.redactedContext ? (
                <>
                  <div style={styles.confirmRedactionStats}>
                    {confirmation.taskType && <span style={styles.redactionBadge}>Task: <strong>{confirmation.taskType}</strong></span>}
                    {confirmation.fieldsIncluded.length > 0 && <span style={styles.redactionBadge}>✓ Sent: {confirmation.fieldsIncluded.join(", ")}</span>}
                    {confirmation.fieldsExcluded.length > 0 && <span style={styles.redactionBadgeExcluded}>✗ Hidden: {confirmation.fieldsExcluded.join(", ")}</span>}
                    <span style={styles.redactionBadge}>Identifiers: {confirmation.tier1Count}</span>
                    <span style={styles.redactionBadge}>Quasi-identifiers: {confirmation.tier2Count}</span>
                  </div>
                  <pre style={styles.confirmRedactedText}>{confirmation.redactedContext}</pre>
                </>
              ) : (
                <div style={styles.confirmLoadingRedaction}>
                  <span className="spinner" style={{ borderTopColor: "var(--primary)" }} /> Preparing redaction preview...
                </div>
              )}
            </div>
          )}
          <div style={styles.confirmButtons}>
            <button className="secondary" onClick={cancelConfirmation} style={{ padding: "0.5rem 1.5rem" }}>Cancel</button>
            <button className="primary" onClick={confirmAndSend}
              disabled={confirmation.patient !== null && !confirmation.redactedContext}
              style={{ padding: "0.5rem 1.5rem" }}>
              ✓ Confirm &amp; Send to AI
            </button>
          </div>
        </div>
      )}

      {/* Input — always visible */}
      {!confirmation && (
        <div style={styles.inputArea}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={selectedPatient ? `Ask about ${selectedPatient.name}...` : "Type a patient name to get started..."}
            style={styles.input}
            rows={1}
            disabled={loading || confirmLoading}
          />
          <button onClick={handleSubmit}
            disabled={loading || confirmLoading || (!input.trim() && !selectedPatient)}
            style={{ ...styles.sendBtn, ...((loading || confirmLoading || (!input.trim() && !selectedPatient)) ? styles.sendBtnDisabled : {}) }}>
            {confirmLoading ? <><span className="spinner" /></> : "→"}
          </button>
        </div>
      )}
      <div style={styles.footer}>
        <span style={styles.footerItem}>🔒 PII redacted before LLM</span>
        <span style={styles.footerItem}>📝 Audit logged</span>
        <span style={styles.footerItem}>🛡️ PHIPA compliant</span>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { display: "flex", flexDirection: "column", height: "calc(100vh - 200px)", minHeight: "500px", background: "var(--surface)", borderRadius: "var(--radius)", border: "1px solid var(--border)", overflow: "hidden", boxShadow: "var(--shadow)" },
  messages: { flex: 1, overflowY: "auto", padding: "1.5rem", scrollBehavior: "smooth" },
  emptyState: { textAlign: "center", paddingTop: "3rem", paddingBottom: "2rem" },
  logo: { fontSize: "3rem", marginBottom: "0.5rem" },
  logoTitle: { color: "var(--primary)", fontSize: "1.5rem", fontFamily: "var(--fontSerif)", marginBottom: "0.5rem" },
  logoSubtitle: { color: "var(--textMuted)", fontSize: "0.875rem", lineHeight: 1.6, marginBottom: "1.5rem" },
  examples: { display: "flex", flexDirection: "column", gap: "0.5rem", alignItems: "center" },
  exampleBtn: { background: "var(--code)", border: "1px solid var(--border)", borderRadius: "8px", padding: "0.5rem 1rem", color: "var(--textMuted)", fontSize: "0.8125rem", cursor: "pointer", textAlign: "left", maxWidth: "500px", width: "100%", transition: "all 0.15s" },
  userMsg: { marginBottom: "1rem" },
  assistantMsg: { marginBottom: "1rem" },
  msgHeader: { display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" },
  userLabel: { fontSize: "0.75rem", fontWeight: 600, color: "var(--primaryLight)", textTransform: "uppercase", letterSpacing: "0.05em" },
  assistantLabel: { fontSize: "0.75rem", fontWeight: 600, color: "var(--success)", textTransform: "uppercase", letterSpacing: "0.05em" },
  patientBadge: { display: "inline-flex", alignItems: "center", gap: "0.25rem", background: "#e6f0fa", border: "1px solid #93c5fd", borderRadius: "999px", padding: "0.125rem 0.5rem", fontSize: "0.6875rem", color: "var(--primary)" },
  matchScore: { color: "var(--textMuted)", fontSize: "0.625rem" },
  msgContent: { color: "var(--text)", fontSize: "0.875rem", lineHeight: 1.7, fontFamily: "var(--fontSans)", whiteSpace: "normal", paddingLeft: "0.75rem", borderLeft: "3px solid var(--primary)", marginLeft: "0.25rem" },
  cursor: { display: "inline-block", color: "var(--primary)", animation: "blink 1s step-end infinite" },
  // ─── Dropdown area (above input) ───
  dropdownArea: { borderTop: "1px solid var(--border)", background: "var(--surface)", maxHeight: "250px", overflowY: "auto", flexShrink: 0 },
  dropdownHeader: { padding: "0.5rem 0.75rem", fontSize: "0.75rem", fontWeight: 600, color: "var(--primary)", background: "#e6f0fa", borderBottom: "1px solid var(--border)" },
  dropdownHeaderSub: { fontWeight: 400, color: "var(--textMuted)" },
  dropdownItem: { display: "flex", alignItems: "center", gap: "0.75rem", width: "100%", padding: "0.5rem 0.75rem", background: "transparent", border: "none", borderBottom: "1px solid var(--border)", cursor: "pointer", textAlign: "left", transition: "background 0.1s" },
  dropdownItemName: { color: "var(--text)", fontWeight: 600, fontSize: "0.8125rem", minWidth: "100px" },
  dropdownItemDob: { color: "var(--textMuted)", fontSize: "0.75rem", fontFamily: "var(--fontMono)" },
  dropdownItemDiagnosis: { color: "var(--textMuted)", fontSize: "0.75rem", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  dropdownItemScore: { color: "var(--success)", fontSize: "0.75rem", fontWeight: 600 },
  // ─── Form options ───
  formOption: { display: "flex", alignItems: "center", gap: "0.625rem", width: "100%", padding: "0.625rem 0.75rem", background: "transparent", border: "none", borderBottom: "1px solid var(--border)", cursor: "pointer", textAlign: "left", transition: "background 0.1s" },
  formOptionIcon: { fontSize: "1.25rem" },
  formOptionText: { flex: 1 },
  formOptionLabel: { fontSize: "0.875rem", fontWeight: 600, color: "var(--text)" },
  formOptionDesc: { fontSize: "0.6875rem", color: "var(--textMuted)" },
  dropdownCancel: { display: "block", width: "100%", padding: "0.5rem 0.75rem", background: "transparent", border: "none", cursor: "pointer", textAlign: "left", fontSize: "0.75rem", color: "var(--textMuted)" },
  // ─── Input ───
  inputArea: { display: "flex", gap: "0.5rem", padding: "0.75rem", borderTop: "1px solid var(--border)", background: "var(--surface)", flexShrink: 0 },
  input: { flex: 1, background: "var(--code)", border: "1px solid var(--border)", borderRadius: "8px", padding: "0.625rem 0.75rem", color: "var(--text)", fontSize: "0.875rem", fontFamily: "var(--fontSans)", resize: "none", outline: "none", minHeight: "40px", maxHeight: "120px" },
  sendBtn: { background: "var(--primary)", border: "none", borderRadius: "8px", padding: "0 1rem", color: "white", fontSize: "1.25rem", fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", minWidth: "44px", transition: "all 0.15s" },
  sendBtnDisabled: { opacity: 0.4, cursor: "not-allowed" },
  footer: { display: "flex", justifyContent: "center", gap: "1.5rem", padding: "0.5rem", borderTop: "1px solid var(--border)", background: "var(--surface)", flexShrink: 0 },
  footerItem: { fontSize: "0.6875rem", color: "var(--textMuted)" },
  // ─── Redaction panel ───
  redactionPanel: { marginTop: "0.5rem", marginBottom: "0.5rem", background: "var(--code)", border: "1px solid var(--border)", borderRadius: "8px", overflow: "hidden", marginLeft: "0.25rem" },
  redactionHeader: { padding: "0.5rem 0.75rem", fontSize: "0.75rem", fontWeight: 600, color: "var(--primary)", background: "#e6f0fa", borderBottom: "1px solid var(--border)" },
  redactionStats: { display: "flex", flexWrap: "wrap", gap: "0.375rem", padding: "0.5rem 0.75rem", borderBottom: "1px solid var(--border)" },
  redactionBadge: { display: "inline-flex", alignItems: "center", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "999px", padding: "0.125rem 0.5rem", fontSize: "0.6875rem", color: "var(--text)" },
  redactionBadgeExcluded: { display: "inline-flex", alignItems: "center", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: "999px", padding: "0.125rem 0.5rem", fontSize: "0.6875rem", color: "var(--danger)" },
  redactedText: { padding: "0.5rem 0.75rem", fontSize: "0.75rem", fontFamily: "var(--fontMono)", color: "var(--textMuted)", whiteSpace: "pre-wrap", wordBreak: "break-word", maxHeight: "150px", overflowY: "auto", margin: 0 },
  // ─── Confirmation panel ───
  confirmPanel: { padding: "1rem", borderTop: "2px solid var(--primary)", background: "var(--surface)", maxHeight: "60%", overflowY: "auto", flexShrink: 0 },
  confirmHeader: { fontSize: "0.875rem", fontWeight: 600, color: "var(--primary)", marginBottom: "1rem", paddingBottom: "0.5rem", borderBottom: "1px solid var(--border)" },
  confirmSection: { marginBottom: "1rem" },
  confirmLabel: { fontSize: "0.75rem", fontWeight: 600, color: "var(--textMuted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.375rem" },
  confirmPatientCard: { background: "#e6f0fa", border: "1px solid #93c5fd", borderRadius: "8px", padding: "0.75rem" },
  confirmPatientName: { fontSize: "0.9375rem", fontWeight: 600, color: "var(--text)" },
  confirmMatchScore: { fontSize: "0.75rem", color: "var(--textMuted)", fontWeight: 400 },
  confirmPatientDob: { fontSize: "0.75rem", color: "var(--textMuted)", marginTop: "0.25rem", fontFamily: "var(--fontMono)" },
  confirmPatientDiagnosis: { fontSize: "0.75rem", color: "var(--textMuted)", marginTop: "0.25rem" },
  confirmNoPatient: { fontSize: "0.8125rem", color: "var(--textMuted)", fontStyle: "italic", padding: "0.5rem", background: "var(--code)", borderRadius: "8px" },
  confirmQuery: { fontSize: "0.875rem", color: "var(--text)", padding: "0.5rem 0.75rem", background: "var(--code)", borderRadius: "8px", border: "1px solid var(--border)" },
  confirmRedactionStats: { display: "flex", flexWrap: "wrap", gap: "0.375rem", marginBottom: "0.5rem" },
  confirmRedactedText: { padding: "0.5rem 0.75rem", fontSize: "0.75rem", fontFamily: "var(--fontMono)", whiteSpace: "pre-wrap", wordBreak: "break-word", maxHeight: "120px", overflowY: "auto", margin: 0, background: "#1e1e1e", color: "#a5d6ff", borderRadius: "8px" },
  confirmLoadingRedaction: { padding: "0.75rem", fontSize: "0.8125rem", color: "var(--textMuted)", display: "flex", alignItems: "center", gap: "0.5rem" },
  confirmButtons: { display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "0.5rem" },
};
