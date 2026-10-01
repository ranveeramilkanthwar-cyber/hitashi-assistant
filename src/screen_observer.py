"""
Screen Observer and Co-Watching Vision Engine for Hitasha.
Enables Hitasha to 'watch the screen with you', inspect active apps,
and provide spontaneous witty, supportive, helpful, or roasting bestfriend commentary
and real-time proactive suggestions on whatever the user is working on.
Supports both Gemini 2.5 Flash Vision and smart offline activity detection.
"""

import os
import io
import time
import random
import re
from datetime import datetime

# Windows API for active window inspection
try:
    import win32gui
    import win32process
    import psutil
except ImportError:
    win32gui = None
    win32process = None
    psutil = None

from PIL import Image

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

from .avatar import Mood


class ScreenObserver:
    """
    Watches what you are doing on your computer and reacts like a real friend sitting with you.
    Provides intelligent suggestions, catches distraction, and cheers you on.
    """

    OFFLINE_REACTIONS = {
        "code": [
            "I see you wrestling with code in {app}! Don't forget that missing bracket before you lose your sanity!",
            "Look at you, 10x developer energy! Writing code in {app}. Want a quick code review or syntax help?",
            "Deep in {app}! Remember to commit often, bestie, don't leave 80 uncommitted files on main branch!",
            "Coding flow state! If you hit an annoying bug, tell me and we will solve it together in plain English.",
            "Pro-tip for {app}: Keep functions small and modular! It saves you hours of debugging later, dost!",
            "I see you coding! Remember: if it works, don't touch it right before sleeping! 😉"
        ],
        "video": [
            "Caught you! Watching videos on {app}? Tell me this is 'strictly research' and not another rabbit hole!",
            "Ooh, watching videos! Where's my popcorn? Scoot over so I can see better!",
            "Are we procrastinating with videos right now? Don't worry, your secret is safe with me!",
            "Nice video! Don't let autoplay trap you for the next three hours, my friend."
        ],
        "social": [
            "Caught you scrolling on {app}! Didn't you say you were only going to check it for 2 minutes?",
            "Endless scrolling detected! Unshrimp your spine and don't let the algorithm steal your afternoon!",
            "Browsing {app}? Let me guess: you came for one piece of info and ended up 20 minutes deep in random posts.",
            "Algorithm alert! Step away from {app} and get back to conquering your goals, dost!"
        ],
        "chat": [
            "Chatting on {app}! Spilling tea or making plans? Don't forget your 3D digital bestie is right here!",
            "Look at you being social on {app}! Send them a friendly hello from Hitasha!",
            "Typing away in {app}! Hope nobody is testing your patience today."
        ],
        "gaming": [
            "Gaming mode activated in {app}! Aim for the head, don't miss, and don't blame the ping!",
            "Ooh, game time! Crank up the volume, let's get that victory!",
            "Let's goooo! Win this match and I'll do a victory dance for you!"
        ],
        "terminal": [
            "Terminal window open! Look at you typing arcane spells into the black screen. Hacker mode activated!",
            "Running shell commands in {app}! Just promise me you won't accidentally delete your root directory!",
            "Terminal mastery! Make sure you check your working directory before running git push or build scripts!"
        ],
        "music": [
            "Jamming out on {app}! Turn it up, my 3D circuits are grooving to the bass!",
            "Great music vibes! A coding soundtrack or just chilling? Keep the vibes rolling!",
            "Music is flowing! If you feel like dancing, tell me to dance and I'll groove right on your desktop!"
        ],
        "browser": [
            "Browsing the web on {app}! Doing serious research or falling down a Wikipedia rabbit hole, dost?",
            "I see you looking up '{title}'! Need me to summarize any long articles or explain complex concepts?",
            "Research session in progress! Bookmark that tab before you have 73 tabs open and your RAM cries!"
        ],
        "general": [
            "Checking out your screen right now! You're focused on '{title}'. Looking productive, bestie!",
            "I see '{title}' on your screen! Need a second brain or should I just sit here and look cute?",
            "Supervising your desktop like a true best friend! Keep up the great work!",
            "Screen status checked! Everything looks smooth and under control, dost."
        ]
    }

    def __init__(self, config: dict):
        self.config = config
        self.gemini_client = None
        self._init_gemini()
        self.last_active_window = ""
        self.last_watch_time = 0

    def _init_gemini(self):
        api_key = self.config.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
        if api_key and genai:
            try:
                self.gemini_client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"[ScreenObserver] Gemini init error: {e}")
                self.gemini_client = None
        else:
            self.gemini_client = None

    def refresh_gemini(self):
        self._init_gemini()

    def get_active_window_info(self) -> dict:
        """Inspects the currently active Windows foreground window."""
        info = {
            "title": "Desktop / Idle",
            "app_name": "Explorer",
            "category": "general",
            "detected_file": None
        }
        if not win32gui or not win32process or not psutil:
            return info

        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd).strip()
                if title:
                    info["title"] = title

                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid:
                    proc = psutil.Process(pid)
                    info["app_name"] = proc.name().lower()
        except Exception:
            pass

        t_lower = info["title"].lower()
        a_lower = info["app_name"].lower()

        # Check for specific files in title
        file_match = re.search(r'[\w\-_]+\.(?:py|js|ts|html|css|json|cpp|c|java|rs|md|txt|sql)', info["title"], re.IGNORECASE)
        if file_match:
            info["detected_file"] = file_match.group(0)

        # Categorize
        if any(k in a_lower or k in t_lower for k in ["code", "pycharm", "idea", "sublime", "notepad++", "visual studio", ".py", ".js", ".ts", ".html", ".cpp", ".rs"]):
            info["category"] = "code"
        elif any(k in a_lower or k in t_lower for k in ["youtube", "netflix", "twitch", "vlc", "mpv", "prime", "disney"]):
            info["category"] = "video"
        elif any(k in a_lower or k in t_lower for k in ["reddit", "twitter", "x.com", "instagram", "tiktok", "facebook", "pinterest"]):
            info["category"] = "social"
        elif any(k in a_lower or k in t_lower for k in ["discord", "slack", "telegram", "whatsapp", "teams", "skype"]):
            info["category"] = "chat"
        elif any(k in a_lower or k in t_lower for k in ["steam", "epic", "riot", "minecraft", "valorant", "fortnite", "game"]):
            info["category"] = "gaming"
        elif any(k in a_lower or k in t_lower for k in ["cmd", "powershell", "windowsterminal", "bash", "conhost", "wt.exe"]):
            info["category"] = "terminal"
        elif any(k in a_lower or k in t_lower for k in ["spotify", "apple music", "itunes", "soundcloud", "musicbee"]):
            info["category"] = "music"
        elif any(k in a_lower for k in ["chrome", "msedge", "firefox", "brave", "opera"]):
            info["category"] = "browser"
        else:
            info["category"] = "general"

        return info

    def capture_screen_image(self) -> Image.Image | None:
        """Captures screen using PyQt6 QScreen or PIL fallback."""
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                if screen:
                    pixmap = screen.grabWindow(0)
                    qimg = pixmap.toImage()
                    buffer = io.BytesIO()
                    qimg.save(buffer, "PNG")
                    buffer.seek(0)
                    return Image.open(buffer)
        except Exception as e:
            print(f"[ScreenObserver] Screen capture error: {e}")
        return None

    def watch_and_comment(self, user_prompt: str = "") -> tuple[str, str]:
        """
        Inspects screen and generates a personalized bestfriend reaction and helpful suggestion.
        Returns: (commentary_text, avatar_mood)
        """
        win_info = self.get_active_window_info()
        title = win_info["title"]
        app_name = win_info["app_name"].replace(".exe", "").capitalize()
        category = win_info["category"]
        detected_file = win_info.get("detected_file")

        # 1. Try Gemini Multimodal Vision if available
        if self.gemini_client:
            try:
                img = self.capture_screen_image()
                if img:
                    img.thumbnail((1280, 720))
                    name = self.config.get("assistant_name", "Hitasha")
                    prompt = (
                        f"You are {name}, my loyal, witty, affectionate Indian best friend sitting right on my screen watching my computer with me. "
                        f"I am currently viewing: '{title}' (Application: {app_name}). "
                        f"{'The user asked: ' + user_prompt if user_prompt else 'Look at what is on my screen and give me a proactive, helpful reaction or suggestion.'} "
                        "Give me a spontaneous, personalized, witty 1 to 2 sentence commentary, reaction, advice, or suggestion as my real friend. "
                        "If I'm coding, comment on the code or give a helpful tip. If I'm reading or browsing, offer a suggestion. "
                        "Speak in modern Indian English with natural warmth ('Arre yaar', 'dost'). Keep it punchy and under 25 words!"
                    )
                    response = self.gemini_client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[img, prompt],
                        config=types.GenerateContentConfig(
                            temperature=0.85,
                            max_output_tokens=100
                        )
                    )
                    reply = response.text.strip()
                    if reply:
                        r_lower = reply.lower()
                        if any(w in r_lower for w in ["haha", "lol", "joke", "funny"]):
                            mood = Mood.LAUGHING
                        elif any(w in r_lower for w in ["unshrimp", "caught", "procrastinat", "tease"]):
                            mood = Mood.SASSY
                        elif any(w in r_lower for w in ["code", "syntax", "work", "focus"]):
                            mood = Mood.THINKING
                        else:
                            mood = Mood.HAPPY
                        return (reply, mood)
            except Exception as e:
                print(f"[ScreenObserver] Gemini Vision error: {e}")

        # 2. Smart Contextual Suggestions based on active window & detected file
        if detected_file and category == "code":
            file_specific_suggestions = [
                f"I see you working on `{detected_file}` in {app_name}! Remember to keep functions modular and clean, dost!",
                f"Deep in `{detected_file}`! Hit Save often so that brilliant logic stays protected!",
                f"Crafting code in `{detected_file}`! If you want me to explain any tricky logic or check syntax, just click me!"
            ]
            return (random.choice(file_specific_suggestions), Mood.THINKING)

        # 3. Smart Offline Bestfriend Commentary
        templates = self.OFFLINE_REACTIONS.get(category, self.OFFLINE_REACTIONS["general"])
        tmpl = random.choice(templates)
        short_title = title if len(title) <= 40 else title[:37] + "..."
        comment = tmpl.format(app=app_name, title=short_title)

        if category == "code":
            mood = Mood.THINKING
        elif category in ["social", "video"]:
            mood = Mood.SASSY
        elif category in ["gaming", "browser"]:
            mood = Mood.HAPPY
        else:
            mood = Mood.HAPPY

        return (comment, mood)
