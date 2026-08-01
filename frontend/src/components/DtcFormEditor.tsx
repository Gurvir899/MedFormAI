"use client";

import { useState } from "react";

/**
 * DtcFormEditor — editable T2201 form fields with PDF download.
 * Renders all filled fields as editable inputs.
 * Doctor can modify any value, then download the PDF.
 */

interface DtcFormEditorProps {
  initialData: Record<string, unknown>;
  patientName?: string;
  onDownload: (data: Record<string, unknown>) => void;
}

// Field metadata: which fields are textareas vs inputs vs booleans
const TEXTAREA_FIELDS = new Set([
  "q1Diagnoses", "q4Examples", "q3DevicesTherapy", "claimantSupportDetails",
  "mentalQ6Examples", "cumulativeQ2Examples", "lstQ3EligibleActivities",
  "certAddress",
]);

const BOOL_FIELDS = new Set([
  "q5MarkedRestriction", "q6AllOrSubstantiallyAll", "q8Prolonged12Months",
  "visionQ3MeetsCriteria", "visionQ5Prolonged12Months",
  "mentalQ4ImpairedIndependence", "mentalQ7MarkedRestriction", "mentalQ8AllOrSubstantiallyAll", "mentalQ10Prolonged12Months",
  "cumulativeQ3ExistTogether", "cumulativeQ4EquivalentToMarked", "cumulativeQ6Prolonged12Months",
  "lstQ4SupportsVitalFunction", "lstQ8Prolonged12Months",
  "isSelfOrLegalRep", "certHasMedicalInfoOnFile",
  "claimantCohabitates", "claimantProvidesFood", "claimantProvidesShelter", "claimantProvidesClothing",
]);

const TRISTATE_FIELDS = new Set([
  "q2Medication", "q9LikelyToImprove",
  "visionQ6LikelyToImprove",
  "mentalQ11LikelyToImprove",
  "cumulativeQ7LikelyToImprove",
  "lstQ9LikelyToImprove",
]);

// Section labels
const SECTION_LABELS: Record<string, string> = {
  personWithDisability: "Person with Disability",
  supportingFamilyMember: "Supporting Family Member",
  adjustments: "Tax Return Adjustments",
  authorization: "Authorization",
  vision: "Vision",
  speaking: "Speaking",
  hearing: "Hearing",
  walking: "Walking",
  eliminating: "Eliminating",
  feeding: "Feeding",
  dressing: "Dressing",
  mentalFunctions: "Mental Functions",
  cumulativeEffect: "Cumulative Effect",
  lifeSustainingTherapy: "Life-Sustaining Therapy",
};

// Field labels
const FIELD_LABELS: Record<string, string> = {
  personFirstName: "First Name", personLastName: "Last Name", personSin: "SIN",
  personMailingAddress: "Mailing Address", personCity: "City", personProvince: "Province",
  personPostalCode: "Postal Code", personDateOfBirth: "Date of Birth",
  claimantFirstName: "First Name", claimantLastName: "Last Name", claimantRelationship: "Relationship",
  claimantSin: "SIN", claimantCohabitates: "Cohabitates?",
  claimantProvidesFood: "Provides Food?", claimantProvidesShelter: "Provides Shelter?",
  claimantProvidesClothing: "Provides Clothing?", claimantSupportDetails: "Support Details",
  claimantSignature: "Signature",
  isSelfOrLegalRep: "Self or Legal Rep?", adjustPreviousReturns: "Adjust Previous Returns?",
  partAQ4Signature: "Signature", partAQ4Telephone: "Telephone", partAQ4Date: "Date",
  patientNameHeader: "Patient Name",
  designation: "Practitioner Designation", initials: "Initials",
  q1Diagnoses: "Diagnoses", q2Medication: "Medication?",
  q3DevicesTherapy: "Devices/Therapy", q4Examples: "Examples of Impairment",
  q5MarkedRestriction: "Marked Restriction?", q6AllOrSubstantiallyAll: "All/Substantially All?",
  q7YearImpaired: "Year Impaired", q8Prolonged12Months: "Prolonged 12+ Months?",
  q9LikelyToImprove: "Likely to Improve?", q9ImprovementYear: "Improvement Year",
  visionDesignation: "Designation", visionQ1Diagnoses: "Diagnoses",
  visionQ2AspectImpaired: "Aspect Impaired", visionQ3MeetsCriteria: "Meets Criteria?",
  visionQ4YearImpaired: "Year Impaired", visionQ5Prolonged12Months: "Prolonged 12+ Months?",
  visionQ6LikelyToImprove: "Likely to Improve?", visionQ6ImprovementYear: "Improvement Year",
  mentalDesignation: "Designation", mentalQ1Diagnoses: "Diagnoses",
  mentalQ2Medication: "Medication?", mentalQ3DevicesTherapy: "Devices/Therapy",
  mentalQ4ImpairedIndependence: "Impaired Independence?",
  mentalQ6Examples: "Examples", mentalQ7MarkedRestriction: "Marked Restriction?",
  mentalQ8AllOrSubstantiallyAll: "All/Substantially All?", mentalQ9YearImpaired: "Year Impaired",
  mentalQ10Prolonged12Months: "Prolonged 12+ Months?", mentalQ11LikelyToImprove: "Likely to Improve?",
  cumulativeDesignation: "Designation", cumulativeQ1Categories: "Categories",
  cumulativeQ2Examples: "Examples", cumulativeQ3ExistTogether: "Exist Together?",
  cumulativeQ4EquivalentToMarked: "Equivalent to Marked?", cumulativeQ5YearBegan: "Year Began",
  cumulativeQ6Prolonged12Months: "Prolonged 12+ Months?", cumulativeQ7LikelyToImprove: "Likely to Improve?",
  lstDesignation: "Designation", lstQ2TherapyTypes: "Therapy Types",
  lstQ2MedicalConditions: "Medical Conditions", lstQ3EligibleActivities: "Eligible Activities",
  lstQ4SupportsVitalFunction: "Supports Vital Function?", lstQ5TimesPerWeek: "Times/Week",
  lstQ6HoursPerWeek: "Hours/Week", lstQ7YearBegan: "Year Began",
  lstQ8Prolonged12Months: "Prolonged 12+ Months?", lstQ9LikelyToImprove: "Likely to Improve?",
  certYearFrom: "Year From", certYearTo: "Year To", certHasMedicalInfoOnFile: "Medical Info on File?",
  certPractitionerType: "Practitioner Type", certSignature: "Signature",
  certNamePrinted: "Name (Printed)", certLicenseNumber: "License Number",
  certTelephone: "Telephone", certDate: "Date", certAddress: "Address",
};

function getLabel(key: string): string {
  return FIELD_LABELS[key] || key;
}

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return "";
  if (val === true) return "true";
  if (val === false) return "false";
  if (Array.isArray(val)) return val.join(", ");
  return String(val);
}

export function DtcFormEditor({ initialData, patientName, onDownload }: DtcFormEditorProps) {
  const [formData, setFormData] = useState<Record<string, unknown>>(initialData);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const updateField = (section: string, key: string, value: string) => {
    const sectionData = { ...(formData[section] as Record<string, unknown>) };
    // Convert string back to appropriate type
    if (BOOL_FIELDS.has(key)) {
      sectionData[key] = value === "true" ? true : value === "false" ? false : null;
    } else if (value === "") {
      sectionData[key] = null;
    } else if (!isNaN(Number(value)) && key.match(/Year|Times|Hours|From|To/)) {
      sectionData[key] = Number(value);
    } else {
      sectionData[key] = value;
    }
    setFormData({ ...formData, [section]: sectionData });
  };

  const toggleSection = (section: string) => {
    setExpanded({ ...expanded, [section]: !expanded[section] });
  };

  const inputStyle: React.CSSProperties = {
    width: "100%", background: "var(--code)", border: "1px solid var(--border)",
    borderRadius: "4px", padding: "0.375rem 0.5rem", color: "var(--text)",
    fontSize: "0.8125rem", fontFamily: "var(--fontSans)", outline: "none",
  };

  const labelStyle: React.CSSProperties = {
    fontSize: "0.6875rem", fontWeight: 600, color: "var(--textMuted)",
    textTransform: "uppercase" as const, letterSpacing: "0.03em", marginBottom: "0.125rem",
    display: "block",
  };

  const sectionHeaderStyle: React.CSSProperties = {
    fontSize: "0.8125rem", fontWeight: 600, color: "var(--primary)",
    padding: "0.5rem 0.75rem", cursor: "pointer", userSelect: "none",
    background: "#e6f0fa", borderBottom: "1px solid var(--border)",
    display: "flex", justifyContent: "space-between", alignItems: "center",
  };

  const sectionBodyStyle: React.CSSProperties = {
    padding: "0.75rem", display: "flex", flexDirection: "column", gap: "0.5rem",
  };

  // Render a single field
  const renderField = (section: string, key: string, val: unknown) => {
    const valueStr = formatValue(val);
    const isTextarea = TEXTAREA_FIELDS.has(key);
    const isBool = BOOL_FIELDS.has(key);
    const isTriState = TRISTATE_FIELDS.has(key);

    return (
      <div key={key}>
        <label style={labelStyle}>{getLabel(key)}</label>
        {isTriState ? (
          <select style={inputStyle} value={valueStr}
            onChange={(e) => updateField(section, key, e.target.value)}>
            <option value="">—</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
            <option value="unsure">Unsure</option>
          </select>
        ) : isBool ? (
          <select style={inputStyle} value={valueStr}
            onChange={(e) => updateField(section, key, e.target.value)}>
            <option value="">—</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        ) : isTextarea ? (
          <textarea style={{ ...inputStyle, minHeight: "60px", resize: "vertical" }}
            value={valueStr}
            onChange={(e) => updateField(section, key, e.target.value)} />
        ) : (
          <input style={inputStyle} type="text" value={valueStr}
            onChange={(e) => updateField(section, key, e.target.value)} />
        )}
      </div>
    );
  };

  // Render a section
  const renderSection = (sectionKey: string, sectionData: Record<string, unknown> | null) => {
    if (!sectionData || typeof sectionData !== "object") return null;
    const entries = Object.entries(sectionData);
    if (entries.length === 0) return null;

    const label = SECTION_LABELS[sectionKey] || sectionKey;
    const isExpanded = expanded[sectionKey] ?? true;
    const filledCount = entries.filter(([, v]) => v !== null && v !== undefined && v !== "").length;

    return (
      <div key={sectionKey} style={{
        border: "1px solid var(--border)", borderRadius: "8px", overflow: "hidden",
      }}>
        <div style={sectionHeaderStyle} onClick={() => toggleSection(sectionKey)}>
          <span>{label}</span>
          <span style={{ fontSize: "0.6875rem", color: "var(--textMuted)" }}>
            {filledCount}/{entries.length} filled {isExpanded ? "▾" : "▸"}
          </span>
        </div>
        {isExpanded && (
          <div style={sectionBodyStyle}>
            {entries.map(([key, val]) => {
              // If value is a nested object (not a primitive), render sub-section
              if (val && typeof val === "object" && !Array.isArray(val)) {
                return renderSection(`${sectionKey}.${key}`, val as Record<string, unknown>);
              }
              return renderField(sectionKey, key, val);
            })}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{
      marginTop: "0.75rem", paddingLeft: "0.75rem",
      display: "flex", flexDirection: "column", gap: "0.5rem",
    }}>
      <div style={{
        fontSize: "0.8125rem", fontWeight: 600, color: "var(--primary)",
        marginBottom: "0.25rem",
      }}>
        📋 T2201 Form — Editable Fields
      </div>

      {/* Part A */}
      {(formData.partA as Record<string, unknown>) && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {renderSection("personWithDisability", (formData.partA as Record<string, unknown>).personWithDisability as Record<string, unknown>)}
          {renderSection("supportingFamilyMember", (formData.partA as Record<string, unknown>).supportingFamilyMember as Record<string, unknown>)}
          {renderSection("adjustments", (formData.partA as Record<string, unknown>).adjustments as Record<string, unknown>)}
          {renderSection("authorization", (formData.partA as Record<string, unknown>).authorization as Record<string, unknown>)}
        </div>
      )}

      {/* Part B */}
      {(formData.partB as Record<string, unknown>) && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {(formData.partB as Record<string, unknown>).patientNameHeader !== undefined && (
            <div style={{ border: "1px solid var(--border)", borderRadius: "8px", overflow: "hidden" }}>
              <div style={sectionHeaderStyle} onClick={() => toggleSection("patientNameHeader")}>
                <span>Patient Name</span>
                <span style={{ fontSize: "0.6875rem", color: "var(--textMuted)" }}>
                  {expanded["patientNameHeader"] ?? true ? "▾" : "▸"}
                </span>
              </div>
              {(expanded["patientNameHeader"] ?? true) && (
                <div style={sectionBodyStyle}>
                  {renderField("partB", "patientNameHeader", (formData.partB as Record<string, unknown>).patientNameHeader)}
                </div>
              )}
            </div>
          )}
          {Object.entries(formData.partB as Record<string, unknown>)
            .filter(([key]) => key !== "patientNameHeader")
            .map(([catKey, catData]) => {
              if (catData && typeof catData === "object" && !Array.isArray(catData)) {
                return renderSection(catKey, catData as Record<string, unknown>);
              }
              return null;
            })}
        </div>
      )}

      {/* Certification */}
      {renderSection("certification", formData.certification as Record<string, unknown>)}

      {/* Download button */}
      <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem" }}>
        <button className="primary"
          onClick={() => onDownload(formData)}
          style={{ padding: "0.5rem 1rem", fontSize: "0.8125rem" }}>
          📋 Download T2201 PDF
        </button>
      </div>
    </div>
  );
}
