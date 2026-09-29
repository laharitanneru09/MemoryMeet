"""Central place for settings. Values come from the .env file."""
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "")
HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "openai/gpt-oss-120b")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "qwen/qwen3-32b")


def missing_config():
    """Return a list of settings the user forgot to fill in."""
    missing = []
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if "localhost" not in HINDSIGHT_BASE_URL and not HINDSIGHT_API_KEY:
        missing.append("HINDSIGHT_API_KEY")
    return missing
