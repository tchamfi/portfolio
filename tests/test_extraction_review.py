"""Redundancy-audit boundaries, not a claim of live semantic correctness."""
from copy import deepcopy
import json
import unittest
from unittest.mock import Mock

import extraction_review as review


def row(identifier, text, **extra):
    return {"id": identifier, "text": text, "importance": "required", "kind": "skill",
            "critical": False, "critical_ambiguity": False, **extra}


def absorption(rows, remove="R2", keep="R1", **extra):
    by_id = {r["id"]: r for r in rows}
    return {"remove_id": remove, "keep_id": keep,
            "reason": "La formulation conservée couvre la même capacité et toutes ses contraintes.",
            "removed_quote": by_id[remove]["text"], "kept_quote": by_id[keep]["text"], **extra}


def audit(*items):
    return {"version": review.EXTRACTION_REVIEW_VERSION, "absorptions": list(items)}


class ExtractionReviewTests(unittest.TestCase):
    def test_retains_original_broader_source_without_rewriting_or_renumbering(self):
        rows = [row("R001", "Il est responsable du Product Backlog. Il s’assure que la direction métier prise est la bonne, les priorités respectées suivant un critère de valeur métier, et que la qualité des livrables de chaque cycle agile est en adéquation avec les attentes du métier."),
                row("R002", "Roadmap produit : Plan stratégique décrivant les évolutions du produit sur le long terme."),
                row("R006", "Gestion de backlog : Capacité à définir, prioriser et gérer le backlog produit de manière efficace.")]
        original = deepcopy(rows)
        item = absorption(rows, "R006", "R001")
        provider = Mock(return_value=(json.dumps({"absorptions": [item]}), {"tokens_input": 80, "cout_usd": .02}))
        kept, trace, metrics = review.review_extraction(rows, "test", provider)
        self.assertEqual(kept, [original[0], original[1]])
        self.assertEqual(rows, original)
        self.assertEqual(trace, audit(item))
        self.assertEqual(metrics["tokens_input"], 80)
        self.assertEqual(metrics["extraction_review_calls"], 1)
        self.assertEqual(review.validate_extraction_review(original, trace), kept)

    def test_empty_audit_keeps_every_original_criterion(self):
        rows = [row("R1", "Administration avancée de Jira"), row("R2", "Gestion du backlog produit")]
        provider = Mock(return_value=('{"absorptions":[]}', {}))
        kept, trace, _ = review.review_extraction(rows, "test", provider)
        self.assertEqual(kept, rows)
        self.assertEqual(trace, audit())

    def test_single_and_empty_lists_do_not_call_provider(self):
        provider = Mock(side_effect=AssertionError("No paid call"))
        for rows in ([], [row("R1", "Scrum")]):
            kept, trace, metrics = review.review_extraction(rows, "test", provider)
            self.assertEqual(kept, rows)
            self.assertEqual(trace, audit())
            self.assertEqual(metrics["extraction_review_calls"], 0)
        provider.assert_not_called()

    def test_profile_scores_and_evidence_are_never_sent_to_reviewer(self):
        rows = [row("R1", "Gestion de projet", score=100, status="direct", profile="SECRET", evidence=["PRIVATE"]),
                row("R2", "Gestion du produit")]
        provider = Mock(return_value=('{"absorptions":[]}', {}))
        review.review_extraction(rows, "test", provider)
        payload = json.loads(provider.call_args.kwargs["user_content"])
        self.assertNotIn("score", payload["requirements"][0])
        self.assertNotIn("status", payload["requirements"][0])
        self.assertNotIn("SECRET", provider.call_args.kwargs["user_content"])
        self.assertNotIn("PRIVATE", provider.call_args.kwargs["user_content"])

    def test_unknown_ids_partial_removed_quote_or_invented_kept_quote_are_rejected(self):
        rows = [row("R1", "Gestion du backlog produit complet"), row("R2", "Priorisation du backlog produit")]
        item = absorption(rows)
        changes = [{"remove_id": "UNKNOWN"}, {"keep_id": "UNKNOWN"}, {"keep_id": "R2"},
                   {"removed_quote": "Priorisation"}, {"kept_quote": "Texte totalement inventé"},
                   {"kept_quote": "du"}, {"reason": ""}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(review.ExtractionReviewError):
                review.validate_extraction_review(rows, audit({**item, **change}))

    def test_different_importance_kind_or_critical_conditions_are_preserved(self):
        for difference in ({"importance": "optional"}, {"kind": "constraint"},
                           {"critical": True}, {"critical_ambiguity": True}):
            rows = [row("R1", "Gestion du backlog produit complet"), row("R2", "Gestion du backlog produit", **difference)]
            with self.subTest(difference=difference), self.assertRaises(review.ExtractionReviewError):
                review.validate_extraction_review(rows, audit(absorption(rows)))

    def test_additional_numeric_values_cannot_disappear(self):
        rows = [row("R1", "Coordination de 2 équipes"), row("R2", "Coordination de 3 équipes")]
        with self.assertRaises(review.ExtractionReviewError):
            review.validate_extraction_review(rows, audit(absorption(rows)))

    def test_explicit_tools_and_certifications_cannot_disappear(self):
        pairs = [("Utilisation de Jira", "Utilisation de Jira et Trello"),
                 ("Certification AWS", "Certification CKA"),
                 ("Tests d'API", "Tests avec SoapUI"),
                 ("Trello", "Jira")]
        for kept, removed in pairs:
            rows = [row("R1", kept), row("R2", removed)]
            with self.subTest(kept=kept, removed=removed), self.assertRaises(review.ExtractionReviewError):
                review.validate_extraction_review(rows, audit(absorption(rows)))

    def test_named_tokens_are_compared_case_insensitively_without_substring_matches(self):
        rows = [row("R1", "Maîtrise de jira et trello"), row("R2", "Utilisation de Jira")]
        self.assertEqual(review.validate_extraction_review(rows, audit(absorption(rows))), [rows[0]])
        rows[0]["text"] = "Maîtrise de JiraServiceManagement"
        with self.assertRaises(review.ExtractionReviewError):
            review.validate_extraction_review(rows, audit(absorption(rows)))

    def test_observed_user_testing_requirement_is_not_absorbed_by_release_acceptance(self):
        rows = [row("R1", "Validation des livrables : Évaluation et acceptation des fonctionnalités développées avant leur mise en production."),
                row("R2", "Tests et validation : Compétences pour participer aux tests utilisateurs et valider les livrables avant leur lancement.")]
        with self.assertRaisesRegex(review.ExtractionReviewError, "tests utilisateurs"):
            review.validate_extraction_review(rows, audit(absorption(rows)))

    def test_explicit_stakeholders_and_technical_test_scopes_cannot_disappear(self):
        pairs = [("Tests frontend", "Tests frontend et backend"),
                 ("Frontend tests", "Frontend and backend tests"),
                 ("Accept release features", "Participate in user testing and accept release features"),
                 ("Tests des fonctionnalités", "Tests de sécurité des fonctionnalités"),
                 ("Tests des fonctionnalités", "Tests de performance des fonctionnalités"),
                 ("Tests des fonctionnalités", "Tests d'accessibilité des fonctionnalités"),
                 ("Tests des fonctionnalités", "Tests automatisés des fonctionnalités"),
                 ("Suivi des parties prenantes", "Suivi des clients et parties prenantes")]
        for kept, removed in pairs:
            rows = [row("R1", kept), row("R2", removed)]
            with self.subTest(kept=kept, removed=removed), self.assertRaises(review.ExtractionReviewError):
                review.validate_extraction_review(rows, audit(absorption(rows)))

    def test_shared_explicit_scopes_remain_eligible_for_true_redundancy(self):
        rows = [row("R1", "Tests frontend et backend avant livraison"), row("R2", "Tests backend")]
        self.assertEqual(review.validate_extraction_review(rows, audit(absorption(rows))), [rows[0]])

    def test_one_repair_restores_user_testing_without_rewriting_criteria(self):
        rows = [row("R1", "Validation des livrables : Évaluation et acceptation des fonctionnalités développées avant leur mise en production."),
                row("R2", "Tests et validation : Compétences pour participer aux tests utilisateurs et valider les livrables avant leur lancement.")]
        invalid = json.dumps({"absorptions": [absorption(rows)]})
        provider = Mock(side_effect=[(invalid, {"tokens_input": 80}), ('{"absorptions":[]}', {"tokens_input": 30})])
        kept, trace, metrics = review.review_extraction(rows, "test", provider)
        self.assertEqual(kept, rows)
        self.assertEqual(trace, audit())
        self.assertEqual(metrics["tokens_input"], 110)
        self.assertEqual(metrics["extraction_review_calls"], 2)
        payload = json.loads(provider.call_args.kwargs["user_content"])
        self.assertEqual(payload["requirements"], rows)
        self.assertIn("tests utilisateurs", payload["validation_feedback"])

    def test_repeated_scope_loss_after_repair_still_fails_closed(self):
        rows = [row("R1", "Tests frontend"), row("R2", "Tests frontend et backend")]
        invalid = json.dumps({"absorptions": [absorption(rows)]})
        provider = Mock(return_value=(invalid, {"tokens_input": 40}))
        with self.assertRaises(review.ExtractionReviewError) as raised:
            review.review_extraction(rows, "test", provider)
        self.assertEqual(provider.call_count, 2)
        self.assertEqual(raised.exception.metrics["tokens_input"], 80)

    def test_experience_duration_and_scope_cannot_disappear(self):
        exp = {"minimum_years": 5, "scope": "product_owner", "scope_text": "comme Product Owner"}
        for change in ({"minimum_years": 10}, {"scope": "data_product_owner"}, {"scope_text": "comme Product Owner data"}):
            rows = [row("R1", "5 ans comme Product Owner", kind="experience", experience=exp),
                    row("R2", "5 ans comme Product Owner data", kind="experience", experience={**exp, **change})]
            with self.subTest(change=change), self.assertRaises(review.ExtractionReviewError):
                review.validate_extraction_review(rows, audit(absorption(rows)))

    def test_language_and_proficiency_cannot_disappear(self):
        language = {"name": "anglais", "level": "B2"}
        for change in ({"name": "espagnol"}, {"level": "C1"}, {"level": None}):
            rows = [row("R1", "Anglais niveau B2", kind="language", language=language),
                    row("R2", "Compétence linguistique demandée", kind="language", language={**language, **change})]
            with self.subTest(change=change), self.assertRaises(review.ExtractionReviewError):
                review.validate_extraction_review(rows, audit(absorption(rows)))

    def test_cycles_chains_and_duplicate_removals_are_rejected(self):
        rows = [row(f"R{i}", "Gestion du backlog produit") for i in range(1, 4)]
        combinations = [
            [absorption(rows, "R1", "R2"), absorption(rows, "R2", "R1")],
            [absorption(rows, "R1", "R2"), absorption(rows, "R2", "R3")],
            [absorption(rows, "R1", "R2"), absorption(rows, "R1", "R3")],
        ]
        for items in combinations:
            with self.subTest(items=items), self.assertRaises(review.ExtractionReviewError):
                review.validate_extraction_review(rows, audit(*items))

    def test_multiple_distinct_rows_can_be_absorbed_into_one_survivor(self):
        rows = [row(f"R{i}", "Gestion du backlog produit") for i in range(1, 4)]
        kept = review.validate_extraction_review(rows, audit(absorption(rows, "R2", "R1"), absorption(rows, "R3", "R1")))
        self.assertEqual(kept, [rows[0]])

    def test_invalid_provider_output_fails_closed_and_retains_usage(self):
        rows = [row("R1", "Gestion du backlog produit"), row("R2", "Gestion du produit")]
        invalid = ["invalid JSON", '{"absorptions":[],"absorptions":[]}', '{"rewritten_requirements":[]}',
                   '{"absorptions":[{"remove_id":"R2"}]}']
        for raw in invalid:
            provider = Mock(return_value=(raw, {"tokens_input": 50}))
            with self.subTest(raw=raw), self.assertRaises(review.ExtractionReviewError) as raised:
                review.review_extraction(rows, "test", provider)
            self.assertEqual(raised.exception.metrics["tokens_input"], 100)
            self.assertEqual(provider.call_count, 2)

    def test_provider_error_is_not_silently_accepted_as_empty_audit(self):
        rows = [row("R1", "Gestion du backlog produit"), row("R2", "Gestion du produit")]
        provider = Mock(side_effect=RuntimeError("API failure"))
        with self.assertRaises(review.ExtractionReviewError):
            review.review_extraction(rows, "test", provider)


if __name__ == "__main__":
    unittest.main()
