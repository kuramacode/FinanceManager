import sys
import os
import types
import unittest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.formatting import format_day, format_month, format_time
from utils.jinja_filters import color_change, format_date_for_website, CURRENT_YEAR
# `utils.jinja_filters` imports `config`, which requires `dotenv`.
# Provide a lightweight stub so tests can run without optional dependency.
dotenv_stub = types.ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda *args, **kwargs: None
sys.modules.setdefault("dotenv", dotenv_stub)




class TestFormattingUtils(unittest.TestCase):
    def test_format_day_removes_leading_zero(self):
        self.assertEqual(format_day("07"), "7")

    def test_format_day_keeps_non_zero_prefixed_value(self):
        self.assertEqual(format_day("17"), "17")

    def test_format_month_returns_short_name_for_known_month(self):
        self.assertEqual(format_month("12"), "Dec")

    def test_format_month_returns_original_value_for_unknown_month(self):
        self.assertEqual(format_month("99"), "99")

    def test_format_time_returns_hours_and_minutes(self):
        self.assertEqual(format_time("14:25:59"), "14:25")

    def test_format_time_returns_original_value_if_not_colon_separated(self):
        self.assertEqual(format_time("no-time"), "no-time")


class TestJinjaFilters(unittest.TestCase):
    def test_color_change_positive_negative_and_neutral(self):
        self.assertEqual(color_change(10), "pos")
        self.assertEqual(color_change(-1), "neg")
        self.assertEqual(color_change(0), "neutral")

    def test_format_date_omits_year_for_current_year(self):
        rendered = format_date_for_website(f"{CURRENT_YEAR}-03-05 09:10:11")
        self.assertEqual(rendered, "Mar 5 09:10")

    def test_format_date_includes_year_for_non_current_year(self):
        not_current_year = CURRENT_YEAR - 1 if CURRENT_YEAR > 1 else CURRENT_YEAR + 1
        rendered = format_date_for_website(f"{not_current_year}-03-05 09:10:11")
        self.assertEqual(rendered, f"Mar 5 {not_current_year} 09:10")


if __name__ == "__main__":
    unittest.main()
