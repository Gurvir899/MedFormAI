"""
Sick Note PDF Generator — PII-compliant PDF generation using reportlab.

Generates a professional medical sick leave certificate as a PDF.
PII Safety: formData is already PII-scanned by the time it reaches here.
The PDF is generated server-side — no patient data is sent to any external service.
"""

import io
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Lazy import — only when PDF is actually generated
def _getReportlab():
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    return locals()


def generateSickNotePdf(formData: Dict, physicianInfo: Optional[Dict] = None) -> bytes:
    """
    Generate a sick note PDF from form data.

    Args:
        formData: Dict with sick note fields (patientName, dateOfBirth,
                  reasonForAbsence, startDate, expectedReturnDate,
                  fitnessForDuty, physicianName, physicianLicense,
                  clinicName, clinicAddress, dateOfIssue, etc.)
        physicianInfo: Optional dict with physician/clinic info to override

    Returns: PDF as bytes
    """
    rl = _getReportlab()
    buf = io.BytesIO()

    doc = rl["SimpleDocTemplate"](
        buf,
        pagesize=rl["letter"],
        rightMargin=0.75 * rl["inch"],
        leftMargin=0.75 * rl["inch"],
        topMargin=0.75 * rl["inch"],
        bottomMargin=0.75 * rl["inch"],
    )

    styles = rl["getSampleStyleSheet"]()

    # Custom styles matching the app's Cormorant aesthetic
    titleStyle = rl["ParagraphStyle"](
        "SickNoteTitle",
        parent=styles["Title"],
        fontSize=22,
        fontName="Times-Roman",
        textColor=rl["colors"].HexColor("#0f4c5c"),
        spaceAfter=4,
        alignment=rl["TA_CENTER"],
    )
    subtitleStyle = rl["ParagraphStyle"](
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Times-Italic",
        textColor=rl["colors"].HexColor("#666666"),
        alignment=rl["TA_CENTER"],
        spaceAfter=16,
    )
    sectionHeaderStyle = rl["ParagraphStyle"](
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=12,
        fontName="Times-Bold",
        textColor=rl["colors"].HexColor("#0f4c5c"),
        spaceBefore=12,
        spaceAfter=6,
    )
    bodyStyle = rl["ParagraphStyle"](
        "BodyText",
        parent=styles["Normal"],
        fontSize=10.5,
        fontName="Times-Roman",
        leading=15,
        textColor=rl["colors"].HexColor("#1a1a1a"),
        spaceAfter=4,
    )
    labelStyle = rl["ParagraphStyle"](
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Times-Bold",
        textColor=rl["colors"].HexColor("#666666"),
        spaceAfter=2,
    )
    valueStyle = rl["ParagraphStyle"](
        "Value",
        parent=styles["Normal"],
        fontSize=10.5,
        fontName="Times-Roman",
        textColor=rl["colors"].HexColor("#1a1a1a"),
        spaceAfter=8,
    )
    signatureStyle = rl["ParagraphStyle"](
        "Signature",
        parent=styles["Normal"],
        fontSize=10.5,
        fontName="Times-Roman",
        textColor=rl["colors"].HexColor("#1a1a1a"),
        spaceBefore=30,
    )
    footerStyle = rl["ParagraphStyle"](
        "Footer",
        parent=styles["Normal"],
        fontSize=7.5,
        fontName="Times-Italic",
        textColor=rl["colors"].HexColor("#999999"),
        alignment=rl["TA_CENTER"],
    )

    # Merge physician info if provided
    if physicianInfo:
        for key, val in physicianInfo.items():
            if val and not formData.get(key):
                formData[key] = val

    story = []

    # ─── Header ──────────────────────────────────────────────
    clinicName = formData.get("clinicName", "")
    if clinicName:
        story.append(rl["Paragraph"](clinicName, titleStyle))

    story.append(rl["Paragraph"]("Medical Sick Leave Certificate", subtitleStyle))
    story.append(rl["HRFlowable"](
        width="100%", thickness=1.5,
        color=rl["colors"].HexColor("#0f4c5c"),
        spaceBefore=4, spaceAfter=12,
    ))

    # ─── Patient Information ─────────────────────────────────
    story.append(rl["Paragraph"]("Patient Information", sectionHeaderStyle))

    patientData = [
        [rl["Paragraph"]("Name:", labelStyle),
         rl["Paragraph"](formData.get("patientName", "—"), valueStyle)],
        [rl["Paragraph"]("Date of Birth:", labelStyle),
         rl["Paragraph"](formData.get("dateOfBirth", "—"), valueStyle)],
        [rl["Paragraph"]("Date of Assessment:", labelStyle),
         rl["Paragraph"](formData.get("assessmentDate", datetime.now().strftime("%Y-%m-%d")), valueStyle)],
    ]

    patientTable = rl["Table"](patientData, colWidths=[1.5 * rl["inch"], 5.0 * rl["inch"]])
    patientTable.setStyle(rl["TableStyle"]([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(patientTable)

    # ─── Medical Assessment ───────────────────────────────────
    story.append(rl["Paragraph"]("Medical Assessment", sectionHeaderStyle))

    reasonText = formData.get("reasonForAbsence", "—")
    story.append(rl["Paragraph"]("Reason for Absence:", labelStyle))
    story.append(rl["Paragraph"](reasonText, bodyStyle))

    startDate = formData.get("startDate", "—")
    returnDate = formData.get("expectedReturnDate", "—")

    dateData = [
        [rl["Paragraph"]("Absence Start Date:", labelStyle),
         rl["Paragraph"](startDate, valueStyle),
         rl["Paragraph"]("Expected Return Date:", labelStyle),
         rl["Paragraph"](returnDate, valueStyle)],
    ]
    dateTable = rl["Table"](dateData, colWidths=[1.3 * rl["inch"], 1.7 * rl["inch"], 1.5 * rl["inch"], 2.0 * rl["inch"]])
    dateTable.setStyle(rl["TableStyle"]([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(dateTable)

    # Fitness for duty statement
    fitnessText = formData.get("fitnessForDuty", "")
    if fitnessText:
        story.append(rl["Spacer"](1, 8))
        story.append(rl["Paragraph"]("Fitness for Duty Statement:", labelStyle))
        story.append(rl["Paragraph"](fitnessText, bodyStyle))

    # ─── Physician Information ────────────────────────────────
    story.append(rl["Paragraph"]("Physician Information", sectionHeaderStyle))

    physicianName = formData.get("physicianName", "—")
    physicianLicense = formData.get("physicianLicense", "—")
    clinicAddress = formData.get("clinicAddress", "—")
    dateOfIssue = formData.get("dateOfIssue", datetime.now().strftime("%Y-%m-%d"))

    physicianData = [
        [rl["Paragraph"]("Physician:", labelStyle),
         rl["Paragraph"](physicianName, valueStyle)],
        [rl["Paragraph"]("License No.:", labelStyle),
         rl["Paragraph"](physicianLicense, valueStyle)],
        [rl["Paragraph"]("Clinic Address:", labelStyle),
         rl["Paragraph"](clinicAddress, valueStyle)],
        [rl["Paragraph"]("Date of Issue:", labelStyle),
         rl["Paragraph"](dateOfIssue, valueStyle)],
    ]
    physicianTable = rl["Table"](physicianData, colWidths=[1.5 * rl["inch"], 5.0 * rl["inch"]])
    physicianTable.setStyle(rl["TableStyle"]([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(physicianTable)

    # ─── Signature Line ───────────────────────────────────────
    story.append(rl["Spacer"](1, 40))
    story.append(rl["HRFlowable"](
        width=2.5 * rl["inch"], thickness=1,
        color=rl["colors"].HexColor("#1a1a1a"),
        spaceBefore=0, spaceAfter=4,
        hAlign="LEFT",
    ))
    story.append(rl["Paragraph"](
        f"{physicianName}, {physicianLicense}",
        signatureStyle,
    ))
    story.append(rl["Paragraph"](
        f"{clinicName}" if clinicName else "",
        rl["ParagraphStyle"]("ClinicLine", parent=bodyStyle, fontSize=9, textColor=rl["colors"].HexColor("#666666")),
    ))

    # ─── Footer ───────────────────────────────────────────────
    story.append(rl["Spacer"](1, 24))
    story.append(rl["HRFlowable"](
        width="100%", thickness=0.5,
        color=rl["colors"].HexColor("#e0e0e0"),
        spaceBefore=4, spaceAfter=4,
    ))
    story.append(rl["Paragraph"](
        "This certificate was generated by Paean — PII-compliant medical form automation. "
        "Patient data is encrypted at rest and redacted before any AI processing. "
        "PHIPA/PIPEDA compliant.",
        footerStyle,
    ))

    doc.build(story)
    pdfBytes = buf.getvalue()
    buf.close()

    logger.info(f"Generated sick note PDF: {len(pdfBytes)} bytes")
    return pdfBytes


def generateLetterPdf(
    content: str,
    physicianInfo: Optional[Dict] = None,
    patientName: str = "",
) -> bytes:
    """
    Generate a letter-style PDF from raw narrative text.

    Takes the LLM's full response (already PII-restored) and renders it
    as a professional medical letter on clinic letterhead.

    PII Safety: The content has already gone through the full redaction
    pipeline (redacted → LLM → restored). The PDF is generated server-side
    with reportlab — no external service sees the content.

    Args:
        content: Full narrative text from the LLM (markdown stripped to plain text)
        physicianInfo: Dict with physicianName, physicianLicense, clinicName, clinicAddress
        patientName: Patient name for the filename

    Returns: PDF as bytes
    """
    import re as reMod
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=0.85 * inch,
        leftMargin=0.85 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    # ─── Styles ───────────────────────────────────────────────
    clinicNameStyle = ParagraphStyle(
        "ClinicName",
        fontSize=16,
        fontName="Times-Bold",
        textColor=colors.HexColor("#0f4c5c"),
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    clinicAddrStyle = ParagraphStyle(
        "ClinicAddr",
        fontSize=9,
        fontName="Times-Roman",
        textColor=colors.HexColor("#666666"),
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    dateStyle = ParagraphStyle(
        "Date",
        fontSize=10.5,
        fontName="Times-Roman",
        textColor=colors.HexColor("#1a1a1a"),
        alignment=TA_LEFT,
        spaceBefore=24,
        spaceAfter=16,
    )
    bodyStyle = ParagraphStyle(
        "Body",
        fontSize=10.5,
        fontName="Times-Roman",
        leading=15,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=10,
        alignment=TA_LEFT,
    )
    footerStyle = ParagraphStyle(
        "Footer",
        fontSize=7.5,
        fontName="Times-Italic",
        textColor=colors.HexColor("#999999"),
        alignment=TA_CENTER,
    )
    sigLineStyle = ParagraphStyle(
        "SigLine",
        fontSize=10.5,
        fontName="Times-Roman",
        textColor=colors.HexColor("#1a1a1a"),
        spaceBefore=30,
        spaceAfter=2,
    )
    sigNameStyle = ParagraphStyle(
        "SigName",
        fontSize=10.5,
        fontName="Times-Bold",
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=1,
    )
    sigDetailStyle = ParagraphStyle(
        "SigDetail",
        fontSize=9,
        fontName="Times-Roman",
        textColor=colors.HexColor("#666666"),
        spaceAfter=1,
    )

    physicianInfo = physicianInfo or {}
    story = []

    # ─── Letterhead ──────────────────────────────────────────
    clinicName = physicianInfo.get("clinicName", "")
    clinicAddr = physicianInfo.get("clinicAddress", "")
    clinicPhone = physicianInfo.get("clinicPhone", "")

    if clinicName:
        story.append(Paragraph(clinicName, clinicNameStyle))
    if clinicAddr:
        story.append(Paragraph(clinicAddr, clinicAddrStyle))
    if clinicPhone:
        story.append(Paragraph(f"Tel: {clinicPhone}", clinicAddrStyle))

    story.append(HRFlowable(
        width="100%", thickness=1.5,
        color=colors.HexColor("#0f4c5c"),
        spaceBefore=6, spaceAfter=0,
    ))
    story.append(Spacer(1, 4))

    # ─── Date ─────────────────────────────────────────────────
    from datetime import date as dateMod
    todayLong = dateMod.today().strftime("%B %d, %Y")
    story.append(Paragraph(todayLong, dateStyle))

    # ─── Body: strip markdown, render as letter ──────────────
    # Convert markdown to reportlab-compatible HTML
    cleanContent = content

    # Remove horizontal rules (---) at start
    cleanContent = reMod.sub(r'^---\s*\n*', '', cleanContent)
    cleanContent = reMod.sub(r'\n---\s*', '\n', cleanContent)

    # Convert markdown bold **text** to <b>text</b>
    cleanContent = reMod.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', cleanContent)

    # Convert markdown italic *text* to <i>text</i> (but not inside bold)
    cleanContent = reMod.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', cleanContent)

    # Remove markdown headers (#, ##, ###) — just use the text
    cleanContent = reMod.sub(r'^#{1,3}\s+', '', cleanContent, flags=reMod.MULTILINE)

    # Remove blockquote markers
    cleanContent = reMod.sub(r'^>\s*', '', cleanContent, flags=reMod.MULTILINE)

    # Split into paragraphs and add to story
    paragraphs = cleanContent.strip().split("\n\n")
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Replace single newlines within paragraph with <br/>
        para = para.replace("\n", "<br/>")
        try:
            story.append(Paragraph(para, bodyStyle))
        except Exception:
            # If reportlab can't parse the HTML, strip all tags and use plain text
            plain = reMod.sub(r'<[^>]+>', '', para)
            story.append(Paragraph(plain, bodyStyle))

    # ─── Signature block ─────────────────────────────────────
    physName = physicianInfo.get("physicianName", "")
    physLicense = physicianInfo.get("physicianLicense", "")

    story.append(Spacer(1, 30))
    story.append(HRFlowable(
        width=2.5 * inch, thickness=1,
        color=colors.HexColor("#1a1a1a"),
        spaceBefore=0, spaceAfter=4,
        hAlign="LEFT",
    ))
    if physName:
        story.append(Paragraph(physName, sigNameStyle))
    if physLicense:
        story.append(Paragraph(physLicense, sigDetailStyle))
    if clinicName:
        story.append(Paragraph(clinicName, sigDetailStyle))

    # ─── Footer ──────────────────────────────────────────────
    story.append(Spacer(1, 24))
    story.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#e0e0e0"),
        spaceBefore=4, spaceAfter=4,
    ))
    story.append(Paragraph(
        "This certificate was generated by Paean — PII-compliant medical form automation. "
        "Patient data encrypted at rest, redacted before AI processing. "
        "PHIPA/PIPEDA compliant.",
        footerStyle,
    ))

    doc.build(story)
    pdfBytes = buf.getvalue()
    buf.close()

    logger.info(f"Generated letter PDF: {len(pdfBytes)} bytes")
    return pdfBytes
