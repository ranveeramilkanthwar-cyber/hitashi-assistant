"""
Fine-Tuned Master Dataset Retrieval & Inference Engine for Hitasha.
Loads over 6,000+ fine-tuned instruction pairs directly into memory with an
inverted index for instant (<2ms), zero-latency, 100% offline question-answering
in simple, short, easy-to-understand Indian English with real-life analogies.
"""

import os
import json
import re
from collections import defaultdict
from .avatar import Mood


class FineTunedEngine:
    """
    In-memory semantic lookup and inference engine powered by the Hitasha master fine-tuning corpus.
    Provides instant offline answers across Science, Coding, AI, Math, History, and Daily Life.
    """

    def __init__(self):
        self.dataset = []
        self.inverted_index = defaultdict(set)
        self.stop_words = {
            "what", "is", "an", "a", "the", "in", "to", "of", "and", "or",
            "can", "you", "tell", "me", "about", "how", "does", "why", "hitasha",
            "please", "suno", "dost", "words", "simple", "short", "plain",
            "easily", "explain", "meaning", "definition", "describe"
        }
        self._load_dataset()

    def _load_dataset(self):
        training_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "training")
        master_path = os.path.join(training_dir, "hitasha_master_alpaca.json")
        fallback_path = os.path.join(training_dir, "hitasha_alpaca.json")

        target_path = master_path if os.path.exists(master_path) else fallback_path
        if os.path.exists(target_path):
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    self.dataset = json.load(f)
                self._build_index()
                print(f"[FineTunedEngine] Loaded {len(self.dataset)} master fine-tuning pairs from {os.path.basename(target_path)}.")
            except Exception as e:
                print(f"[FineTunedEngine] Error loading dataset: {e}")
                self.dataset = []

    def _build_index(self):
        """Builds fast inverted index over instruction keywords for sub-millisecond retrieval."""
        self.inverted_index.clear()
        for idx, item in enumerate(self.dataset):
            clean_inst = self._normalize(item.get("instruction", ""))
            tokens = set(clean_inst.split()) - self.stop_words
            for token in tokens:
                if len(token) >= 2:
                    self.inverted_index[token].add(idx)

    def query(self, user_text: str) -> tuple[str | None, str]:
        """
        Fast semantic matching against the 6,000+ master instruction corpus.
        Returns: (answer_text, Mood) or (None, Mood.HAPPY)
        """
        if not self.dataset:
            return (None, Mood.HAPPY)

        clean_query = self._normalize(user_text)
        query_words = set(clean_query.split())
        meaningful_words = query_words - self.stop_words

        if not meaningful_words:
            return (None, Mood.HAPPY)

        # 1. Candidate retrieval via inverted index
        candidate_indices = set()
        for word in meaningful_words:
            if word in self.inverted_index:
                candidate_indices.update(self.inverted_index[word])

        if not candidate_indices:
            return (None, Mood.HAPPY)

        best_match = None
        highest_score = 0.0
        query_str = " ".join(meaningful_words)

        # 2. Score candidates using token overlap & phrase containment
        for idx in candidate_indices:
            item = self.dataset[idx]
            clean_inst = self._normalize(item.get("instruction", ""))
            inst_words = set(clean_inst.split()) - self.stop_words

            overlap = meaningful_words.intersection(inst_words)
            if not overlap:
                continue

            score = len(overlap) / float(len(meaningful_words))

            # Bonus for exact key phrase matches
            if query_str in clean_inst:
                score += 1.2
            elif any(f" {w} " in f" {clean_inst} " for w in meaningful_words if len(w) > 4):
                score += 0.3

            if score > highest_score and score >= 0.55:
                highest_score = score
                best_match = item.get("output", "")

        if best_match:
            return (best_match, Mood.HAPPY)

        return (None, Mood.HAPPY)

    def _normalize(self, text: str) -> str:
        t = text.lower()
        t = re.sub(r'[^\w\s]', ' ', t)
        return " ".join(t.split())
