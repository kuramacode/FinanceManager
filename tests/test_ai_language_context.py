import unittest

from app import create_app
from app.ai.services import analyze_expenses as analyze_expenses_module
from app.ai.services.analyze_expenses import AnalyzeExpensesUseCase
from app.i18n import get_current_language, get_language_context
from tests.test_support import make_test_db_uri


class FakeAIClient:
    def __init__(self):
        self.prompt = ""
        self.json_response = None

    def send_prompt(self, prompt, *, json_response=False):
        self.prompt = prompt
        self.json_response = json_response
        return '{"insights":["ok"],"problems":[],"recommendations":[]}'


class TestAiLanguageContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "ai-language-test-secret",
                "SQLALCHEMY_DATABASE_URI": make_test_db_uri(),
            }
        )

    def test_get_current_language_uses_ai_request_header(self):
        with self.app.test_request_context("/api/ai/expense-analysis", headers={"X-Ledger-Language": "uk"}):
            self.assertEqual(get_current_language(), "uk")

    def test_language_context_contains_prompt_instruction(self):
        language_context = get_language_context("uk")

        self.assertEqual(language_context["language"], "uk")
        self.assertEqual(language_context["locale"], "uk-UA")
        self.assertIn("українською", language_context["ai_instruction"])

    def test_expense_analysis_prompt_receives_requested_language(self):
        original_builder = analyze_expenses_module.build_expense_analysis_context
        fake_client = FakeAIClient()
        seen = {}

        def fake_builder(user_id, date_from=None, date_to=None, language=None):
            seen["language"] = language
            return {
                "response_language": get_language_context(language),
                "period": {
                    "date_from": "2026-04-01",
                    "date_to": "2026-04-21",
                },
                "totals": {
                    "income": 1000,
                    "expense": 250,
                    "balance": 750,
                },
                "top_expense_categories": [],
                "top_income_categories": [],
                "transactions_count": 0,
                "currency": "UAH",
            }

        analyze_expenses_module.build_expense_analysis_context = fake_builder
        try:
            result = AnalyzeExpensesUseCase(client=fake_client).execute(user_id=1, language="uk")
        finally:
            analyze_expenses_module.build_expense_analysis_context = original_builder

        self.assertTrue(result.ok)
        self.assertEqual(seen["language"], "uk")
        self.assertTrue(fake_client.json_response)
        self.assertIn("українською", fake_client.prompt)


if __name__ == "__main__":
    unittest.main()
