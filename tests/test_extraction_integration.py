"""Redundancy review affects scoring inputs and is revalidated from cache."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

import agent
import matching_service
from matching_cache import CacheUnavailable


TEXTS = [
    "Je pilote le backlog, ses priorités métier et la qualité des livrables.",
    "Gestion de backlog : prioriser et gérer le backlog produit.",
    "Validation des livrables avant mise en production.",
]
OFFER = "\n".join(TEXTS)
EXTRACTION = {"titre": "PO", "requirements": [
    {"text": text, "kind": "skill", "importance": "required"} for text in TEXTS]}
ABSORPTION = {"remove_id": "R002", "keep_id": "R001",
    "removed_quote": TEXTS[1], "kept_quote": TEXTS[0],
    "reason": "La responsabilité de gestion et de priorisation du backlog est déjà couverte."}


class ExtractionIntegrationTests(unittest.TestCase):
    def analyze(self, absorptions):
        with patch.object(agent, "_get_llm_config", return_value={"model": "test-model"}), \
             patch.object(agent, "llm_complete", return_value=(json.dumps(EXTRACTION), {"tokens_input": 100})), \
             patch("extraction_review.llm_complete", return_value=(
                 json.dumps({"absorptions": absorptions}), {"tokens_input": 12})):
            return agent.analyze_job_posting(OFFER)

    def test_review_removes_duplicate_but_keeps_quality_and_distinct_acceptance(self):
        analysis, metrics = self.analyze([ABSORPTION])
        self.assertNotIn("error", analysis)
        self.assertEqual([r["text"] for r in analysis["requirements"]], [TEXTS[0], TEXTS[2]])
        self.assertEqual([r["id"] for r in analysis["requirements"]], ["R001", "R002"])
        self.assertEqual(len(analysis["extraction_review"]["original_requirements"]), 3)
        self.assertEqual(analysis["extraction_review"]["audit"]["absorptions"], [ABSORPTION])
        self.assertEqual(metrics["tokens_input"], 112)

    def test_invalid_audit_aborts_before_retrieval_or_score(self):
        invalid = dict(ABSORPTION, remove_id="R999")
        analysis, metrics = self.analyze([invalid])
        self.assertIn("error", analysis)
        self.assertEqual(metrics["tokens_input"], 112)
        with patch.object(agent, "analyze_job_posting", return_value=(analysis, metrics)), \
             patch.object(agent, "search_matching_evidence") as search:
            result = agent.run_agent(OFFER)
        self.assertIsNone(result["matching"]["score_global"])
        search.assert_not_called()

    def test_cached_audit_cannot_be_removed_or_rewritten(self):
        analysis, _ = self.analyze([ABSORPTION])
        evidence = [{"id": "C01", "text": "J’ai piloté le backlog et la recette.", "metadata": {}}]
        rows = [agent._validate_judgment(r, {
            "requirement_id": r["id"], "status": "direct", "evidence_ids": ["C01"],
            "justification": "J’ai piloté ces activités."}, evidence) for r in analysis["requirements"]]
        result = {"job_analysis": analysis, "matching": agent._summarize_matching(rows)}
        matching_service._validate_result(result, OFFER)
        for changed in ("missing", "invented_quote", "removed_distinct_requirement"):
            invalid = deepcopy(result)
            review = invalid["job_analysis"]["extraction_review"]
            if changed == "missing":
                del invalid["job_analysis"]["extraction_review"]
            elif changed == "invented_quote":
                review["audit"]["absorptions"][0]["kept_quote"] = "Invented source"
            else:
                review["audit"]["absorptions"] = []
            with self.subTest(changed=changed), self.assertRaises(CacheUnavailable):
                matching_service._validate_result(invalid, OFFER)


if __name__ == "__main__":
    unittest.main()
