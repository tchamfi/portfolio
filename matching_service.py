"""Reuse one validated assessment for an offer and an exact evaluation context.

The provider remains probabilistic. Repeatability comes from preserving the
validated assessment, not from assuming temperature=0 is deterministic.
"""
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import threading
import unicodedata

import agent
from matching_cache import CacheUnavailable, get_cached_matching, save_cached_matching
from rag_pipeline import get_evidence_by_ids, get_knowledge_status
from extraction_review import validate_extraction_review

SERVICE_VERSION = "reviewed-matching-v2"
_MEMORY = OrderedDict()
_MEMORY_LOCK = threading.RLock()
_KEY_LOCKS = [threading.RLock() for _ in range(32)]
_MEMORY_LIMIT = 64


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _implementation_fingerprint():
    root = Path(__file__).resolve().parent
    names = ("agent.py", "rag_pipeline.py", "doc_loader.py", "experience.py", "llm_provider.py",
             "matching_service.py", "matching_cache.py", "knowledge_store.py", "hybrid_retrieval.py",
             "extraction_review.py")
    return _digest({name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names})


def _context(status, config):
    # Tenure is computed to the month. A daily provenance timestamp alone must
    # not send an unchanged offer back to the probabilistic evaluator tomorrow.
    period = (status.get("as_of") or "")[:7]
    reference = (status.get("reference_fingerprint") or status.get("fingerprint"))
    if status.get("fingerprint") and status.get("experience_fingerprint") and period:
        reference = _digest({"corpus": status["fingerprint"],
                             "experience": status["experience_fingerprint"], "period": period})
    return {"service": SERVICE_VERSION, "implementation": _implementation_fingerprint(),
            "reference": reference,
            "corpus": status.get("fingerprint"), "experience": status.get("experience_fingerprint"),
            "as_of": period, "scoring": agent.SCORING_VERSION,
            "assessment": agent.ASSESSMENT_VERSION, "extraction": agent.EXTRACTION_VERSION,
            "review": agent.REVIEW_VERSION,
            "model_config": deepcopy(config)}


def evaluation_key(job_text, context, language):
    # Whitespace and Unicode composition do not create a different offer. Keep
    # punctuation, case, numbers, negations and qualifications intact.
    offer = unicodedata.normalize("NFC", " ".join(job_text.split()))
    return _digest({"offer": offer, "context": context, "language": language})


def _signature(result):
    return _digest({"criteria": result["job_analysis"]["requirements"],
                    "incomplete": result["job_analysis"].get("incomplete_excerpts", [])})


def _validate_result(result, job_text):
    """A provider/schema failure must never become the canonical assessment."""
    matching = result.get("matching") or {}
    analysis = result.get("job_analysis") or {}
    if not isinstance(matching, dict) or not isinstance(analysis, dict):
        raise CacheUnavailable("Invalid assessment snapshot")
    rows = matching.get("requirements", [])
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        raise CacheUnavailable("Invalid assessment rows")
    if (matching.get("error") or matching.get("analysis_unavailable") or not rows
            or any(r.get("assessment_valid") is not True for r in rows)):
        raise CacheUnavailable("The matching is not fully validated")
    try:
        # Normalize both retained quotes and the original extraction/audit.
        comparison = json.loads(unicodedata.normalize("NFC", json.dumps(analysis, ensure_ascii=False)))
        normalized = agent._validate_extraction(comparison, unicodedata.normalize("NFC", job_text))
        requirements = normalized["requirements"]
        review = comparison.get("extraction_review")
        if not isinstance(review, dict) or set(review) != {"original_requirements", "audit"}:
            raise ValueError("Missing extraction review")
        original = agent._validate_extraction(dict(comparison, requirements=review["original_requirements"]),
                                              unicodedata.normalize("NFC", job_text))
        if original["requirements"] != review["original_requirements"]:
            raise ValueError("Invalid original extraction")
        kept = validate_extraction_review(original["requirements"], review["audit"])
        expected = agent._validate_extraction(dict(comparison, requirements=kept),
                                              unicodedata.normalize("NFC", job_text))
        if expected["requirements"] != requirements:
            raise ValueError("Retained criteria do not match the extraction review")
        if len(rows) != len(requirements):
            raise ValueError("Incomplete assessment")
        for requirement, row in zip(requirements, rows):
            if (row.get("requirement_id") != requirement["id"]
                    or unicodedata.normalize("NFC", row.get("text", "")) != requirement["text"]
                    or row.get("importance") != requirement["importance"]
                    or row.get("kind") != requirement["kind"]
                    or any(row.get(flag) != requirement[flag] for flag in (
                        "critical", "critical_quote", "critical_ambiguity"))
                    or row.get("status") not in agent.STATUS_CREDIT):
                raise ValueError("Assessment no longer matches its requirements")
            ids = row.get("evidence_ids")
            if not isinstance(ids, list) or any(not isinstance(i, str) for i in ids) or len(ids) != len(set(ids)):
                raise ValueError("Invalid evidence IDs")
            if not isinstance(row.get("noncompliance_evidence"), list):
                raise ValueError("Missing noncompliance provenance")
        score = matching.get("score_global")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or score != agent._compute_score(rows):
            raise ValueError("Invalid score")
        summary = agent._summarize_matching(rows)
        if any(matching.get(key) != summary[key] for key in (
                "prerequisites", "prerequisite_ambiguities", "review_version", "reviewed_count", "disputed_count")):
            raise ValueError("Invalid prerequisite or review summary")
    except (ValueError, TypeError, KeyError) as exc:
        raise CacheUnavailable("Invalid assessment snapshot") from exc


def _compact(result, key, context, language):
    result = deepcopy(result)
    # The source texts already exist in the versioned corpus. Preserve their IDs
    # and hydrate them on read instead of duplicating large blocks in Airtable.
    source_context = result.pop("profile_context", None)
    if not isinstance(source_context, dict):
        raise CacheUnavailable("Missing candidate provenance")
    result["candidate_evidence_ids"] = {
        requirement["id"]: [item["id"] for item in source_context.get(requirement["id"], [])]
        for requirement in result["job_analysis"]["requirements"]}
    for row in result["matching"]["requirements"]:
        row.pop("evidence", None)
    return {"version": SERVICE_VERSION, "key": key, "context": context,
            "language": language, "created_at": datetime.now(timezone.utc).isoformat(),
            "result": result}


def _restore(snapshot, key, context, language, job_text):
    if (not isinstance(snapshot, dict) or snapshot.get("version") != SERVICE_VERSION
            or snapshot.get("key") != key or snapshot.get("context") != context
            or snapshot.get("language") != language or not isinstance(snapshot.get("result"), dict)):
        raise CacheUnavailable("Snapshot context mismatch")
    try:
        timestamp = datetime.fromisoformat(snapshot["created_at"])
        if timestamp.tzinfo is None:
            raise ValueError("Timestamp must include its timezone")
    except (KeyError, TypeError, ValueError):
        raise CacheUnavailable("Invalid snapshot timestamp") from None
    result = deepcopy(snapshot["result"])
    _validate_result(result, job_text)
    candidates = result.get("candidate_evidence_ids")
    requirements = result["job_analysis"]["requirements"]
    if (not isinstance(candidates, dict) or set(candidates) != {r["id"] for r in requirements}
            or any(not isinstance(values, list) or len(values) > agent.TOP_K
                   or any(not isinstance(value, str) for value in values)
                   or len(values) != len(set(values)) for values in candidates.values())):
        raise CacheUnavailable("Invalid candidate provenance")
    ids = {identifier for values in candidates.values() for identifier in values}
    evidence = {item["id"]: item for item in get_evidence_by_ids(sorted(ids))}
    if set(evidence) != ids:
        raise CacheUnavailable("Snapshot evidence no longer available")
    result["profile_context"] = {}
    for row in result["matching"]["requirements"]:
        allowed = candidates[row["requirement_id"]]
        if any(identifier not in allowed for identifier in row["evidence_ids"]):
            raise CacheUnavailable("Snapshot citation outside its original candidate set")
        row["evidence"] = [{"id": i, "text": evidence[i]["text"],
                            "metadata": deepcopy(evidence[i]["metadata"])} for i in row.get("evidence_ids", [])]
        result["profile_context"][row["requirement_id"]] = [deepcopy(evidence[i]) for i in allowed]
    # Retrieve only the recorded candidates by ID. Re-running semantic search on
    # a cache hit would add cost and could reject a stable result due to drift.
    for requirement, row in zip(requirements, result["matching"]["requirements"]):
        if requirement["kind"] == "experience":
            exp = requirement["experience"]
            check = agent.evaluate_experience_requirement(exp["minimum_years"], exp["scope"])
            expected = {"meets": "direct", "not_met": "not_met"}.get(check["status"], "unknown")
            if (row["status"] != expected or row.get("experience_check", {}).get("counted_months") != check["counted_months"]
                    or row.get("review_status") != "deterministic" or "review" in row):
                raise CacheUnavailable("Snapshot tenure no longer matches the reference")
        else:
            current_evidence = result["profile_context"][requirement["id"]]
            validated = agent._validate_judgment(requirement, row, current_evidence, language=language)
            if (not validated["assessment_valid"]
                    or any(row.get(field) != validated[field] for field in (
                        "status", "evidence_ids", "justification", "uncovered_aspects", "noncompliance_evidence"))
                    or not agent._validate_review(row, requirement, current_evidence, language)):
                raise CacheUnavailable("Snapshot assessment or review no longer validates")
    return result


def _remember(key, snapshot):
    with _MEMORY_LOCK:
        _MEMORY[key] = deepcopy(snapshot)
        _MEMORY.move_to_end(key)
        while len(_MEMORY) > _MEMORY_LIMIT:
            _MEMORY.popitem(last=False)


def _still_current(context):
    if _context(get_knowledge_status(), agent._get_llm_config()) != context:
        raise CacheUnavailable("The evaluation context changed")


def run_matching(job_text, response_type="email", language="fr"):
    """Persist before displaying a score; never re-run after an uncertain lookup.

    The striped locks coalesce simultaneous identical requests in Streamlit's
    process. Airtable keeps their result across sessions and process restarts.
    Email and pitch formats share the same assessment, regardless of wording.
    """
    if not isinstance(job_text, str) or not job_text.strip() or len(job_text) > 40000:
        return {"matching": {"error": "Invalid job document", "score_global": None}, "metrics": {}}
    if language not in {"fr", "en"} or response_type not in {"email", "pitch"}:
        raise ValueError("Unsupported matching presentation")
    context = _context(get_knowledge_status(), agent._get_llm_config())
    key = evaluation_key(job_text, context, language)
    with _KEY_LOCKS[int(key[:2], 16) % len(_KEY_LOCKS)]:
        with _MEMORY_LOCK:
            snapshot = deepcopy(_MEMORY.get(key))
        origin = "memory"
        if snapshot is None:
            snapshot = get_cached_matching(key)  # Raises if the lookup is uncertain.
            origin = "persistent"
        if snapshot is not None:
            result = _restore(snapshot, key, context, language, job_text)
            result["metrics"] = {"tokens_input": 0, "tokens_output": 0,
                                 "cout_usd": 0, "latence_ms": 0,
                                 "model": context["model_config"]["model"]}
        else:
            origin = "generated"
            result = agent.run_agent(job_text, "email", language=language)
            matching = result.get("matching") or {}
            if matching.get("score_global") is None or matching.get("error"):
                return result
            _validate_result(result, job_text)
            _still_current(context)
            proposal = _compact(result, key, context, language)
            _restore(proposal, key, context, language, job_text)
            snapshot = save_cached_matching(key, proposal)
            result = _restore(snapshot, key, context, language, job_text)
        _still_current(context)
        _remember(key, snapshot)
    metrics = result.setdefault("metrics", {})
    metrics.update({k: result["matching"][k] for k in (
        "corpus_version", "corpus_fingerprint", "experience_fingerprint", "reference_fingerprint",
        "as_of", "scoring_version", "assessment_version") if k in result["matching"]})
    metrics.update(evaluation_key=key, cache_origin=origin, extraction_version=agent.EXTRACTION_VERSION,
                   requirement_signature=_signature(result),
                   chunks_used=len({i for row in result["matching"]["requirements"] for i in row.get("evidence_ids", [])}))
    result["matching"].update(evaluation_key=key, cache_origin=origin,
                              evaluated_at=snapshot["created_at"], requirement_signature=_signature(result))
    if response_type == "pitch":
        try:
            result["response"], draft_metrics = agent.draft_response(
                result["job_analysis"], result["matching"], "pitch", language=language)
            result["metrics"].update(agent._merge_metrics([metrics, draft_metrics]))
        except Exception:
            result["response"] = ""
            result["draft_error"] = "The pitch is unavailable." if language == "en" else "Le pitch est indisponible."
        _still_current(context)
    return result
