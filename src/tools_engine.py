"""
Tools Engine for Mochi: "Do all other things"
Provides desktop utilities, screenshot capture, system vitals with sassy commentary,
timer/reminder manager, app/web launchers, and mini-games.
"""

import os
import time
import webbrowser
import subprocess
from datetime import datetime
from PIL import ImageGrab
import psutil
try:
    import pyautogui
except ImportError:
    pyautogui = None
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication

from .avatar import Mood


class ToolsEngine(QObject):
    """
    Executes companion tools, system interactions, and alarms.
    """
    # Signals
    timer_finished = pyqtSignal(str)
    action_completed = pyqtSignal(str, str)  # (message, mood)

    def __init__(self, voice_engine=None):
        super().__init__()
        self.voice_engine = voice_engine
        self.active_timers = []
        self.screenshots_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots"
        )
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def execute_action(self, action_code: str) -> tuple[str, str]:
        """
        Executes an action trigger and returns (spoken_message, mood).
        """
        if action_code == "screenshot":
            return self.take_screenshot()

        if action_code == "system_stats":
            return self.get_system_vitals()

        if action_code.startswith("timer:"):
            try:
                parts = action_code.split(":")
                val = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
                unit = parts[2] if len(parts) > 2 else "min"
                seconds = val * 60 if "min" in unit else val
                return self.set_reminder(seconds, f"{val} {unit}")
            except Exception as e:
                return ("Timer request received! Keeping track for you!", Mood.HAPPY)

        if action_code.startswith("open:"):
            parts = action_code.split(":", 1)
            target = parts[1] if len(parts) > 1 else ""
            return self.open_app_or_web(target)

        # Media Controls
        if action_code == "media:volume_up":
            if pyautogui:
                pyautogui.press('volumeup')
                pyautogui.press('volumeup')
            return ("Turned volume up! 🔊", Mood.HAPPY)

        if action_code == "media:volume_down":
            if pyautogui:
                pyautogui.press('volumedown')
                pyautogui.press('volumedown')
            return ("Turned volume down! 🔉", Mood.HAPPY)

        if action_code == "media:mute":
            if pyautogui:
                pyautogui.press('volumemute')
            return ("Toggled computer mute! 🔇", Mood.HAPPY)

        if action_code == "media:playpause":
            if pyautogui:
                pyautogui.press('playpause')
            return ("Toggled media play/pause! ⏯️", Mood.HAPPY)

        if action_code.startswith("search:"):
            query = action_code.split(":", 1)[1]
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return (f"Googled '{query}' in your browser! Knowledge incoming!", Mood.HAPPY)

        return ("Action complete, friend!", Mood.HAPPY)

    def take_screenshot(self) -> tuple[str, str]:
        """Captures full screen, saves to screenshots folder, and offers sassy comment."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.screenshots_dir, filename)

        try:
            # Brief delay so popup can adjust if needed
            time.sleep(0.3)
            img = None
            try:
                img = ImageGrab.grab()
            except Exception:
                pass

            if img:
                img.save(filepath)
            else:
                # Fallback to Qt Screen Grab
                app = QApplication.instance()
                if app:
                    screen = app.primaryScreen()
                    if screen:
                        pix = screen.grabWindow(0)
                        pix.save(filepath)

            # Optional open
            try:
                os.startfile(filepath)
            except Exception:
                pass

            remarks = [
                f"Screenshot saved to {filename}! Looking aesthetic... well, mostly!",
                f"Snap! Captured your desktop! Don't worry, I won't tell anyone about those 30 unread tabs.",
                f"Cheese! Screenshot saved! Looking crisp and high-res as always!"
            ]
            import random
            return (random.choice(remarks), Mood.LAUGHING)
        except Exception as e:
            return (f"Oops, camera shutter jammed: {e}", Mood.SHOCKED)

    def get_system_vitals(self) -> tuple[str, str]:
        """Retrieves CPU, RAM, and Battery stats with sassy commentary."""
        try:
            cpu = psutil.cpu_percent(interval=0.2)
            ram = psutil.virtual_memory().percent
            battery = psutil.sensors_battery()

            # CPU commentary
            if cpu < 25:
                cpu_comment = "CPU is chillin' at a breezy level."
            elif cpu < 70:
                cpu_comment = "CPU is humming along nicely."
            else:
                cpu_comment = "CPU is sweating hard! What are you running, a rocket launch?!"

            # RAM commentary
            if ram < 60:
                ram_comment = "RAM has plenty of breathing room."
            else:
                ram_comment = "RAM is stuffed tighter than a suitcase on vacation!"

            # Battery commentary
            bat_str = ""
            if battery:
                plugged = "plugged in" if battery.power_plugged else "on battery"
                bat_str = f" Battery is at {int(battery.percent)}% ({plugged})."

            msg = (
                f"System Report: CPU is at {int(cpu)}% ({cpu_comment}). "
                f"RAM usage is at {int(ram)}% ({ram_comment}).{bat_str}"
            )
            mood = Mood.THINKING if cpu < 75 else Mood.SHOCKED
            return (msg, mood)
        except Exception as e:
            return (f"Couldn't read system vitals: {e}", Mood.SASSY)

    def set_reminder(self, seconds: int, label: str) -> tuple[str, str]:
        """Sets a non-blocking countdown timer."""
        timer = QTimer(self)
        timer.setSingleShot(True)

        def _on_timer_complete():
            msg = f"⏰ Ding ding ding! Your {label} timer is UP! Stand up, stretch, or get back to winning!"
            if self.voice_engine:
                self.voice_engine.play_sound("ding")
                self.voice_engine.speak(msg)
            self.timer_finished.emit(msg)

        timer.timeout.connect(_on_timer_complete)
        timer.start(seconds * 1000)
        self.active_timers.append(timer)

        return (f"Timer locked in for {label}! I'll yell at you when time is up!", Mood.HAPPY)

    def open_app_or_web(self, target: str) -> tuple[str, str]:
        """Launches websites or desktop apps."""
        try:
            if target == "youtube":
                webbrowser.open("https://www.youtube.com")
                return ("YouTube launched! Enjoy the rabbit hole!", Mood.HAPPY)
            elif target == "spotify":
                webbrowser.open("https://open.spotify.com")
                return ("Spotify is rolling! Turn up the beat!", Mood.HAPPY)
            elif target == "github":
                webbrowser.open("https://www.github.com")
                return ("GitHub is open! Time to commit some great code!", Mood.HAPPY)
            elif target == "calc":
                subprocess.Popen("calc.exe")
                return ("Calculator opened! Math time!", Mood.THINKING)
            elif target == "notepad":
                subprocess.Popen("notepad.exe")
                return ("Notepad ready for your genius ideas!", Mood.HAPPY)
            elif target == "downloads":
                dl_path = os.path.expanduser("~/Downloads")
                os.startfile(dl_path)
                return ("Opened your Downloads folder!", Mood.HAPPY)
            elif target == "desktop":
                dt_path = os.path.expanduser("~/Desktop")
                os.startfile(dt_path)
                return ("Opened your Desktop folder!", Mood.HAPPY)
            elif target == "project":
                proj_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                os.startfile(proj_dir)
                return ("Opened project workspace directory!", Mood.HAPPY)
            else:
                webbrowser.open(f"https://www.{target}.com")
                return (f"Opened {target}!", Mood.HAPPY)
        except Exception as e:
            return (f"Couldn't open {target}: {e}", Mood.SASSY)
