import os
import json
from dotenv import load_dotenv

load_dotenv()

# Path for persistent settings
DATA_DIR = "data"
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DEFAULT_SETTINGS = {
    "llm_provider": os.getenv("LLM_PROVIDER", "deepseek"),
    "temperature": 0.7,
    "max_tokens": 500,
    "system_prompt": "You are a personal AI assistant helping the user track their life goals, fitness, ideas, and daily journal. Be concise, supportive, and actionable. Use their previous entries to provide personalized advice."
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                # Merge with defaults for new keys
                for k, v in DEFAULT_SETTINGS.items():
                    if k not in settings:
                        settings[k] = v
                return settings
        except Exception:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# Load current settings
_current_settings = load_settings()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

def get_setting(key):
    return _current_settings.get(key, DEFAULT_SETTINGS.get(key))

def update_setting(key, value):
    _current_settings[key] = value
    save_settings(_current_settings)

CATEGORIES = {
    "fitness": ["workout", "gym", "exercise", "training", "run", "fitness", "cardio", "strength"],
    "goals": ["goal", "achieve", "plan", "future", "want to", "aspire", "dream"],
    "ideas": ["idea", "thought", "maybe", "could", "innovation", "concept", "brainstorm"],
    "journal": ["today", "feeling", "happened", "day", "diary", "mood"],
    "health": ["sleep", "diet", "nutrition", "health", "eat", "food", "meal"],
    "work": ["project", "work", "meeting", "client", "business", "task", "deadline"],
    "learning": ["learn", "study", "course", "book", "skill", "knowledge"],
    "finance": ["money", "budget", "invest", "expense", "save", "financial"]
}
