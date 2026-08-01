"""
Patient Matcher — fuzzy name matching for clinical copilot.

Doctors say names wrong: "Jon Doe" instead of "John Doe", "J Smith",
"Sarah J", "Mike Chen" instead of "Michael Chen".

This module finds the best matching patient using:
  1. Fuzzy string matching (difflib ratio)
  2. Phonetic matching (Soundex-like)
  3. Token-based matching (first/last name parts)
"""

import logging
from typing import List, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def _soundex(name: str) -> str:
    """
    Simplified Soundex encoding for phonetic matching.
    Handles: Smith/Smyth, Johnson/Johnsen, Chen/Chinn, etc.
    """
    if not name or not name[0].isalpha():
        return "0000"

    soundexMap = {
        "b": "1", "f": "1", "p": "1", "v": "1",
        "c": "2", "g": "2", "j": "2", "k": "2",
        "q": "2", "s": "2", "x": "2", "z": "2",
        "d": "3", "t": "3",
        "l": "4",
        "m": "5", "n": "5",
        "r": "6",
    }

    name = name.lower().strip()
    result = name[0].upper()
    prevCode = soundexMap.get(name[0], "0")

    for char in name[1:]:
        code = soundexMap.get(char, "0")
        if code != "0" and code != prevCode:
            result += code
        if code != "0":
            prevCode = code
        if len(result) >= 4:
            break

    return (result + "000")[:4]


def _nameTokens(name: str) -> List[str]:
    """Split a name into normalized tokens."""
    return [t.lower().strip() for t in name.replace(",", " ").split() if t.strip()]


def _similarity(a: str, b: str) -> float:
    """String similarity ratio (0.0 to 1.0)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def matchPatient(query: str, patients: list, threshold: float = 0.45) -> List[dict]:
    """
    Find matching patients from a query string.

    Args:
        query: What the doctor typed (e.g. "Jon Doe", "Sarah J", "Mike Chen")
        patients: List of Patient model objects with patientName, dateOfBirth
        threshold: Minimum match score (0.0 to 1.0)

    Returns:
        List of {patient, score, matchType} sorted by score descending.
    """
    query = query.strip().lower()
    if not query or len(query) < 2:
        return []

    queryTokens = _nameTokens(query)
    results = []

    for patient in patients:
        fullName = (patient.patientName or "").strip()
        if not fullName:
            continue

        fullNameLower = fullName.lower()
        patientTokens = _nameTokens(fullName)

        score = 0.0
        matchType = "none"

        # 1. Exact match
        if query == fullNameLower:
            score = 1.0
            matchType = "exact"

        # 2. Full name fuzzy match
        elif queryTokens and len(queryTokens) >= 1:
            fullScore = _similarity(query, fullNameLower)
            score = max(score, fullScore)
            if fullScore > 0.6:
                matchType = "fuzzy_full"

            # 3. Token-based matching
            # Match query tokens against patient name tokens
            tokenScores = []
            for qt in queryTokens:
                bestTokenScore = 0.0
                for pt in patientTokens:
                    ts = _similarity(qt, pt)
                    if ts > bestTokenScore:
                        bestTokenScore = ts

                    # Phonetic match
                    if _soundex(qt) == _soundex(pt) and ts > 0.3:
                        bestTokenScore = max(bestTokenScore, 0.7)

                tokenScores.append(bestTokenScore)

            if tokenScores:
                avgTokenScore = sum(tokenScores) / len(tokenScores)
                # Bonus if all tokens matched well
                if all(ts > 0.6 for ts in tokenScores):
                    avgTokenScore = min(1.0, avgTokenScore + 0.15)
                score = max(score, avgTokenScore)
                if avgTokenScore > 0.6 and matchType == "none":
                    matchType = "token"

            # 4. Prefix/abbreviation match (e.g. "Mike" → "Michael")
            if len(queryTokens) >= 1 and len(patientTokens) >= 1:
                qt0 = queryTokens[0]
                pt0 = patientTokens[0]
                if pt0.startswith(qt0) and len(qt0) >= 3:
                    prefixScore = len(qt0) / len(pt0) * 0.85
                    if len(queryTokens) > 1 and len(patientTokens) > 1:
                        # Check last name too
                        if patientTokens[-1].startswith(queryTokens[-1]):
                            prefixScore = min(0.95, prefixScore + 0.1)
                    score = max(score, prefixScore)
                    if prefixScore > 0.6 and matchType == "none":
                        matchType = "prefix"

        # 5. Phonetic (Soundex) full-name match
        if score < 0.5:
            querySoundex = " ".join(_soundex(t) for t in queryTokens)
            patientSoundex = " ".join(_soundex(t) for t in patientTokens)
            if querySoundex == patientSoundex and querySoundex != "0000":
                score = max(score, 0.65)
                if matchType == "none":
                    matchType = "phonetic"

        if score >= threshold:
            results.append({
                "patient": patient,
                "score": round(score, 3),
                "matchType": matchType,
            })

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    logger.info(f"Patient match for '{query}': {len(results)} matches above {threshold}")
    for r in results[:5]:
        logger.info(f"  → {r['patient'].patientName} (score={r['score']}, type={r['matchType']})")

    return results
