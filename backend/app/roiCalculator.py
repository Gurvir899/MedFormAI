"""
ROI Calculator — uses real data from the CMA/CFIB 2026 report.

"Losing doctors to desk work: Canadian physicians lose 20 million hours
each year to red tape" (January 2026)

Source data:
  - 42.7M total admin hours/year nationally
  - 19.8M hours unnecessary (47%)
  - 9,093 FTE physicians recoverable
  - DTC: 36.6 min avg, 32.2 completions/yr, 45.3% compensated
  - Private insurance: 28.9 min avg, 54 completions/yr, 52.3% compensated
  - CPP disability: 43.3 min avg, 14.1 completions/yr, 54.9% compensated
  - Sick notes: 10.4 min avg, 136 completions/yr, 25% compensated
  - 99,555 physicians in Canada (CIHI)
  - Avg physician works 49.4 hrs/week, 44 weeks/year
  - AI scribe users save 64 min/day
"""

from dataclasses import dataclass
from typing import Dict


# ─── Real CMA/CFIB report data ─────────────────────────────────────────

nationalData = {
    "totalPhysicians": 99555,
    "totalAdminHoursPerYear": 42_700_000,
    "unnecessaryAdminHoursPerYear": 19_800_000,
    "unnecessaryPercentage": 47,
    "recoverableFte": 9093,
    "avgWeeklyAdminHours": 9.1,
    "avgWeeklyWorkHours": 49.4,
    "avgWeeksWorkedPerYear": 44,
    "aiScribeMinutesSavedPerDay": 64,
    "aiScribeAdoptionRate": 0.28,
    "aiScribeInterestRate": 0.42,
    "physiciansCuttingHoursPercent": 54,
    "physiciansLeavingPercent": 25,
    "unnecessaryHoursDelegable": 12_000_000,
    "unnecessaryHoursEliminable": 7_800_000,
    "fteFromDelegation": 5518,
    "fteFromElimination": 3575,
}

formBurdenData = {
    "dtc": {
        "name": "Disability Tax Credit (T2201)",
        "avgMinutesPerCompletion": 36.6,
        "avgCompletionsPerYear": 32.2,
        "percentCompensated": 45.3,
        "percentMajorBurden": 53,
        "percentModerateBurden": 32,
    },
    "privateInsurance": {
        "name": "Private Insurance Forms",
        "avgMinutesPerCompletion": 28.9,
        "avgCompletionsPerYear": 54,
        "percentCompensated": 52.3,
        "percentMajorBurden": 49,
        "percentModerateBurden": 35,
    },
    "cppDisability": {
        "name": "CPP Disability Benefits",
        "avgMinutesPerCompletion": 43.3,
        "avgCompletionsPerYear": 14.1,
        "percentCompensated": 54.9,
        "percentMajorBurden": 35,
        "percentModerateBurden": 34,
    },
    "sickNotes": {
        "name": "Sick Notes",
        "avgMinutesPerCompletion": 10.4,
        "avgCompletionsPerYear": 136,
        "percentCompensated": 25,
        "percentMajorBurden": 19,
        "percentModerateBurden": 36,
    },
}

provinceData = {
    "ontario": {"fteGain": 3602, "totalPhysicians": 30000},
    "quebec": {"fteGain": 1707, "totalPhysicians": 23000},
    "britishColumbia": {"fteGain": 1426, "totalPhysicians": 13000},
    "alberta": {"fteGain": 1206, "totalPhysicians": 11750},
    "manitoba": {"fteGain": 326, "totalPhysicians": 3500},
    "novaScotia": {"fteGain": 204, "totalPhysicians": 2500},
    "territories": {"fteGain": 14, "totalPhysicians": 200},
}


@dataclass
class RoiResult:
    physicianCount: int
    province: str
    formsAutomated: list
    hoursSavedPerYear: float
    fteRecovered: float
    costSavingsPerYear: float
    aiScribeBonusHours: float
    timeSavedPerPhysicianHours: float
    patientVisitsRecovered: float
    summary: dict


# Average cost of physician hour — blended GP/specialist estimate
avgPhysicianHourlyCost = 150  # CAD, conservative blended rate
avgPatientVisitMinutes = 15  # minutes per standard visit


def calculateRoi(
    physicianCount: int = 10,
    province: str = "ontario",
    formsAutomated: list = None,
    useAiScribe: bool = True,
) -> Dict:
    """
    Calculate ROI for a clinic or region.

    Args:
        physicianCount: Number of physicians in clinic/region
        province: Province name (lowercase)
        formsAutomated: List of form types being automated
        useAiScribe: Whether to include AI scribe time savings

    Returns: RoiResult as dict
    """
    if formsAutomated is None:
        formsAutomated = ["dtc"]

    # ─── Form automation savings ───────────────────────────
    formHoursSaved = 0.0
    formBreakdown = {}

    for formType in formsAutomated:
        if formType not in formBurdenData:
            continue

        data = formBurdenData[formType]
        annualMinutesPerPhysician = data["avgMinutesPerCompletion"] * data["avgCompletionsPerYear"]
        annualHoursPerPhysician = annualMinutesPerPhysician / 60
        totalHours = annualHoursPerPhysician * physicianCount

        # Paean automation saves ~80% of form completion time
        automationRate = 0.80
        automatedHours = totalHours * automationRate

        formHoursSaved += automatedHours
        formBreakdown[formType] = {
            "formName": data["name"],
            "hoursPerPhysicianPerYear": round(annualHoursPerPhysician, 1),
            "totalHoursSaved": round(automatedHours, 1),
            "automationRate": automationRate,
        }

    # ─── AI scribe bonus ────────────────────────────────────
    aiScribeHours = 0.0
    if useAiScribe:
        dailyMinutesSaved = nationalData["aiScribeMinutesSavedPerDay"]
        weeklyMinutes = dailyMinutesSaved * 5  # 5 working days
        weeklyHours = weeklyMinutes / 60
        annualHoursPerPhysician = weeklyHours * nationalData["avgWeeksWorkedPerYear"]
        aiScribeHours = annualHoursPerPhysician * physicianCount

    # ─── Total savings ──────────────────────────────────────
    totalHoursSaved = formHoursSaved + aiScribeHours
    hoursPerPhysician = totalHoursSaved / max(1, physicianCount)

    # ─── FTE recovery ───────────────────────────────────────
    annualFteHours = nationalData["avgWeeklyWorkHours"] * nationalData["avgWeeksWorkedPerYear"]
    fteRecovered = totalHoursSaved / annualFteHours

    # ─── Cost savings ───────────────────────────────────────
    costSavings = totalHoursSaved * avgPhysicianHourlyCost

    # ─── Patient visits recovered ───────────────────────────
    patientVisits = totalHoursSaved * 60 / avgPatientVisitMinutes

    # ─── Province context ────────────────────────────────────
    provinceInfo = provinceData.get(province.lower(), provinceData["ontario"])

    result = {
        "physicianCount": physicianCount,
        "province": province,
        "formsAutomated": formsAutomated,
        "useAiScribe": useAiScribe,
        "hoursSavedPerYear": round(totalHoursSaved, 1),
        "hoursSavedPerPhysician": round(hoursPerPhysician, 1),
        "fteRecovered": round(fteRecovered, 2),
        "costSavingsPerYear": round(costSavings, 2),
        "aiScribeBonusHours": round(aiScribeHours, 1),
        "formAutomationHours": round(formHoursSaved, 1),
        "patientVisitsRecovered": round(patientVisits, 0),
        "formBreakdown": formBreakdown,
        "provinceContext": {
            "provinceFteGain": provinceInfo["fteGain"],
            "provincePhysicians": provinceInfo["totalPhysicians"],
        },
        "nationalContext": {
            "totalUnnecessaryHours": nationalData["unnecessaryAdminHoursPerYear"],
            "nationalFteRecoverable": nationalData["recoverableFte"],
            "nationalPhysicianCount": nationalData["totalPhysicians"],
        },
        "summary": {
            "headline": (
                f"Automating {', '.join(formsAutomated)} forms for "
                f"{physicianCount} physicians saves "
                f"{totalHoursSaved:,.0f} hours/year "
                f"(${costSavings:,.0f} CAD) — "
                f"equivalent to {fteRecovered:.1f} FTE physicians."
            ),
            "source": "CMA/CFIB 2026 Report: 'Losing doctors to desk work'",
        },
    }

    return result
