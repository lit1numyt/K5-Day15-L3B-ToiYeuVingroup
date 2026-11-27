import importlib.util
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "evidence" / "analyze_matchrn.py"


class DataTests(unittest.TestCase):
    def test_missing_and_invalid_overtime_are_not_zero_or_in_denominator(self):
        self.assertTrue(PATH.exists(), "chưa có script EDA")
        spec = importlib.util.spec_from_file_location("matchrn_eda", PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.overtime_summary([{"C2.6":v} for v in ["0", "29", "30", "60", "NA", "-1", "nan"]])
        self.assertEqual(result, {"valid_n":4,"at_least_30_min":2,"missing_or_invalid":3})
