"""Canonical assessment reuse across sessions, restarts and failure boundaries."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import threading
import unicodedata
import unittest
from unittest.mock import patch

import agent
import matching_service as service
from matching_cache import CacheUnavailable


OFFER = """Gestion de backlog : définir et prioriser le backlog produit.
Tests et validation : valider les livrables avant leur lancement.
Outils Agile : maîtrise de Trello."""
STATUS = {"version": "V3.0", "fingerprint": "corpus-a",
          "reference_fingerprint": "reference-a", "experience_fingerprint": "experience-a",
          "as_of": "2026-09-13"}
CONFIG = {"model": "test-model", "temp_matching": .2, "max_tokens_matching": 1500}
EVIDENCE = {"id": "C01", "text": "J’ai géré le backlog et validé les livrables chez EPSA.",
            "metadata": {"role": "contribution attribuée", "sources": ["L01", "U01"]}}
METRICS = {"tokens_input": 100, "tokens_output": 40, "cout_usd": .01,
           "latence_ms": 50, "model": "test-model"}


def assessment(job_text=OFFER, statuses=("direct", "direct", "unknown")):
    """Use production extraction/judgment/summary validators for valid snapshots."""
    analysis = agent._validate_extraction({"titre": "Product Owner", "requirements": [
        {"text": line, "importance": "required", "kind": "skill"}
        for line in OFFER.splitlines()]}, job_text)
    rows, context = [], {}
    for requirement, status in zip(analysis["requirements"], statuses):
        sources = [deepcopy(EVIDENCE)] if status != "unknown" else []
        context[requirement["id"]] = sources
        judgment = {"requirement_id": requirement["id"], "status": status,
                    "evidence_ids": ["C01"] if sources else [],
                    "justification": ("Chez EPSA, j’ai piloté ces activités." if sources
                                      else "Ma pratique de Trello reste à confirmer.")}
        row = agent._validate_judgment(requirement, judgment, sources)
        if status in agent.REVIEW_STATUSES:
            row = agent._apply_review(row, row)
        rows.append(row)
    matching = agent._summarize_matching(rows)
    matching.update(corpus_version=STATUS["version"], corpus_fingerprint=STATUS["fingerprint"],
                    reference_fingerprint=STATUS["reference_fingerprint"],
                    experience_fingerprint=STATUS["experience_fingerprint"], as_of=STATUS["as_of"])
    return {"steps": ["Évaluation terminée"], "job_analysis": analysis,
            "profile_context": context, "matching": matching,
            "response": "Bonjour, voici mon expérience.", "metrics": deepcopy(METRICS)}


class MatchingServiceTests(unittest.TestCase):
    def setUp(self):
        self.store = {}
        self.status = deepcopy(STATUS)
        self.config = deepcopy(CONFIG)
        self.clear_memory()
        self.addCleanup(self.clear_memory)
        self.status_mock = self.patch("get_knowledge_status", side_effect=lambda: deepcopy(self.status))
        self.config_mock = self.patch("_get_llm_config", target=agent,
                                      side_effect=lambda: deepcopy(self.config))
        self.code = self.patch("_implementation_fingerprint", return_value="code-a")
        self.lookup = self.patch("get_cached_matching", side_effect=lambda key: deepcopy(self.store.get(key)))
        self.save = self.patch("save_cached_matching", side_effect=self.persist)
        self.evidence = self.patch("get_evidence_by_ids", side_effect=lambda ids:
                                   [deepcopy(EVIDENCE)] if ids == ["C01"] else [])
        self.retrieval = self.patch("query_rag_profile", target=agent, side_effect=lambda requirements:
                                   {r["id"]: ([deepcopy(EVIDENCE)] if r["id"] != "R003" else [])
                                    for r in requirements})
        self.generate = self.patch("run_agent", target=agent, side_effect=lambda job, *_args, **_kwargs: assessment(job))
        self.draft = self.patch("draft_response", target=agent,
                               return_value=("Mon pitch.", deepcopy(METRICS)))

    def patch(self, name, target=service, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    @staticmethod
    def clear_memory():
        with service._MEMORY_LOCK:
            service._MEMORY.clear()

    def persist(self, key, snapshot):
        self.store.setdefault(key, deepcopy(snapshot))
        return deepcopy(self.store[key])

    def test_identical_offer_and_whitespace_reuse_all_criteria_scores_and_reasons(self):
        first = service.run_matching(OFFER)
        self.generate.side_effect = AssertionError("A repeated offer must not be reassessed")
        repeated = service.run_matching(OFFER)
        whitespace = service.run_matching("\n\t" + OFFER.replace(" ", "  ").replace("\n", "\n\n") + "  ")
        for result in (repeated, whitespace):
            self.assertEqual(result["matching"]["score_global"], first["matching"]["score_global"])
            self.assertEqual(result["matching"]["requirements"], first["matching"]["requirements"])
            self.assertEqual(result["job_analysis"], first["job_analysis"])
            self.assertEqual(result["matching"]["requirement_signature"], first["matching"]["requirement_signature"])
            self.assertEqual(result["matching"]["evaluated_at"], first["matching"]["evaluated_at"])
            self.assertEqual(result["response"], first["response"])
            self.assertEqual(result["metrics"]["cache_origin"], "memory")
        self.generate.assert_called_once()
        self.save.assert_called_once()
        self.lookup.assert_called_once()

    def test_unicode_equivalent_offer_reuses_the_validated_assessment(self):
        first = service.run_matching(OFFER)
        repeated = service.run_matching(unicodedata.normalize("NFD", OFFER))
        self.assertEqual(repeated["matching"]["requirements"], first["matching"]["requirements"])
        self.assertEqual(repeated["metrics"]["evaluation_key"], first["metrics"]["evaluation_key"])
        self.generate.assert_called_once()

    def test_process_restart_restores_persistent_result_without_another_model_call(self):
        first = service.run_matching(OFFER)
        self.clear_memory()
        repeated = service.run_matching(OFFER)
        self.assertEqual(repeated["metrics"]["cache_origin"], "persistent")
        self.assertEqual(repeated["matching"]["requirements"], first["matching"]["requirements"])
        self.assertEqual(repeated["matching"]["score_global"], first["matching"]["score_global"])
        self.assertEqual(self.lookup.call_count, 2)
        self.generate.assert_called_once()
        self.save.assert_called_once()
        self.retrieval.assert_not_called()

    def test_concurrent_identical_requests_coalesce_one_generation(self):
        generating, second_entering, release = threading.Event(), threading.Event(), threading.Event()

        def slow_generation(job, *_args, **_kwargs):
            generating.set()
            if not release.wait(5):
                raise AssertionError("Generation release event was not signaled")
            return assessment(job)

        def second_request():
            second_entering.set()
            return service.run_matching(OFFER)

        self.generate.side_effect = slow_generation
        with ThreadPoolExecutor(max_workers=2) as pool:
            first_future = pool.submit(service.run_matching, OFFER)
            try:
                self.assertTrue(generating.wait(5))
                second_future = pool.submit(second_request)
                self.assertTrue(second_entering.wait(5))
            finally:
                release.set()
            first, second = first_future.result(timeout=5), second_future.result(timeout=5)
        self.assertEqual(first["matching"]["requirements"], second["matching"]["requirements"])
        self.assertEqual(first["matching"]["score_global"], second["matching"]["score_global"])
        self.generate.assert_called_once()
        self.save.assert_called_once()

    def test_incomplete_assessment_is_never_frozen_and_can_be_retried(self):
        invalid = assessment()
        invalid["matching"]["requirements"][1]["assessment_valid"] = False
        invalid["matching"] = agent._summarize_matching(invalid["matching"]["requirements"])
        self.generate.side_effect = [invalid, assessment()]
        first = service.run_matching(OFFER)
        self.assertIsNone(first["matching"]["score_global"])
        self.assertTrue(first["matching"]["analysis_unavailable"])
        self.assertFalse(self.store)
        self.assertFalse(service._MEMORY)
        self.save.assert_not_called()
        second = service.run_matching(OFFER)
        self.assertIsInstance(second["matching"]["score_global"], int)
        self.assertEqual(self.generate.call_count, 2)
        self.save.assert_called_once()

    def test_fully_assessed_unknown_zero_is_cacheable(self):
        self.generate.return_value = assessment(statuses=("unknown",) * 3)
        self.generate.side_effect = None
        first, second = service.run_matching(OFFER), service.run_matching(OFFER)
        self.assertEqual(first["matching"]["score_global"], 0)
        self.assertEqual(second["matching"]["score_global"], 0)
        self.assertFalse(second["matching"]["analysis_unavailable"])
        self.assertEqual(second["matching"]["unknown_count"], 3)
        self.generate.assert_called_once()
        self.save.assert_called_once()

    def test_uncertain_lookup_does_not_start_a_new_model_assessment(self):
        self.lookup.side_effect = CacheUnavailable("storage unavailable")
        with self.assertRaises(CacheUnavailable):
            service.run_matching(OFFER)
        self.generate.assert_not_called()
        self.save.assert_not_called()
        self.assertFalse(service._MEMORY)

    def test_failed_persistence_does_not_publish_or_cache_a_score(self):
        self.save.side_effect = CacheUnavailable("write cannot be confirmed")
        with self.assertRaises(CacheUnavailable):
            service.run_matching(OFFER)
        self.assertFalse(service._MEMORY)
        self.assertFalse(self.store)
        self.generate.assert_called_once()
        self.save.assert_called_once()

    def test_context_changes_select_new_evaluation_keys(self):
        baseline = service._context(deepcopy(self.status), deepcopy(self.config))
        first = service.evaluation_key(OFFER, baseline, "fr")
        variants = [
            ("implementation", "code-b"), ("reference", "reference-b"),
            ("corpus", "corpus-b"), ("experience", "experience-b"),
            ("as_of", "2026-10-01"), ("scoring", "scoring-b"),
            ("assessment", "assessment-b"), ("extraction", "extraction-b"),
            ("service", "service-b"),
        ]
        for field, value in variants:
            with self.subTest(field=field):
                context = deepcopy(baseline)
                context[field] = value
                self.assertNotEqual(first, service.evaluation_key(OFFER, context, "fr"))
        for field, value in (("model", "different-model"), ("temp_matching", .4),
                             ("max_tokens_matching", 3000)):
            with self.subTest(config=field):
                context = deepcopy(baseline)
                context["model_config"][field] = value
                self.assertNotEqual(first, service.evaluation_key(OFFER, context, "fr"))
        self.assertNotEqual(first, service.evaluation_key(OFFER, baseline, "en"))
        numeric = OFFER + "\nExpérience minimale de 10 ans."
        self.assertNotEqual(service.evaluation_key(numeric, baseline, "fr"),
                            service.evaluation_key(numeric.replace("10 ans", "15 ans"), baseline, "fr"))

    def test_runtime_model_profile_code_and_language_changes_reassess(self):
        results = [service.run_matching(OFFER)]
        self.config["model"] = "another-model"
        results.append(service.run_matching(OFFER))
        self.status["fingerprint"] = "corpus-b"
        results.append(service.run_matching(OFFER))
        self.code.return_value = "code-b"
        results.append(service.run_matching(OFFER))
        results.append(service.run_matching(OFFER, language="en"))
        self.assertEqual(len({r["metrics"]["evaluation_key"] for r in results}), 5)
        self.assertEqual(self.generate.call_count, 5)

    def test_same_month_reuses_original_evaluation_but_new_month_reassesses(self):
        first = service.run_matching(OFFER)
        self.clear_memory()
        self.status.update(as_of="2026-09-29", reference_fingerprint="daily-reference-b")
        later = service.run_matching(OFFER)
        self.assertEqual(later["metrics"]["evaluation_key"], first["metrics"]["evaluation_key"])
        self.assertEqual(later["matching"]["evaluated_at"], first["matching"]["evaluated_at"])
        self.assertEqual(later["matching"]["as_of"], "2026-09-13")
        self.generate.assert_called_once()
        self.status.update(as_of="2026-10-01", reference_fingerprint="daily-reference-c")
        next_month = service.run_matching(OFFER)
        self.assertNotEqual(next_month["metrics"]["evaluation_key"], first["metrics"]["evaluation_key"])
        self.assertEqual(self.generate.call_count, 2)

    def test_pitch_can_change_draft_without_reassessing_or_overwriting_email(self):
        email = service.run_matching(OFFER)
        pitch = service.run_matching(OFFER, response_type="pitch")
        email_again = service.run_matching(OFFER)
        self.assertEqual(pitch["response"], "Mon pitch.")
        self.assertEqual(pitch["matching"]["requirements"], email["matching"]["requirements"])
        self.assertEqual(pitch["matching"]["score_global"], email["matching"]["score_global"])
        self.assertEqual(email_again["response"], email["response"])
        self.assertEqual(pitch["metrics"]["tokens_input"], METRICS["tokens_input"])
        self.assertEqual(pitch["metrics"]["cout_usd"], METRICS["cout_usd"])
        self.generate.assert_called_once_with(OFFER, "email", language="fr")
        self.draft.assert_called_once()
        self.save.assert_called_once()

    def test_corrupt_snapshot_is_refused_without_new_generation(self):
        service.run_matching(OFFER)
        key, original = next(iter(self.store.items()))
        variants = {
            "key": lambda s: s.update(key="0" * 64),
            "context": lambda s: s["context"].update(reference="wrong-reference"),
            "version": lambda s: s.update(version="future-schema"),
            "language": lambda s: s.update(language="en"),
            "score": lambda s: s["result"]["matching"].update(score_global=99),
            "row mismatch": lambda s: s["result"]["matching"]["requirements"][0].update(text="Invented criterion"),
            "non-array rows": lambda s: s["result"]["matching"].update(requirements=None),
            "non-object row": lambda s: s["result"]["matching"]["requirements"].__setitem__(0, None),
            "invalid evidence ids": lambda s: s["result"]["matching"]["requirements"][0].update(evidence_ids=None),
            "missing timestamp": lambda s: s.pop("created_at"),
        }
        for name, corrupt in variants.items():
            with self.subTest(corruption=name):
                self.clear_memory()
                snapshot = deepcopy(original)
                corrupt(snapshot)
                self.store[key] = snapshot
                self.generate.reset_mock()
                self.save.reset_mock()
                with self.assertRaises(CacheUnavailable):
                    service.run_matching(OFFER)
                self.generate.assert_not_called()
                self.save.assert_not_called()
                self.assertFalse(service._MEMORY)

    def test_cached_direct_without_proof_and_partial_without_anchored_gap_are_refused(self):
        service.run_matching(OFFER)
        key, original = next(iter(self.store.items()))
        for corruption in ("direct without proof", "partial without gap"):
            with self.subTest(corruption=corruption):
                self.clear_memory()
                snapshot = deepcopy(original)
                matching = snapshot["result"]["matching"]
                row = matching["requirements"][0]
                if corruption == "direct without proof":
                    row["evidence_ids"] = []
                else:
                    row.update(status="partial", uncovered_aspects=[])
                matching["score_global"] = agent._compute_score(matching["requirements"])
                self.store[key] = snapshot
                self.generate.reset_mock()
                with self.assertRaises(CacheUnavailable):
                    service.run_matching(OFFER)
                self.generate.assert_not_called()
                self.assertFalse(service._MEMORY)

    def test_known_source_from_another_criterion_cannot_be_injected_into_cache(self):
        service.run_matching(OFFER)
        self.clear_memory()
        key, snapshot = next(iter(self.store.items()))
        snapshot["result"]["matching"]["requirements"][0]["evidence_ids"] = ["C02"]
        other = {"id": "C02", "text": "Une preuve pour un autre besoin.", "metadata": {}}
        self.evidence.side_effect = lambda ids: [deepcopy(EVIDENCE if i == "C01" else other) for i in ids]
        self.generate.reset_mock()
        with self.assertRaises(CacheUnavailable):
            service.run_matching(OFFER)
        self.generate.assert_not_called()
        self.assertFalse(service._MEMORY)

    def test_sources_are_compacted_then_hydrated_from_same_corpus(self):
        first = service.run_matching(OFFER)
        snapshot = next(iter(self.store.values()))
        self.assertNotIn("profile_context", snapshot["result"])
        self.assertTrue(all("evidence" not in r for r in snapshot["result"]["matching"]["requirements"]))
        self.assertEqual(first["matching"]["requirements"][0]["evidence"], [EVIDENCE])
        self.assertEqual(first["profile_context"]["R001"], [EVIDENCE])
        self.clear_memory()
        self.evidence.return_value = []
        self.evidence.side_effect = None
        with self.assertRaises(CacheUnavailable):
            service.run_matching(OFFER)
        self.generate.assert_called_once()

    def test_cache_reuses_original_candidate_set_without_semantic_or_lexical_search(self):
        self.retrieval.side_effect = AssertionError("Cache restoration must never run retrieval")
        with patch.object(agent, "search_matching_evidence", side_effect=AssertionError("No hybrid search on cache restoration")):
            first = service.run_matching(OFFER)
            self.clear_memory()
            repeated = service.run_matching(OFFER)
        self.assertEqual(repeated["matching"]["requirements"], first["matching"]["requirements"])
        saved = next(iter(self.store.values()))["result"]
        self.assertEqual(saved["candidate_evidence_ids"], {"R001": ["C01"], "R002": ["C01"], "R003": []})
        self.generate.assert_called_once()

    def test_forged_or_missing_review_and_prerequisite_metadata_is_not_reused(self):
        service.run_matching(OFFER)
        key, original = next(iter(self.store.items()))
        variants = {
            "missing review": lambda m: m["requirements"][2].pop("review"),
            "missing review status": lambda m: m["requirements"][2].pop("review_status"),
            "new review version": lambda m: m["requirements"][2]["review"].update(version="future"),
            "second verdict changed": lambda m: m["requirements"][2]["review"]["second"].update(status="direct"),
            "initial source invented": lambda m: m["requirements"][2]["review"]["initial"].update(evidence_ids=["C01"]),
            "invented blocker": lambda m: m["requirements"][0].update(critical=True, critical_quote="obligatoire"),
            "invented blocker summary": lambda m: m.update(prerequisites=[{"text": "Invented"}]),
        }
        for name, corrupt in variants.items():
            with self.subTest(corruption=name):
                self.clear_memory()
                snapshot = deepcopy(original)
                corrupt(snapshot["result"]["matching"])
                self.store[key] = snapshot
                self.generate.reset_mock()
                with self.assertRaises(CacheUnavailable):
                    service.run_matching(OFFER)
                self.generate.assert_not_called()

    def test_failed_review_is_not_persisted_and_can_be_retried(self):
        failed = assessment()
        failed["matching"]["requirements"][2].update(review_status="unavailable", assessment_valid=False)
        failed["matching"] = agent._summarize_matching(failed["matching"]["requirements"])
        self.generate.side_effect = [failed, assessment()]
        result = service.run_matching(OFFER)
        self.assertIsNone(result["matching"]["score_global"])
        self.save.assert_not_called()
        self.assertFalse(service._MEMORY)
        second = service.run_matching(OFFER)
        self.assertIsInstance(second["matching"]["score_global"], int)
        self.save.assert_called_once()

    def test_disputed_review_reuses_validated_uncertainty_with_both_judgments(self):
        generated = assessment()
        requirement = generated["job_analysis"]["requirements"][0]
        sources = generated["profile_context"][requirement["id"]]
        initial = agent._validate_judgment(requirement, {
            "requirement_id": requirement["id"], "status": "unknown", "evidence_ids": [],
            "justification": "Je dois préciser mon rôle."}, sources)
        second = generated["matching"]["requirements"][0]
        generated["matching"]["requirements"][0] = agent._apply_review(initial, second)
        generated["matching"] = agent._summarize_matching(generated["matching"]["requirements"])
        self.generate.side_effect = None
        self.generate.return_value = generated
        first = service.run_matching(OFFER)
        self.clear_memory()
        repeated = service.run_matching(OFFER)
        row = repeated["matching"]["requirements"][0]
        self.assertEqual(row["review_status"], "disputed")
        self.assertEqual(row["status"], "unknown")
        self.assertEqual(row, first["matching"]["requirements"][0])
        self.assertEqual(row["review"]["initial"]["status"], "unknown")
        self.assertEqual(row["review"]["second"]["status"], "direct")
        self.generate.assert_called_once()

    def test_reuse_has_zero_model_cost_and_tokens_with_evaluation_provenance(self):
        first = service.run_matching(OFFER)
        self.assertEqual(first["metrics"]["tokens_input"], 100)
        for restart in (False, True):
            with self.subTest(restart=restart):
                if restart:
                    self.clear_memory()
                result = service.run_matching(OFFER)
                for counter in ("tokens_input", "tokens_output", "cout_usd", "latence_ms"):
                    self.assertEqual(result["metrics"][counter], 0)
                self.assertEqual(result["metrics"]["model"], "test-model")
                self.assertEqual(result["metrics"]["reference_fingerprint"], "reference-a")
                self.assertEqual(result["metrics"]["evaluation_key"], first["metrics"]["evaluation_key"])
        self.generate.assert_called_once()

    def test_returned_objects_cannot_mutate_the_canonical_artifact(self):
        first = service.run_matching(OFFER)
        expected = deepcopy(first)
        first["matching"]["requirements"][0]["justification"] = "Mutated reason"
        first["matching"]["requirements"][0]["evidence"][0]["metadata"]["sources"].append("FAKE")
        first["job_analysis"]["requirements"][0]["text"] = "Mutated offer"
        first["profile_context"]["R001"][0]["text"] = "Mutated source"
        first["response"] = "Mutated draft"
        repeated = service.run_matching(OFFER)
        for field in ("job_analysis", "profile_context", "response"):
            self.assertEqual(repeated[field], expected[field])
        self.assertEqual(repeated["matching"]["requirements"], expected["matching"]["requirements"])
        self.clear_memory()
        restored = service.run_matching(OFFER)
        self.assertEqual(restored["matching"]["requirements"], expected["matching"]["requirements"])

    def test_profile_or_config_change_during_generation_blocks_persistence(self):
        for change in ("profile", "config"):
            with self.subTest(change=change):
                self.clear_memory()
                self.store.clear()
                self.save.reset_mock()

                def generate_with_change(job, *_args, **_kwargs):
                    if change == "profile":
                        self.status["fingerprint"] += "-changed"
                    else:
                        self.config["model"] += "-changed"
                    return assessment(job)

                self.generate.side_effect = generate_with_change
                with self.assertRaises(CacheUnavailable):
                    service.run_matching(OFFER)
                self.save.assert_not_called()
                self.assertFalse(service._MEMORY)


if __name__ == "__main__":
    unittest.main()
