import unittest

from app.ai.clients.openrouter import OpenRouterClient
from app.ai.config import (
    DEFAULT_OPENROUTER_BASE_URL,
    AIConnectionSettings,
    load_ai_settings,
    normalize_openrouter_model,
)
from app.ai.exceptions import AIClientError, AIConfigurationError


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text="", headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response


def make_settings(**overrides):
    defaults = {
        "provider": "openrouter",
        "api_key": "test-key",
        "model": "openrouter/elephant-alpha",
        "base_url": DEFAULT_OPENROUTER_BASE_URL,
        "timeout_seconds": 15,
        "max_completion_tokens": 300,
        "temperature": 0.1,
        "site_url": "",
        "app_title": "Finance Manager",
    }
    defaults.update(overrides)
    return AIConnectionSettings(**defaults)


class TestOpenRouterConfig(unittest.TestCase):
    def test_load_ai_settings_supports_app_env_names_and_normalizes_bad_base_url(self):
        settings = load_ai_settings(
            {
                "OPENROUTER_API_KEY": "secret",
                "MODEL_NAME": "inclusionai/ling-2.6-flash:free",
                "OPENROUTER_BASE_URL": "https://openrouter.ai/inclusionai/ling-2.6-flash:free",
                "TIMEOUT_SECONDS": "7",
                "MAX_COMPLETION_TOKENS": "123",
                "TEMPERATURE": "0.3",
            }
        )

        self.assertEqual(settings.api_key, "secret")
        self.assertEqual(settings.model, "inclusionai/ling-2.6-flash:free")
        self.assertEqual(settings.base_url, DEFAULT_OPENROUTER_BASE_URL)
        self.assertEqual(settings.timeout_seconds, 7)
        self.assertEqual(settings.max_completion_tokens, 123)
        self.assertEqual(settings.temperature, 0.3)

    def test_normalize_openrouter_model_accepts_model_page_url(self):
        self.assertEqual(
            normalize_openrouter_model("https://openrouter.ai/inclusionai/ling-2.6-flash:free"),
            "inclusionai/ling-2.6-flash:free",
        )


class TestOpenRouterClient(unittest.TestCase):
    def test_send_prompt_posts_chat_completion_payload(self):
        response = FakeResponse(
            payload={
                "choices": [
                    {
                        "message": {
                            "content": "{\"ok\": true}",
                        }
                    }
                ]
            }
        )
        session = FakeSession(response)
        client = OpenRouterClient(settings=make_settings(), session=session)

        result = client.send_prompt("Analyze this")

        self.assertEqual(result, "{\"ok\": true}")
        args, kwargs = session.calls[0]
        self.assertEqual(args[0], "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["headers"]["X-Title"], "Finance Manager")
        self.assertEqual(kwargs["json"]["model"], "openrouter/elephant-alpha")
        self.assertEqual(kwargs["json"]["messages"][0]["content"], "Analyze this")
        self.assertEqual(kwargs["timeout"], 15)

    def test_missing_api_key_raises_configuration_error(self):
        with self.assertRaises(AIConfigurationError):
            OpenRouterClient(settings=make_settings(api_key=""))

    def test_provider_error_raises_client_error(self):
        session = FakeSession(FakeResponse(status_code=401, text="Unauthorized"))
        client = OpenRouterClient(settings=make_settings(), session=session)

        with self.assertRaises(AIClientError):
            client.send_prompt("Analyze this")

    def test_html_404_points_to_base_url_configuration(self):
        response = FakeResponse(
            status_code=404,
            text='<!DOCTYPE html><html lang="en"></html>',
            headers={"Content-Type": "text/html"},
        )
        session = FakeSession(response)
        client = OpenRouterClient(settings=make_settings(), session=session)

        with self.assertRaisesRegex(AIClientError, "OPENROUTER_BASE_URL"):
            client.send_prompt("Analyze this")


if __name__ == "__main__":
    unittest.main()
