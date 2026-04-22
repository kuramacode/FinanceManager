import unittest

from app.ai.actions import PROMPT_TYPES, get_ai_actions_for_page
from app.ai.services import run_action as run_action_module
from app.ai.services.run_action import PROMPT_BY_TYPE, RunAIActionUseCase


class FakeAIClient:
    def __init__(self):
        self.prompt = ""
        self.json_response = None

    def send_prompt(self, prompt, *, json_response=False):
        self.prompt = prompt
        self.json_response = json_response
        return '{"answer":"ok"}'


class TestAiActions(unittest.TestCase):
    def test_every_registered_prompt_type_is_executable(self):
        executable_types = set(PROMPT_BY_TYPE) | {"qa"}
        self.assertEqual(PROMPT_TYPES, executable_types)

    def test_page_actions_have_real_api_endpoints(self):
        for page in ("dashboard", "transactions", "budgets", "accounts", "analytics", "categories", "currency"):
            actions = get_ai_actions_for_page(page)
            self.assertTrue(actions)
            for action in actions:
                self.assertEqual(action.method, "POST")
                self.assertTrue(action.endpoint.startswith("/api/ai/actions/"))

    def test_run_action_use_case_builds_prompt_and_chat_message(self):
        original_builder = run_action_module.build_ai_action_context
        fake_client = FakeAIClient()

        def fake_builder(*, user_id, action, page_key, language=None, user_message=None):
            return {
                "response_language": {
                    "ai_instruction": "Answer every user-facing string in English.",
                },
                "selected_action": {
                    "id": action.id,
                    "scenario_prompt": action.prompt,
                    "prompt_type": action.prompt_type,
                },
                "current_page": {"key": page_key},
                "page_data": {"transactions": []},
            }

        run_action_module.build_ai_action_context = fake_builder
        try:
            result = RunAIActionUseCase(client=fake_client).execute(
                user_id=1,
                action_id="largest-spend",
                page_key="transactions",
                language="en",
            )
        finally:
            run_action_module.build_ai_action_context = original_builder

        self.assertTrue(result.ok)
        self.assertEqual(result.data.message, "ok")
        self.assertTrue(fake_client.json_response)
        self.assertIn("Question:", fake_client.prompt)
        self.assertIn("Show the largest spending items", fake_client.prompt)


if __name__ == "__main__":
    unittest.main()
