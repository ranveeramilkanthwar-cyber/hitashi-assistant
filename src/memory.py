"""
Persistent Memory and Knowledge Core for Hitasha (Jarvis Assistant).
Enables Hitasha to remember user facts, notes, preferences, and context across sessions.
"""

import json
import os
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory.json")


class MemoryCore:
    """
    Manages long-term memory, user facts, to-do notes, and preferences.
    """

    def __init__(self):
        self.memories = {
            "facts": {},      # e.g., {"user_name": "User", "favorite_editor": "VS Code"}
            "notes": [],      # e.g., [{"text": "finish report", "timestamp": "..."}]
            "interactions": 0
        }
        self.load()

    def load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.memories.update(data)
            except Exception as e:
                print(f"[MemoryCore] Error loading memory: {e}")

    def save(self):
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=4)
        except Exception as e:
            print(f"[MemoryCore] Error saving memory: {e}")

    def store_fact(self, key: str, value: str):
        self.memories["facts"][key.lower().strip()] = value.strip()
        self.save()

    def get_fact(self, key: str) -> str | None:
        return self.memories["facts"].get(key.lower().strip())

    def add_note(self, text: str):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.memories["notes"].append({"text": text.strip(), "created_at": now_str})
        self.save()

    def get_all_notes(self) -> list[dict]:
        return self.memories.get("notes", [])

    def clear_notes(self):
        self.memories["notes"] = []
        self.save()

    def get_all_facts(self) -> dict:
        return self.memories.get("facts", {})

    def increment_interaction(self):
        self.memories["interactions"] = self.memories.get("interactions", 0) + 1
        if self.memories["interactions"] % 10 == 0:
            self.save()
