"""Run grounded matching acceptance cases without disguising mocks as LLM tests.

Offline: python evaluations/evaluate_matching.py
Live:    python evaluations/evaluate_matching.py --live --case jira_professional_use
All real generations, including the actual offer: add --live --full-offer.

Live mode bypasses the result cache and calls the configured provider (paid),
including hybrid retrieval and the independent review. It never publishes facts,
logs a recruiter contact, or generates an application draft. Only source facts
already published into the real corpus are used. Reports go to stdout unless
--output explicitly names a file. CI must never silently switch to live mode.
"""

import argparse
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DATASET_PATH = Path(__file__).with_name("matching_cases.json")
STATUS_CREDITS = {"direct": Decimal("1"), "partial": Decimal(".5"),
                  "training": Decimal(".25"), "historical": Decimal(".25"),
                  "unknown": Decimal("0"), "not_met": Decimal("0")}
WEIGHTS = {"required": 3, "optional": 1}


def normalized(text):
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


def load_dataset(path=DATASET_PATH):
    dataset = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_dataset(dataset)
    return dataset


def validate_dataset(dataset):
    """Fail on unclear or malformed expected outcomes, before any API expense."""
    if dataset.get("schema_version") != 1:
        raise ValueError("Unsupported benchmark schema")
    date.fromisoformat(dataset["reference_date"])
    cases = dataset.get("cases", [])
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Cases need distinct IDs")
    for case in cases:
        expected = case["expected"]
        if not case.get("offer") or not case.get("source_basis") or not expected.get("reason"):
            raise ValueError(f"{case['id']}: offer, source basis and rationale are required")
        if not expected.get("statuses") or not set(expected["statuses"]) <= STATUS_CREDITS.keys():
            raise ValueError(f"{case['id']}: unsupported expected status")
        if expected.get("importance") not in WEIGHTS or type(expected.get("critical")) is not bool:
            raise ValueError(f"{case['id']}: explicit weighting and prerequisite expectation required")
        if expected.get("kind") not in {"skill", "experience", "language", "constraint"}:
            raise ValueError(f"{case['id']}: invalid kind")
        for pattern in expected.get("forbidden_claim_patterns", []):
            re.compile(pattern, re.I)
        if "duration" in case:
            if expected["kind"] != "experience" or case["duration"]["minimum_years"] < 0:
                raise ValueError(f"{case['id']}: invalid experience check")
    full = dataset["full_offer"]
    path = (ROOT / full["path"]).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("Full offer fixture must be an existing repository file")
    text = normalized(path.read_text(encoding="utf-8"))
    for group in full["expected_semantic_groups"]:
        if not all(normalized(anchor) in text for anchor in group["anchors"]):
            raise ValueError(f"Full offer anchor absent: {group['name']}")
    if full["score_expectation"] is not None:
        raise ValueError("The full offer deliberately has no frozen score target")


def expected_score(rows):
    """Acceptance oracle from the documented rubric, not the scorer under test."""
    if not rows or any(not row.get("assessment_valid", False) for row in rows):
        return None
    total = sum(WEIGHTS[row["importance"]] for row in rows)
    credit = sum(WEIGHTS[row["importance"]] * STATUS_CREDITS[row["status"]] for row in rows)
    return int((100 * credit / total).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def publication_ready(case, chunks):
    terms = case.get("publication_terms", [])
    if not terms:
        return True
    # All terms must coexist in one attributable record. Different employers
    # elsewhere in the CV must not satisfy the publication prerequisite.
    return any(all(normalized(term) in normalized(chunk["text"]) for term in terms)
               for chunk in chunks)


def check_result_integrity(offer, analysis, matching, context):
    """Check source quotation, own evidence and score; not semantic entailment."""
    failures = []
    requirements = analysis.get("requirements", [])
    rows = matching.get("requirements", [])
    ids = [item["id"] for item in requirements]
    if sorted(row.get("requirement_id", "") for row in rows) != sorted(ids):
        failures.append("Missing, repeated or extra requirement assessment")
    by_id = {item["id"]: item for item in requirements}
    for requirement in requirements:
        if normalized(requirement["text"]) not in normalized(offer):
            failures.append(f"{requirement['id']}: criterion is not quoted from the offer")
    if len({normalized(item["text"]) for item in requirements}) != len(requirements):
        failures.append("Repeated exact criterion")
    for row in rows:
        rid = row.get("requirement_id")
        if rid not in by_id:
            continue
        requirement = by_id[rid]
        if row.get("importance") != requirement["importance"]:
            failures.append(f"{rid}: assessor changed the requirement's weight")
        evidence_ids = row.get("evidence_ids", [])
        available = {item["id"]: item for item in context.get(rid, [])}
        if len(evidence_ids) != len(set(evidence_ids)) or any(i not in available for i in evidence_ids):
            failures.append(f"{rid}: invented, repeated or foreign evidence ID")
        if row.get("status") not in STATUS_CREDITS:
            failures.append(f"{rid}: unrecognized status")
        if not row.get("assessment_valid"):
            failures.append(f"{rid}: incomplete or invalid assessment")
        if (row.get("status") not in {"unknown", None} and requirement.get("kind") != "experience"
                and not evidence_ids):
            failures.append(f"{rid}: supported status without cited evidence")
        for gap in row.get("uncovered_aspects", []):
            quote = gap.get("requirement_quote", "")
            if not quote or normalized(quote) not in normalized(requirement["text"]):
                failures.append(f"{rid}: invented uncovered aspect")
        if requirement.get("critical") and row.get("status") != "direct":
            if not any(item.get("requirement_id") == rid for item in matching.get("prerequisites", [])):
                failures.append(f"{rid}: explicit unresolved prerequisite missing from summary")
    try:
        if matching.get("score_global") != expected_score(rows):
            failures.append("Score differs from the documented weighted rubric")
    except (KeyError, TypeError, ValueError):
        failures.append("Cannot independently verify score")
    return failures


def evaluate_case_result(case, analysis, matching, context):
    failures = check_result_integrity(case["offer"], analysis, matching, context)
    expected = case["expected"]
    requirements, rows = analysis.get("requirements", []), matching.get("requirements", [])
    if len(requirements) != 1 or len(rows) != 1:
        return failures + ["This single-clause acceptance case expects one criterion; review any split or omission"]
    requirement, row = requirements[0], rows[0]
    for key in ("kind", "importance", "critical"):
        if requirement.get(key) != expected[key]:
            failures.append(f"Expected {key}={expected[key]!r}, received {requirement.get(key)!r}")
    if row.get("status") not in expected["statuses"]:
        failures.append(f"Expected status among {expected['statuses']}, received {row.get('status')}")
    cited_ids = set(row.get("evidence_ids", []))
    cited = "\n".join(item["text"] for item in context.get(requirement["id"], []) if item["id"] in cited_ids)
    for term in expected.get("evidence_terms", []):
        if normalized(term) not in normalized(cited):
            failures.append(f"Expected fact absent from cited evidence: {term}")
    justification = row.get("justification", "") + " " + " ".join(
        item.get("reason", "") for item in row.get("uncovered_aspects", []))
    for pattern in expected.get("forbidden_claim_patterns", []):
        if re.search(pattern, justification, re.I):
            failures.append(f"Forbidden claim pattern: {pattern}")
    duration = case.get("duration")
    if duration:
        from experience import evaluate_experience_requirement
        check = evaluate_experience_requirement(duration["minimum_years"], duration["scope"])
        status = {"meets": "direct", "not_met": "not_met", "unknown": "unknown"}[check["status"]]
        if row.get("status") != status:
            failures.append("The live duration verdict differs from the exact scoped chronology")
        if requirement.get("experience", {}).get("minimum_years") != duration["minimum_years"]:
            failures.append("The extracted experience threshold differs from the offer")
    return failures


def evaluate_full_offer(offer, fixture, analysis, matching, context):
    failures = check_result_integrity(offer, analysis, matching, context)
    requirements = analysis.get("requirements", [])
    if len(requirements) != fixture["expected_requirement_count"]:
        failures.append(f"Review segmentation: expected {fixture['expected_requirement_count']} criteria, received {len(requirements)}")
    for group in fixture["expected_semantic_groups"]:
        matched = [r for r in requirements if any(normalized(a) in normalized(r["text"]) for a in group["anchors"])]
        if not matched:
            failures.append(f"Missing expected source clause: {group['name']}")
        if len(matched) > group.get("maximum_rows", 1):
            failures.append(f"Potential repeated skill to review: {group['name']}")
    for fragment in fixture["excluded_fragments"]:
        if any(normalized(fragment) in normalized(r["text"]) for r in requirements):
            failures.append(f"Context or truncated text was scored: {fragment}")
    if not any(normalized(fixture["expected_incomplete_fragment"]) in normalized(excerpt)
               for excerpt in analysis.get("incomplete_excerpts", [])):
        failures.append("Truncated final clause was not reported as incomplete")
    return failures


def run_offline(dataset, cases):
    """Use the repository reference only, without reading remote owner records."""
    from unittest.mock import patch
    import rag_pipeline as rag

    previous_index = rag._index
    try:
        with patch.object(rag, "published_snapshot", return_value={"facts": [], "fingerprint": "offline-base-only"}):
            return _run_offline_base(dataset, cases)
    finally:
        rag._index = previous_index


def _run_offline_base(dataset, cases):
    import agent
    import doc_loader
    from experience import evaluate_experience_requirement
    import rag_pipeline as rag

    chunks = doc_loader.load_documents_as_chunks()
    known_ids = {c["id"] for c in chunks}
    results = []
    for case in cases:
        failures, checks = [], ["fixture_schema", "explicit_prerequisite_rule"]
        expected = case["expected"]
        if agent._critical_requirement(case["offer"], expected["importance"])["critical"] != expected["critical"]:
            failures.append("Explicit prerequisite rule differs from business expectation")
        retrieval = case.get("retrieval")
        found = []
        if retrieval:
            checks.append("real_lexical_retrieval")
            expected_ids = set(retrieval["any_ids"])
            if not expected_ids <= known_ids:
                failures.append("Referenced acceptance source no longer exists; review fixture")
            found = [r["id"] for r in rag.search_evidence(case["offer"], top_k=5)]
            if not expected_ids.intersection(found):
                failures.append(f"Expected relevant source among {sorted(expected_ids)}, retrieved {found}")
        if case.get("duration"):
            checks.append("real_scoped_duration_at_reference_date")
            duration = case["duration"]
            check = evaluate_experience_requirement(duration["minimum_years"], duration["scope"], dataset["reference_date"])
            if check["status"] != duration["expected_check"]:
                failures.append(f"Duration expected {duration['expected_check']}, received {check['status']}")
        ready = publication_ready(case, chunks)
        results.append({"id": case["id"], "checks": checks, "retrieved_ids": found,
                        "semantic_status": "not_evaluated", "publication_ready": ready,
                        "outcome": "failed" if failures else "passed", "failures": failures})
    return results


def run_live_case(case, model=None):
    import agent
    import rag_pipeline as rag

    reference_before = rag.get_knowledge_status()
    if not publication_ready(case, rag._ensure_index()["chunks"]):
        return {"id": case["id"], "outcome": "blocked", "failures": ["Required owner facts are not published in the real corpus"],
                "semantic_status": "not_evaluated", "publication_terms": case.get("publication_terms", [])}
    # --model is a temporary explicit runner override; it never changes admin
    # configuration. Patch only model selection, never a generation or proof.
    from unittest.mock import patch
    llm_config = agent._get_llm_config()
    if model:
        llm_config["model"] = model
    with patch.object(agent, "_get_llm_config", return_value=llm_config):
        analysis, extraction_metrics = agent.analyze_job_posting(case["offer"])
        context, retrieval_metrics = rag.search_matching_evidence(
            analysis.get("requirements", []), model=llm_config["model"], language=case.get("language", "fr"))
        matching, assessment_metrics = agent.compute_matching(analysis, context, language=case.get("language", "fr"))
    if case.get("full_offer_fixture"):
        failures = evaluate_full_offer(case["offer"], case["full_offer_fixture"], analysis, matching, context)
    else:
        failures = evaluate_case_result(case, analysis, matching, context)
    reference_after = rag.get_knowledge_status()
    if reference_before["reference_fingerprint"] != reference_after["reference_fingerprint"]:
        failures.append("The published reference changed during evaluation; rerun against one stable version")
    return {"id": case["id"], "outcome": "failed" if failures else "passed",
            "semantic_status": "evaluated_with_real_provider", "failures": failures,
            "model": llm_config["model"], "reference": reference_before,
            "analysis": analysis, "matching": matching,
            "retrieved_evidence": context,
            "metrics": {"extraction": extraction_metrics, "retrieval": retrieval_metrics, "assessment": assessment_metrics}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Call the real provider, bypassing matching cache (billable)")
    parser.add_argument("--case", action="append", default=[], help="Select a case ID; repeat for multiple cases")
    parser.add_argument("--full-offer", action="store_true", help="Also evaluate the user's full offer in live mode")
    parser.add_argument("--model", help="Explicit live-run model override; does not modify application configuration")
    parser.add_argument("--output", type=Path, help="Explicit JSON report path; defaults to stdout")
    args = parser.parse_args(argv)
    dataset = load_dataset()
    selected = set(args.case)
    full_id = dataset["full_offer"]["id"]
    unknown = selected - {c["id"] for c in dataset["cases"]} - {full_id}
    if unknown:
        parser.error(f"Unknown case IDs: {sorted(unknown)}")
    if (args.full_offer or args.model or full_id in selected) and not args.live:
        parser.error("--full-offer and --model require explicit --live")
    cases = [c for c in dataset["cases"] if not selected or c["id"] in selected]
    if args.live:
        if args.full_offer or full_id in selected:
            fixture = dataset["full_offer"]
            cases.append({"id": fixture["id"], "offer": (ROOT / fixture["path"]).read_text(encoding="utf-8"), "full_offer_fixture": fixture})
        results = []
        for case in cases:
            print(f"Evaluating {case['id']} with the real provider…", file=sys.stderr, flush=True)
            try:
                results.append(run_live_case(case, args.model))
            except Exception as exc:
                # Provider exception messages may contain request or credential
                # information. Record the type only; keep reports shareable.
                results.append({"id": case["id"], "outcome": "error", "semantic_status": "incomplete",
                                "failures": [f"Live evaluation failed: {type(exc).__name__}"]})
    else:
        results = run_offline(dataset, cases)
    report = {"dataset_schema": dataset["schema_version"], "reference_date": dataset["reference_date"],
              "run_at": datetime.now(timezone.utc).isoformat(), "mode": "live" if args.live else "offline",
              "live_mode_requested": args.live,
              "semantic_evaluation_run": any(r["semantic_status"] == "evaluated_with_real_provider" for r in results),
              "limitations": ("Automated status/source/claim-pattern checks; a pass is not proof of full semantic entailment or human agreement."
                              if args.live else "No model generation or remote owner records were evaluated. This checks fixtures, repository-reference lexical recall, scoped dates and prerequisite rules only."),
              "summary": {outcome: sum(r["outcome"] == outcome for r in results) for outcome in ("passed", "failed", "blocked", "error")},
              "results": results}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if all(r["outcome"] == "passed" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
