"""Exercise Streamlit flows with external services stubbed at their boundary."""
from contextlib import ExitStack
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from agent import SCORING_VERSION
from rag_pipeline import get_knowledge_status

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
        self.assertTrue(any("Bruno" in item.label for item in app.expander))
        self.assertTrue(any("Points d’attention" in m.value for m in app.markdown))
        self.assertEqual(app.metric[0].value, "95/100")

    def test_empty_matching_does_not_show_a_perfect_score(self):
        app = self.app()
        app.session_state["current_tab"] = "matching"
        app.session_state["agent_results"] = {"matching": {"score_global": None, "requirements": []}, "job_analysis": {}}
        app.run()
        self.assertEqual(list(app.exception), [])
        self.assertFalse(app.metric)
        self.assertTrue(any("Aucune exigence" in m.value for m in app.info))

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
                              "status": "unknown", "justification": "Évaluation invalide", "evidence_ids": []}]}}
        app.run()
        self.assertEqual(list(app.exception), [])
        self.assertFalse(app.metric)
        self.assertTrue(any("indisponible" in m.value for m in app.warning))


if __name__ == "__main__":
    unittest.main()
