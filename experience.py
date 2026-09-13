"""Deterministic experience durations, scoped to documented professional roles.

Source dates have month precision. Inclusive calendar-month unions prevent
double-counting overlapping client missions; they are not exact day durations.
No domain or tool inherits the candidate's total years of IT experience.
"""

import calendar
import hashlib
import json
import math
from datetime import date, datetime
from pathlib import Path


EXPERIENCE_PATH = Path(__file__).resolve().parent / "knowledge" / "experience.json"
SCOPES = ("total_it", "product_owner", "qa", "data_product_owner")
SCOPE_LABELS = {
    "total_it": "IT professionnel",
    "product_owner": "Product Ownership",
    "qa": "postes QA",
    "data_product_owner": "Data Product Ownership",
}
_SCOPE_ALIASES = {
    "it": "total_it",
    "total it": "total_it",
    "po": "product_owner",
    "product owner": "product_owner",
    "product ownership": "product_owner",
    "proxy product owner": "product_owner",
    "quality assurance": "qa",
    "po_data": "data_product_owner",
    "po data": "data_product_owner",
    "data product owner": "data_product_owner",
}
COUNTING_METHOD = (
    "Union des mois calendaires des missions, mois de début et de fin inclus. "
    "Aucun mois postérieur à la date de calcul n'est compté. Le mois courant "
    "est inclus s'il est commencé : les résultats sont approximatifs au mois, "
    "et non une ancienneté calculée au jour près. Pour vérifier un seuil exact, "
    "les deux mois de bord de chaque période continue ne sont pas considérés "
    "comme nécessairement complets. Un seuil dans cette marge reste à confirmer."
)


def _as_date(as_of):
    if as_of is None:
        return date.today()
    if isinstance(as_of, datetime):
        return as_of.date()
    if isinstance(as_of, date):
        return as_of
    if isinstance(as_of, str):
        return date.fromisoformat(as_of)
    raise ValueError("as_of doit être une date ou une chaîne ISO YYYY-MM-DD")


def _month_index(value):
    if not isinstance(value, str) or len(value) != 7 or value[4] != "-":
        raise ValueError("Les dates des missions doivent respecter YYYY-MM")
    parsed = date.fromisoformat(value + "-01")
    return parsed.year * 12 + parsed.month - 1


def _month_label(index):
    year, month = divmod(index, 12)
    return f"{year:04d}-{month + 1:02d}"


def _union_intervals(intervals):
    """Merge inclusive month intervals, including directly adjacent intervals."""
    merged = []
    for start, end in sorted(intervals):
        if end < start:
            raise ValueError("Une mission ne peut pas se terminer avant son début")
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def _canonical_scope(scope):
    if not isinstance(scope, str):
        return None
    normalized = scope.strip().lower()
    return _SCOPE_ALIASES.get(normalized, normalized)


def get_experience_fingerprint():
    """Identify the dated source independently of the Markdown reference."""
    return hashlib.sha256(EXPERIENCE_PATH.read_bytes()).hexdigest()


def _load_experiences():
    raw = EXPERIENCE_PATH.read_bytes()
    data = json.loads(raw)
    if data.get("schema_version") != 1:
        raise ValueError("Version du référentiel d'expérience non prise en charge")
    if not isinstance(data.get("experiences"), list):
        raise ValueError("Le référentiel doit contenir une liste de missions")
    seen = set()
    for entry in data["experiences"]:
        identifier = entry["id"]
        if identifier in seen:
            raise ValueError("Identifiant de mission dupliqué")
        seen.add(identifier)
        start = _month_index(entry["start"])
        if entry["end"] is not None and _month_index(entry["end"]) < start:
            raise ValueError("Dates de mission incohérentes")
        if not isinstance(entry.get("professional"), bool):
            raise ValueError("Chaque mission doit préciser son statut professionnel")
        if any(scope not in SCOPES for scope in entry["scopes"]):
            raise ValueError("Périmètre de mission non reconnu")
        if not entry["professional"] and entry["scopes"]:
            raise ValueError("Un stage exclu ne doit pas alimenter les durées professionnelles")
    return data, hashlib.sha256(raw).hexdigest()


def experience_summary(as_of=None):
    """Return JSON-serializable scoped durations and their source provenance.

    ``as_of`` accepts a date or ISO date string and defaults to today. Missions
    after that date contribute zero months, including already known future ends.
    Only named scopes with dated evidence are counted; tool durations are absent.
    """
    cutoff = _as_date(as_of)
    cutoff_month = cutoff.year * 12 + cutoff.month - 1
    data, source_fingerprint = _load_experiences()
    result = {
        "as_of": cutoff.isoformat(),
        "source_version": data["source_version"],
        "source_fingerprint": source_fingerprint,
        "date_precision": "month",
        "counting_method": COUNTING_METHOD,
        "current_month_partial": cutoff.day < calendar.monthrange(cutoff.year, cutoff.month)[1],
        "scope_definitions": data["scope_definitions"],
        "duration_limits": data["duration_limits"],
        "scopes": {},
        "experiences": data["experiences"],
    }
    for scope in SCOPES:
        intervals = []
        included = []
        for entry in data["experiences"]:
            if not entry["professional"] or scope not in entry["scopes"]:
                continue
            start = _month_index(entry["start"])
            end = min(_month_index(entry["end"]), cutoff_month) if entry["end"] else cutoff_month
            if start > end:
                continue
            intervals.append((start, end))
            included.append(entry)
        merged = _union_intervals(intervals)
        months = sum(end - start + 1 for start, end in merged)
        # The dates of the first and last day worked are not known. Counting
        # only interior months is a conservative full-month lower bound. Do
        # this once per union period, not per employer, to avoid penalizing
        # continuous work merely because multiple client missions are listed.
        guaranteed_months = sum(max(0, end - start - 1) for start, end in merged)
        full_years, remainder = divmod(months, 12)
        result["scopes"][scope] = {
            "months": months,
            "years": round(months / 12, 4),
            "years_and_months": {"years": full_years, "months": remainder},
            "duration_bounds": {
                "conservative_completed_months": guaranteed_months,
                "observed_calendar_months": months,
            },
            "periods": [{"start": _month_label(start), "end": _month_label(end)} for start, end in merged],
            "references": sorted({ref for entry in included for ref in entry["references"]}),
            "experience_ids": [entry["id"] for entry in included],
            "includes_current_month": any(start <= cutoff_month <= end for start, end in merged),
        }
    return result


def evaluate_experience_requirement(min_years, scope, as_of=None):
    """Evaluate a minimum against the exact scope, never against a fallback total.

    Status is ``meets``, ``not_met`` or ``unknown``. Unknown domains, unspecified
    experience and tool durations return ``unknown`` rather than an invented gap.
    Source references (Lxx/Uxx) correspond to the skills V3 provenance register.
    """
    canonical = _canonical_scope(scope)
    cutoff = _as_date(as_of)
    result = {
        "status": "unknown",
        "scope": canonical,
        "required_years": None,
        "counted_months": None,
        "counted_years": None,
        "references": [],
        "experience_ids": [],
        "as_of": cutoff.isoformat(),
        "date_precision": "month",
        "counting_method": COUNTING_METHOD,
        "source_fingerprint": get_experience_fingerprint(),
    }
    try:
        if isinstance(min_years, bool):
            raise ValueError
        minimum = float(min_years)
        if not math.isfinite(minimum) or minimum < 0:
            raise ValueError
    except (TypeError, ValueError):
        result["reason"] = "Durée minimale absente ou invalide ; aucun seuil d'ancienneté ne peut être vérifié."
        return result
    result["required_years"] = minimum
    if canonical not in SCOPES:
        result["reason"] = (
            "La durée de ce périmètre ou de cet outil n'est pas renseignée. "
            "Cela ne signifie pas que la compétence est absente ; l'expérience "
            "totale IT ou PO ne peut pas lui être attribuée automatiquement."
        )
        return result
    summary = experience_summary(cutoff)
    counted = summary["scopes"][canonical]
    months = counted["months"]
    minimum_months = math.ceil(minimum * 12)
    lower_bound = counted["duration_bounds"]["conservative_completed_months"]
    if minimum_months <= lower_bound:
        status = "meets"
    elif minimum_months > months:
        status = "not_met"
    else:
        status = "unknown"
    result.update({
        "status": status,
        "counted_months": months,
        "counted_years": counted["years"],
        "references": counted["references"],
        "experience_ids": counted["experience_ids"],
        "source_version": summary["source_version"],
        "source_fingerprint": summary["source_fingerprint"],
        "duration_bounds": counted["duration_bounds"],
        "includes_partial_current_month": summary["current_month_partial"] and counted["includes_current_month"],
    })
    duration = counted["years_and_months"]
    result["reason"] = (
        f"{SCOPE_LABELS[canonical]} : {months} mois documentés "
        f"({duration['years']} ans et {duration['months']} mois), contre "
        f"{minimum:g} ans demandés. Calcul par union des mois, sans double compte."
    )
    if result["includes_partial_current_month"]:
        result["reason"] += " Le mois courant commencé est inclus ; précision au mois."
    if status == "unknown":
        result["reason"] += (
            f" Le seuil est dans la marge liée aux dates mensuelles "
            f"({lower_bound} mois complets retenus de façon conservatrice). "
            "Les dates exactes de début et de fin sont nécessaires pour confirmer ce seuil."
        )
    return result
