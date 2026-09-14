"""Deterministic boundary tests; stubs do not measure live model correctness."""
import json
import unittest
from unittest.mock import patch

import hybrid_retrieval as hybrid


def chunk(identifier, title, category="skill", body="Full source including actual role and limits"):
    return {"id": identifier, "text": body, "metadata": {
        "title": title, "category": category, "keywords": title,
        "role": "Owner-confirmed practice", "scope": "No inferred duration or advanced mastery"}}


class HybridRetrievalTests(unittest.TestCase):
    def test_semantic_paraphrase_adds_real_complete_evidence(self):
        blocks = [chunk("C01", "Stratégie de test"), chunk("C02", "Adoption d'une application RH",
                  body="I delivered the HR application into production and HR adopted it. No adoption percentage stated.")]
        requirements = [{"id": "R01", "text": "Accompagner les équipes métiers dans leurs nouveaux usages"}]
        response = json.dumps({"results": [{"requirement_id": "R01", "evidence_ids": ["C02"]}]})
        with patch.object(hybrid, "llm_complete", return_value=(response, {"tokens_input": 10, "tokens_output": 5})) as llm:
            result, metrics = hybrid.retrieve(requirements, blocks, {"R01": [blocks[0]]}, "test")
        self.assertEqual(result["R01"][0]["id"], "C02")
        self.assertEqual(result["R01"][0]["text"], blocks[1]["text"])
        self.assertEqual(result["R01"][0]["metadata"], blocks[1]["metadata"])
        self.assertEqual(metrics["retrieval_calls"], 1)
        self.assertEqual(metrics["tokens_input"], 10)
        payload = json.loads(llm.call_args.kwargs["user_content"])
        self.assertEqual(payload["requirements"], requirements)
        self.assertIn("scope_and_limits", payload["catalog"][1])
        self.assertNotIn("score", payload)

    def test_exact_named_tool_is_preserved_when_semantic_selector_omits_it(self):
        blocks = [chunk("K123456789abc", "Jira", "tool", "Jira used at GRDF and BNP PF; no admin mastery stated")]
        blocks += [chunk(f"C{i:02}", f"Generic Agile capability {i}") for i in range(1, 8)]
        requirements = [{"id": "R01", "text": "Utilisation de Jira et communication Agile"}]
        response = json.dumps({"results": [{"requirement_id": "R01", "evidence_ids": [b["id"] for b in blocks[1:]]}]})
        with patch.object(hybrid, "llm_complete", return_value=(response, {})):
            result, _ = hybrid.retrieve(requirements, blocks, {"R01": blocks}, "test")
        self.assertEqual(len(result["R01"]), 5)
        self.assertEqual(result["R01"][0]["id"], "K123456789abc")
        self.assertIn("no admin mastery", result["R01"][0]["text"])

    def test_invalid_ids_missing_or_duplicate_requirements_fail_closed(self):
        blocks = [chunk("C01", "QA")]
        requirements = [{"id": "R01", "text": "QA"}]
        invalid = [
            {"results": [{"requirement_id": "R01", "evidence_ids": ["INVENTED"]}]},
            {"results": [{"requirement_id": "R01", "evidence_ids": ["C01", "C01"]}]},
            {"results": [{"requirement_id": "R02", "evidence_ids": ["C01"]}]},
            {"results": []}, {"results": [None]},
        ]
        for payload in invalid:
            with self.subTest(payload=payload), patch.object(hybrid, "llm_complete", return_value=(json.dumps(payload), {})):
                with self.assertRaises(hybrid.HybridRetrievalError):
                    hybrid.retrieve(requirements, blocks, {"R01": blocks}, "test")

    def test_failed_provider_is_not_a_lexical_matching_result(self):
        with patch.object(hybrid, "llm_complete", side_effect=RuntimeError("provider unavailable")):
            with self.assertRaises(hybrid.HybridRetrievalError):
                hybrid.retrieve([{"id": "R01", "text": "QA"}], [chunk("C01", "QA")], {"R01": []}, "test")

    def test_invalid_response_retains_usage_for_fallback_accounting(self):
        with patch.object(hybrid, "llm_complete", return_value=("invalid JSON", {"tokens_input": 50, "cout_usd": 0.02})):
            with self.assertRaises(hybrid.HybridRetrievalError) as raised:
                hybrid.retrieve([{"id": "R01", "text": "QA"}], [chunk("C01", "QA")], {"R01": []}, "test")
        self.assertEqual(raised.exception.metrics["tokens_input"], 50)
        self.assertEqual(raised.exception.metrics["cout_usd"], 0.02)

    def test_requirements_are_batched_at_eight_and_usage_is_aggregated(self):
        blocks = [chunk("C01", "QA")]
        requirements = [{"id": f"R{i:02}", "text": "QA"} for i in range(17)]
        def select(**kwargs):
            batch = json.loads(kwargs["user_content"])["requirements"]
            self.assertLessEqual(len(batch), 8)
            return json.dumps({"results": [{"requirement_id": r["id"], "evidence_ids": ["C01"]} for r in batch]}), {"tokens_input": 10, "cout_usd": 0.01}
        with patch.object(hybrid, "llm_complete", side_effect=select) as llm:
            result, metrics = hybrid.retrieve(requirements, blocks, {}, "test")
        self.assertEqual(set(result), {r["id"] for r in requirements})
        self.assertEqual(llm.call_count, 3)
        self.assertEqual(metrics["tokens_input"], 30)
        self.assertAlmostEqual(metrics["cout_usd"], 0.03)

    def test_catalog_and_fusion_do_not_mutate_sources(self):
        blocks = [chunk("C01", "QA", body="A" * 2000)]
        original = json.loads(json.dumps(blocks))
        response = '{"results":[{"requirement_id":"R01","evidence_ids":["C01"]}]}'
        with patch.object(hybrid, "llm_complete", return_value=(response, {})):
            results, _ = hybrid.retrieve([{"id": "R01", "text": "QA"}], blocks, {}, "test")
        self.assertEqual(blocks, original)
        self.assertEqual(len(hybrid.catalog(blocks)[0]["summary"]), 700)
        self.assertEqual(len(results["R01"][0]["text"]), 2000)


if __name__ == "__main__":
    unittest.main()
