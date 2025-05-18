import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

# Defaults
DEFAULT_LOCATION_CODE = int(os.getenv("DEFAULT_LOCATION_CODE", 2840))  # US
DEFAULT_LANGUAGE_CODE = os.getenv("DEFAULT_LANGUAGE_CODE", "en")
DEFAULT_DEVICE = os.getenv("DEFAULT_DEVICE", "desktop")

# OpenAI settings
MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.7))
