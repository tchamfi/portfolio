"""Conservative checks for observed public-chat regressions, without rewriting.

These patterns are defense in depth, not exhaustive semantic verification.
They reject a whole draft for one bounded repair; they never establish a fact.
"""
import re
import unicodedata


def _fold(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.lower())
                   if not unicodedata.combining(c)).replace("’", "'")


_REF = r"(?:[CEQFTLUDM]\d{2,}|K[0-9a-fA-F]{8,})"
_REFS = re.compile(r"\[\s*" + _REF + r"(?:\s*[,;·]\s*" + _REF + r")*\s*\]")
_THIRD_PERSON = re.compile(
    r"\blionel(?:\s+tchamfong)?\s+(?:a\s+(?:pilote|travaille|coordonne|ete|une)|"
    r"est\s+(?:product|certifie|titulaire)|has\s+(?:led|worked|coordinated|experience)|"
    r"worked|led|holds)\b|(?:^|[.!?\n]\s*)(?:il\s+a\s+(?:pilote|travaille|coordonne|ete)|"
    r"he\s+(?:has\s+(?:worked|led|coordinated)|worked|led))\b")
_CREDENTIAL = re.compile(r"\b(?:certifi\w*|uncertifi\w*|credentials?)\b")
_ABSENCE = re.compile(
    r"\b(?:je|lionel(?:\s+tchamfong)?)\s+(?:ne\s+(?:detiens|possede|dispose)\s+pas|"
    r"n'ai\s+(?:pas|aucun\w*)|ne\s+suis\s+pas\s+certifi\w*)\b|"
    r"\bi\s+(?:(?:do\s+not|don't)\s+(?:hold|have|possess)|"
    r"have\s+no|am\s+(?:not\s+certified|uncertified))\b|"
    r"\bi'm\s+(?:not\s+certified|uncertified)\b")


def _general_experience_question(question):
    q = _fold(question).strip().rstrip("?!. ")
    if not re.fullmatch(
        r"(?:(?:quel|quelle)\s+est\s+(?:votre|ton|son)\s+experience|"
        r"what\s+is\s+(?:your|his)\s+experience)\s+[^?!;:\n]+", q):
        return False
    # A compound or explicit scope question may legitimately require caveats.
    return not re.search(
        r"\b(?:et|and|mais|but|sans|without|pas|not|no|lack\w*|limit\w*|"
        r"personnel\w*|personally|direct\w*|hands[- ]on|certifi\w*|sla|"
        r"concep\w*|design\w*|develop\w*|cod\w*|programm\w*|techni\w*|"
        r"architect\w*|administ\w*|execut\w*|realis\w*|deploy\w*|deploi\w*)\b", q)


def response_issues(question, text):
    """Return targeted violations; absence of issues is not a factual guarantee."""
    issues = []
    folded = _fold(text)
    if _THIRD_PERSON.search(folded):
        issues.append("third_person")
    if _REFS.search(text):
        issues.append("internal_references")
    # Only credential sentences: an unrelated negative about another role is valid.
    for sentence in re.split(r"[.!?;]+|\n\s*\n", folded):
        if _CREDENTIAL.search(sentence) and _ABSENCE.search(sentence):
            issues.append("credential_absence")
            break
    if _general_experience_question(question):
        for sentence in re.split(r"[.!?]+|\n\s*\n", folded):
            contrast = re.search(r"\b(?:pas|not|rather than|plutot que|sans|without)\b|don't", sentence)
            technical = re.search(
                r"\b(?:concep\w*|design\w*|develop\w*|cod\w*|architect\w*|administ\w*|"
                r"devops|hands[- ]on|sla|pentest\w*|intrusion|technical|technique\w*|"
                r"documented\s+experience|experience\s+documentee)\b", sentence)
            if contrast and technical:
                issues.append("unsolicited_caveat")
                break
    return issues


def safe_fallback(language):
    return ("I can't confirm this from the information available."
            if language == "en" else
            "Je ne peux pas confirmer ce point avec les informations disponibles.")
