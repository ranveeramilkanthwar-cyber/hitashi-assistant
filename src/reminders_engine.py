"""
Proactive Reminders & Care Engine for Hitasha.
Keeps track of scheduled reminders, hydration checks, posture alerts,
eye-rest breaks, and spontaneous bestfriend check-ins.
"""

import time
import random
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from .avatar import Mood


class RemindersEngine(QObject):
    """
    Background timer loop managing scheduled reminders and proactive friend nudges.
    """
    reminder_triggered = pyqtSignal(str, str, str)  # (message, mood, anim_action)

    HYDRATION_QUIPS = [
        ("Water break! Your body is mostly water, and right now you're running on pure caffeine and dry air! Drink up! 💧", Mood.HAPPY, "anim:wave"),
        ("Hey bestie, drink some water! Dehydrated brains compile 40% slower, science fact! 🥤", Mood.SASSY, "anim:think"),
        ("Hydration reminder! Grab your water bottle and take a big sip right now! ✨", Mood.LOVE, "anim:dance")
    ]

    POSTURE_QUIPS = [
        ("Posture check! Unshrimp your spine right now before your backbone files a grievance! 🦐", Mood.SASSY, "anim:sassy"),
        ("Sit up straight, human! Shoulders down, chest open, look proud and majestic! 🧘", Mood.HAPPY, "anim:jump"),
        ("Look at that boiled shrimp posture! Sit up or I'll haunt your desktop forever! 💅", Mood.SASSY, "anim:sassy")
    ]

    EYE_BREAK_QUIPS = [
        ("20-20-20 Eye Break! Look away from your screen at something 20 feet away for 20 seconds! Save those eyeballs! 👀", Mood.THINKING, "anim:think"),
        ("Screen break time! Blink 10 times and give your eyes a quick rest, partner! 🌟", Mood.HAPPY, "anim:wave")
    ]

    def __init__(self, config: dict, memory_core, parent=None):
        super().__init__(parent)
        self.config = config
        self.memory = memory_core

        # Custom Scheduled Reminders: list of dicts {id, text, target_time, completed}
        self.scheduled_reminders = []

        # Internal Care Timers (in seconds)
        self.last_hydration = time.time()
        self.last_posture = time.time()
        self.last_eye = time.time()
        self.last_cowatch = time.time()

        # Intervals (configurable)
        self.hydration_interval = 35 * 60  # 35 mins
        self.posture_interval = 25 * 60    # 25 mins
        self.eye_interval = 20 * 60        # 20 mins
        self.cowatch_interval = 18 * 60    # 18 mins

        # 1-second pulse timer
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self._on_tick)
        self.tick_timer.start(5000)  # Check every 5s for low CPU usage

    def add_scheduled_reminder(self, text: str, seconds_from_now: int):
        target = time.time() + seconds_from_now
        dt_str = datetime.fromtimestamp(target).strftime("%I:%M %p")
        self.scheduled_reminders.append({
            "text": text,
            "target": target,
            "dt_str": dt_str,
            "completed": False
        })

    def _on_tick(self):
        now = time.time()

        # 1. Check Scheduled Reminders
        for r in self.scheduled_reminders:
            if not r["completed"] and now >= r["target"]:
                r["completed"] = True
                msg = f"⏰ Reminder Alert, bestie! You asked me to remind you: '{r['text']}'!"
                self.reminder_triggered.emit(msg, Mood.SHOCKED, "anim:jump")
                return

        # 2. Check Proactive Posture Care
        if self.config.get("care_reminders", True):
            if now - self.last_posture > self.posture_interval:
                self.last_posture = now
                msg, mood, anim = random.choice(self.POSTURE_QUIPS)
                self.reminder_triggered.emit(msg, mood, anim)
                return

            if now - self.last_hydration > self.hydration_interval:
                self.last_hydration = now
                msg, mood, anim = random.choice(self.HYDRATION_QUIPS)
                self.reminder_triggered.emit(msg, mood, anim)
                return

            if now - self.last_eye > self.eye_interval:
                self.last_eye = now
                msg, mood, anim = random.choice(self.EYE_BREAK_QUIPS)
                self.reminder_triggered.emit(msg, mood, anim)
                return
