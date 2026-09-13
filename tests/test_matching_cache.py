"""Durable matching cache fails closed without calling the real Airtable API."""

import copy
import json
import unittest
from unittest.mock import Mock, patch

import requests

import airtable_store
import matching_cache as cache


KEY = "a" * 64
RESULT = {"matching": {"score_global": 82, "requirements": [{"id": "R001", "status": "direct"}]} }


def record(result=None, **envelope_updates):
    envelope = {"version": 1, "key": KEY, "result": copy.deepcopy(RESULT if result is None else result)}
    envelope.update(envelope_updates)
    return {"id": "recCanonical", "fields": {
        "Name": airtable_store.MATCHING_CACHE_PREFIX + KEY,
        "Notes": json.dumps(envelope, ensure_ascii=False),
    }}


def response(records=None, **updates):
    value = {"records": [] if records is None else records, **updates}
    result = Mock()
    result.json.return_value = value
    return result


class MatchingCacheTests(unittest.TestCase):
    def setUp(self):
        token = patch.object(airtable_store, "get_token", return_value="test-token")
        self.get_patch = patch.object(cache.requests, "get")
        self.post_patch = patch.object(cache.requests, "post")
        token.start()
        self.get = self.get_patch.start()
        self.post = self.post_patch.start()
        self.addCleanup(token.stop)
        self.addCleanup(self.get_patch.stop)
        self.addCleanup(self.post_patch.stop)

    def test_confirmed_miss_is_none_and_lookup_is_restricted_to_one_hash(self):
        self.get.return_value = response()
        self.assertIsNone(cache.get_cached_matching(KEY))
        call = self.get.call_args.kwargs
        self.assertEqual(call["params"]["filterByFormula"], f'{{Name}} = "{airtable_store.MATCHING_CACHE_PREFIX}{KEY}"')
        self.assertEqual(call["timeout"], 10)

    def test_hit_returns_the_artifact_without_the_storage_envelope(self):
        self.get.return_value = response([record()])
        self.assertEqual(cache.get_cached_matching(KEY.upper()), RESULT)
        self.post.assert_not_called()

    def test_conflicting_duplicates_fail_closed_but_identical_duplicates_are_safe(self):
        self.get.return_value = response([record(), record({"matching": {"score_global": 64}})])
        with self.assertRaises(cache.CacheUnavailable):
            cache.get_cached_matching(KEY)
        self.get.return_value = response([record(), record()])
        self.assertEqual(cache.get_cached_matching(KEY), RESULT)

    def test_incomplete_lookup_never_becomes_a_hit_or_miss(self):
        for records in ([], [record()]):
            with self.subTest(records=bool(records)):
                self.get.return_value = response(records, offset="another-page")
                with self.assertRaises(cache.CacheUnavailable):
                    cache.get_cached_matching(KEY)

    def test_missing_credentials_never_fall_through_to_a_new_evaluation(self):
        with patch.object(airtable_store, "get_token", return_value=""):
            with self.assertRaises(cache.CacheUnavailable):
                cache.get_cached_matching(KEY)
            with self.assertRaises(cache.CacheUnavailable):
                cache.save_cached_matching(KEY, RESULT)
        self.get.assert_not_called()
        self.post.assert_not_called()

    def test_backend_and_json_errors_are_not_cache_misses_or_sensitive_messages(self):
        failures = [requests.Timeout("private-content"), requests.ConnectionError("private-content")]
        for error in failures:
            with self.subTest(error=type(error).__name__):
                self.get.side_effect = error
                with self.assertRaises(cache.CacheUnavailable) as raised:
                    cache.get_cached_matching(KEY)
                self.assertNotIn("private-content", str(raised.exception))
        self.get.side_effect = None
        for failure in ("http", "json"):
            with self.subTest(failure=failure):
                failed = response()
                if failure == "http":
                    failed.raise_for_status.side_effect = requests.HTTPError("private-content")
                else:
                    failed.json.side_effect = ValueError("private-content")
                self.get.return_value = failed
                with self.assertRaises(cache.CacheUnavailable):
                    cache.get_cached_matching(KEY)

    def test_invalid_response_shapes_never_report_a_miss(self):
        for payload in (None, [], {}, {"records": {}}, {"records": [None]}):
            with self.subTest(payload=payload):
                self.get.return_value = response()
                self.get.return_value.json.return_value = payload
                with self.assertRaises(cache.CacheUnavailable):
                    cache.get_cached_matching(KEY)

    def test_invalid_keys_cannot_enter_a_formula_or_write(self):
        for key in (None, "", "a" * 63, "g" * 64, '" OR(1) "' + "a" * 55):
            with self.subTest(key=key):
                with self.assertRaises(cache.CacheUnavailable):
                    cache.get_cached_matching(key)
                with self.assertRaises(cache.CacheUnavailable):
                    cache.save_cached_matching(key, RESULT)
        self.get.assert_not_called()
        self.post.assert_not_called()

    def test_malformed_mismatched_and_oversized_envelopes_are_rejected(self):
        bad_records = [record(version=2), record(version=True), record(key="b" * 64),
                       record(result=[]), record(result={}), record(result={"score": float("nan")}),
                       record(result={"text": "x" * cache.MAX_NOTES_CHARS})]
        for notes in ("not json", "[]", '{"version":1,"version":1,"key":"' + KEY + '","result":{"x":1}}'):
            broken = record()
            broken["fields"]["Notes"] = notes
            bad_records.append(broken)
        unexpected = record()
        unexpected["fields"]["Name"] = "hero_title"
        bad_records.append(unexpected)
        for index, broken in enumerate(bad_records):
            with self.subTest(case=index):
                self.get.return_value = response([broken])
                with self.assertRaises(cache.CacheUnavailable):
                    cache.get_cached_matching(KEY)

    def test_existing_canonical_result_is_never_overwritten(self):
        self.get.return_value = response([record()])
        proposed = {"matching": {"score_global": 64}}
        self.assertEqual(cache.save_cached_matching(KEY, proposed), RESULT)
        self.post.assert_not_called()

    def test_write_occurs_after_confirmed_miss_and_returns_verified_readback(self):
        self.get.side_effect = [response(), response([record()])]
        self.post.return_value = response([record()])
        self.assertEqual(cache.save_cached_matching(KEY, RESULT), RESULT)
        self.assertEqual(self.get.call_count, 2)
        written = self.post.call_args.kwargs
        fields = written["json"]["records"][0]["fields"]
        self.assertEqual(set(fields), {"Name", "Notes"})
        self.assertEqual(json.loads(fields["Notes"]), {"version": 1, "key": KEY, "result": RESULT})
        self.assertLessEqual(len(fields["Notes"]), cache.MAX_NOTES_CHARS)
        self.assertEqual(written["timeout"], 10)

    def test_uncertain_prewrite_lookup_does_not_write(self):
        self.get.side_effect = requests.Timeout()
        with self.assertRaises(cache.CacheUnavailable):
            cache.save_cached_matching(KEY, RESULT)
        self.post.assert_not_called()

    def test_unconfirmed_or_conflicting_write_readback_is_an_error(self):
        for records in ([], [record(), record({"different": True})]):
            with self.subTest(records=len(records)):
                self.get.side_effect = [response(), response(records)]
                self.post.return_value = response([record()])
                with self.assertRaises(cache.CacheUnavailable):
                    cache.save_cached_matching(KEY, RESULT)

    def test_bad_write_response_is_not_accepted(self):
        for records in ([], [record(), record()], [record({"wrong": True})]):
            with self.subTest(records=records):
                self.get.return_value = response()
                self.post.return_value = response(records)
                with self.assertRaises(cache.CacheUnavailable):
                    cache.save_cached_matching(KEY, RESULT)

    def test_oversized_or_non_json_artifacts_are_rejected_before_any_request(self):
        for payload in ({}, [], None, {"score": float("inf")}, {"set": {1, 2}}, {"text": "x" * cache.MAX_NOTES_CHARS}):
            with self.subTest(payload_type=type(payload).__name__):
                with self.assertRaises(cache.CacheUnavailable):
                    cache.save_cached_matching(KEY, payload)
        self.get.assert_not_called()
        self.post.assert_not_called()

    def test_config_filters_cached_records_before_pagination_and_defensively_after(self):
        self.get.return_value = response([
            {"id": "recTitle", "fields": {"Name": "hero_title", "Notes": "Product Owner"}},
            record(),
        ])
        config = airtable_store.load_config()
        self.assertEqual(config["hero_title"], "Product Owner")
        self.assertEqual(config["_record_ids"], {"hero_title": "recTitle"})
        self.assertNotIn(airtable_store.MATCHING_CACHE_PREFIX + KEY, config)
        formula = self.get.call_args.kwargs["params"]["filterByFormula"]
        self.assertEqual(formula, f'LEFT({{Name}}, {len(airtable_store.MATCHING_CACHE_PREFIX)}) != "{airtable_store.MATCHING_CACHE_PREFIX}"')

    def test_analytics_provenance_retains_evaluation_identity_and_cache_origin(self):
        metadata = {"evaluation_key": KEY, "cache_origin": "persistent", "extraction_version": "v2", "requirement_signature": "c" * 64}
        output = airtable_store._versioned_response("Résumé", metadata)
        for value in metadata.values():
            self.assertIn(value, output)


if __name__ == "__main__":
    unittest.main()
