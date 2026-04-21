import os
from pathlib import Path
from dotenv import load_dotenv

# Знаходимо шлях до кореня проекту (піднімаємося на 2 рівні вгору від config.py)



class AIConfig:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    env_path = BASE_DIR / '.env'

    # Завантажуємо змінні
    load_dotenv(dotenv_path=env_path)
    
    OPENROUTER_API_KEY=""
    PROVIDER_NAME = "openrouter"
    MODEL_NAME = os.getenv("AI_MODEL_NAME", "openrouter/elephant-alpha")
    API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/openrouter/elephant-alpha")
    TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS", "60"))
    MAX_COMPLETION_TOKENS = int(os.getenv("AI_MAX_COMPLETION_TOKENS", "800"))
    TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.2"))