"""
config.py
---------
This is the ONLY file that should read environment variables directly.
Every other file in the project imports settings FROM here.

Why do this instead of calling os.getenv() everywhere?
1. One place to check if the API key is missing (fail fast, with a clear message).
2. One place to change defaults later (e.g. lead scoring thresholds).
3. Keeps secrets out of the rest of the codebase.
"""

import os
from dotenv import load_dotenv

# Load variables from the .env file into the environment.
# If .env doesn't exist, this simply does nothing (no crash).
load_dotenv()

# --- LLM settings ---
# We use Groq's free API. Groq's endpoint is "OpenAI-compatible", meaning
# we can still use the same `openai` Python package - we just point it at
# Groq's server address (base_url) instead of OpenAI's, and use a Groq model name.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b") # Free, fast, strong general-purpose model on Groq

# --- Web research settings (Phase 5) ---
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# --- Lead scoring thresholds (used starting Phase 2) ---
# Kept here so they are easy to find and tune later, per your project brief.
PRIORITY_THRESHOLDS = {
    "HIGH": 80,
    "MEDIUM": 60,
    # anything below MEDIUM threshold = LOW
}

# --- Company size assumptions (used starting Phase 2) ---
COMPANY_SIZE_BANDS = {
    "SMALL_MAX": 99,      # < 100 employees = Small
    "MEDIUM_MAX": 500,    # 100-500 = Medium
    # > 500 = Large
}


def validate_config():
    """
    Checks that the essential configuration is present.
    Returns (is_valid: bool, message: str) instead of crashing the app,
    so the Streamlit UI can show a friendly error instead of a stack trace.
    """
    if not GROQ_API_KEY:
        return False, (
            "GROQ_API_KEY is missing. "
            "Copy .env.example to .env and add your real Groq API key "
            "(get a free one at https://console.groq.com/keys)."
        )
    if not GROQ_API_KEY.startswith("gsk_"):
        return False, (
            "GROQ_API_KEY doesn't look like a valid Groq key "
            "(should start with 'gsk_'). Please double-check your .env file."
        )
    return True, "Configuration OK"
