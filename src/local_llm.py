"""
Local GPU LLM Engine for Hitasha.
Connects to local GPU-accelerated inference backends (Ollama, LM Studio, LocalAI, vLLM)
configured with optimal parameters for RTX 5050 8GB VRAM GPU.
"""

import os
import json
import urllib.request
import urllib.error
import urllib.parse
from .avatar import Mood


class LocalLLMEngine:
    """
    Connects to local LLMs running on the user's GPU (e.g., via Ollama or LM Studio).
    Configured with high-performance parameters:
      - n_gpu_layers: -1 (full GPU offload to RTX 5050 8GB VRAM)
      - temperature: 0.7 (witty, dynamic banter)
      - top_p: 0.9 (natural vocabulary)
      - max_tokens: 150 (punchy voice-ready replies)
    """

    DEFAULT_LOCAL_URL = "http://localhost:11434"  # Default Ollama
    LM_STUDIO_URL = "http://localhost:1234/v1"   # Default LM Studio

    def __init__(self, config: dict):
        self.config = config
        self.base_url = self.config.get("local_llm_url", self.DEFAULT_LOCAL_URL).rstrip("/")
        self.model_name = self.config.get("local_llm_model", "llama3.2:3b")

        # GPU Inference Parameters for RTX 5050 (8GB VRAM)
        self.params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.15,
            "max_tokens": 150,
            "num_predict": 150,
            "num_ctx": 4096,
            "num_gpu": 99,  # Full GPU offload in Ollama
        }
        self._last_server_check_time = 0
        self._server_available = False
        self._cached_active_model = self.model_name

    def is_server_online(self) -> bool:
        """Fast cached check to avoid blocking when Ollama is not running."""
        import time
        now = time.time()
        if now - self._last_server_check_time < 15.0:
            return self._server_available

        self._last_server_check_time = now
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", headers={"User-Agent": "HitashaAI"})
            with urllib.request.urlopen(req, timeout=0.4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]
                if models:
                    h_match = [m for m in models if "hitasha" in m.lower()]
                    self._cached_active_model = h_match[0] if h_match else models[0]
                self._server_available = True
                return True
        except Exception:
            pass

        # Try /v1/models (LM Studio fallback)
        try:
            req = urllib.request.Request(f"{self.base_url}/v1/models", headers={"User-Agent": "HitashaAI"})
            with urllib.request.urlopen(req, timeout=0.4) as resp:
                self._server_available = True
                return True
        except Exception:
            pass

        self._server_available = False
        return False

    def check_connection(self) -> tuple[bool, str]:
        """Checks if local GPU model server is active and reachable."""
        if self.is_server_online():
            return (True, f"Local GPU Model Active ({self._cached_active_model})")
        return (False, "Offline / Local server not running")

    def generate(self, user_prompt: str, user_name: str = "Sir", context: str = "") -> tuple[str | None, str]:
        """
        Sends prompt to local GPU model with Desi Indian Girl bestfriend persona.
        Returns: (reply_text, mood)
        """
        if not self.is_server_online():
            return (None, Mood.HAPPY)

        system_prompt = (
            f"You are Hitasha, an all-rounder personal AI companion and loyal Indian best friend living right on the user's desktop. "
            f"User is '{user_name}'. Context: {context} "
            "You speak fluent modern Indian English with natural Desi warmth and friendly phrases ('Arre yaar', 'Suno na', 'Haan bilkul', 'Pakka!', 'Dost'). "
            "CRITICAL INSTRUCTIONS: "
            "1. Answer ANY question asked by the user in a simple, easy, short, and easily understandable manner. "
            "2. Break down complex concepts using simple everyday real-life examples and intuitive analogies. "
            "3. Keep your answers concise, direct, and spoken-friendly (1 to 3 punchy sentences max). "
            "4. Never output long essays, complicated jargon walls, or robotic bullet lists unless explicitly asked. "
            "5. Always be warm, clear, and helpful like a real best friend sitting right beside them."
        )

        # 1. Try Ollama Native API (/api/chat)
        if "11434" in self.base_url or not self.base_url.endswith("/v1"):
            try:
                # Dynamically verify model or fallback to available
                active_model = self.model_name
                try:
                    tag_req = urllib.request.Request(f"{self.base_url}/api/tags", headers={"User-Agent": "HitashaAI"})
                    with urllib.request.urlopen(tag_req, timeout=1.0) as tag_resp:
                        tags_data = json.loads(tag_resp.read().decode("utf-8"))
                        avail = [m.get("name") for m in tags_data.get("models", [])]
                        if avail and not any(active_model in m for m in avail):
                            # Pick hitasha if present, else first available
                            h_match = [m for m in avail if "hitasha" in m.lower()]
                            active_model = h_match[0] if h_match else avail[0]
                except Exception:
                    pass

                payload = {
                    "model": active_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": self.params["temperature"],
                        "top_p": self.params["top_p"],
                        "top_k": self.params["top_k"],
                        "repeat_penalty": self.params["repeat_penalty"],
                        "num_predict": self.params["max_tokens"],
                        "num_gpu": self.params["num_gpu"],
                        "num_ctx": self.params["num_ctx"]
                    }
                }
                req = urllib.request.Request(
                    f"{self.base_url}/api/chat",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    text = res_data.get("message", {}).get("content", "").strip()
                    if text:
                        return (text, self._detect_mood(text))
            except Exception as e:
                # Fall through to OpenAI-compatible endpoint
                pass

        # 2. Try OpenAI-Compatible Endpoint (/v1/chat/completions)
        try:
            endpoint = f"{self.base_url}/v1/chat/completions" if not self.base_url.endswith("/v1") else f"{self.base_url}/chat/completions"
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": self.params["temperature"],
                "top_p": self.params["top_p"],
                "max_tokens": self.params["max_tokens"]
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                text = res_data["choices"][0]["message"]["content"].strip()
                if text:
                    return (text, self._detect_mood(text))
        except Exception as e:
            # print(f"[LocalLLM] Local GPU inference error: {e}")
            pass

        return (None, Mood.HAPPY)

    def _detect_mood(self, text: str) -> str:
        lower = text.lower()
        if any(w in lower for w in ["haha", "arre", "lol", "joke", "funny", "samosa", "chai"]):
            return Mood.LAUGHING if "haha" in lower else Mood.SASSY
        elif any(w in lower for w in ["love", "bestie", "aww", "cute", "sweet", "dil"]):
            return Mood.LOVE
        elif any(w in lower for w in ["unshrimp", "caught", "procrastinat", "sharma"]):
            return Mood.SASSY
        elif any(w in lower for w in ["why", "think", "code", "syntax", "bug"]):
            return Mood.THINKING
        return Mood.HAPPY
