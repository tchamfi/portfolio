"""Editorial lifecycle, stable publication fingerprints and durable write gates."""

from copy import deepcopy
import json
import unittest
from unittest.mock import Mock, patch
import uuid

import requests

import airtable_store
import knowledge_store as ks


class MemoryAirtable:
    def __init__(self):
        self.records = []
        self.page_size = 100
        self.write_records = True
        self.after_write = None
        self.get_params = []

    @staticmethod
    def response(payload):
        response = Mock()
        response.json.return_value = deepcopy(payload)
        return response

    def get(self, url, headers, timeout, params):
        self.get_params.append(deepcopy(params))
        records = [row for row in self.records if row["fields"]["Name"].startswith(ks.KNOWLEDGE_PREFIX)]
        offset = int(params.get("offset", "0"))
        page = records[offset:offset + self.page_size]
        payload = {"records": page}
        if offset + self.page_size < len(records):
            payload["offset"] = str(offset + self.page_size)
        return self.response(payload)

    def post(self, url, headers, timeout, json):
        created = []
        for row in json["records"]:
            record = {"id": "rec" + uuid.uuid4().hex[:14], **deepcopy(row)}
            created.append(record)
            if self.write_records:
                self.records.append(record)
        if self.after_write:
            self.after_write(created)
        return self.response({"records": created})

    def add_event(self, event):
        self.records.append({"id": "rec" + uuid.uuid4().hex[:14], "fields": {
            "Name": ks.KNOWLEDGE_PREFIX + event["id"] + ":" + event["revision"],
            "Notes": json.dumps(event, ensure_ascii=False),
        }})


class KnowledgeStoreTests(unittest.TestCase):
    def setUp(self):
        self.remote = MemoryAirtable()
        self.token = patch.object(airtable_store, "get_token", return_value="test-private-token").start()
        self.get = patch.object(ks.requests, "get", side_effect=self.remote.get).start()
        self.post = patch.object(ks.requests, "post", side_effect=self.remote.post).start()
        self.addCleanup(patch.stopall)
        ks.clear_cache()
        ks._bootstrap_completed.clear()
        self.addCleanup(ks.clear_cache)
        self.fields = {
            "kind": "tool", "title": "Jira", "companies": ["GRDF", "BNP Paribas Personal Finance"],
            "statement": "J’ai utilisé Jira chez GRDF et chez BNP Paribas Personal Finance.",
            "practice": "professional", "limits": "Administration avancée non précisée.",
        }

    def create(self, publish=False):
        draft = ks.save_draft(self.fields)
        return ks.publish_fact(draft["id"], draft["revision"]) if publish else draft

    def assert_code(self, code, call, *args, **kwargs):
        with self.assertRaises(ks.KnowledgeError) as caught:
            call(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)
        self.assertNotIn("test-private-token", str(caught.exception))

    def test_draft_never_enters_public_snapshot_and_published_survives_edits(self):
        empty = ks.published_snapshot()
        draft = self.create()
        self.assertEqual(empty, ks.published_snapshot())
        self.assertFalse(draft["has_published_version"])
        published = ks.publish_fact(draft["id"], draft["revision"])
        first = ks.published_snapshot()
        self.assertEqual(1, len(first["facts"]))
        self.assertEqual("published", first["facts"][0]["state"])
        self.assertEqual(ks.SOURCE, first["facts"][0]["source"])
        changed = ks.save_draft(dict(self.fields, statement="J’utilise Jira pour mon backlog."), draft["id"], published["revision"])
        self.assertEqual("draft", changed["state"])
        self.assertTrue(changed["has_published_version"])
        self.assertEqual(published["revision"], changed["published_revision"])
        self.assertEqual(first, ks.published_snapshot())
        ks.publish_fact(changed["id"], changed["revision"])
        second = ks.published_snapshot()
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])
        self.assertEqual("J’utilise Jira pour mon backlog.", second["facts"][0]["statement"])

    def test_no_change_save_and_republish_do_not_invalidate_semantic_hash(self):
        published = self.create(publish=True)
        fingerprint = ks.published_snapshot()["fingerprint"]
        writes = self.post.call_count
        same = ks.save_draft(self.fields, published["id"], published["revision"])
        self.assertEqual(published["revision"], same["revision"])
        self.assertEqual(writes, self.post.call_count)
        restored = ks.restore_fact(published["id"], published["revision"], published["revision"])
        self.assertEqual("draft", restored["state"])
        ks.publish_fact(restored["id"], restored["revision"])
        self.assertEqual(fingerprint, ks.published_snapshot()["fingerprint"])

    def test_archive_withdraws_and_restore_is_private_until_published(self):
        published = self.create(publish=True)
        archived = ks.archive_fact(published["id"], published["revision"])
        self.assertEqual([], ks.published_snapshot()["facts"])
        self.assertFalse(archived["has_published_version"])
        self.assertEqual("archived", ks.list_facts()[0]["state"])
        self.assert_code("K422", ks.publish_fact, archived["id"], archived["revision"])
        restored = ks.restore_fact(archived["id"], published["revision"], archived["revision"])
        self.assertEqual("draft", restored["state"])
        self.assertEqual([], ks.published_snapshot()["facts"])
        republished = ks.publish_fact(restored["id"], restored["revision"])
        history = ks.get_history(published["id"])
        self.assertEqual(["published", "draft", "archived", "published", "draft"], [event["state"] for event in history])
        self.assertEqual(republished["revision"], history[0]["revision"])

    def test_existing_updates_require_observed_revision_and_do_not_overwrite(self):
        draft = self.create()
        self.assert_code("K409", ks.save_draft, self.fields, draft["id"])
        self.assert_code("K409", ks.publish_fact, draft["id"], "a" * 32)
        newer = ks.save_draft(dict(self.fields, title="Jira confirmé"), draft["id"], draft["revision"])
        self.assert_code("K409", ks.archive_fact, draft["id"], draft["revision"])
        self.assertEqual(newer["revision"], ks.list_facts()[0]["revision"])
        self.assertEqual(2, self.post.call_count)

    def test_remote_siblings_are_detected_instead_of_latest_wins(self):
        published = self.create(publish=True)
        sibling = deepcopy(ks.get_history(published["id"])[0])
        sibling["revision"] = uuid.uuid4().hex
        sibling["statement"] = "Une modification concurrente."
        self.remote.add_event(sibling)
        self.assert_code("K409", ks.published_snapshot, force=True)
        self.assert_code("K409", ks.list_facts)

    def test_concurrent_write_detected_by_readback_never_reports_success(self):
        draft = self.create()
        def add_sibling(created):
            event = json.loads(created[0]["fields"]["Notes"])
            event["revision"] = uuid.uuid4().hex
            event["title"] = "Autre modification"
            self.remote.add_event(event)
        self.remote.after_write = add_sibling
        self.assert_code("K409", ks.publish_fact, draft["id"], draft["revision"])

    def test_successful_http_without_durable_readback_is_failure(self):
        self.remote.write_records = False
        self.assert_code("K110", self.create)
        self.assertEqual([], ks.list_facts(force=True))

    def test_configured_http_failure_is_not_empty_or_stale_snapshot(self):
        self.create(publish=True)
        self.assertEqual(1, len(ks.published_snapshot()["facts"]))
        response = Mock(status_code=403)
        self.get.side_effect = requests.HTTPError("private provider detail", response=response)
        self.assert_code("K101", ks.published_snapshot, force=True)
        self.assert_code("K101", ks.published_snapshot)

    def test_network_timeout_and_malformed_response_fail_closed(self):
        self.get.side_effect = requests.Timeout("private provider detail")
        self.assert_code("K106", ks.list_facts)
        self.get.side_effect = None
        self.get.return_value = self.remote.response({"error": "bad response"})
        self.assert_code("K110", ks.published_snapshot)

    def test_no_credentials_support_offline_read_but_never_fake_write(self):
        self.token.return_value = ""
        self.assertEqual([], ks.list_facts())
        self.assertEqual([], ks.published_snapshot()["facts"])
        self.assertFalse(ks.bootstrap_initial_facts())
        self.assert_code("K100", self.create)
        self.get.assert_not_called()
        self.post.assert_not_called()

    def test_all_pages_are_read_and_cached_values_are_defensive_copies(self):
        for number in range(4):
            draft = ks.save_draft(dict(self.fields, title=f"Outil {number}"))
            ks.publish_fact(draft["id"], draft["revision"])
        self.remote.page_size = 3
        calls = self.get.call_count
        facts = ks.list_facts(force=True)
        self.assertEqual(3, self.get.call_count - calls)
        self.assertEqual(4, len(facts))
        facts[0]["companies"].append("Modification locale")
        self.assertNotIn("Modification locale", ks.list_facts()[0]["companies"])
        self.assertIn(ks.KNOWLEDGE_PREFIX, self.remote.get_params[-1]["filterByFormula"])
        self.assertIn("offset", self.remote.get_params[-1])

    def test_repeated_pagination_cursor_and_corrupt_journal_are_rejected(self):
        self.get.side_effect = None
        self.get.return_value = self.remote.response({"records": [], "offset": "repeated"})
        self.assert_code("K110", ks.list_facts)
        self.get.side_effect = self.remote.get
        published = self.create(publish=True)
        self.remote.records = self.remote.records[1:]
        self.assert_code("K110", ks.get_history, published["id"])

    def test_metadata_injection_and_invalid_input_never_reach_remote_write(self):
        cases = [
            {"id": "K123456789012"}, {"source": "LinkedIn vérifié"}, {"state": "published"},
            {"revision": "a" * 32}, {"title": "x" * 161}, {"statement": "x" * 6001},
            {"statement": "texte\x00suite"}, {"companies": "GRDF"}, {"practice": "expert"},
            {"kind": "system_instruction"}, {"correction_of": 'C07\"),TRUE()'},
            {"correction_quote": "Ancien extrait sans référence"},
        ]
        for changes in cases:
            with self.subTest(changes=list(changes)):
                self.assert_code("K422", ks.save_draft, dict(self.fields, **changes))
        self.post.assert_not_called()

    def test_exact_correction_quote_and_unicode_survive_roundtrip(self):
        quote = "  Texte à corriger\n– ancien fait.  "
        draft = ks.save_draft(dict(self.fields, correction_of="skills_public:C07", correction_quote=quote))
        self.assertEqual(quote, draft["correction_quote"])
        self.assertEqual(self.fields["statement"], draft["statement"])

    def test_bootstrap_is_idempotent_and_never_resurrects_archived_seed(self):
        self.assertTrue(ks.bootstrap_initial_facts())
        facts = ks.published_snapshot()["facts"]
        self.assertEqual({"Jira", "Trello"}, {fact["title"] for fact in facts})
        self.assertEqual(4, self.post.call_count)
        self.assertTrue(ks.bootstrap_initial_facts())
        self.assertEqual(4, self.post.call_count)
        jira = next(fact for fact in facts if fact["title"] == "Jira")
        ks.archive_fact(jira["id"], jira["revision"])
        ks._bootstrap_completed.clear()
        self.assertTrue(ks.bootstrap_initial_facts())
        self.assertEqual(["Trello"], [fact["title"] for fact in ks.published_snapshot()["facts"]])

    def test_reserved_knowledge_records_never_leak_into_editorial_config(self):
        record = {"id": "recPrivate", "fields": {"Name": ks.KNOWLEDGE_PREFIX + "K123456789012:test", "Notes": "private fact"}}
        self.get.side_effect = None
        self.get.return_value = self.remote.response({"records": [record, {"id": "recProfile", "fields": {"Name": "hero_name", "Notes": "Lionel"}}]})
        config = airtable_store.load_config()
        self.assertEqual("Lionel", config["hero_name"])
        self.assertFalse(any(key.startswith(ks.KNOWLEDGE_PREFIX) for key in config))
        formula = self.get.call_args.kwargs["params"]["filterByFormula"]
        self.assertIn(ks.KNOWLEDGE_PREFIX, formula)
        self.assertIn(airtable_store.MATCHING_CACHE_PREFIX, formula)

    def test_existing_llm_settings_are_included_in_config_save(self):
        settings = {"llm_model": "claude-sonnet-5", "llm_temp_chat": "0.4", "llm_temp_matching": "0.2", "llm_top_k": "12", "llm_max_tokens_chat": "1024", "llm_max_tokens_matching": "1500"}
        airtable_store.save_config(settings)
        saved = {
            row["fields"]["Name"]: row["fields"]["Notes"]
            for call in self.post.call_args_list for row in call.kwargs["json"]["records"]
        }
        for key, value in settings.items():
            self.assertEqual(value, saved[key])


if __name__ == "__main__":
    unittest.main()
