"""
Configuration and settings manager for Hitasha (Jarvis Desktop Assistant).
Persists preferences into config.json.
"""

import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

DEFAULT_CONFIG = {
    "assistant_name": "Hitasha",
    "personality": "jarvis",  # 'jarvis', 'sassy', 'roast', 'chill', 'smart'
    "voice_enabled": True,
    "voice_rate": 185,       # words per minute
    "voice_volume": 1.0,     # 0.0 to 1.0
    "voice_id": "",          # Default system SAPI5 voice if empty
    "always_on_top": True,
    "gemini_api_key": "",
    "sound_effects": True,
    "window_pos": [1200, 350],
    "compact_mode": False,
    "local_llm_model": "hitasha",
    "local_llm_url": "http://localhost:11434",
    "response_style": "simple_indian_english"
}


def load_config() -> dict:
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            print(f"[Config] Error loading config: {e}")
    # Also check environment variable for GEMINI_API_KEY
    if not config.get("gemini_api_key") and os.environ.get("GEMINI_API_KEY"):
        config["gemini_api_key"] = os.environ.get("GEMINI_API_KEY")
    return config


def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"[Config] Error saving config: {e}")
