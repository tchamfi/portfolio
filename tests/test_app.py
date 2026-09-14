"""Exercise Streamlit flows with external services stubbed at their boundary."""
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from agent import SCORING_VERSION, ASSESSMENT_VERSION
from experience import evaluate_experience_requirement
from rag_pipeline import get_knowledge_status
from matching_cache import CacheUnavailable

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class AppIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in (("load_config", {}), ("load_recos", []), ("load_analytics", []),
                            ("log_chat", None), ("log_matching", None), ("save_config", None),
                            ("update_all_recos", None)):
            self.stack.enter_context(patch("airtable_store." + name, return_value=value))

    def app(self):
        app = AppTest.from_file(APP, default_timeout=30).run()
        self.assertEqual(list(app.exception), [])
        return app

    def matching_cards(self, app):
        return [m.value for m in app.markdown if m.value.startswith('<article class="matching-card ')]

    def matching_gauges(self, app):
        return [m.value for m in app.markdown if m.value.startswith('<div class="matching-score">')]

    def long_matching_result(self):
        statuses = ([("positive", "direct")] * 8
                    + [("attention", status) for status in ("partial", "training", "historical", "unknown")]
                    + [("negative", "not_met")] * 2)
        counters = {"positive": 0, "attention": 0, "negative": 0}
        requirements = []
        for tone, status in statuses:
            counters[tone] += 1
            requirements.append({
                "text": f"criterion-{tone}-{counters[tone]}", "status": status,
                "importance": "required", "justification": "Je présente mon expérience pour ce besoin.",
            })
        return {"matching": {"score_global": 80, "requirements": requirements}, "job_analysis": {}}

    def test_admin_displays_actual_corpus_and_scoped_durations(self):
        app = self.app()
        app.session_state["admin_view"] = True
        app.session_state["is_private"] = True
        app.run()
        self.assertEqual(list(app.exception), [])
        self.assertTrue(app.dataframe)
        self.assertFalse(any(widget.key == "a_annees_exp" for widget in app.number_input))
        self.assertFalse(any(widget.key == "llm_sev" for widget in app.selectbox))
        self.assertTrue(any("compétences" in m.value for m in app.markdown))
        self.assertTrue(any(tab.label == "🧠 Connaissances IA" for tab in app.tabs))

    def test_knowledge_failure_keeps_admin_reachable_and_removes_old_score(self):
        app = self.app()
        app.session_state["agent_results"] = self.long_matching_result()
        with patch("rag_pipeline.get_knowledge_status", side_effect=ValueError("Invalid correction")):
            app.run()
            self.assertEqual(list(app.exception), [])
            self.assertNotIn("agent_results", app.session_state)
            self.assertTrue(any("temporairement indisponible" in e.value for e in app.error))
            app.session_state["is_private"] = True
            app.session_state["admin_view"] = True
            app.run()
            self.assertEqual(list(app.exception), [])
            self.assertTrue(any(tab.label == "🧠 Connaissances IA" for tab in app.tabs))

    def test_admin_view_alone_does_not_grant_private_editing(self):
        app = self.app()
        app.session_state["admin_view"] = True
        app.run()
        self.assertEqual(list(app.exception), [])
        self.assertFalse(any(tab.label == "🧠 Connaissances IA" for tab in app.tabs))
        self.assertFalse(any(button.key == "a_save" for button in app.button))

    def test_prerequisite_visible_at_high_score_and_disagreement_needs_review(self):
        app = self.app()
        app.session_state["current_tab"] = "matching"
        row = {"requirement_id": "R001", "text": "Certification obligatoire", "status": "unknown",
               "review_status": "disputed", "importance": "required", "justification": "Je dois préciser ce point."}
        app.session_state["agent_results"] = {"matching": {"score_global": 95, "requirements": [row],
            "prerequisites": [dict(row, state="to_review")]}}
        app.run()
        self.assertEqual(list(app.exception), [])
        self.assertIn("95/100", self.matching_gauges(app)[0])
        self.assertTrue(any("1 à clarifier" in e.value for e in app.warning))
        self.assertIn("À vérifier", self.matching_cards(app)[0])
        self.assertFalse(any(e.label == "Signaler une correction" for e in app.expander))
        app.session_state["is_private"] = True
        app.run()
        self.assertEqual(list(app.exception), [])
        self.assertTrue(any(e.label == "Signaler une correction" for e in app.expander))

    def test_high_score_does_not_hide_unknown_requirement(self):
        app = self.app()
        app.session_state["current_tab"] = "matching"
        app.session_state["agent_results"] = {
            "matching": {"score_global": 95, "scoring_version": SCORING_VERSION,
                "points_forts": ["Expertise QA"], "points_attention": ["Durée avec Bruno à préciser"],
                "requirements": [{"requirement_id": "R001", "text": "3 ans avec Bruno", "status": "unknown",
                                  "importance": "required", "evidence_ids": ["C02"],
                                  "justification": "Outil pratiqué ; durée non précisée."}]},
            "response": "draft", "metrics": {}, "job_analysis": {},
        }
        app.run()
        self.assertEqual(list(app.exception), [])
        card = self.matching_cards(app)[0]
        self.assertIn("Bruno", card)
        self.assertIn("À préciser", card)
        self.assertNotIn("Non satisfait", card)
        self.assertTrue(any("Points d’attention" in m.value for m in app.markdown))
        self.assertIn("95/100", self.matching_gauges(app)[0])

    def test_empty_matching_does_not_show_a_perfect_score(self):
        app = self.app()
        app.session_state["current_tab"] = "matching"
        app.session_state["agent_results"] = {"matching": {"score_global": None, "requirements": []}, "job_analysis": {}}
        app.run()
        self.assertEqual(list(app.exception), [])
        self.assertFalse(app.metric)
        self.assertFalse(self.matching_gauges(app))
        self.assertTrue(any("Aucune exigence" in m.value for m in app.info))

    def test_single_criterion_uses_first_person_and_keeps_sources_private(self):
        check = evaluate_experience_requirement(10, "product_owner", as_of="2026-09-13")
        for language in ("fr", "en"):
            with self.subTest(language=language):
                app = self.app()
                if language == "en":
                    app.radio(key="lang_radio").set_value("EN").run()
                app.session_state["current_tab"] = "matching"
                app.session_state["agent_results"] = {"matching": {"score_global": 100,
                    "requirements": [{"requirement_id": "R001", "text": "10 years as Product Owner",
                        "status": "direct", "importance": "required", "evidence_ids": [],
                        "justification": check["reason"], "experience_check": check}]}}
                app.run()
                self.assertEqual(list(app.exception), [])
                self.assertIn("100/100", self.matching_gauges(app)[0])
                self.assertIn("1 criterion" if language == "en" else "1 critère", self.matching_gauges(app)[0])
                self.assertTrue(any(("full job description" if language == "en" else "fiche de poste complète") in c.value for c in app.caption))
                summary = self.matching_cards(app)[0]
                self.assertNotIn("R001", summary)
                self.assertIn("I have about" if language == "en" else "J’ai environ", summary)
                self.assertIn("10 years and 5 months" if language == "en" else "10 ans et 5 mois", summary)
                self.assertNotIn("union des mois", summary)
                sources_label = "Sources and scoring method" if language == "en" else "Sources et méthode de calcul"
                self.assertFalse(any(e.label == sources_label for e in app.expander))
                self.assertFalse(any(check["reason"] in m.value for m in app.markdown))
                app.session_state["is_private"] = True
                app.run()
                self.assertEqual(list(app.exception), [])
                sources = next(e for e in app.expander if e.label == sources_label)
                self.assertTrue(any(check["reason"] in m.value for m in sources.markdown))
                self.assertTrue(sources.json)

    def test_short_tenure_explanation_preserves_uncertainty_at_a_boundary(self):
        check = evaluate_experience_requirement(125 / 12, "product_owner", as_of="2026-09-13")
        self.assertEqual(check["status"], "unknown")
        app = self.app()
        app.session_state["current_tab"] = "matching"
        app.session_state["agent_results"] = {"matching": {"score_global": 0,
            "requirements": [{"requirement_id": "R001", "text": "Ancienneté minimale",
                "status": "unknown", "importance": "required", "evidence_ids": [],
                "justification": check["reason"], "experience_check": check}]}}
        app.run()
        self.assertEqual(list(app.exception), [])
        summary = self.matching_cards(app)[0]
        self.assertIn("À préciser", summary)
        self.assertIn("Je dois encore préciser les dates exactes", summary)
        self.assertNotIn("Je couvre donc", summary)

    def test_cards_escape_offer_and_model_markup_and_keep_unknown_separate_from_gap(self):
        app = self.app()
        app.session_state["current_tab"] = "matching"
        app.session_state["agent_results"] = {"matching": {"score_global": 0, "requirements": [
            {"text": '<img src=x onerror="alert(1)">', "status": "not_met", "importance": "required",
             "justification": '<script>alert("model")</script>'},
            {"text": "Certification CKA", "status": "unknown", "importance": "optional",
             "justification": "Je ne peux pas confirmer cette certification."}]}}
        app.run()
        self.assertEqual(list(app.exception), [])
        cards = self.matching_cards(app)
        gap = next(card for card in cards if 'matching-card negative' in card)
        unknown = next(card for card in cards if 'matching-card attention' in card)
        self.assertIn("Non satisfait", gap)
        self.assertIn("&lt;img", gap)
        self.assertIn("&lt;script&gt;", gap)
        self.assertNotIn("<img", gap)
        self.assertNotIn("<script", gap)
        self.assertIn("À préciser", unknown)
        self.assertIn("Optionnel", unknown)
        self.assertNotIn("Non satisfait", unknown)

    def test_matching_categories_paginate_every_point_without_another_analysis(self):
        app = self.app()
        app.session_state["current_tab"] = "matching"
        app.session_state["agent_results"] = self.long_matching_result()
        labels = ["Points forts · 8", "Points d’attention · 4", "Écarts · 2"]

        def cards_in(label):
            tab = next(tab for tab in app.tabs if tab.label == label)
            return self.matching_cards(tab)

        def point_numbers(label, tone):
            return [number for number in range(1, 9)
                    if any(f"criterion-{tone}-{number}</div>" in card for card in cards_in(label))]

        with patch("matching_service.run_matching") as run_matching:
            app.run()
            self.assertEqual(list(app.exception), [])
            self.assertEqual([tab.label for tab in app.tabs], labels)
            self.assertEqual(point_numbers(labels[0], "positive"), [1, 2, 3])
            self.assertEqual(point_numbers(labels[1], "attention"), [1, 2, 3])
            self.assertEqual(point_numbers(labels[2], "negative"), [1, 2])
            self.assertTrue(app.button(key="matching_page_positive_prev").disabled)
            self.assertTrue(app.button(key="matching_page_attention_prev").disabled)
            self.assertFalse(any(b.key == "matching_page_negative_next" for b in app.button))
            self.assertTrue(any(c.value == "Points 1–3 sur 8" for c in app.caption))

            # Each point appears on exactly one page, including the short last page.
            positive_points = point_numbers(labels[0], "positive")
            for expected in ([4, 5, 6], [7, 8]):
                app.button(key="matching_page_positive_next").click().run()
                self.assertEqual(list(app.exception), [])
                self.assertEqual(point_numbers(labels[0], "positive"), expected)
                positive_points.extend(point_numbers(labels[0], "positive"))
                self.assertEqual(point_numbers(labels[1], "attention"), [1, 2, 3])
                self.assertIn("80/100", self.matching_gauges(app)[0])
            self.assertEqual(positive_points, list(range(1, 9)))
            self.assertTrue(app.button(key="matching_page_positive_next").disabled)
            self.assertTrue(any(c.value == "Points 7–8 sur 8" for c in app.caption))

            app.button(key="matching_page_attention_next").click().run()
            self.assertEqual(point_numbers(labels[1], "attention"), [4])
            self.assertIn("À préciser", cards_in(labels[1])[0])
            self.assertNotIn("Non satisfait", cards_in(labels[1])[0])
            self.assertTrue(app.button(key="matching_page_attention_next").disabled)
            self.assertEqual(point_numbers(labels[0], "positive"), [7, 8])
            self.assertEqual(point_numbers(labels[2], "negative"), [1, 2])

            # Going backwards affects only the selected category and reaches page one.
            for expected in ([4, 5, 6], [1, 2, 3]):
                app.button(key="matching_page_positive_prev").click().run()
                self.assertEqual(point_numbers(labels[0], "positive"), expected)
                self.assertEqual(point_numbers(labels[1], "attention"), [4])
            self.assertTrue(app.button(key="matching_page_positive_prev").disabled)
            app.button(key="matching_page_attention_prev").click().run()
            self.assertEqual(point_numbers(labels[1], "attention"), [1, 2, 3])
            self.assertTrue(app.button(key="matching_page_attention_prev").disabled)
            self.assertEqual(list(app.exception), [])
            run_matching.assert_not_called()

    def test_matching_pages_persist_for_same_result_and_reset_for_a_new_result(self):
        app = self.app()
        app.session_state["current_tab"] = "matching"
        result = self.long_matching_result()
        app.session_state["agent_results"] = result
        with patch("matching_service.run_matching") as run_matching:
            app.run()
            app.button(key="matching_page_positive_next").click().run()
            app.button(key="matching_page_positive_next").click().run()
            app.button(key="matching_page_attention_next").click().run()

            app.session_state["agent_results"] = deepcopy(result)
            app.run()
            self.assertEqual(app.session_state["matching_page_positive"], 2)
            self.assertEqual(app.session_state["matching_page_attention"], 1)
            self.assertTrue(any("criterion-positive-7</div>" in card for card in self.matching_cards(app)))

            updated = deepcopy(result)
            updated["matching"]["requirements"][0]["text"] = "Nouveau besoin métier"
            app.session_state["agent_results"] = updated
            app.run()
            self.assertEqual(list(app.exception), [])
            self.assertEqual(app.session_state["matching_page_positive"], 0)
            self.assertEqual(app.session_state["matching_page_attention"], 0)
            self.assertTrue(any("Nouveau besoin métier" in card for card in self.matching_cards(app)))
            self.assertTrue(any("criterion-attention-1</div>" in card for card in self.matching_cards(app)))
            run_matching.assert_not_called()

    def test_matching_categories_and_page_ranges_are_translated_and_include_empty_groups(self):
        app = self.app()
        app.radio(key="lang_radio").set_value("EN").run()
        app.session_state["current_tab"] = "matching"
        result = self.long_matching_result()
        result["matching"]["requirements"] = result["matching"]["requirements"][:8]
        app.session_state["agent_results"] = result
        app.run()
        self.assertEqual(list(app.exception), [])
        self.assertEqual([tab.label for tab in app.tabs], ["Strengths · 8", "Points to consider · 0", "Gaps · 0"])
        self.assertTrue(any(c.value == "Points 1–3 of 8" for c in app.caption))
        self.assertEqual(len(self.matching_cards(app.tabs[0])), 3)
        for tab in app.tabs[1:]:
            self.assertEqual(self.matching_cards(tab), [])
            self.assertTrue(tab.caption)

    def test_data_tenure_gap_does_not_claim_total_po_tenure_in_first_person(self):
        check = evaluate_experience_requirement(5, "data_product_owner", as_of="2026-09-13")
        self.assertEqual(check["status"], "not_met")
        for language in ("fr", "en"):
            with self.subTest(language=language):
                app = self.app()
                if language == "en":
                    app.radio(key="lang_radio").set_value("EN").run()
                app.session_state["current_tab"] = "matching"
                app.session_state["agent_results"] = {"matching": {"score_global": 0, "requirements": [
                    {"text": "5 years as Data Product Owner", "status": "not_met",
                     "importance": "required", "experience_check": check, "justification": check["reason"]}]}}
                app.run()
                self.assertEqual(list(app.exception), [])
                summary = self.matching_cards(app)[0]
                self.assertIn("I have about 1 year and 2 months" if language == "en"
                              else "J’ai environ 1 an et 2 mois", summary)
                self.assertIn("less than the 5 years" if language == "en"
                              else "moins que les 5 ans", summary)
                self.assertNotIn("10 years" if language == "en" else "10 ans", summary)

    def test_incomplete_offer_is_reported_without_exposing_private_method(self):
        app = self.app()
        app.session_state["current_tab"] = "matching"
        app.session_state["agent_results"] = {"matching": {"score_global": 100, "requirements": [
            {"text": "Backlog", "status": "direct", "importance": "required", "justification": "Je gère le backlog."}]},
            "job_analysis": {"incomplete_excerpts": ["Connaissances techniques : Sensibilisation aux prat"]}}
        app.run()
        self.assertEqual(list(app.exception), [])
        self.assertTrue(any("incomplet" in item.value and "Sensibilisation aux prat" in item.value for item in app.info))
        self.assertFalse(any("Sources et méthode" in item.label for item in app.expander))

    def test_service_error_keeps_private_details_hidden_and_does_not_claim_empty_offer(self):
        app = self.app()
        app.session_state["current_tab"] = "matching"
        app.run()
        app.text_area(key="job_input").set_value("Gestion de backlog")
        with patch("matching_service.run_matching", side_effect=CacheUnavailable("private diagnostic", "M101")):
            next(b for b in app.button if b.label == "Analyser").click().run()
        self.assertEqual(list(app.exception), [])
        warnings = " ".join(w.value for w in app.warning)
        self.assertIn("M101", warnings)
        self.assertNotIn("private diagnostic", warnings)
        self.assertNotIn("Veuillez coller", warnings)
        self.assertFalse(self.matching_gauges(app))

    def test_new_assessment_version_clears_old_result_without_calling_model(self):
        app = self.app()
        app.session_state["current_tab"] = "matching"
        app.session_state["matching_assessment_version"] = "requested-role-v2"
        app.session_state["agent_results"] = {"matching": {"score_global": 100, "requirements": []}}
        with patch("agent.run_agent") as run_agent:
            app.run()
        self.assertEqual(list(app.exception), [])
        self.assertFalse(self.matching_gauges(app))
        self.assertEqual(app.session_state["matching_assessment_version"], ASSESSMENT_VERSION)
        run_agent.assert_not_called()

    def test_chat_passes_question_language_and_business_facts_separately(self):
        app = self.app()
        app.session_state["current_tab"] = "chat"
        app.run()
        app.radio(key="lang_radio").set_value("EN").run()
        with patch("rag_pipeline.ask", return_value=("I have a QA background.", {"corpus_version": "3.0", "chunks_used": 2})) as ask:
            app.text_input(key="chat_typed").set_value("What is your QA experience?")
            submit = next(b for b in app.button if b.label == "↑")
            submit.click().run()
        self.assertEqual(list(app.exception), [])
        self.assertEqual(ask.call_args.args, ("What is your QA experience?",))
        self.assertEqual(ask.call_args.kwargs["language"], "en")
        self.assertEqual(set(ask.call_args.kwargs["operational_context"]), {"tjm", "disponibilite", "remote"})

    def test_failed_assessment_is_unavailable_and_not_zero_match(self):
        app = self.app()
        app.session_state["current_tab"] = "matching"
        app.session_state["agent_results"] = {"matching": {
            "score_global": None, "analysis_unavailable": True,
            "requirements": [{"requirement_id": "R001", "text": "QA", "importance": "required",
                              "status": "unknown", "assessment_valid": False,
                              "justification": "Private validation details", "evidence_ids": []}]}}
        app.run()
        self.assertEqual(list(app.exception), [])
        self.assertFalse(app.metric)
        self.assertFalse(self.matching_gauges(app))
        self.assertNotIn("Private validation details", self.matching_cards(app)[0])
        self.assertTrue(any("indisponible" in m.value for m in app.warning))


if __name__ == "__main__":
    unittest.main()
