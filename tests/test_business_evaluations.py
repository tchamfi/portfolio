"""Business acceptance gates: real sources/rules, with no paid LLM in CI.

The provider-based status expectations are exercised only by the explicitly
opted-in evaluations/evaluate_matching.py --live runner. These tests do not
claim that mocked generations validate semantic judgment quality.
"""

from copy import deepcopy
import unittest
from unittest.mock import patch

import agent
import doc_loader
import rag_pipeline as rag
from evaluations.evaluate_matching import (
    check_result_integrity, evaluate_case_result, evaluate_full_offer,
    expected_score, load_dataset, publication_ready, ROOT, run_live_case, run_offline,
    validate_dataset,
)


class BusinessAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_dataset()

    def test_real_sources_recall_scoped_dates_and_prerequisites_without_llm(self):
        with patch.object(agent, "llm_complete", side_effect=AssertionError("CI must not call the provider")), \
                patch.object(rag, "llm_complete", side_effect=AssertionError("Offline recall is not LLM judgment")):
            results = run_offline(self.dataset, self.dataset["cases"])
        failures = {row["id"]: row["failures"] for row in results if row["outcome"] != "passed"}
        self.assertFalse(failures, failures)
        self.assertTrue(all(row["semantic_status"] == "not_evaluated" for row in results))

    def test_benchmark_requires_traceable_expectations_and_real_full_offer(self):
        broken = deepcopy(self.dataset)
        broken["cases"][0]["source_basis"] = ""
        with self.assertRaisesRegex(ValueError, "source basis"):
            validate_dataset(broken)
        broken = deepcopy(self.dataset)
        broken["cases"][0]["expected"]["statuses"] = ["almost_perfect"]
        with self.assertRaisesRegex(ValueError, "unsupported expected status"):
            validate_dataset(broken)
        self.assertIsNone(self.dataset["full_offer"]["score_expectation"])

    def test_tools_publication_needs_attribution_in_same_record(self):
        case = next(c for c in self.dataset["cases"] if c["id"] == "jira_professional_use")
        # A global bag of CV keywords must not fabricate a Jira-at-employer fact.
        self.assertFalse(publication_ready(case, [
            {"text": "Jira"}, {"text": "GRDF"}, {"text": "BNP Paribas Personal Finance"}]))
        self.assertTrue(publication_ready(case, [{"text": "J’ai utilisé Jira chez GRDF puis BNP Paribas Personal Finance."}]))

    def test_live_publication_gate_reads_effective_corpus_before_provider(self):
        # A boundary unit test only: no generated judgment is fabricated or
        # scored. Published facts must reach the real-provider boundary even
        # when they are absent from the checked-in Markdown reference.
        case = next(c for c in self.dataset["cases"] if c["id"] == "jira_professional_use")
        manual = {"id": "Ktest", "text": "J’ai utilisé Jira chez GRDF puis BNP Paribas Personal Finance."}
        with patch.object(rag, "get_knowledge_status", return_value={"reference_fingerprint": "unit-reference"}), \
                patch.object(rag, "_ensure_index", return_value={"chunks": [manual]}), \
                patch.object(doc_loader, "load_documents_as_chunks", return_value=[]), \
                patch.object(agent, "_get_llm_config", return_value={"model": "unit-model"}), \
                patch.object(agent, "analyze_job_posting", side_effect=RuntimeError("real-provider boundary reached")) as analyze:
            with self.assertRaisesRegex(RuntimeError, "real-provider boundary reached"):
                run_live_case(case)
            analyze.assert_called_once_with(case["offer"])

        with patch.object(rag, "get_knowledge_status", return_value={"reference_fingerprint": "unit-reference"}), \
                patch.object(rag, "_ensure_index", return_value={"chunks": []}), \
                patch.object(agent, "analyze_job_posting") as analyze:
            result = run_live_case(case)
            self.assertEqual(result["outcome"], "blocked")
            self.assertEqual(result["semantic_status"], "not_evaluated")
            analyze.assert_not_called()

    def test_weighting_and_unavailable_results_match_business_rubric(self):
        rows = [{"importance": "required", "status": "direct", "assessment_valid": True},
                {"importance": "required", "status": "partial", "assessment_valid": True},
                {"importance": "optional", "status": "unknown", "assessment_valid": True}]
        # 4.5 earned points / 7 available => 64.2857; optional absence has less
        # weight, and unknown is retained in the denominator.
        self.assertEqual(expected_score(rows), 64)
        self.assertEqual(agent._compute_score(rows), 64)
        rows[2]["assessment_valid"] = False
        self.assertIsNone(expected_score(rows))
        self.assertIsNone(expected_score([]))

    def test_result_checker_rejects_wrong_score_and_borrowed_evidence(self):
        case = next(c for c in self.dataset["cases"] if c["id"] == "qa_frontend_backend_strategy")
        source = next(c for c in doc_loader.load_documents_as_chunks() if c["id"] == "C01")
        req = {"id": "R001", "text": case["offer"], "kind": "skill", "importance": "required", "critical": False}
        row = {"requirement_id": "R001", "text": req["text"], "importance": "required", "status": "direct",
               "assessment_valid": True, "evidence_ids": ["C01"], "uncovered_aspects": [],
               "justification": "Je rédige les stratégies et les plans de test frontend et backend."}
        analysis, context = {"requirements": [req]}, {"R001": [source]}
        matching = {"requirements": [row], "score_global": 100, "prerequisites": []}
        self.assertEqual(evaluate_case_result(case, analysis, matching, context), [])
        matching["score_global"] = 82
        self.assertIn("Score differs from the documented weighted rubric",
                      evaluate_case_result(case, analysis, matching, context))
        matching["score_global"] = 100
        row["evidence_ids"] = ["C02"]
        failures = check_result_integrity(case["offer"], analysis, matching, context)
        self.assertTrue(any("foreign evidence" in failure for failure in failures), failures)

    def test_prerequisite_missing_from_public_summary_is_a_gate_failure(self):
        case = next(c for c in self.dataset["cases"] if c["id"] == "spanish_mandatory")
        req = {"id": "R001", "text": case["offer"], "kind": "language", "importance": "required", "critical": True}
        row = {"requirement_id": "R001", "text": req["text"], "importance": "required", "status": "unknown",
               "assessment_valid": True, "evidence_ids": [], "uncovered_aspects": [],
               "justification": "Je ne peux pas confirmer mon niveau d’espagnol avec les informations disponibles."}
        matching = {"requirements": [row], "score_global": 0, "prerequisites": []}
        failures = evaluate_case_result(case, {"requirements": [req]}, matching, {})
        self.assertTrue(any("prerequisite missing" in failure for failure in failures), failures)

    def test_full_offer_gate_detects_missing_meaning_and_scored_team_context(self):
        fixture = self.dataset["full_offer"]
        offer = (ROOT / fixture["path"]).read_text(encoding="utf-8")
        analysis = {"requirements": [{"id": "R001", "text": "1 architecte", "kind": "skill", "importance": "required"}],
                    "incomplete_excerpts": []}
        matching = {"requirements": [{"requirement_id": "R001", "text": "1 architecte", "importance": "required",
                                      "assessment_valid": True, "status": "unknown", "evidence_ids": []}], "score_global": 0}
        failures = evaluate_full_offer(offer, fixture, analysis, matching, {})
        self.assertTrue(any("Context or truncated text was scored" in item for item in failures))
        self.assertTrue(any("Missing expected source clause: backlog" in item for item in failures))
        self.assertTrue(any("Truncated final clause was not reported" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
