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

    def test_public_voice_repair_reuses_original_sources_and_counts_both_calls(self):
        question = "Quel est votre expérience sur AWS ?"
        context = rag.format_evidence(rag.get_evidence_by_ids(["C17", "E04"]))
        draft = "Chez EssilorLuxottica, Lionel a piloté l'évolution d'une API vers AWS [C17, E04]."
        answer = "Chez EssilorLuxottica, j'ai piloté l'évolution d'une API vers AWS dans mon rôle de Product Owner."
        first = {"tokens_input": 10, "tokens_output": 20, "cout_usd": .002, "latence_ms": 100}
        second = {"tokens_input": 30, "tokens_output": 40, "cout_usd": .004, "latence_ms": 200}
        with patch.object(rag, "llm_complete", side_effect=[(draft, first), (answer, second)]) as llm:
            response, metrics = rag.generate_response(question, context, operational_context={"remote": "Hybride"})
        self.assertEqual(response, answer)
        self.assertEqual(llm.call_count, 2)
        original, repair = [json.loads(call.kwargs["user_content"]) for call in llm.call_args_list]
        for field in ("question", "knowledge_excerpts", "experience_summary", "operational_facts"):
            self.assertEqual(repair[field], original[field])
        self.assertEqual(repair["knowledge_excerpts"], context)
        self.assertEqual(repair["previous_draft"], draft)
        self.assertNotIn(draft, llm.call_args.kwargs["system"])
        self.assertEqual(metrics["response_review"]["status"], "corrected")
        self.assertEqual(metrics["tokens_input"], 40)
        self.assertEqual(metrics["tokens_output"], 60)
        self.assertAlmostEqual(metrics["cout_usd"], .006)
        self.assertEqual(metrics["latence_ms"], 300)

    def test_repeated_credential_absence_returns_unknown_without_a_third_call(self):
        question = "Détenez-vous la certification AWS Certified Solutions Architect Professional ?"
        draft = "Je ne détiens pas la certification AWS Certified Solutions Architect Professional."
        with patch.object(rag, "llm_complete", return_value=(draft, {})) as llm:
            response, metrics = rag.generate_response(question, "AWS Cloud Practitioner : certification mentionnée.")
        self.assertEqual(llm.call_count, 2)
        self.assertNotIn("ne détiens pas", response)
        self.assertIn("confirmer", response)
        self.assertEqual(metrics["response_review"]["status"], "fallback")
        self.assertIn("credential_absence", metrics["response_review"]["remaining_issues"])

    def test_failed_repair_never_exposes_the_invalid_draft_or_provider_details(self):
        draft = "I do not hold the AWS Certified Solutions Architect Professional certification."
        with patch.object(rag, "llm_complete", side_effect=[(draft, {"tokens_input": 10}),
                RuntimeError("PRIVATE_PROVIDER_DIAGNOSTIC")]) as llm:
            response, metrics = rag.generate_response("Do you hold this AWS certification?", "AWS Cloud Practitioner", language="en")
        self.assertEqual(llm.call_count, 2)
        self.assertIn("confirm", response)
        self.assertNotIn("do not hold", response)
        self.assertNotIn("PRIVATE_PROVIDER_DIAGNOSTIC", response + json.dumps(metrics))
        self.assertEqual(metrics["response_review"]["error"], "Q201")
        self.assertEqual(metrics["tokens_input"], 10)

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


class PublishedKnowledgeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.published = []
        self.snapshot = patch.object(rag, "published_snapshot", side_effect=lambda **_: {
            "facts": self.published, "fingerprint": "store-hash"})
        self.snapshot.start()
        self.addCleanup(self.snapshot.stop)
        self.index = patch.object(rag, "_index", None)
        self.index.start()
        self.addCleanup(self.index.stop)

    def fact(self, **overrides):
        return {"id": "K123456789abc", "title": "Jira", "kind": "tool",
                "companies": ["GRDF", "BNP Paribas Personal Finance"],
                "statement": "J'ai utilisé Jira chez GRDF et BNP Paribas Personal Finance.",
                "practice": "professional", "period": "", "limits": "Administration avancée non précisée.",
                "keywords": ["Jira"], "correction_of": "", "correction_quote": "",
                "source": "Précision confirmée par Lionel", "state": "published", "revision": "first", **overrides}

    def aws_fact(self):
        seeds = json.loads((doc_loader.KNOWLEDGE_PATH.parent / "initial_facts.json").read_text(encoding="utf-8"))
        seed = next(item for item in seeds if item["id"] == "K617773657373")
        return self.fact(id=seed["id"], **seed["fields"])

    def test_aws_publication_enriches_only_its_source_scope_and_preserves_po_attribution(self):
        before_status = rag.get_knowledge_status()
        before = {chunk["id"]: chunk for chunk in rag.get_evidence_by_ids(["C17", "C18"])}
        self.published = [self.aws_fact()]
        fact = self.published[0]
        after_status = rag.get_knowledge_status()
        after = {chunk["id"]: chunk for chunk in rag.get_evidence_by_ids(["C17", "C18", fact["id"]])}
        self.assertNotEqual(before_status["fingerprint"], after_status["fingerprint"])
        self.assertNotEqual(before_status["reference_fingerprint"], after_status["reference_fingerprint"])
        self.assertEqual(before["C18"]["text"], after["C18"]["text"])
        self.assertNotIn(fact["correction_quote"], after["C17"]["text"])
        self.assertIn(fact["statement"], after["C17"]["text"])
        self.assertIn("La roadmap du chantier cloud", after["C17"]["text"])
        self.assertIn("ne pas attribuer un SLA chiffré", after["C17"]["text"])
        self.assertEqual(before["C17"]["metadata"]["role"], after["C17"]["metadata"]["role"])
        self.assertTrue({"L05", "D05", "D07", fact["id"]}.issubset(after["C17"]["metadata"]["source_refs"]))
        self.assertIn(fact["limits"], after[fact["id"]]["text"])
        for term in ("AWS", "EyeCloud", "SSP"):
            self.assertIn(term, fact["statement"][:700])
        for term in ("Angular", "ASP.NET", "EC2", "ASG", "ALB", "API Gateway", "DynamoDB", "S3", "WAF", "PostgreSQL"):
            self.assertIn(term, after[fact["id"]]["text"])

    def test_aws_products_reach_chat_and_matching_as_complete_attributable_evidence(self):
        self.published = [self.aws_fact()]
        fact = self.published[0]
        aws_ids = {"C17", fact["id"]}
        questions = (
            "quel est votre experience sur aws ?",
            "Quelle expérience SSP Angular ASP.NET EC2 ASG ALB ?",
            "EyeCloud API Gateway DynamoDB S3 WAF",
        )
        for question in questions:
            with self.subTest(question=question):
                found = rag.search_evidence(question, top_k=8)
                relevant = [chunk for chunk in found if chunk["id"] in aws_ids]
                self.assertTrue(relevant, [chunk["id"] for chunk in found])
                for chunk in relevant:
                    self.assertIn(fact["statement"], chunk["text"])
                    self.assertIn(fact["id"], chunk["metadata"]["source_refs"])

        def select(**kwargs):
            payload = json.loads(kwargs["user_content"])
            if "catalog" not in payload:
                self.assertIn(fact["statement"], payload["knowledge_excerpts"])
                return "J’ai piloté EyeCloud et SSP, deux produits hébergés sur AWS chez EssilorLuxottica.", {}
            return json.dumps({"results": [{"requirement_id": req["id"],
                                            "evidence_ids": [fact["id"], "C17"]}
                                           for req in payload["requirements"]]}), {"tokens_input": 10}

        with patch.object(rag, "_get_llm_config", return_value=LLM_CONFIG), \
             patch.object(rag, "llm_complete", side_effect=select), \
             patch("hybrid_retrieval.llm_complete", side_effect=select):
            _, chat_metrics = rag.ask(questions[0])
            evidence, matching_metrics = rag.search_matching_evidence(
                [{"id": "R01", "text": "Pilotage de produits AWS avec EC2, ASG, ALB et WAF"}], "test")
        matching_aws = [chunk for chunk in evidence["R01"] if chunk["id"] in aws_ids]
        self.assertTrue(matching_aws)
        for chunk in matching_aws:
            self.assertIn(fact["statement"], chunk["text"])
            self.assertIn(fact["id"], chunk["metadata"]["source_refs"])
        self.assertTrue(aws_ids.intersection(chat_metrics["evidence_ids"]))
        self.assertEqual(chat_metrics["corpus_fingerprint"], matching_metrics["corpus_fingerprint"])

    def test_published_tool_updates_common_corpus_and_both_content_fingerprints(self):
        before = rag.get_knowledge_status()
        self.published = [self.fact()]
        after = rag.get_knowledge_status()
        self.assertNotEqual(before["fingerprint"], after["fingerprint"])
        self.assertNotEqual(before["reference_fingerprint"], after["reference_fingerprint"])
        self.assertEqual(after["published_count"], 1)
        found = rag.search_evidence("Jira GRDF BNP", 5)
        self.assertEqual(found[0]["id"], "K123456789abc")
        self.assertIn("Contribution attribuée à Lionel", found[0]["text"])
        self.assertIn("Administration avancée non précisée", found[0]["text"])
        self.assertIn("Ne pas déduire une durée", found[0]["text"])
        self.assertEqual(found[0]["metadata"]["knowledge_fingerprint"], after["fingerprint"])
        self.assertIn("Précision confirmée par Lionel", rag.format_evidence(found))

    def test_drafts_and_revision_only_edits_do_not_invalidate_factual_results(self):
        baseline = rag.get_knowledge_status()
        self.published = [self.fact(state="draft")]
        self.assertEqual(baseline["fingerprint"], rag.get_knowledge_status()["fingerprint"])
        self.published = [self.fact()]
        first = rag.get_knowledge_status()
        self.published = [self.fact(revision="second", updated_at="later")]
        second = rag.get_knowledge_status()
        self.assertEqual(first["fingerprint"], second["fingerprint"])
        self.assertEqual(first["indexed_at"], second["indexed_at"])

    def test_archiving_removes_facts_without_leaving_stale_retrieval(self):
        baseline = rag.get_knowledge_status()
        self.published = [self.fact()]
        self.assertTrue(rag.get_evidence_by_ids(["K123456789abc"]))
        self.published = []
        self.assertEqual(rag.get_evidence_by_ids(["K123456789abc"]), [])
        self.assertEqual(baseline["fingerprint"], rag.get_knowledge_status()["fingerprint"])

    def test_unavailable_publications_never_silently_return_old_index(self):
        self.published = [self.fact()]
        self.assertTrue(rag.get_evidence_by_ids(["K123456789abc"]))
        with patch.object(rag, "published_snapshot", side_effect=RuntimeError("storage failed")):
            with self.assertRaises(RuntimeError):
                rag.search_evidence("Jira", 5)

    def test_exact_source_correction_preserves_other_facts_and_provenance(self):
        before = {c["id"]: c for c in rag.get_evidence_by_ids(["C13", "C12"])}
        quote = "Lionel s’assure que les règles de transformation attendues sont effectivement implémentées."
        self.published = [self.fact(kind="skill", title="Validation fonctionnelle EPSA",
            statement="Je vérifie l'implémentation des règles métier dans mon rôle de PO data chez EPSA.",
            correction_of="C13", correction_quote=quote)]
        after = {c["id"]: c for c in rag.get_evidence_by_ids(["C13", "C12"])}
        self.assertNotIn(quote, after["C13"]["text"])
        self.assertIn(self.published[0]["statement"], after["C13"]["text"])
        self.assertIn("distincte de l’écriture du code d’ingestion", after["C13"]["text"])
        self.assertIn("Profil LinkedIn, pages 3–4", after["C13"]["text"])
        self.assertEqual(before["C12"]["text"], after["C12"]["text"])
        self.assertIn("K123456789abc", after["C13"]["metadata"]["source_refs"])

    def test_ambiguous_missing_or_overlapping_source_edits_are_rejected(self):
        quote = "Lionel s’assure que les règles de transformation attendues sont effectivement implémentées."
        for source_id, excerpt in (("INVENTED", quote), ("C13", "Not a real citation in this source"),
                                   ("C13", "[C13] Validation des règles de transformation des données")):
            with self.subTest(source_id=source_id, excerpt=excerpt), self.assertRaises(ValueError):
                rag.validate_knowledge_publication(self.fact(correction_of=source_id, correction_quote=excerpt), [])
        first = self.fact(correction_of="C13", correction_quote=quote)
        second = self.fact(id="Kabcdef123456", correction_of="C13", correction_quote=quote)
        with self.assertRaises(ValueError):
            rag.validate_knowledge_publication(second, [first])

    def test_chat_and_matching_use_the_same_published_tool_and_report_retrieval_mode(self):
        self.published = [self.fact()]
        def select(**kwargs):
            payload = json.loads(kwargs["user_content"])
            if "catalog" not in payload:
                return "J'ai utilisé Jira chez GRDF et BNP PF.", {}
            return json.dumps({"results": [{"requirement_id": req["id"], "evidence_ids": ["K123456789abc"]}
                                           for req in payload["requirements"]]}), {"tokens_input": 10}
        with patch.object(rag, "_get_llm_config", return_value=LLM_CONFIG), \
             patch.object(rag, "llm_complete", side_effect=select), \
             patch("hybrid_retrieval.llm_complete", side_effect=select):
            _, chat_metrics = rag.ask("As-tu utilisé Jira ?")
            evidence, matching_metrics = rag.search_matching_evidence([{"id": "R01", "text": "Jira"}], "test")
        self.assertIn("K123456789abc", chat_metrics["evidence_ids"])
        self.assertIn("K123456789abc", {item["id"] for item in evidence["R01"]})
        self.assertEqual(chat_metrics["corpus_fingerprint"], matching_metrics["corpus_fingerprint"])
        self.assertEqual(chat_metrics["retrieval"]["retrieval_mode"], "catalog-hybrid-v1")

    def test_chat_fallback_is_explicit_in_private_metrics(self):
        with patch.object(rag, "_get_llm_config", return_value=LLM_CONFIG), \
             patch.object(rag, "llm_complete", side_effect=[RuntimeError("semantic provider unavailable"), ("answer", {})]):
            answer, metrics = rag.ask("Quelle est ton expertise QA ?")
        self.assertEqual(answer, "answer")
        self.assertEqual(metrics["retrieval"]["retrieval_mode"], "lexical-fallback")
        self.assertEqual(metrics["retrieval"]["retrieval_error"], "R101")


if __name__ == "__main__":
    unittest.main()
