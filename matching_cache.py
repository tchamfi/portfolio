"""Durable canonical matching artifacts in the existing Airtable config table.

The service validates scoring and reference provenance before persistence and
after retrieval. This boundary validates the storage envelope and fails closed:
an unavailable/corrupt store is never interpreted as a cache miss. No job text,
result or credential is logged here.
"""

import json
import re

import requests

import airtable_store


ENVELOPE_VERSION = 1
MAX_NOTES_CHARS = 90_000
REQUEST_TIMEOUT = 10


class CacheUnavailable(RuntimeError):
    """The persistent canonical result cannot currently be trusted or saved."""

    def __init__(self, message, code="M110"):
        super().__init__(message)
        self.code = code


def _key(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", value):
        raise CacheUnavailable("Invalid matching cache key.")
    return value.lower()


def _encode(key, result):
    if not isinstance(result, dict) or not result:
        raise CacheUnavailable("Invalid matching cache result.")
    try:
        encoded = json.dumps(
            {"version": ENVELOPE_VERSION, "key": key, "result": result},
            ensure_ascii=False, allow_nan=False, separators=(",", ":"),
        )
    except (ValueError, TypeError, OverflowError, RecursionError):
        raise CacheUnavailable("Invalid matching cache result.") from None
    if len(encoded) > MAX_NOTES_CHARS:
        raise CacheUnavailable("Matching cache result exceeds the storage limit.")
    return encoded


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _decode_record(record, key):
    if not isinstance(record, dict) or not isinstance(record.get("id"), str):
        raise CacheUnavailable("Malformed matching cache record.")
    fields = record.get("fields")
    if not isinstance(fields, dict) or fields.get("Name") != airtable_store.MATCHING_CACHE_PREFIX + key:
        raise CacheUnavailable("Unexpected matching cache record.")
    notes = fields.get("Notes")
    if not isinstance(notes, str) or len(notes) > MAX_NOTES_CHARS:
        raise CacheUnavailable("Invalid matching cache envelope.")
    try:
        envelope = json.loads(notes, object_pairs_hook=_unique_object)
    except (ValueError, TypeError, RecursionError):
        raise CacheUnavailable("Invalid matching cache envelope.") from None
    if (
        not isinstance(envelope, dict)
        or set(envelope) != {"version", "key", "result"}
        or type(envelope["version"]) is not int
        or envelope["version"] != ENVELOPE_VERSION
        or envelope["key"] != key
    ):
        raise CacheUnavailable("Mismatched matching cache envelope.")
    # Also rejects non-JSON values such as NaN accepted by Python's JSON reader.
    _encode(key, envelope["result"])
    return envelope["result"]


def _request(method, **kwargs):
    token = airtable_store.get_token()
    if not isinstance(token, str) or not token.strip():
        raise CacheUnavailable("Matching cache credentials are unavailable.", "M100")
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
        code = {401: "M101", 403: "M101", 404: "M104", 422: "M122", 429: "M129"}.get(status, "M105")
        raise CacheUnavailable("Matching cache request failed.", code) from None
    except (requests.RequestException, ValueError, TypeError):
        raise CacheUnavailable("Matching cache request failed.", "M106") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise CacheUnavailable("Malformed matching cache response.")
    return payload


def get_cached_matching(key):
    """Return a stored artifact, or None only after a confirmed empty lookup."""
    key = _key(key)
    response = _request("get", params={
        "pageSize": 100,
        "filterByFormula": f'{{Name}} = "{airtable_store.MATCHING_CACHE_PREFIX}{key}"',
    })
    # More than a page of exact-key duplicates is already an invalid store state;
    # never silently ignore later records that could conflict with the first.
    if response.get("offset"):
        raise CacheUnavailable("Matching cache lookup is incomplete.")
    canonical = None
    for record in response["records"]:
        result = _decode_record(record, key)
        if canonical is not None and result != canonical:
            raise CacheUnavailable("Conflicting canonical matching results.")
        canonical = result
    return canonical


def save_cached_matching(key, payload):
    """Preserve an existing result, or create after a confirmed miss and read back.

    Airtable does not enforce uniqueness on Name. The service serializes each key
    within its process. Conflicting concurrent records from multiple processes
    fail closed on readback; this function never overwrites a canonical result.
    """
    key = _key(key)
    notes = _encode(key, payload)
    existing = get_cached_matching(key)
    if existing is not None:
        return existing
    response = _request("post", json={"records": [{"fields": {
        "Name": airtable_store.MATCHING_CACHE_PREFIX + key,
        "Notes": notes,
    }}]})
    if response.get("offset") or len(response["records"]) != 1:
        raise CacheUnavailable("Malformed matching cache write response.")
    created = _decode_record(response["records"][0], key)
    # Compare JSON representations, not a reference to the caller's mutable dict.
    if _encode(key, created) != notes:
        raise CacheUnavailable("Matching cache write did not preserve the result.")
    stored = get_cached_matching(key)
    if stored is None:
        raise CacheUnavailable("Matching cache write could not be confirmed.")
    return stored
