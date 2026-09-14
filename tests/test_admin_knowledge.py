"""Exercise the owner's knowledge publication UI with storage/LLM boundaries stubbed."""

from contextlib import ExitStack
from copy import deepcopy
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import admin_knowledge as admin
import knowledge_store as store
import rag_pipeline as rag


FACT_ID = "K6a6972610001"
FACT = {
    "id": FACT_ID, "revision": "a" * 32, "state": "published",
    "updated_at": "2026-09-14T09:00:00+00:00", "has_published_version": True,
    "title": "Jira", "kind": "tool", "practice": "professional",
    "companies": ["GRDF", "BNP Paribas Personal Finance"],
    "statement": "J’ai utilisé Jira chez GRDF et je l’utilise chez BNP Paribas Personal Finance.",
    "period": "", "limits": "Administration avancée non précisée.",
    "keywords": ["Jira"], "correction_of": "", "correction_quote": "",
}
BASE = {"id": "C01", "text": "[C01] Backlog\nJ’ai piloté le backlog produit.",
        "metadata": {"title": "Backlog", "knowledge_version": "V3.0"}}


class KnowledgeAdminTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.facts = []
        self.history = []
        self.published = []
        self.list_facts = self.stub(store, "list_facts", side_effect=lambda **_: deepcopy(self.facts))
        self.get_history = self.stub(store, "get_history", side_effect=lambda *_: deepcopy(self.history))
        self.save = self.stub(store, "save_draft", side_effect=self._save)
        self.publish = self.stub(store, "publish_fact", side_effect=self._publish)
        self.archive = self.stub(store, "archive_fact", side_effect=self._archive)
        self.restore = self.stub(store, "restore_fact", side_effect=self._restore)
        self.stub(store, "published_snapshot", side_effect=lambda **_: {"facts": deepcopy(self.published)})
        self.stub(rag, "published_snapshot", side_effect=lambda **_: {"facts": deepcopy(self.published)})
        self.stub(rag, "load_documents_as_chunks", return_value=[deepcopy(BASE)])
        self.validate = self.stub(admin, "validate_knowledge_publication", wraps=rag.validate_knowledge_publication)
        self.status = self.stub(admin, "get_knowledge_status", return_value={"fingerprint": "published"})
        self.search = self.stub(admin, "search_evidence", return_value=[])
        self.ask = self.stub(admin, "ask", return_value=("J’ai utilisé Jira chez GRDF.", {"evidence_ids": [FACT_ID]}))
        self.hydrate = self.stub(admin, "get_evidence_by_ids", return_value=[])

    def stub(self, target, name, **kwargs):
        return self.stack.enter_context(patch.object(target, name, **kwargs))

    def _save(self, fields, fact_id=None, expected_revision=None):
        business = store._business(fields)
        row = {**business, "id": fact_id or FACT_ID, "revision": "b" * 32,
               "state": "draft", "has_published_version": bool(self.published)}
        self.facts = [deepcopy(row)]
        return deepcopy(row)

    def _publish(self, fact_id, expected_revision=None):
        self.facts[0].update(state="published", revision="c" * 32, has_published_version=True)
        self.published = deepcopy(self.facts)
        return deepcopy(self.facts[0])

    def _archive(self, fact_id, expected_revision=None):
        self.facts[0].update(state="archived", revision="d" * 32, has_published_version=False)
        self.published = []
        return deepcopy(self.facts[0])

    def _restore(self, fact_id, revision, expected_revision=None):
        restored = next(deepcopy(row) for row in self.history if row["revision"] == revision)
        restored.update(state="draft", revision="e" * 32, has_published_version=bool(self.published))
        self.facts = [restored]
        return deepcopy(restored)

    def app(self, private=True, correction=None):
        if correction is None:
            code = "from admin_knowledge import render_knowledge_admin\nrender_knowledge_admin()"
        else:
            code = ("import streamlit as st\nfrom admin_knowledge import render_correction_form\n"
                    "render_correction_form(st.session_state['requirement'])")
        app = AppTest.from_string(code, default_timeout=10)
        app.session_state["is_private"] = private
        if correction is not None:
            app.session_state["requirement"] = deepcopy(correction)
        return self.rerun(app)

    def rerun(self, app):
        app.run()
        self.assertEqual(list(app.exception), [])
        return app

    @staticmethod
    def widget(app, collection, label):
        return next(item for item in getattr(app, collection) if item.label == label)

    def click(self, app, label):
        self.widget(app, "button", label).click()
        return self.rerun(app)

    def fill_new(self, app):
        self.widget(app, "text_input", "Compétence, outil ou réalisation").set_value("Jira")
        self.widget(app, "text_input", "Entreprises concernées (séparées par des virgules)").set_value("GRDF, BNP Paribas Personal Finance")
        self.widget(app, "text_area", "Ce que j’ai personnellement fait").set_value(FACT["statement"])
        self.widget(app, "selectbox", "Nature de la pratique").select("professional")

    def select_existing(self, app):
        app.selectbox(key="knowledge_selected").select(FACT_ID)
        return self.rerun(app)

    def test_public_session_has_no_editor_correction_or_storage_access(self):
        for correction in (None, {"requirement_id": "R001", "text": "Jira"}):
            with self.subTest(correction=correction):
                app = self.app(private=False, correction=correction)
                self.assertFalse(app.button)
                self.assertFalse(app.text_input)
                self.assertFalse(app.text_area)
        self.list_facts.assert_not_called()
        self.save.assert_not_called()
        self.publish.assert_not_called()

    def test_new_preview_passes_real_id_and_factual_validation_without_saving(self):
        app = self.app()
        self.fill_new(app)
        self.click(app, "Voir l’aperçu")
        self.assertFalse(app.error)
        self.assertTrue(any(FACT["statement"] == text.value for text in app.text))
        self.assertTrue(any("Contribution attribuée à Lionel" in text.value for text in app.text))
        candidate = self.validate.call_args.args[0]
        self.assertRegex(candidate["id"], r"^K[0-9a-f]{12}$")
        self.assertEqual(candidate["practice"], "professional")
        self.save.assert_not_called()
        self.publish.assert_not_called()

    def test_new_draft_stays_private_and_preserves_current_matching(self):
        app = self.app()
        app.session_state["agent_results"] = {"matching": {"score_global": 79}}
        self.fill_new(app)
        self.click(app, "Enregistrer le brouillon")
        self.save.assert_called_once()
        self.assertEqual(self.save.call_args.kwargs, {"fact_id": None, "expected_revision": None})
        self.assertEqual(self.save.call_args.args[0]["companies"], FACT["companies"])
        self.publish.assert_not_called()
        self.assertFalse(self.published)
        self.assertEqual(app.session_state["agent_results"]["matching"]["score_global"], 79)
        self.assertTrue(any("Brouillon enregistré" in message.value for message in app.success))
        self.assertEqual(app.selectbox(key="knowledge_selected").value, FACT_ID)

    def test_new_publish_validates_saves_then_publishes_saved_revision_and_clears_old_result(self):
        app = self.app()
        app.session_state["agent_results"] = {"matching": {"score_global": 79}}
        app.session_state["knowledge_test_result"] = {"question": "Old", "evidence": [], "answer": "Old"}
        self.fill_new(app)
        self.click(app, "Enregistrer et publier")
        self.assertEqual(self.validate.call_count, 2)
        self.assertEqual(self.validate.call_args_list[1].args[0]["id"], FACT_ID)
        self.assertEqual(self.validate.call_args_list[1].kwargs["published_facts"], [])
        self.save.assert_called_once()
        self.publish.assert_called_once_with(FACT_ID, expected_revision="b" * 32)
        self.assertEqual(self.published[0]["statement"], FACT["statement"])
        self.assertNotIn("agent_results", app.session_state)
        self.assertNotIn("knowledge_test_result", app.session_state)
        self.assertTrue(any("Connaissance publiée" in message.value for message in app.success))
        self.assertEqual(app.selectbox(key="knowledge_selected").value, FACT_ID)
        self.status.assert_called_once()

    def test_editing_published_fact_only_creates_draft_and_explains_previous_version_remains_active(self):
        self.facts = [deepcopy(FACT)]
        self.published = deepcopy(self.facts)
        app = self.select_existing(self.app())
        revised = "J’ai utilisé Jira pour le backlog chez GRDF et BNP Paribas Personal Finance."
        self.widget(app, "text_area", "Ce que j’ai personnellement fait").set_value(revised)
        self.click(app, "Enregistrer le brouillon")
        self.save.assert_called_once()
        self.assertEqual(self.save.call_args.kwargs, {"fact_id": FACT_ID, "expected_revision": FACT["revision"]})
        self.assertEqual(self.published[0]["statement"], FACT["statement"])
        self.assertEqual(self.facts[0]["statement"], revised)
        self.assertTrue(any("dernière version publiée reste utilisée" in message.value for message in app.info))
        self.publish.assert_not_called()

    def test_archive_clears_displayed_results_and_restore_prepares_unpublished_draft(self):
        self.facts = [deepcopy(FACT)]
        self.published = deepcopy(self.facts)
        self.history = deepcopy(self.facts)
        app = self.select_existing(self.app())
        app.session_state["agent_results"] = {"matching": {"score_global": 79}}
        self.click(app, "Archiver cette fiche")
        self.archive.assert_called_once_with(FACT_ID, expected_revision=FACT["revision"])
        self.assertFalse(self.published)
        self.assertNotIn("agent_results", app.session_state)
        self.assertTrue(any("Fiche archivée" in message.value for message in app.success))
        self.click(app, "Restaurer cette version en brouillon")
        self.restore.assert_called_once_with(FACT_ID, FACT["revision"], expected_revision="d" * 32)
        self.assertEqual(self.facts[0]["state"], "draft")
        self.assertFalse(self.published)
        self.assertTrue(any("Version restaurée en brouillon" in message.value for message in app.success))
        self.publish.assert_not_called()

    def test_failed_publication_reports_no_success_and_keeps_previous_matching(self):
        app = self.app()
        app.session_state["agent_results"] = {"matching": {"score_global": 79}}
        self.fill_new(app)
        self.publish.side_effect = store.KnowledgeError("Private Airtable response and token", "K503")
        self.click(app, "Enregistrer et publier")
        self.assertTrue(any("K503" in message.value for message in app.error))
        self.assertFalse(app.success)
        self.assertNotIn("Private Airtable", " ".join(message.value for message in app.error))
        self.assertEqual(app.session_state["agent_results"]["matching"]["score_global"], 79)
        self.assertEqual(self.facts[0]["state"], "draft")
        self.assertFalse(self.published)

    def test_invalid_empty_fact_is_not_saved_or_published(self):
        app = self.app()
        self.click(app, "Enregistrer et publier")
        self.assertTrue(app.error)
        self.assertFalse(app.success)
        self.save.assert_not_called()
        self.publish.assert_not_called()

    def test_invalid_correction_quote_is_rejected_before_writing(self):
        app = self.app()
        self.fill_new(app)
        self.widget(app, "text_input", "Référence de la fiche à corriger").set_value("C01")
        self.widget(app, "text_area", "Passage exact à remplacer").set_value("Ce passage ne figure pas dans la source.")
        self.click(app, "Enregistrer et publier")
        self.assertTrue(app.error)
        self.assertFalse(app.success)
        self.save.assert_not_called()
        self.publish.assert_not_called()

    def test_publication_conflict_after_draft_save_prevents_publishing(self):
        app = self.app()
        self.fill_new(app)
        self.validate.side_effect = [{"text": "Preview accepted"}, ValueError("Deux corrections actives se chevauchent.")]
        self.click(app, "Enregistrer et publier")
        self.save.assert_called_once()
        self.publish.assert_not_called()
        self.assertTrue(app.error)
        self.assertFalse(app.success)
        self.assertEqual(self.facts[0]["state"], "draft")

    def test_effective_corpus_failure_after_publication_does_not_claim_success(self):
        app = self.app()
        self.fill_new(app)
        self.status.side_effect = RuntimeError("private diagnostic")
        self.click(app, "Enregistrer et publier")
        self.publish.assert_called_once()
        self.assertTrue(app.error)
        self.assertFalse(app.success)
        self.assertNotIn("private diagnostic", " ".join(message.value for message in app.error))

    def test_answer_inspection_shows_actual_answer_evidence_not_separate_search_hits(self):
        self.search.return_value = [deepcopy(BASE)]
        actual = {"id": FACT_ID, "text": "Jira utilisé chez GRDF et BNP Paribas Personal Finance.",
                  "metadata": {"title": "Jira"}}
        self.hydrate.return_value = [actual]
        app = self.app()
        self.click(app, "Tester la réponse IA")
        self.ask.assert_called_once_with("Quels outils Agile ai-je utilisés, et dans quelles entreprises ?", language="fr")
        self.hydrate.assert_called_once_with([FACT_ID])
        self.assertEqual(app.session_state["knowledge_test_result"]["evidence"], [actual])
        self.assertTrue(any(actual["text"] == text.value for text in app.text))
        self.assertFalse(any(BASE["text"] == text.value for text in app.text))
        self.save.assert_not_called()
        self.publish.assert_not_called()

    def test_search_inspection_does_not_call_language_model(self):
        self.search.return_value = [deepcopy(BASE)]
        app = self.app()
        self.click(app, "Voir les informations retrouvées")
        self.ask.assert_not_called()
        self.hydrate.assert_not_called()
        self.assertTrue(any(BASE["text"] == text.value for text in app.text))

    def test_private_matching_correction_only_saves_draft_and_keeps_score(self):
        requirement = {"requirement_id": "R001", "text": "Maîtrise Jira", "status": "unknown"}
        app = self.app(correction=requirement)
        app.session_state["agent_results"] = {"matching": {"score_global": 79, "requirements": [requirement]}}
        self.widget(app, "text_area", "Ma précision factuelle").set_value(FACT["statement"])
        self.widget(app, "text_input", "Entreprises (séparées par des virgules)").set_value("GRDF, BNP Paribas Personal Finance")
        self.click(app, "Enregistrer en brouillon")
        self.save.assert_called_once()
        payload = self.save.call_args.args[0]
        self.assertEqual(payload["statement"], FACT["statement"])
        self.assertEqual(payload["companies"], FACT["companies"])
        self.assertEqual(payload["practice"], "unspecified")
        self.assertEqual(payload["correction_of"], "")
        self.assertEqual(app.session_state["agent_results"]["matching"]["score_global"], 79)
        self.assertTrue(any("Brouillon enregistré" in message.value for message in app.success))
        self.publish.assert_not_called()

    def test_correction_input_does_not_leak_into_another_offer_with_same_requirement_id(self):
        app = self.app(correction={"requirement_id": "R001", "text": "Maîtrise Jira"})
        self.widget(app, "text_area", "Ma précision factuelle").set_value(FACT["statement"])
        self.rerun(app)
        app.session_state["requirement"] = {"requirement_id": "R001", "text": "Certification CKA"}
        self.rerun(app)
        self.assertEqual(self.widget(app, "text_area", "Ma précision factuelle").value, "")
        self.save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
