"""Reject misleading comparisons instead of silently publishing percentages."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compare', ROOT / 'scripts/compare-search-windows.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MeasurementContractTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'data/search-checkpoint-2026-09-14.json').read_text())

    def test_cohort_decline_is_not_hidden_by_sitewide_growth(self):
        result = module.compare(self.data)['cohorts']
        self.assertEqual(result['sitewide']['clicks_change_percent'], 60.0)
        self.assertEqual(result['english_directory']['impressions_change_percent'], -78.47)
        self.assertEqual(result['english_mvp']['clicks_change'], -1)

    def test_unequal_windows_are_rejected(self):
        self.data['after_window']['end'] = '2026-09-10'
        with self.assertRaises(ValueError): module.compare(self.data)

    def test_incomplete_window_is_rejected(self):
        self.data['complete_through'] = '2026-09-10'
        with self.assertRaises(ValueError): module.compare(self.data)

    def test_overlapping_windows_are_rejected(self):
        self.data['before_window'] = copy.deepcopy(self.data['after_window'])
        with self.assertRaises(ValueError): module.compare(self.data)

    def test_zero_baseline_is_not_infinite_growth(self):
        self.data['cohorts']['english_mvp']['before'] = {'clicks': 0, 'impressions': 0}
        result = module.compare(self.data)['cohorts']['english_mvp']
        self.assertIsNone(result['clicks_change_percent'])
        self.assertIsNone(result['ctr_change_percentage_points'])

    def test_invalid_counts_are_rejected(self):
        self.data['cohorts']['sitewide']['after']['clicks'] = -1
        with self.assertRaises(ValueError): module.compare(self.data)


if __name__ == '__main__':
    unittest.main()
