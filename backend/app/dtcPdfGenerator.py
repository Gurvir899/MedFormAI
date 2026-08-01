"""
DTC T2201 PDF Generator — renders a filled Disability Tax Credit form as PDF.

Takes structured form data (matching the T2201 JSON schema) and produces
a professional multi-page PDF that mirrors the CRA T2201 form layout.

PII Safety: formData has already been through the PII compliance pipeline
(encryption, redaction, audit). PDF is generated server-side with reportlab.
"""

import io
import logging
from typing import Dict, Optional, List
from datetime import date

logger = logging.getLogger(__name__)


def _getRl():
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak, KeepTogether
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    return locals()


# ─── Colors ───────────────────────────────────────────────────────────
CRA_BLUE = colors.HexColor("#1a3a5c") if False else None  # Set below
PRIMARY = "#0f4c5c"
MUTED = "#666666"
BORDER = "#e0e0e0"
LIGHT_BG = "#f4f4f4"


def generateDtcPdf(formData: Dict) -> bytes:
    """
    Generate a T2201 DTC form PDF from structured form data.

    Args:
        formData: Dict matching the T2201 JSON schema (partA, partB, certification)

    Returns: PDF as bytes
    """
    rl = _getRl()
    buf = io.BytesIO()

    doc = rl["SimpleDocTemplate"](
        buf,
        pagesize=rl["letter"],
        rightMargin=0.6 * rl["inch"],
        leftMargin=0.6 * rl["inch"],
        topMargin=0.6 * rl["inch"],
        bottomMargin=0.6 * rl["inch"],
    )

    styles = rl["getSampleStyleSheet"]()

    # ─── Custom styles ───────────────────────────────────────
    titleStyle = rl["ParagraphStyle"]("Title2", parent=styles["Title"],
        fontSize=16, fontName="Times-Bold", textColor=rl["colors"].HexColor(PRIMARY),
        spaceAfter=4, alignment=rl["TA_CENTER"])

    subtitleStyle = rl["ParagraphStyle"]("Subtitle2", parent=styles["Normal"],
        fontSize=9, fontName="Times-Roman", textColor=rl["colors"].HexColor(MUTED),
        alignment=rl["TA_CENTER"], spaceAfter=12)

    sectionStyle = rl["ParagraphStyle"]("Section", parent=styles["Heading2"],
        fontSize=11, fontName="Times-Bold", textColor=rl["colors"].HexColor(PRIMARY),
        spaceBefore=16, spaceAfter=8, borderWidth=0, borderPadding=0)

    labelStyle = rl["ParagraphStyle"]("Label2", parent=styles["Normal"],
        fontSize=8, fontName="Times-Bold", textColor=rl["colors"].HexColor(MUTED),
        spaceAfter=1)

    valueStyle = rl["ParagraphStyle"]("Value2", parent=styles["Normal"],
        fontSize=10, fontName="Times-Roman", textColor=rl["colors"].HexColor("#1a1a1a"),
        spaceAfter=6)

    narrativeStyle = rl["ParagraphStyle"]("Narrative", parent=styles["Normal"],
        fontSize=9.5, fontName="Times-Roman", textColor=rl["colors"].HexColor("#1a1a1a"),
        leading=13, spaceAfter=6, alignment=rl["TA_LEFT"])

    footerStyle = rl["ParagraphStyle"]("Footer2", parent=styles["Normal"],
        fontSize=7, fontName="Times-Italic", textColor=rl["colors"].HexColor("#999999"),
        alignment=rl["TA_CENTER"])

    story = []

    # ─── Helper functions ─────────────────────────────────────
    def val(key, data=None):
        """Get a value from form data, return '—' if null/empty."""
        if data is None:
            data = formData
        v = data.get(key) if isinstance(data, dict) else None
        if v is None or v == "" or v == "null":
            return "—"
        if isinstance(v, bool):
            return "Yes" if v else "No"
        return str(v)

    def fieldRow(label, key, data=None):
        """Create a label + value row."""
        return [
            rl["Paragraph"](label, labelStyle),
            rl["Paragraph"](val(key, data), valueStyle),
        ]

    def sectionDivider():
        story.append(rl["HRFlowable"](width="100%", thickness=0.5,
            color=rl["colors"].HexColor(BORDER), spaceBefore=8, spaceAfter=8))

    # ─── Header ──────────────────────────────────────────────
    story.append(rl["Paragraph"]("Disability Tax Credit Certificate", titleStyle))
    story.append(rl["Paragraph"](
        "Form T2201 E (23) · Protected B when completed · "
        "canada.ca/disability-tax-credit · 1-800-959-8281", subtitleStyle))
    story.append(rl["HRFlowable"](width="100%", thickness=1.5,
        color=rl["colors"].HexColor(PRIMARY), spaceBefore=0, spaceAfter=12))

    partA = formData.get("partA", {})
    partB = formData.get("partB", {})
    cert = formData.get("certification", {})

    # ─── Part A: Person with disability ─────────────────────
    story.append(rl["Paragraph"]("Part A — Individual's Section", sectionStyle))

    pwd = partA.get("personWithDisability", {})
    story.append(rl["Paragraph"]("Person with the Disability", labelStyle))
    pwdData = [
        fieldRow("First Name", "personFirstName", pwd),
        fieldRow("Last Name", "personLastName", pwd),
        fieldRow("SIN", "personSin", pwd),
        fieldRow("Date of Birth", "personDateOfBirth", pwd),
        fieldRow("Mailing Address", "personMailingAddress", pwd),
        fieldRow("City", "personCity", pwd),
        fieldRow("Province", "personProvince", pwd),
        fieldRow("Postal Code", "personPostalCode", pwd),
    ]
    pwdTable = rl["Table"](pwdData, colWidths=[1.5*rl["inch"], 5.5*rl["inch"]])
    pwdTable.setStyle(rl["TableStyle"]([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 1),
        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
    ]))
    story.append(pwdTable)

    # Supporting family member
    sfm = partA.get("supportingFamilyMember", {})
    if sfm.get("claimantFirstName"):
        sectionDivider()
        story.append(rl["Paragraph"]("Supporting Family Member Claiming the Amount", labelStyle))
        sfmData = [
            fieldRow("First Name", "claimantFirstName", sfm),
            fieldRow("Last Name", "claimantLastName", sfm),
            fieldRow("Relationship", "claimantRelationship", sfm),
            fieldRow("SIN", "claimantSin", sfm),
            fieldRow("Cohabitates", "claimantCohabitates", sfm),
            fieldRow("Provides Food", "claimantProvidesFood", sfm),
            fieldRow("Provides Shelter", "claimantProvidesShelter", sfm),
            fieldRow("Provides Clothing", "claimantProvidesClothing", sfm),
            fieldRow("Support Details", "claimantSupportDetails", sfm),
        ]
        sfmTable = rl["Table"](sfmData, colWidths=[1.5*rl["inch"], 5.5*rl["inch"]])
        sfmTable.setStyle(rl["TableStyle"]([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 1),
            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
        ]))
        story.append(sfmTable)

    # Adjustments
    adj = partA.get("adjustments", {})
    sectionDivider()
    story.append(rl["Paragraph"]("Previous Tax Return Adjustments", labelStyle))
    adjData = [
        fieldRow("Self or Legal Rep", "isSelfOrLegalRep", adj),
        fieldRow("Adjust Previous Returns", "adjustPreviousReturns", adj),
    ]
    adjTable = rl["Table"](adjData, colWidths=[2*rl["inch"], 5*rl["inch"]])
    adjTable.setStyle(rl["TableStyle"]([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 1),
        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
    ]))
    story.append(adjTable)

    # Authorization
    auth = partA.get("authorization", {})
    sectionDivider()
    story.append(rl["Paragraph"]("Individual's Authorization", labelStyle))
    authData = [
        fieldRow("Signature", "partAQ4Signature", auth),
        fieldRow("Telephone", "partAQ4Telephone", auth),
        fieldRow("Date", "partAQ4Date", auth),
    ]
    authTable = rl["Table"](authData, colWidths=[1.5*rl["inch"], 5.5*rl["inch"]])
    authTable.setStyle(rl["TableStyle"]([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 1),
        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
    ]))
    story.append(authTable)

    # ─── Part B: Impairment Categories ───────────────────────
    story.append(rl["PageBreak"]())
    story.append(rl["Paragraph"]("Part B — Disability Details", sectionStyle))

    patientName = val("patientNameHeader", partB) or f"{val('personFirstName', pwd)} {val('personLastName', pwd)}"
    story.append(rl["Paragraph"](f"Patient: {patientName}", labelStyle))

    # Standard category renderer
    standardCategories = [
        ("speaking", "Speaking"),
        ("hearing", "Hearing"),
        ("walking", "Walking"),
        ("eliminating", "Eliminating"),
        ("feeding", "Feeding"),
        ("dressing", "Dressing"),
    ]

    for catKey, catLabel in standardCategories:
        catData = partB.get(catKey)
        if catData and isinstance(catData, dict) and any(v is not None for v in catData.values()):
            _renderStandardCategory(rl, story, catLabel, catData, labelStyle, narrativeStyle, sectionStyle)

    # Vision
    vision = partB.get("vision")
    if vision and isinstance(vision, dict) and any(v is not None for v in vision.values()):
        _renderVision(rl, story, vision, labelStyle, narrativeStyle, sectionStyle)

    # Mental functions
    mental = partB.get("mentalFunctions")
    if mental and isinstance(mental, dict) and any(v is not None for v in mental.values()):
        _renderMental(rl, story, mental, labelStyle, narrativeStyle, sectionStyle)

    # Cumulative effect
    cumulative = partB.get("cumulativeEffect")
    if cumulative and isinstance(cumulative, dict) and any(v is not None for v in cumulative.values()):
        _renderCumulative(rl, story, cumulative, labelStyle, narrativeStyle, sectionStyle)

    # Life-sustaining therapy
    lst = partB.get("lifeSustainingTherapy")
    if lst and isinstance(lst, dict) and any(v is not None for v in lst.values()):
        _renderLst(rl, story, lst, labelStyle, narrativeStyle, sectionStyle)

    # ─── Certification ───────────────────────────────────────
    story.append(rl["PageBreak"]())
    story.append(rl["Paragraph"]("Certification", sectionStyle))

    certData = [
        fieldRow("Year From", "certYearFrom", cert),
        fieldRow("Year To", "certYearTo", cert),
        fieldRow("Medical Info on File", "certHasMedicalInfoOnFile", cert),
        fieldRow("Practitioner Type", "certPractitionerType", cert),
        fieldRow("Signature", "certSignature", cert),
        fieldRow("Name (Printed)", "certNamePrinted", cert),
        fieldRow("License Number", "certLicenseNumber", cert),
        fieldRow("Telephone", "certTelephone", cert),
        fieldRow("Date", "certDate", cert),
        fieldRow("Address", "certAddress", cert),
    ]
    certTable = rl["Table"](certData, colWidths=[1.5*rl["inch"], 5.5*rl["inch"]])
    certTable.setStyle(rl["TableStyle"]([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 1),
        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
    ]))
    story.append(certTable)

    # ─── Footer ──────────────────────────────────────────────
    story.append(rl["Spacer"](1, 24))
    story.append(rl["HRFlowable"](width="100%", thickness=0.5,
        color=rl["colors"].HexColor(BORDER), spaceBefore=4, spaceAfter=4))
    story.append(rl["Paragraph"](
        "Generated by Paean — PII-compliant medical form automation. "
        "Patient data encrypted at rest, redacted before AI processing. "
        "PHIPA/PIPEDA compliant. Form T2201 E (23).", footerStyle))

    doc.build(story)
    pdfBytes = buf.getvalue()
    buf.close()
    logger.info(f"Generated DTC T2201 PDF: {len(pdfBytes)} bytes")
    return pdfBytes


def _renderStandardCategory(rl, story, label, data, labelStyle, narrativeStyle, sectionStyle):
    """Render a standard impairment category (speaking, walking, etc.)."""
    story.append(rl["Paragraph"](label, sectionStyle))

    def v(key):
        val = data.get(key)
        if val is None or val == "":
            return "—"
        if isinstance(val, bool):
            return "Yes" if val else "No"
        return str(val)

    fields = [
        ("Designation", v("designation")),
        ("Initials", v("initials")),
        ("Medical Conditions/Diagnoses", v("q1Diagnoses")),
        ("Medication for Impairment", v("q2Medication")),
        ("Devices/Therapy", v("q3DevicesTherapy")),
        ("Examples of Impairment", v("q4Examples")),
        ("Marked Restriction", v("q5MarkedRestriction")),
        ("All or Substantially All the Time", v("q6AllOrSubstantiallyAll")),
        ("Year Impaired", v("q7YearImpaired")),
        ("Prolonged 12+ Months", v("q8Prolonged12Months")),
        ("Likely to Improve", v("q9LikelyToImprove")),
        ("Improvement Year", v("q9ImprovementYear")),
    ]

    for labelTxt, valTxt in fields:
        story.append(rl["Paragraph"](labelTxt, labelStyle))
        story.append(rl["Paragraph"](valTxt, narrativeStyle))


def _renderVision(rl, story, data, labelStyle, narrativeStyle, sectionStyle):
    """Render the Vision category."""
    story.append(rl["Paragraph"]("Vision", sectionStyle))

    def v(key):
        val = data.get(key)
        if val is None or val == "": return "—"
        if isinstance(val, bool): return "Yes" if val else "No"
        return str(val)

    fields = [
        ("Designation", v("visionDesignation")),
        ("Diagnoses", v("visionQ1Diagnoses")),
        ("Aspect Impaired", v("visionQ2AspectImpaired")),
        ("Left Eye Acuity Type", v("visionLeftAcuityType")),
        ("Left Eye Snellen", v("visionLeftAcuitySnellen")),
        ("Left Eye Field (degrees)", v("visionLeftFieldDegrees")),
        ("Right Eye Acuity Type", v("visionRightAcuityType")),
        ("Right Eye Snellen", v("visionRightAcuitySnellen")),
        ("Right Eye Field (degrees)", v("visionRightFieldDegrees")),
        ("Meets Criteria (both eyes)", v("visionQ3MeetsCriteria")),
        ("Year Impaired", v("visionQ4YearImpaired")),
        ("Prolonged 12+ Months", v("visionQ5Prolonged12Months")),
        ("Likely to Improve", v("visionQ6LikelyToImprove")),
        ("Improvement Year", v("visionQ6ImprovementYear")),
    ]
    for labelTxt, valTxt in fields:
        story.append(rl["Paragraph"](labelTxt, labelStyle))
        story.append(rl["Paragraph"](valTxt, narrativeStyle))


def _renderMental(rl, story, data, labelStyle, narrativeStyle, sectionStyle):
    """Render Mental functions category."""
    story.append(rl["Paragraph"]("Mental Functions Necessary for Everyday Life", sectionStyle))

    def v(key):
        val = data.get(key)
        if val is None or val == "": return "—"
        if isinstance(val, bool): return "Yes" if val else "No"
        return str(val)

    fields = [
        ("Designation", v("mentalDesignation")),
        ("Diagnoses", v("mentalQ1Diagnoses")),
        ("Medication", v("mentalQ2Medication")),
        ("Supervision for Medication", v("mentalQ2SupervisionForMedication")),
        ("Medication Effectiveness", v("mentalQ2MedicationEffectiveness")),
        ("Devices/Therapy", v("mentalQ3DevicesTherapy")),
        ("Impaired Independence", v("mentalQ4ImpairedIndependence")),
        ("Support Types (Adult)", v("mentalQ4SupportTypesAdult")),
        ("Support Types (Child)", v("mentalQ4SupportTypesChild")),
        ("Support Details", v("mentalQ4SupportDetails")),
        ("Examples", v("mentalQ6Examples")),
        ("Marked Restriction", v("mentalQ7MarkedRestriction")),
        ("All or Substantially All", v("mentalQ8AllOrSubstantiallyAll")),
        ("Year Impaired", v("mentalQ9YearImpaired")),
        ("Prolonged 12+ Months", v("mentalQ10Prolonged12Months")),
        ("Likely to Improve", v("mentalQ11LikelyToImprove")),
        ("Improvement Year", v("mentalQ11ImprovementYear")),
    ]
    for labelTxt, valTxt in fields:
        story.append(rl["Paragraph"](labelTxt, labelStyle))
        story.append(rl["Paragraph"](valTxt, narrativeStyle))

    # Mental grid (limitation assessment)
    gridFields = [
        ("Adapt to Change", "mentalGridAdaptChange"),
        ("Express Basic Needs", "mentalGridExpressBasicNeeds"),
        ("Go Into Community", "mentalGridGoIntoCommunity"),
        ("Initiate Transactions", "mentalGridInitiateTransactions"),
        ("Basic Hygiene", "mentalGridBasicHygiene"),
        ("Everyday Tasks", "mentalGridEverydayTasks"),
        ("Awareness of Danger", "mentalGridAwarenessOfDanger"),
        ("Impulse Control", "mentalGridImpulseControl"),
        ("Focus on Simple Task", "mentalGridFocusSimpleTask"),
        ("Short-term Information", "mentalGridShortTermInformation"),
        ("Carry Out Plans", "mentalGridCarryOutPlans"),
        ("Self-direct Tasks", "mentalGridSelfDirectTasks"),
        ("Weather-appropriate Clothing", "mentalGridWeatherClothing"),
        ("Treatment Decisions", "mentalGridTreatmentDecisions"),
        ("Recognize Exploitation", "mentalGridRecognizeExploitation"),
        ("Understand Consequences", "mentalGridUnderstandConsequences"),
        ("Remember Personal Info", "mentalGridRememberPersonalInfo"),
        ("Remember Material of Interest", "mentalGridRememberMaterialOfInterest"),
        ("Remember Instructions", "mentalGridRememberInstructions"),
        ("Understanding of Reality", "mentalGridUnderstandingOfReality"),
        ("Distinguish Delusions", "mentalGridDistinguishDelusions"),
        ("Identify Problems", "mentalGridIdentifyProblems"),
        ("Implement Solutions", "mentalGridImplementSolutions"),
        ("Behave Appropriately", "mentalGridBehaveAppropriately"),
        ("Emotional Responses", "mentalGridEmotionalResponses"),
        ("Regulate Mood", "mentalGridRegulateMood"),
        ("Non-verbal Cues", "mentalGridNonVerbalCues"),
        ("Verbal Information", "mentalGridVerbalInformation"),
    ]

    story.append(rl["Paragraph"]("Limitation Assessment Grid", labelStyle))
    gridData = [[rl["Paragraph"]("Function", labelStyle), rl["Paragraph"]("Assessment", labelStyle)]]
    for funcLabel, funcKey in gridFields:
        v = data.get(funcKey)
        displayVal = "—"
        if v: displayVal = str(v).replace("noLimitations", "No Limitations").replace("someLimitations", "Some Limitations").replace("severeLimitations", "Severe Limitations")
        gridData.append([rl["Paragraph"](funcLabel, narrativeStyle), rl["Paragraph"](displayVal, narrativeStyle)])

    gridTable = rl["Table"](gridData, colWidths=[3.5*rl["inch"], 3*rl["inch"]])
    gridTable.setStyle(rl["TableStyle"]([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.25, rl["colors"].HexColor("#e0e0e0")),
        ("BACKGROUND", (0,0), (-1,0), rl["colors"].HexColor("#f4f4f4")),
    ]))
    story.append(gridTable)


def _renderCumulative(rl, story, data, labelStyle, narrativeStyle, sectionStyle):
    """Render Cumulative effect category."""
    story.append(rl["Paragraph"]("Cumulative Effect of Significant Limitations", sectionStyle))

    def v(key):
        val = data.get(key)
        if val is None or val == "": return "—"
        if isinstance(val, bool): return "Yes" if val else "No"
        return str(val)

    fields = [
        ("Designation", v("cumulativeDesignation")),
        ("Categories", v("cumulativeQ1Categories")),
        ("Examples", v("cumulativeQ2Examples")),
        ("Exist Together", v("cumulativeQ3ExistTogether")),
        ("Equivalent to Marked", v("cumulativeQ4EquivalentToMarked")),
        ("Year Began", v("cumulativeQ5YearBegan")),
        ("Prolonged 12+ Months", v("cumulativeQ6Prolonged12Months")),
        ("Likely to Improve", v("cumulativeQ7LikelyToImprove")),
        ("Improvement Year", v("cumulativeQ7ImprovementYear")),
    ]
    for labelTxt, valTxt in fields:
        story.append(rl["Paragraph"](labelTxt, labelStyle))
        story.append(rl["Paragraph"](valTxt, narrativeStyle))


def _renderLst(rl, story, data, labelStyle, narrativeStyle, sectionStyle):
    """Render Life-sustaining therapy category."""
    story.append(rl["Paragraph"]("Life-Sustaining Therapy", sectionStyle))

    def v(key):
        val = data.get(key)
        if val is None or val == "": return "—"
        if isinstance(val, bool): return "Yes" if val else "No"
        return str(val)

    fields = [
        ("Designation", v("lstDesignation")),
        ("T1 Diabetes Diagnosis Timing", v("lstQ1DiabetesDiagnosisTiming")),
        ("T1 Diabetes Diagnosis Year", v("lstQ1DiabetesDiagnosisYear")),
        ("Therapy Types", v("lstQ2TherapyTypes")),
        ("Other Therapy", v("lstQ2TherapyOther")),
        ("Medical Conditions", v("lstQ2MedicalConditions")),
        ("Other Condition", v("lstQ2ConditionOther")),
        ("Eligible Activities", v("lstQ3EligibleActivities")),
        ("Supports Vital Function", v("lstQ4SupportsVitalFunction")),
        ("Times Per Week", v("lstQ5TimesPerWeek")),
        ("Hours Per Week", v("lstQ6HoursPerWeek")),
        ("Year Began", v("lstQ7YearBegan")),
        ("Prolonged 12+ Months", v("lstQ8Prolonged12Months")),
        ("Likely to Improve", v("lstQ9LikelyToImprove")),
        ("Improvement Year", v("lstQ9ImprovementYear")),
    ]
    for labelTxt, valTxt in fields:
        story.append(rl["Paragraph"](labelTxt, labelStyle))
        story.append(rl["Paragraph"](valTxt, narrativeStyle))
