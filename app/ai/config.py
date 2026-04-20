import os

class AIConfig:
    PROVIDER_NAME = "openrouter"
    MODEL_NAME = os.getenv("AI_MODEL_NAME", "openai/gpt-4o-mini")
    API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS", "60"))
    MAX_COMPLETION_TOKENS = int(os.getenv("AI_MAX_COMPLETION_TOKENS", "800"))
    TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.2"))