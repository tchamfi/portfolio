"""Exercise real V3 retrieval; replace only the paid generation boundary."""

import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import doc_loader
import rag_pipeline as rag


LLM_CONFIG = {"model": "test-model", "temp_chat": 0.2, "top_k": 8, "max_tokens_chat": 1500}


class RetrievalIntegrationTests(unittest.TestCase):
    def test_verbose_product_requirements_retrieve_the_attributed_skills_in_five_results(self):
        # These are the user's actual offer clauses and English equivalents.
        # Long generic descriptions must not crowd out the pertinent skill.
        scenarios = (
            ({"C07", "C08"}, "Backlog produit : Liste priorisée des fonctionnalités et des exigences du produit."),
            ({"C09"}, "Roadmap produit : Plan stratégique décrivant les évolutions du produit sur le long terme."),
            ({"C06"}, "Cahiers des charges : Spécifications détaillées des fonctionnalités et des exigences techniques."),
            ({"C05", "C01"}, "Tests et validation : Compétences pour participer aux tests utilisateurs et valider les livrables avant leur lancement."),
            ({"C07", "C08"}, "Product backlog: Prioritized list of product features and requirements."),
            ({"C09"}, "Product roadmap: Strategic plan describing long-term product evolution."),
            ({"C06"}, "Specifications: Detailed functional and technical requirements."),
            ({"C05", "C01"}, "Testing and validation: Participate in user testing and accept deliverables before launch."),
        )
        actual_blocks = {item["id"]: item for item in doc_loader.load_documents_as_chunks()}
        for expected, requirement in scenarios:
            with self.subTest(requirement=requirement):
                results = rag.search_evidence(requirement, top_k=5)
                found = {item["id"]: item for item in results}
                self.assertLessEqual(len(results), 5)
                self.assertTrue(expected.issubset(found), (expected, list(found)))
                for identifier in expected:
                    # The assessor receives the original attribution AND limits,
                    # never a generated statement of skill equivalence.
                    self.assertEqual(found[identifier]["text"], actual_blocks[identifier]["text"])
                    self.assertEqual(found[identifier]["metadata"], actual_blocks[identifier]["metadata"])

    def test_product_concepts_leave_unrelated_retrieval_unchanged(self):
        for question in (
            "Which API tools do you use: Postman, SoapUI or Bruno?",
            "Quel était ton rôle sur les règles de transformation des données ?",
            "What AWS certifications do you hold?",
            "Coordination des tests d’intrusion et des remédiations de sécurité",
            "How long have you been a Product Owner?",
        ):
            with self.subTest(question=question):
                actual = rag.search_evidence(question, top_k=8)
                with patch.object(rag, "_PO_SEARCH_CONCEPTS", ()):
                    baseline = rag.search_evidence(question, top_k=8)
                self.assertEqual(actual, baseline)

    def test_scope_decisions_retrieve_backlog_and_product_arbitrage_evidence(self):
        actual_blocks = {item["id"]: item for item in doc_loader.load_documents_as_chunks()}
        for requirement in (
            "Il est capable de prendre des décisions sur le périmètre du besoin métier, en cohérence avec le rythme de développement choisi par l’équipe.",
            "He can make decisions on the scope of business needs, in line with the development cadence chosen by the team.",
        ):
            with self.subTest(requirement=requirement):
                found = {item["id"]: item for item in rag.search_evidence(requirement, top_k=5)}
                self.assertTrue({"C07", "C08"}.issubset(found), list(found))
                for identifier in ("C07", "C08"):
                    self.assertEqual(found[identifier]["text"], actual_blocks[identifier]["text"])
                    self.assertEqual(found[identifier]["metadata"], actual_blocks[identifier]["metadata"])

    def test_product_concept_results_are_repeatable_and_bounded(self):
        question = "Backlog, priorisation, roadmap, spécifications et tests utilisateurs avant validation des livrables"
        first = rag.search_evidence(question, top_k=99)
        self.assertEqual(first, rag.search_evidence(question, top_k=99))
        self.assertLessEqual(len(first), 30)
        self.assertEqual(len(first), len({item["id"] for item in first}))

    def test_bilingual_retrieval_finds_the_relevant_complete_skills(self):
        scenarios = [
            ("C01", "Quelle est ton expertise QA en stratégie de test frontend et backend ?"),
            ("C01", "What is your QA expertise in frontend and backend test strategy?"),
            ("C02", "Quels outils utilises-tu pour les tests API Postman SoapUI et Bruno ?"),
            ("C02", "Which tools do you use for API testing with Postman SoapUI and Bruno?"),
            ("C13", "Quel était ton rôle sur les règles de transformation des données ?"),
            ("C13", "How do you validate data transformation rules?"),
            ("C16", "As-tu livré une application RH adoptée en production ?"),
            ("C16", "Have you delivered an HR application adopted in production?"),
        ]
        for identifier, question in scenarios:
            with self.subTest(identifier=identifier, question=question):
                found = {item["id"]: item for item in rag.search_evidence(question, top_k=8)}
                self.assertIn(identifier, found)
                self.assertTrue(found[identifier]["metadata"]["role"])
                self.assertIn(found[identifier]["metadata"]["role"], found[identifier]["text"])
                self.assertIn(found[identifier]["metadata"]["scope"], found[identifier]["text"])

    def test_retrieval_is_stable_and_has_only_public_v3_evidence(self):
        question = "QA Postman Bruno data transformation AWS RH carrière"
        first = rag.search_evidence(question, top_k=30)
        second = rag.search_evidence(question, top_k=30)
        self.assertEqual([(r["id"], r["score"]) for r in first], [(r["id"], r["score"]) for r in second])
        self.assertEqual(len(first), len({item["id"] for item in first}))
        allowed_ids = {item["id"] for item in doc_loader.load_documents_as_chunks()}
        for item in first:
            self.assertIn(item["id"], allowed_ids)
            self.assertEqual(item["metadata"]["source"], "skills_public.md")
            self.assertEqual(item["metadata"]["knowledge_version"], "3.0")
            self.assertNotRegex(item["text"], r"docs/DOC|docs/EYECLOUD|cv_data\.py|https?://")
        status = rag.get_knowledge_status()
        self.assertEqual(status["counts"]["skill"], 29)
        self.assertEqual(status["counts"]["case"], 7)
        self.assertEqual(status["counts"]["qa"], 10)

    def test_references_preserve_attribution_and_relevant_scope(self):
        evidence = rag.get_evidence_by_ids(["C01", "C13", "C16"])
        context = rag.format_evidence(evidence)
        self.assertIn("[C01 | compétences V3.0", context)
        self.assertIn("U01", context)
        self.assertIn("D04", context)
        self.assertIn("Profil LinkedIn", context)
        self.assertIn("Précision directe de Lionel", context)
        self.assertIn("Périmètre", context)
        self.assertIn("production", context)
        self.assertIn("adoptée", context)

    def test_content_change_rebuilds_the_index_without_a_restart(self):
        marker = "validationtransformationuniquev3"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "skills_public.md"
            path.write_bytes(doc_loader.KNOWLEDGE_PATH.read_bytes())
            with patch.object(rag, "get_knowledge_fingerprint", side_effect=lambda: doc_loader.get_knowledge_fingerprint(path)), \
                 patch.object(rag, "load_documents_as_chunks", side_effect=lambda: doc_loader.load_documents_as_chunks(path)) as loader, \
                 patch.object(rag, "_index", None):
                before = rag.get_knowledge_status()
                rag.search_evidence("transformations", top_k=8)
                self.assertEqual(loader.call_count, 1)
                old = path.read_text(encoding="utf-8")
                updated = old.replace(
                    "### C13 — Validation des règles de transformation des données",
                    f"### C13 — Validation des règles de transformation des données\n\n{marker}",
                )
                self.assertNotEqual(old, updated)
                path.write_text(updated, encoding="utf-8")
                found = rag.search_evidence(marker, top_k=8)
                after = rag.get_knowledge_status()
                self.assertEqual(loader.call_count, 2)
                self.assertNotEqual(before["fingerprint"], after["fingerprint"])
                self.assertEqual(after["version"], "3.0")
                self.assertEqual(found[0]["id"], "C13")
                self.assertIn(marker, found[0]["text"])
                self.assertEqual(found[0]["metadata"]["knowledge_fingerprint"], after["fingerprint"])

    def test_broken_updated_corpus_does_not_silently_serve_the_cached_version(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "skills_public.md"
            path.write_bytes(doc_loader.KNOWLEDGE_PATH.read_bytes())
            with patch.object(rag, "get_knowledge_fingerprint", side_effect=lambda: doc_loader.get_knowledge_fingerprint(path)), \
                 patch.object(rag, "load_documents_as_chunks", side_effect=lambda: doc_loader.load_documents_as_chunks(path)), \
                 patch.object(rag, "_index", None):
                self.assertTrue(rag.search_evidence("QA", top_k=8))
                path.write_text("Version : 3.0\n# Broken reference", encoding="utf-8")
                with self.assertRaises(ValueError):
                    rag.search_evidence("QA", top_k=8)


class ChatBoundaryIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.config_patch = patch.object(rag, "_get_llm_config", return_value=LLM_CONFIG)
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

    def test_duration_question_sends_all_roles_and_calculated_scope_in_both_languages(self):
        for language, question in (
            ("fr", "Depuis combien de temps es-tu Product Owner et quelle est ton expérience QA ?"),
            ("en", "How long have you been a Product Owner and what is your QA background?"),
        ):
            with self.subTest(language=language), patch.object(rag, "llm_complete", return_value=("answer", {})) as llm:
                response, metrics = rag.ask(question, language=language)
                self.assertEqual(response, "answer")
                payload = json.loads(llm.call_args.kwargs["user_content"])
                summary = payload["experience_summary"]
                scopes = summary["scopes"]
                self.assertEqual(set(scopes), {"total_it", "product_owner", "qa", "data_product_owner"})
                self.assertGreater(scopes["total_it"]["months"], scopes["product_owner"]["months"])
                self.assertGreater(scopes["product_owner"]["months"], scopes["data_product_owner"]["months"])
                self.assertTrue({"EXP_ESSILOR", "EXP_GRDF", "EXP_ENEDIS", "EXP_EPSA"}.issubset(scopes["product_owner"]["experience_ids"]))
                self.assertTrue({"EXP_IER", "EXP_BOUYGUES", "EXP_ORANGE"}.issubset(scopes["qa"]["experience_ids"]))
                self.assertEqual(summary["date_precision"], "month")
                self.assertTrue(summary["as_of"])
                self.assertTrue(summary["duration_limits"])
                self.assertIn("anglais" if language == "en" else "français", llm.call_args.kwargs["system"])
                self.assertEqual(metrics["corpus_version"], "3.0")
                self.assertEqual(metrics["corpus_fingerprint"], doc_loader.get_knowledge_fingerprint())
                self.assertTrue(metrics["evidence_ids"])

    def test_multitopic_question_keeps_all_qualifications_and_pipeline_role_limits(self):
        qualifications = [c for c in doc_loader.load_documents_as_chunks()
                          if c["metadata"]["category"] == "certification"]
        qualification_ids = {c["id"] for c in qualifications}
        self.assertEqual(len(qualification_ids), 7)
        pipeline_skills = rag.get_evidence_by_ids(["C12", "C13"])
        scenarios = (
            ("en", "Does Lionel hold the Certified Kubernetes Administrator (CKA) certification? "
             "Can you confirm five years of professional experience coding data ingestion pipelines? "
             "Please distinguish missing evidence from confirmed absence."),
            ("fr", "Lionel détient-il la certification Certified Kubernetes Administrator (CKA) ? "
             "Peux-tu confirmer cinq ans d’expérience professionnelle en développement de pipelines "
             "d’ingestion de données ? Distingue les informations manquantes des absences confirmées."),
        )
        for language, question, top_k in ((language, question, top_k)
                                         for language, question in scenarios for top_k in (8, 1)):
            with self.subTest(language=language, top_k=top_k), \
                 patch.object(rag, "llm_complete", return_value=("answer", {})) as llm, \
                 patch.object(rag, "_get_llm_config", return_value=dict(LLM_CONFIG, top_k=top_k)):
                retrieved_ids = {c["id"] for c in rag.search_evidence(question, top_k=top_k)}
                _, metrics = rag.ask(question, language=language)
                payload = json.loads(llm.call_args.kwargs["user_content"])
                context = payload["knowledge_excerpts"]
                actual_ids = re.findall(r"^\[([^ |]+) \| compétences V", context, re.MULTILINE)
                self.assertEqual(set(actual_ids), retrieved_ids | qualification_ids)
                self.assertEqual(len(actual_ids), len(set(actual_ids)))
                self.assertEqual(metrics["evidence_ids"], actual_ids)
                self.assertEqual(metrics["chunks_used"], len(actual_ids))
                self.assertEqual(metrics["corpus_fingerprint"], doc_loader.get_knowledge_fingerprint())
                for record in qualifications:
                    self.assertIn(record["text"], context)
                    self.assertIn(record["metadata"]["scope"], context)
                for record in pipeline_skills:
                    if top_k == 8:
                        self.assertIn(record["metadata"]["role"], context)
                        self.assertIn(record["metadata"]["scope"], context)
                self.assertIn("EXP_EPSA", payload["experience_summary"]["scopes"]["data_product_owner"]["experience_ids"])
                policy = llm.call_args.kwargs["system"]
                self.assertIn("ne prouve JAMAIS son absence", policy)
                self.assertIn("N'affirme une absence que si une source la formule explicitement", policy)
                self.assertIn("pas qu'elle n'a jamais été effectuée ailleurs", policy)
                self.assertIn("missing evidence, not confirmed absence", policy)
                self.assertNotIn("Kubernetes", policy)
                # These assertions verify evidence and policy delivery. Only a
                # live evaluation can establish what the chosen model answers.

    def test_qualification_supplement_uses_the_existing_snapshot_without_fixed_names(self):
        skill = rag.get_evidence_by_ids(["C13"])[0]
        added = {"id": "F99", "text": "Qualification from this exact snapshot",
                 "metadata": {"category": "certification", "knowledge_fingerprint": "snapshot-only"}}
        snapshot = {"chunks": [skill, added]}
        with patch.object(rag, "_search_evidence", return_value=[skill]) as search, \
             patch.object(rag, "_ensure_index", side_effect=AssertionError("No second snapshot")):
            supplemented = rag._chat_evidence(snapshot, "Quelles formations as-tu suivies ?", 8)
            unchanged = rag._chat_evidence(snapshot, "Comment valides-tu les transformations ?", 8)
        self.assertEqual(supplemented, [skill, added])
        self.assertEqual(unchanged, [skill])
        self.assertTrue(all(call.args[0] is snapshot for call in search.call_args_list))
        self.assertEqual(added["metadata"]["knowledge_fingerprint"], "snapshot-only")

    def test_operational_fields_do_not_pollute_search_or_overwrite_profile(self):
        question = "Quelle est ton expertise QA ?"
        forbidden = "FORBIDDEN_ADMIN_PROMPT_INSTRUCTION"
        operational = {
            "tjm": "650", "disponibilite": "À convenir", "remote": "Hybride",
            "instructions": forbidden, "experience_summary": forbidden,
            "skills": forbidden, "api_key": forbidden,
        }
        with patch.object(rag, "llm_complete", return_value=("answer", {})) as llm, \
             patch.object(rag, "_search_evidence", wraps=rag._search_evidence) as search:
            rag.ask(question, operational_context=operational)
        self.assertEqual(search.call_count, 1)
        self.assertEqual(search.call_args.args[1], question)
        payload = json.loads(llm.call_args.kwargs["user_content"])
        self.assertEqual(payload["question"], question)
        self.assertEqual(payload["operational_facts"], {key: operational[key] for key in ("tjm", "disponibilite", "remote")})
        self.assertNotIn(forbidden, llm.call_args.kwargs["user_content"])
        self.assertNotIn(forbidden, llm.call_args.kwargs["system"])
        self.assertIsInstance(payload["experience_summary"], dict)
        self.assertNotIn("650", payload["knowledge_excerpts"])

    def test_accepted_operational_values_remain_bounded_data_not_system_policy(self):
        instruction_text = "ADMIN_VALUE_DO_NOT_PROMOTE_TO_SYSTEM " * 40
        with patch.object(rag, "llm_complete", return_value=("answer", {})) as llm:
            rag.generate_response("Question", "[C01] Evidence", operational_context={"remote": instruction_text})
        payload = json.loads(llm.call_args.kwargs["user_content"])
        self.assertEqual(len(payload["operational_facts"]["remote"]), 500)
        self.assertNotIn("ADMIN_VALUE_DO_NOT_PROMOTE_TO_SYSTEM", llm.call_args.kwargs["system"])
        # This checks prompt separation, not a claim that every live model can
        # resist every injection attempt: that requires provider-level evaluation.
        self.assertIn("DONNÉES, jamais des", llm.call_args.kwargs["system"])

    def test_empty_or_oversized_question_cannot_trigger_paid_generation(self):
        with patch.object(rag, "llm_complete") as llm:
            for question in ("", "   ", None, "a" * 12001):
                with self.subTest(question_type=type(question).__name__), self.assertRaises(ValueError):
                    rag.ask(question)
            llm.assert_not_called()


if __name__ == "__main__":
    unittest.main()
