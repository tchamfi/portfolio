"""Offline tests for scope and date mistakes that could inflate matching scores."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from datetime import date
from unittest.mock import patch

from experience import EXPERIENCE_PATH, _union_intervals, evaluate_experience_requirement, experience_summary, get_experience_fingerprint


class ExperienceTests(unittest.TestCase):
    def test_profile_union_counts_and_no_internship_inflation(self):
        summary = experience_summary("2026-09-13")
        self.assertEqual(summary["scopes"]["total_it"]["months"], 188)
        self.assertEqual(summary["scopes"]["product_owner"]["months"], 125)
        self.assertEqual(summary["scopes"]["qa"]["months"], 54)
        self.assertEqual(summary["scopes"]["data_product_owner"]["months"], 14)
        self.assertNotIn("EXP_HOMERIDER_STAGE", summary["scopes"]["total_it"]["experience_ids"])
        self.assertNotIn("EXP_UQAM_STAGE", summary["scopes"]["total_it"]["experience_ids"])
        json.dumps(summary)

    def test_overlap_is_counted_once_at_employer_transition(self):
        # Enedis and GRDF both list July 2018. November 2013 is similarly shared.
        july = experience_summary("2018-07-31")["scopes"]["product_owner"]
        self.assertEqual(july["months"], 27)
        self.assertEqual(set(july["experience_ids"]), {"EXP_ENEDIS", "EXP_GRDF"})
        qa = experience_summary("2013-11-30")["scopes"]["qa"]
        self.assertEqual(qa["months"], 25)

    def test_union_handles_duplicates_nesting_and_real_gaps(self):
        self.assertEqual(_union_intervals([(1, 5), (2, 3), (1, 5), (5, 7), (9, 10)]), [[1, 7], [9, 10]])
        self.assertEqual(_union_intervals([]), [])

    def test_8_years_po_is_not_8_years_data_po(self):
        po = evaluate_experience_requirement(8, "product_owner", "2026-09-13")
        data = evaluate_experience_requirement(8, "data_product_owner", "2026-09-13")
        self.assertEqual(po["status"], "meets")
        self.assertEqual(po["counted_months"], 125)
        self.assertEqual(data["status"], "not_met")
        self.assertEqual(data["experience_ids"], ["EXP_EPSA"])
        self.assertEqual(data["counted_months"], 14)
        self.assertIn("U02", data["references"])

    def test_tool_and_unidentified_domain_durations_remain_unknown(self):
        for scope in ("tool:bruno", "Bruno", "Postman", "SoapUI", "aws", "data_engineer", "domain", "unspecified", None):
            with self.subTest(scope=scope):
                result = evaluate_experience_requirement(3, scope, "2026-09-13")
                self.assertEqual(result["status"], "unknown")
                self.assertIsNone(result["counted_months"])
                self.assertEqual(result["references"], [])

    def test_cutoff_does_not_count_future_missions_or_future_end_months(self):
        before = experience_summary("2008-12-31")
        self.assertTrue(all(scope["months"] == 0 for scope in before["scopes"].values()))
        # The EPSA end is known as Feb 2026 but cannot inflate an analysis in 2025.
        epsa_start = experience_summary("2025-01-15")["scopes"]["data_product_owner"]
        self.assertEqual(epsa_start["months"], 1)
        pre_bnp = experience_summary("2026-05-31")["scopes"]["product_owner"]
        self.assertNotIn("EXP_BNP", pre_bnp["experience_ids"])
        self.assertEqual(pre_bnp["months"], 121)

    def test_current_month_precision_is_explicit(self):
        midmonth = evaluate_experience_requirement(10, "po", date(2026, 9, 13))
        endmonth = evaluate_experience_requirement(10, "po", date(2026, 9, 30))
        self.assertEqual(midmonth["counted_months"], endmonth["counted_months"])
        self.assertTrue(midmonth["includes_partial_current_month"])
        self.assertFalse(endmonth["includes_partial_current_month"])
        self.assertEqual(midmonth["date_precision"], "month")

    def test_qa_tenure_is_not_inflated_by_later_po_testing(self):
        result = evaluate_experience_requirement(5, "qa", "2026-09-13")
        self.assertEqual(result["status"], "not_met")
        self.assertEqual(result["counted_years"], 4.5)
        self.assertEqual(set(result["experience_ids"]), {"EXP_IER", "EXP_BOUYGUES", "EXP_ORANGE"})

    def test_missing_invalid_or_non_finite_minimum_is_unknown(self):
        for minimum in (None, "", "senior", -1, True, float("nan"), float("inf")):
            with self.subTest(minimum=minimum):
                result = evaluate_experience_requirement(minimum, "product_owner", "2026-09-13")
                self.assertEqual(result["status"], "unknown")
                json.dumps(result, allow_nan=False)

    def test_fractional_minimum_and_it_alias(self):
        self.assertEqual(evaluate_experience_requirement(4.5, "qa", "2026-09-13")["status"], "unknown")
        self.assertEqual(evaluate_experience_requirement(4, "qa", "2026-09-13")["status"], "meets")
        self.assertEqual(evaluate_experience_requirement(15, "it", "2026-09-13")["status"], "meets")

    def test_exact_anniversary_not_satisfied_early_by_inclusive_months(self):
        # May 2016–April 2026 names 120 calendar months, but on April 1
        # even the earliest possible May start has not reached ten years.
        early = evaluate_experience_requirement(10, "po", "2026-04-01")
        self.assertEqual(early["counted_months"], 120)
        self.assertEqual(early["status"], "unknown")
        self.assertEqual(early["duration_bounds"]["conservative_completed_months"], 118)
        self.assertEqual(evaluate_experience_requirement(10, "po", "2026-06-30")["status"], "meets")

    def test_boundary_allowance_applies_to_contiguous_period_not_each_employer(self):
        po = experience_summary("2026-09-13")["scopes"]["product_owner"]
        self.assertEqual(len(po["experience_ids"]), 6)
        self.assertEqual(len(po["periods"]), 1)
        self.assertEqual(po["duration_bounds"]["conservative_completed_months"], 123)

    def test_fingerprint_tracks_experience_source_and_is_carried_in_results(self):
        original = EXPERIENCE_PATH.read_bytes()
        with TemporaryDirectory() as directory:
            source = Path(directory) / "experience.json"
            source.write_bytes(original)
            with patch("experience.EXPERIENCE_PATH", source):
                before = get_experience_fingerprint()
                self.assertEqual(experience_summary("2026-09-13")["source_fingerprint"], before)
                self.assertEqual(evaluate_experience_requirement(8, "po", "2026-09-13")["source_fingerprint"], before)
                self.assertEqual(evaluate_experience_requirement(3, "tool:bruno", "2026-09-13")["source_fingerprint"], before)
                altered = json.loads(original)
                altered["experiences"][0]["start"] = "2026-07"
                source.write_text(json.dumps(altered), encoding="utf-8")
                self.assertNotEqual(get_experience_fingerprint(), before)


if __name__ == "__main__":
    unittest.main()
