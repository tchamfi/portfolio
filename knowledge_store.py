"""Versioned, owner-confirmed knowledge in the existing Airtable config table.

Every edit appends an immutable snapshot with its parent revision. A draft never
withdraws the last published version. Readers validate the complete journal and
fail closed on corruption or concurrent branches, rather than choosing a winner.
The UI supplies authentication; this module is a server-side storage boundary.
"""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
import threading
import time
import uuid

import requests

import airtable_store


KNOWLEDGE_PREFIX = "__knowledge_v1__:"
SOURCE = "Précision confirmée par Lionel"
KINDS = ("tool", "skill", "language", "certification", "achievement")
PRACTICES = ("professional", "training", "historical", "unspecified")
STATES = ("draft", "published", "archived")
BUSINESS_FIELDS = (
    "kind", "title", "companies", "statement", "practice", "period", "limits",
    "keywords", "correction_of", "correction_quote",
)
CACHE_TTL = 10
REQUEST_TIMEOUT = 10
MAX_NOTES_CHARS = 30_000
_lock = threading.RLock()
_cache = {}
_bootstrap_completed = set()


class KnowledgeError(RuntimeError):
    """Knowledge is unavailable, invalid, or changed since the editor loaded it."""

    def __init__(self, message, code="K110"):
        super().__init__(message)
        self.code = code


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(",", ":"))


def _text(value, field, maximum, required=False, strip=True):
    if not isinstance(value, str):
        raise KnowledgeError(f"Le champ {field} doit être du texte.", "K422")
    value = value.strip() if strip else value
    if (required and not value.strip()) or len(value) > maximum:
        raise KnowledgeError(f"Le champ {field} est vide ou trop long.", "K422")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
        raise KnowledgeError(f"Le champ {field} contient des caractères invalides.", "K422")
    return value


def _text_list(value, field, maximum_items, maximum_length):
    if not isinstance(value, list) or len(value) > maximum_items:
        raise KnowledgeError(f"Le champ {field} doit être une liste limitée.", "K422")
    result = []
    for item in value:
        item = _text(item, field, maximum_length, required=True)
        if item not in result:
            result.append(item)
    return result


def _business(fields):
    if not isinstance(fields, dict) or set(fields) - set(BUSINESS_FIELDS):
        raise KnowledgeError("Les champs de cette fiche sont invalides.", "K422")
    kind = fields.get("kind", "skill")
    practice = fields.get("practice", "unspecified")
    if kind not in KINDS or practice not in PRACTICES:
        raise KnowledgeError("Le type ou la pratique de cette fiche est invalide.", "K422")
    result = {
        "kind": kind,
        "title": _text(fields.get("title", ""), "titre", 160, required=True),
        "companies": _text_list(fields.get("companies", []), "entreprises", 12, 120),
        "statement": _text(fields.get("statement", ""), "contribution", 6000, required=True),
        "practice": practice,
        "period": _text(fields.get("period", ""), "période", 120),
        "limits": _text(fields.get("limits", ""), "limites", 2000),
        "keywords": _text_list(fields.get("keywords", []), "mots-clés", 24, 80),
        "correction_of": _text(fields.get("correction_of", ""), "référence corrigée", 160),
        "correction_quote": _text(fields.get("correction_quote", ""), "extrait corrigé", 4000, strip=False),
    }
    if result["correction_of"] and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,159}", result["correction_of"]):
        raise KnowledgeError("La référence corrigée est invalide.", "K422")
    if result["correction_quote"] and not result["correction_of"]:
        raise KnowledgeError("Précisez la référence de l'extrait corrigé.", "K422")
    return result


def _fact_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"K[0-9a-f]{12}", value):
        raise KnowledgeError("L'identifiant de fiche est invalide.", "K422")
    return value


def _revision(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{32}", value):
        raise KnowledgeError("La version de fiche est invalide.", "K422")
    return value


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _decode(record):
    try:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            raise ValueError("Invalid record")
        fields = record["fields"]
        notes = fields["Notes"]
        if not isinstance(notes, str) or len(notes) > MAX_NOTES_CHARS:
            raise ValueError("Invalid envelope")
        event = json.loads(notes, object_pairs_hook=_unique_object)
        metadata = {"version", "id", "revision", "parent_revision", "state", "source", "created_at", "updated_at"}
        if not isinstance(event, dict) or set(event) != metadata | set(BUSINESS_FIELDS):
            raise ValueError("Invalid fields")
        if type(event["version"]) is not int or event["version"] != 1:
            raise ValueError("Invalid version")
        _fact_id(event["id"])
        _revision(event["revision"])
        if event["parent_revision"] is not None:
            _revision(event["parent_revision"])
        if fields["Name"] != KNOWLEDGE_PREFIX + event["id"] + ":" + event["revision"]:
            raise ValueError("Invalid key")
        if event["state"] not in STATES or event["source"] != SOURCE:
            raise ValueError("Invalid state or source")
        for key in ("created_at", "updated_at"):
            if not isinstance(event[key], str) or not datetime.fromisoformat(event[key]).tzinfo:
                raise ValueError("Invalid timestamp")
        business = {key: event[key] for key in BUSINESS_FIELDS}
        if _business(business) != business:
            raise ValueError("Non-canonical fields")
        _json(event)
        return event
    except (KeyError, ValueError, TypeError, RecursionError, KnowledgeError):
        raise KnowledgeError("Une version de connaissance enregistrée est invalide.", "K110") from None


def _request(method, token, **kwargs):
    url = f"{airtable_store.API_URL}/{airtable_store.BASE_ID}/{airtable_store.CONFIG_TABLE}"
    try:
        response = getattr(requests, method)(
            url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT, **kwargs,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.HTTPError as exc:
        status = getattr(exc.response, "status_code", None)
        code = {401: "K101", 403: "K101", 404: "K104", 422: "K122", 429: "K129"}.get(status, "K105")
        raise KnowledgeError("L'accès aux connaissances enregistrées a échoué.", code) from None
    except (requests.RequestException, ValueError, TypeError):
        raise KnowledgeError("Les connaissances enregistrées sont temporairement inaccessibles.", "K106") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise KnowledgeError("La réponse du stockage des connaissances est invalide.", "K110")
    return payload


def _token():
    value = airtable_store.get_token()
    return value.strip() if isinstance(value, str) else ""


def clear_cache():
    """Invalidate the local short-lived read cache after an editorial action."""
    with _lock:
        _cache.clear()


def _chains(events):
    grouped = {}
    for event in events:
        revisions = grouped.setdefault(event["id"], {})
        existing = revisions.get(event["revision"])
        if existing is not None and existing != event:
            raise KnowledgeError("Deux versions de connaissance sont en conflit.", "K409")
        revisions[event["revision"]] = event
    result = {}
    for fact_id, revisions in grouped.items():
        children = {}
        for event in revisions.values():
            parent = event["parent_revision"]
            if parent in children:
                raise KnowledgeError(f"Des modifications concurrentes concernent la fiche {fact_id}.", "K409")
            children[parent] = event
        chain = []
        parent = None
        while parent in children:
            event = children[parent]
            if len(chain) >= len(revisions):
                raise KnowledgeError("L'historique des connaissances est incohérent.", "K110")
            if chain and event["created_at"] != chain[0]["created_at"]:
                raise KnowledgeError("L'historique des connaissances est incohérent.", "K110")
            chain.append(event)
            parent = event["revision"]
        if len(chain) != len(revisions):
            raise KnowledgeError("L'historique des connaissances est incomplet.", "K110")
        result[fact_id] = chain
    return result


def _journal(force=False):
    token = _token()
    if not token:
        return {}
    key = (airtable_store.BASE_ID, airtable_store.CONFIG_TABLE, hashlib.sha256(token.encode()).hexdigest())
    with _lock:
        cached = _cache.get(key)
        if not force and cached and time.monotonic() - cached[0] < CACHE_TTL:
            return deepcopy(cached[1])
        # Once a refresh is attempted, a failed read must not resurrect an older
        # snapshot through a later non-forced call in the same process.
        _cache.pop(key, None)
        events = []
        seen_offsets = set()
        params = {"pageSize": 100, "filterByFormula": f'LEFT({{Name}}, {len(KNOWLEDGE_PREFIX)}) = "{KNOWLEDGE_PREFIX}"'}
        while True:
            payload = _request("get", token, params=params)
            events.extend(_decode(record) for record in payload["records"])
            offset = payload.get("offset")
            if not offset:
                break
            if not isinstance(offset, str) or offset in seen_offsets or len(seen_offsets) >= 100:
                raise KnowledgeError("La lecture des connaissances est incomplète.", "K110")
            seen_offsets.add(offset)
            params = dict(params, offset=offset)
        journal = _chains(events)
        _cache[key] = (time.monotonic(), journal)
        return deepcopy(journal)


def _published(chain):
    current = None
    for event in chain:
        if event["state"] == "published":
            current = event
        elif event["state"] == "archived":
            current = None
    return current


def _view(chain):
    current = deepcopy(chain[-1])
    published = _published(chain)
    current["published_revision"] = published["revision"] if published else None
    current["has_published_version"] = published is not None
    return current


def list_facts(force=False):
    """Latest editorial version of every fact, including drafts and archives."""
    journal = _journal(force=force)
    return sorted((_view(chain) for chain in journal.values()), key=lambda fact: (fact["title"].casefold(), fact["id"]))


def published_snapshot(force=False):
    """Only published facts; semantic fingerprint excludes drafts and timestamps."""
    journal = _journal(force=force)
    facts = sorted((deepcopy(value) for chain in journal.values() if (value := _published(chain))), key=lambda fact: fact["id"])
    semantic_fields = ("id", "source") + BUSINESS_FIELDS
    semantic = [{key: fact[key] for key in semantic_fields} for fact in facts]
    fingerprint = hashlib.sha256(_json(semantic).encode()).hexdigest()
    return {"facts": facts, "fingerprint": fingerprint}


def get_history(fact_id):
    fact_id = _fact_id(fact_id)
    chain = _journal(force=True).get(fact_id)
    if not chain:
        raise KnowledgeError("Cette fiche n'existe plus.", "K404")
    return deepcopy(list(reversed(chain)))


def _current(journal, fact_id, expected_revision):
    chain = journal.get(_fact_id(fact_id))
    if not chain:
        raise KnowledgeError("Cette fiche n'existe plus.", "K404")
    if expected_revision != chain[-1]["revision"]:
        raise KnowledgeError("La fiche a changé. Rechargez-la avant de poursuivre.", "K409")
    return chain


def _append(business, state, fact_id, chain):
    token = _token()
    if not token:
        raise KnowledgeError("Le stockage des connaissances n'est pas configuré.", "K100")
    now = datetime.now(timezone.utc).isoformat()
    event = {
        "version": 1, "id": fact_id, "revision": uuid.uuid4().hex,
        "parent_revision": chain[-1]["revision"] if chain else None,
        "state": state, "source": SOURCE,
        "created_at": chain[0]["created_at"] if chain else now, "updated_at": now,
        **business,
    }
    notes = _json(event)
    if len(notes) > MAX_NOTES_CHARS:
        raise KnowledgeError("Cette fiche dépasse la taille autorisée.", "K422")
    record = {"fields": {"Name": KNOWLEDGE_PREFIX + fact_id + ":" + event["revision"], "Notes": notes}}
    clear_cache()
    try:
        payload = _request("post", token, json={"records": [record]})
        if payload.get("offset") or len(payload["records"]) != 1 or _decode(payload["records"][0]) != event:
            raise KnowledgeError("L'enregistrement de cette fiche n'a pas pu être vérifié.", "K110")
        stored_chain = _journal(force=True).get(fact_id, [])
        if not stored_chain or stored_chain[-1] != event:
            raise KnowledgeError("La relecture de cette fiche n'a pas confirmé l'enregistrement.", "K110")
        return _view(stored_chain)
    finally:
        clear_cache()


def save_draft(fields, fact_id=None, expected_revision=None):
    business = _business(fields)
    with _lock:
        journal = _journal(force=True)
        if fact_id is None:
            if expected_revision is not None:
                raise KnowledgeError("Une nouvelle fiche n'a pas de version précédente.", "K422")
            fact_id = "K" + uuid.uuid4().hex[:12]
            if fact_id in journal:
                raise KnowledgeError("L'identifiant de fiche existe déjà. Réessayez.", "K409")
            chain = []
        else:
            chain = _current(journal, fact_id, expected_revision)
            current = chain[-1]
            if current["state"] != "archived" and {key: current[key] for key in BUSINESS_FIELDS} == business:
                return _view(chain)
        return _append(business, "draft", fact_id, chain)


def _transition(fact_id, state, expected_revision):
    with _lock:
        chain = _current(_journal(force=True), fact_id, expected_revision)
        current = chain[-1]
        if current["state"] == state:
            return _view(chain)
        if state == "published" and current["state"] == "archived":
            raise KnowledgeError("Restaurez d'abord cette fiche en brouillon.", "K422")
        return _append({key: current[key] for key in BUSINESS_FIELDS}, state, fact_id, chain)


def publish_fact(fact_id, expected_revision=None):
    return _transition(fact_id, "published", expected_revision)


def archive_fact(fact_id, expected_revision=None):
    return _transition(fact_id, "archived", expected_revision)


def restore_fact(fact_id, revision, expected_revision=None):
    """Restore a historical fact as a draft; publication remains explicit."""
    revision = _revision(revision)
    with _lock:
        chain = _current(_journal(force=True), fact_id, expected_revision)
        previous = next((event for event in chain if event["revision"] == revision), None)
        if previous is None:
            raise KnowledgeError("Cette version de la fiche est introuvable.", "K404")
        return _append({key: previous[key] for key in BUSINESS_FIELDS}, "draft", fact_id, chain)


def bootstrap_initial_facts():
    """One-time migration of the owner's explicitly confirmed Jira/Trello facts.

    Called explicitly by app startup. Existing journals, including archives and
    unpublished drafts, are never changed. A failed write is not acknowledged as
    success; the owner can inspect a surviving draft in the knowledge editor.
    """
    token = _token()
    if not token:
        return False
    key = (airtable_store.BASE_ID, airtable_store.CONFIG_TABLE, hashlib.sha256(token.encode()).hexdigest())
    with _lock:
        if key in _bootstrap_completed:
            return True
        initial = (
            ("K6a6972610001", "Jira", ["GRDF", "BNP Paribas Personal Finance"],
             "J’ai utilisé Jira chez GRDF et je l’utilise actuellement chez BNP Paribas Personal Finance."),
            ("K7472656c6c6f", "Trello", ["Enedis"], "J’ai utilisé Trello chez Enedis."),
        )
        journal = _journal(force=True)
        for fact_id, title, companies, statement in initial:
            if fact_id in journal:
                continue
            business = _business({
                "kind": "tool", "title": title, "companies": companies,
                "statement": statement, "practice": "professional", "keywords": [title],
                "limits": "Fonctions avancées et durée précise non renseignées.",
            })
            draft = _append(business, "draft", fact_id, [])
            publish_fact(fact_id, expected_revision=draft["revision"])
            journal = _journal(force=True)
        _bootstrap_completed.add(key)
        return True
