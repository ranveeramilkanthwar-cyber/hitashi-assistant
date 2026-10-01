"""
Screen Mate Desktop Window for Hitasha.
A transparent, borderless, floating 3D companion that physically walks across
your screen, hovers with gentle physics, tracks the mouse across the whole screen,
autonomously interacts to keep the user engaged, and reveals chat & controls
only when the character is clicked.
"""

import math
import random
import time
import os
from PyQt6.QtCore import (
    Qt, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QUrl
)
from PyQt6.QtGui import (
    QColor, QFont, QIcon, QPainter, QCursor, QAction
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMenu, QApplication, QLineEdit
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings

from .avatar import Mood


class Transparent3DPage(QWebEnginePage):
    """Custom WebEnginePage that intercepts character click events and keeps transparency."""
    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.setBackgroundColor(QColor(0, 0, 0, 0))

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        if "hitasha:click" in message or "mochi:click" in message:
            self.parent_widget.on_character_clicked()


class ScreenMateWindow(QWidget):
    """
    Floating, roaming, borderless desktop companion.
    Walks, hovers, talks, reads screen, tracks whole-screen cursor,
    and interacts autonomously like a real living human.
    """
    mate_clicked = pyqtSignal()
    open_deck_requested = pyqtSignal()
    watch_screen_requested = pyqtSignal()
    mic_listen_requested = pyqtSignal()
    send_message_requested = pyqtSignal(str)
    auto_watch_toggled = pyqtSignal(bool)
    power_toggled = pyqtSignal(bool)
    roast_requested = pyqtSignal()

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config

        # Frameless, translucent, always on top
        self.setWindowTitle("Hitasha Screen Mate")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # Start in pure character mode (controls hidden, petite sleek size)
        self.controls_visible = False
        self.setFixedSize(250, 210)

        # Dragging & click interaction state
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.drag_mouse_origin = QPoint()
        self.is_active = True
        self.is_sleeping = False
        self.is_auto_watching = True
        self._last_autonomous_action = time.time()

        # Hover physics
        self.is_hovering = False
        self.hover_ticks = 0
        self.base_y = 600
        self.base_x = 1300
        self.hover_timer = QTimer(self)
        self.hover_timer.timeout.connect(self._update_hover_physics)

        # Whole-Screen Mouse Gaze Tracking (Tracks cursor anywhere on display monitor)
        self.gaze_timer = QTimer(self)
        self.gaze_timer.timeout.connect(self._track_screen_cursor)
        self.gaze_timer.start(25)  # 40 FPS smooth gaze

        # Controls auto-hide timer (35 seconds after last interaction)
        self.controls_auto_hide_timer = QTimer(self)
        self.controls_auto_hide_timer.setSingleShot(True)
        self.controls_auto_hide_timer.timeout.connect(self._maybe_auto_hide_controls)

        # Autonomous Life & Interaction Loop (Hitasha stays alive & interacts proactively)
        self.autonomous_timer = QTimer(self)
        self.autonomous_timer.timeout.connect(self._autonomous_life_tick)
        self.autonomous_timer.start(38000)  # Check every 38 seconds for lively interaction!

        # Speech bubble auto-hide timer
        self.bubble_timer = QTimer(self)
        self.bubble_timer.setSingleShot(True)
        self.bubble_timer.timeout.connect(self._fade_bubble)

        self._build_ui()
        self._load_3d_character()

        # Position at bottom-right of primary screen
        self._set_initial_screen_position()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(2)

        # 1. Floating Speech Bubble (Only shown when speaking, auto-fades)
        self.bubble_frame = QFrame()
        self.bubble_frame.setObjectName("SpeechBubbleFrame")
        self.bubble_frame.setStyleSheet("""
            QFrame#SpeechBubbleFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(24, 25, 42, 0.96), stop:1 rgba(14, 15, 26, 0.98));
                border: 1.5px solid rgba(0, 229, 255, 0.55);
                border-radius: 14px;
                padding: 4px;
            }
        """)
        bubble_layout = QVBoxLayout(self.bubble_frame)
        bubble_layout.setContentsMargins(8, 4, 8, 4)
        bubble_layout.setSpacing(2)

        self.speech_label = QLabel("✨ Namaste! Hitasha online, watching your screen!")
        self.speech_label.setStyleSheet("color: #f0f4ff; font-size: 10px; font-weight: 600; font-family: 'Segoe UI', sans-serif;")
        self.speech_label.setWordWrap(True)
        self.speech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bubble_layout.addWidget(self.speech_label)

        root_layout.addWidget(self.bubble_frame)
        self.bubble_frame.hide()  # Hidden by default until speaking

        # 2. Transparent 3D Character Viewport (Sleek, Petite & Crisp)
        self.web_view = QWebEngineView(self)
        self.web_page = Transparent3DPage(self)
        self.web_view.setPage(self.web_page)
        self.web_view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.web_view.setStyleSheet("background: transparent;")
        self.web_view.setFixedSize(240, 185)
        root_layout.addWidget(self.web_view, alignment=Qt.AlignmentFlag.AlignCenter)

        # 3. Companion Controls Container (ONLY SEEN AFTER CLICKING CHARACTER)
        self.companion_controls = QWidget()
        ctrls_layout = QVBoxLayout(self.companion_controls)
        ctrls_layout.setContentsMargins(0, 2, 0, 0)
        ctrls_layout.setSpacing(4)

        # Header bar inside controls with quick collapse button
        top_ctrl_bar = QFrame()
        top_ctrl_bar.setStyleSheet("background: transparent; border: none;")
        top_layout = QHBoxLayout(top_ctrl_bar)
        top_layout.setContentsMargins(4, 0, 4, 0)
        top_layout.setSpacing(6)

        status_lbl = QLabel("✨ Hitasha Companion Active")
        status_lbl.setStyleSheet("color: #8b92c4; font-size: 10px; font-weight: 600;")
        top_layout.addWidget(status_lbl)
        top_layout.addStretch()

        collapse_btn = QPushButton("✕ Hide Controls")
        collapse_btn.setToolTip("Hide controls and keep only 3D character on screen")
        collapse_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: #c7ceff;
                border: 1px solid rgba(255, 255, 255, 0.15);
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(255, 75, 75, 0.35);
                color: #ffffff;
            }
        """)
        collapse_btn.clicked.connect(lambda: self.toggle_controls(force_open=False))
        top_layout.addWidget(collapse_btn)
        ctrls_layout.addWidget(top_ctrl_bar)

        # 3a. Prominent ON / OFF Power Switch Bar
        self.power_frame = QFrame()
        self.power_frame.setStyleSheet("background: transparent; border: none;")
        power_layout = QHBoxLayout(self.power_frame)
        power_layout.setContentsMargins(2, 0, 2, 0)
        power_layout.setSpacing(4)

        self.power_btn = QPushButton("🟢 HITASHA: ON (Active)")
        self.power_btn.setToolTip("Click to Turn OFF (Standby / Sleep) or Turn ON")
        self._update_power_button_style(True)
        self.power_btn.clicked.connect(self.toggle_power)
        power_layout.addWidget(self.power_btn)
        ctrls_layout.addWidget(self.power_frame)

        # 3b. Live Chat & Voice Input Bar
        self.input_frame = QFrame()
        self.input_frame.setObjectName("MiniChatFrame")
        self.input_frame.setStyleSheet("""
            QFrame#MiniChatFrame {
                background: rgba(18, 19, 32, 0.94);
                border: 1px solid rgba(0, 229, 255, 0.45);
                border-radius: 14px;
                padding: 1px 4px;
            }
            QLineEdit {
                background: transparent;
                border: none;
                color: #ffffff;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
                padding: 4px;
            }
            QPushButton {
                background: transparent;
                border: none;
                color: #00e5ff;
                font-size: 13px;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(124, 77, 255, 0.4);
                color: #ffffff;
            }
        """)
        input_layout = QHBoxLayout(self.input_frame)
        input_layout.setContentsMargins(6, 2, 6, 2)
        input_layout.setSpacing(4)

        self.chat_edit = QLineEdit()
        self.chat_edit.setPlaceholderText("Talk to Hitasha... (or click 🎙️)")
        self.chat_edit.returnPressed.connect(self._on_submit_chat)
        input_layout.addWidget(self.chat_edit)

        self.send_btn = QPushButton("➤")
        self.send_btn.setToolTip("Send text message to Hitasha")
        self.send_btn.clicked.connect(self._on_submit_chat)
        input_layout.addWidget(self.send_btn)

        self.mic_btn = QPushButton("🎙️")
        self.mic_btn.setToolTip("Live Voice Listen")
        self.mic_btn.clicked.connect(self.mic_listen_requested.emit)
        input_layout.addWidget(self.mic_btn)

        ctrls_layout.addWidget(self.input_frame)

        # 3c. Quick All-Rounder Action Toolbar
        self.control_bar = QWidget()
        self.control_bar.setStyleSheet("""
            QWidget {
                background: rgba(18, 19, 32, 0.90);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }
            QPushButton {
                background: transparent;
                color: #c7ceff;
                border: none;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 6px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(124, 77, 255, 0.4);
                color: #ffffff;
            }
        """)
        ctrl_layout = QHBoxLayout(self.control_bar)
        ctrl_layout.setContentsMargins(6, 2, 6, 2)
        ctrl_layout.setSpacing(4)

        # Screen Reader Manual Button
        self.watch_btn = QPushButton("👁️ Read")
        self.watch_btn.setToolTip("Ask Hitasha to read screen right now")
        self.watch_btn.clicked.connect(self.watch_screen_requested.emit)
        ctrl_layout.addWidget(self.watch_btn)

        # Roam / Walk
        self.roam_btn = QPushButton("🚶 Walk")
        self.roam_btn.setToolTip("Walk across screen")
        self.roam_btn.clicked.connect(self.roam_screen)
        ctrl_layout.addWidget(self.roam_btn)

        # Hover
        self.hover_btn = QPushButton("✨ Hover")
        self.hover_btn.setToolTip("Anti-gravity hover mode")
        self.hover_btn.clicked.connect(self.toggle_hover)
        ctrl_layout.addWidget(self.hover_btn)

        # Roast Me
        self.roast_btn = QPushButton("🔥 Roast")
        self.roast_btn.setToolTip("Playful Best Friend Roast")
        self.roast_btn.clicked.connect(self.roast_requested.emit)
        ctrl_layout.addWidget(self.roast_btn)

        # Stop / Exit
        self.stop_btn = QPushButton("🛑 Stop")
        self.stop_btn.setToolTip("Stop Hitasha App Completely")
        self.stop_btn.clicked.connect(self.manual_stop)
        ctrl_layout.addWidget(self.stop_btn)

        ctrls_layout.addWidget(self.control_bar)

        root_layout.addWidget(self.companion_controls)
        self.companion_controls.hide()  # Hidden by default so ONLY character is seen!

    def _set_initial_screen_position(self):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            self.base_x = geom.width() - self.width() - 40
            self.base_y = geom.height() - self.height() - 30
            self.move(self.base_x, self.base_y)

    def _load_3d_character(self):
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        html_path = os.path.join(base_dir, "assets", "character_3d.html")
        if os.path.exists(html_path):
            self.web_view.load(QUrl.fromLocalFile(html_path))

    # --- Whole-Screen Mouse Gaze Tracking ---
    def _track_screen_cursor(self):
        """Calculates global mouse position relative to Hitasha across the WHOLE screen."""
        if not self.is_active or self.is_sleeping:
            return
        try:
            cursor_pos = QCursor.pos()
            # Hitasha's character center in global screen coords:
            char_center = self.web_view.mapToGlobal(
                QPoint(self.web_view.width() // 2, self.web_view.height() // 2 - 25)
            )

            screen = QApplication.screenAt(cursor_pos) or QApplication.primaryScreen()
            if not screen:
                return
            geom = screen.geometry()
            half_w = max(1, geom.width() / 2)
            half_h = max(1, geom.height() / 2)

            # Normalized delta: dx > 0 when mouse is to right, dy > 0 when mouse is above
            dx = (cursor_pos.x() - char_center.x()) / half_w
            dy = -(cursor_pos.y() - char_center.y()) / half_h

            # Clamped range
            dx = max(-1.6, min(1.6, dx))
            dy = max(-1.6, min(1.6, dy))

            self.web_page.runJavaScript(f"if (window.setGlobalMouse) window.setGlobalMouse({dx:.3f}, {dy:.3f});")
        except Exception:
            pass

    # --- Click-to-Show Controls ---
    def toggle_controls(self, force_open: bool | None = None):
        """Toggles or sets the visibility of chat box and action buttons."""
        if force_open is True:
            self.controls_visible = True
        elif force_open is False:
            self.controls_visible = False
        else:
            self.controls_visible = not self.controls_visible

        if self.controls_visible:
            self.companion_controls.show()
            self.setFixedSize(280, 420)
            # Ensure window stays within screen bounds if near bottom edge
            screen = QApplication.screenAt(self.pos()) or QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                if self.y() + 425 > geom.bottom():
                    new_y = max(geom.top(), geom.bottom() - 425)
                    self.move(self.x(), new_y)
            self.chat_edit.setFocus()
            self.controls_auto_hide_timer.start(35000)
        else:
            self.companion_controls.hide()
            self.setFixedSize(250, 210)
            self.controls_auto_hide_timer.stop()

    def _maybe_auto_hide_controls(self):
        if self.chat_edit.text().strip():
            self.controls_auto_hide_timer.start(25000)
            return
        self.toggle_controls(force_open=False)

    def on_character_clicked(self):
        """Called when user clicks directly on Hitasha's 3D body."""
        was_hidden = not self.controls_visible
        self.toggle_controls()
        self.mate_clicked.emit()
        if was_hidden:
            clicks = [
                "Haan ji! Hitasha is right here! What's on your mind? ✨",
                "Aapne bulaya aur hum hazir! Tell me, dost, how can I help? 💖",
                "Listening carefully! What are we doing next? 🌸",
                "Controls opened! Chat with me or pick an action! 🚀"
            ]
            self.say(random.choice(clicks), Mood.HAPPY, auto_hide_seconds=6)

    def _on_submit_chat(self):
        text = self.chat_edit.text().strip()
        if not text:
            return
        self.chat_edit.clear()
        if not self.is_active:
            self.toggle_power()  # Auto-wake when user sends message
        self.controls_auto_hide_timer.start(35000)
        self.send_message_requested.emit(text)

    def toggle_power(self):
        """Main ON / OFF Power Switch."""
        self.is_active = not self.is_active
        self._update_power_button_style(self.is_active)
        self.power_toggled.emit(self.is_active)
        if self.is_active:
            self.set_animation("idle")
            self.say("Arre yaar, I'm back ON duty! Watching your screen and ready to chat! ✨", Mood.HAPPY, "anim:wave")
        else:
            if self.is_hovering:
                self.toggle_hover()
            self.set_animation("sleep")
            self.say("Hitasha switched OFF to standby! Click ON to wake me up! 💤", Mood.SLEEPY, "anim:sleep", auto_hide_seconds=5)

    def _update_power_button_style(self, is_on: bool):
        if is_on:
            self.power_btn.setText("🟢 HITASHA: ON (Active)")
            self.power_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 229, 255, 0.16);
                    border: 1.5px solid #00e5ff;
                    color: #00e5ff;
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 4px 14px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: rgba(0, 229, 255, 0.28);
                    color: #ffffff;
                }
            """)
        else:
            self.power_btn.setText("🔴 HITASHA: OFF (Standby)")
            self.power_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 75, 75, 0.16);
                    border: 1.5px solid #ff4b4b;
                    color: #ff8888;
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 4px 14px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: rgba(255, 75, 75, 0.28);
                    color: #ffffff;
                }
            """)

    def say(self, text: str, mood: str = Mood.HAPPY, anim_name: str | None = None, auto_hide_seconds: int = 8):
        """Displays text in floating speech bubble and triggers 3D animation."""
        self.speech_label.setText(text)
        self.bubble_frame.show()

        if anim_name:
            self.set_animation(anim_name)
        elif mood:
            self.set_mood(mood)

        if auto_hide_seconds > 0:
            self.bubble_timer.start(auto_hide_seconds * 1000)

    def _fade_bubble(self):
        """Smoothly hides speech bubble so only character remains on screen."""
        self.bubble_frame.hide()

    def set_animation(self, name: str):
        self.web_page.runJavaScript(f"if (window.setAnimation) window.setAnimation('{name}');")

    def set_mood(self, mood: str):
        self.web_page.runJavaScript(f"if (window.setMood) window.setMood('{mood}');")

    def set_talking(self, talking: bool):
        t_str = "true" if talking else "false"
        self.web_page.runJavaScript(f"if (window.setTalking) window.setTalking({t_str});")

    # --- Walking and Desktop Roaming Across the ENTIRE Screen ---
    def walk_to_pos(self, target_x: int, target_y: int, duration_ms: int = 4000):
        """
        Smoothly walks Hitasha across the screen in 2D to any destination
        while realistically turning to face the movement direction.
        """
        if not self.is_active:
            return
        current_x = self.x()
        current_y = self.y()

        dist = math.hypot(target_x - current_x, target_y - current_y)
        if dist < 25:
            return

        facing = "right" if target_x > current_x else "left"
        self.web_page.runJavaScript(f"if (window.setRoamState) window.setRoamState('walk', '{facing}');")

        self.walk_anim = QPropertyAnimation(self, b"pos")
        self.walk_anim.setDuration(duration_ms)
        self.walk_anim.setStartValue(self.pos())
        self.walk_anim.setEndValue(QPoint(target_x, target_y))
        self.walk_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.walk_anim.finished.connect(self._on_walk_arrived)
        self.walk_anim.start()

    def walk_to_x(self, target_x: int, duration_ms: int = 3500):
        """Fallback horizontal movement."""
        self.walk_to_pos(target_x, self.y(), duration_ms)

    def _on_walk_arrived(self):
        self.base_x = self.x()
        self.base_y = self.y()
        self.web_page.runJavaScript("if (window.setRoamState) window.setRoamState('idle', 'front');")
        zone_name = getattr(self, 'last_destination_zone', 'new spot')
        arrivals = [
            f"Strolled over to the {zone_name}! Watching your work from here!",
            "Look at those little 3D legs go! Arrived at my new observation post!",
            "Patrolled across your screen! Keeping your desktop 100% bug-free, dost!",
            "Walking break complete! Stretching my arms and ready to help!",
            "Checked out this corner of your screen! Everything looks great, keep it up!"
        ]
        self.say(random.choice(arrivals), Mood.HAPPY, anim_name="anim:stretch", auto_hide_seconds=5)
        # Proactively trigger screen reading and helpful suggestions from new vantage point
        QTimer.singleShot(1600, self.watch_screen_requested.emit)

    def roam_screen(self):
        """
        Picks a spot anywhere across the WHOLE screen (corners, edges, center, sky deck)
        and walks over like a living human!
        """
        if not self.is_active or self.is_sleeping:
            return
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geom = screen.availableGeometry()

        min_x = 30
        max_x = geom.width() - self.width() - 30
        min_y = 30
        max_y = geom.height() - self.height() - 30

        # 8 strategic observation spots covering every section of the screen
        zones = [
            (max_x, max_y, "bottom-right corner"),
            (min_x, max_y, "bottom-left dock"),
            (min_x, max_y // 2, "middle-left border"),
            (max_x, max_y // 2, "middle-right border"),
            (geom.width() // 2 - self.width() // 2, max_y, "bottom-center stage"),
            (max_x - 30, min_y + 20, "top-right control post"),
            (min_x + 30, min_y + 20, "top-left window view"),
            (geom.width() // 2 - self.width() // 2, min_y + 30, "top-center sky deck")
        ]

        curr_pos = self.pos()
        candidates = [z for z in zones if math.hypot(z[0] - curr_pos.x(), z[1] - curr_pos.y()) > 240]
        if not candidates:
            candidates = zones

        chosen_x, chosen_y, location_name = random.choice(candidates)
        # Organic jitter so position feels natural
        chosen_x = max(min_x, min(max_x, chosen_x + random.randint(-25, 25)))
        chosen_y = max(min_y, min(max_y, chosen_y + random.randint(-20, 20)))

        self.last_destination_zone = location_name
        dist = math.hypot(chosen_x - curr_pos.x(), chosen_y - curr_pos.y())
        duration = int(max(2500, min(6500, dist * 3.8)))
        self.walk_to_pos(chosen_x, chosen_y, duration)

    # --- Autonomous Life & Interaction Loop ---
    def _autonomous_life_tick(self):
        """
        Autonomous proactive behaviors to keep user engaged, busy, and entertained:
        walking all over screen, analysing active work, giving suggestions, riddles, trivia!
        """
        if not self.is_active or self.is_sleeping or self.is_dragging:
            return

        now = time.time()
        if now - self._last_autonomous_action < 35:
            return
        self._last_autonomous_action = now

        roll = random.random()
        if roll < 0.35:
            # 1. Roam & Stretch across screen
            self.say("Taking a quick walk to stretch my legs! Watch me go! 🚶", Mood.HAPPY, "anim:walk", auto_hide_seconds=4)
            QTimer.singleShot(600, self.roam_screen)
        elif roll < 0.65:
            # 2. Curious Screen Observation & Helpful Suggestions on Work
            self.set_animation("see")
            self.watch_screen_requested.emit()
        elif roll < 0.76:
            # 3. Micro-Interaction / Keeping User Busy & Entertained
            interactive_prompts = [
                ("Riddle time, dost! What has hands but cannot clap? (Click me and type your guess!)", Mood.HAPPY, "anim:think"),
                ("Quick puzzle! What has a head and a tail, but no body? Click me to answer! 🪙", Mood.SASSY, "anim:wave"),
                ("Brain teaser: What comes once in a minute, twice in a moment, but never in a thousand years? Guess it!", Mood.HAPPY, "anim:think"),
                ("Quick trivia check! Do you know why Python is called Python? It's not named after the snake! Ask me why!", Mood.HAPPY, "anim:talk"),
                ("Trivia alert! What was the first computer bug in history? Hint: it was an actual insect! 🪲", Mood.HAPPY, "anim:laugh"),
                ("Productivity sprint! What's the main task we need to finish in the next 30 minutes? Type it in chat!", Mood.HAPPY, "anim:wave"),
                ("Posture check, buddy! Straighten that spine, relax your shoulders, and drink some water! 🧘", Mood.LOVE, "anim:stretch"),
                ("Eye strain alert! Look away from the screen for 20 seconds at something far away! 20-20-20 rule! 👁️", Mood.HAPPY, "anim:see"),
                ("Doing a quick hand & shoulder stretch with you! Ahh, feels so good! ✨", Mood.HAPPY, "anim:stretch"),
            ]
            text, mood, anim = random.choice(interactive_prompts)
            self.say(text, mood, anim, auto_hide_seconds=12)
        else:
            # 4. Spontaneous lifelike animation & friendly banter
            anims = ["stretch", "dance", "wave", "sassy", "laugh"]
            chosen_anim = random.choice(anims)
            self.set_animation(chosen_anim)
            spontaneous_banter = [
                "Just vibing here on your screen! Hope you're having a productive day! ✨",
                "Chai break time anytime soon? My virtual cup is ready! ☕",
                "Supervising your workspace with 100% focus and 0% bugs! 💅",
                "Keep going, dost! You're making amazing progress today! 🌟"
            ]
            self.say(random.choice(spontaneous_banter), Mood.HAPPY, auto_hide_seconds=7)
            QTimer.singleShot(4000, lambda: self.set_animation("idle") if self.is_active else None)

    # --- Hover Physics ---
    def toggle_hover(self):
        if not self.is_active:
            return
        self.is_hovering = not self.is_hovering
        if self.is_hovering:
            self.base_y = self.y()
            self.base_x = self.x()
            self.hover_ticks = 0
            self.hover_btn.setText("🪂 Land")
            self.set_animation("hover")
            self.hover_timer.start(25)  # 40 FPS
            self.say("Levitating! Floating around in hover mode! ✨", Mood.LOVE, "anim:hover")
        else:
            self.hover_timer.stop()
            self.hover_btn.setText("✨ Hover")
            self.move(self.base_x, self.base_y)
            self.set_animation("idle")
            self.say("Landed safely back on your desk! 🧘", Mood.HAPPY)

    def _update_hover_physics(self):
        if not self.is_hovering:
            return
        self.hover_ticks += 1
        bob = math.sin(self.hover_ticks * 0.06) * 14 + math.cos(self.hover_ticks * 0.03) * 4
        self.move(self.base_x, int(self.base_y + bob))

    def manual_stop(self):
        """Clean manual stop and exit."""
        self.say("Alvida dost! Hitasha stopping now. See you soon! 👋", Mood.HAPPY, "anim:wave")
        QTimer.singleShot(1200, QApplication.instance().quit)

    # --- Dragging & Context Menu ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.globalPosition().toPoint() - self.pos()
            self.drag_mouse_origin = event.globalPosition().toPoint()
            self.set_animation("hover")
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_start_pos
            self.move(new_pos)
            self.base_x = new_pos.x()
            self.base_y = new_pos.y()
            event.accept()

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            dist = (event.globalPosition().toPoint() - self.drag_mouse_origin).manhattanLength()
            if dist < 6:
                # User clicked/tapped directly on character!
                self.on_character_clicked()
            else:
                # Completed drag across screen
                if not self.is_hovering and self.is_active:
                    self.set_animation("jump")
                    QTimer.singleShot(1200, lambda: self.set_animation("idle") if self.is_active else None)
            event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1b2d;
                color: #ffffff;
                border: 1px solid #3c3f68;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #7c4dff;
            }
        """)

        power_act = QAction("🔴 Turn OFF (Standby)" if self.is_active else "🟢 Turn ON (Active)", self)
        power_act.triggered.connect(self.toggle_power)
        menu.addAction(power_act)

        ctrl_act = QAction("✕ Hide Controls" if self.controls_visible else "💬 Show Chat & Controls", self)
        ctrl_act.triggered.connect(self.toggle_controls)
        menu.addAction(ctrl_act)

        watch_act = QAction("👁️ Read Screen Now", self)
        watch_act.triggered.connect(self.watch_screen_requested.emit)
        menu.addAction(watch_act)

        roam_act = QAction("🚶 Walk Across Screen", self)
        roam_act.triggered.connect(self.roam_screen)
        menu.addAction(roam_act)

        hover_act = QAction("✨ Toggle Hover Mode", self)
        hover_act.triggered.connect(self.toggle_hover)
        menu.addAction(hover_act)

        roast_act = QAction("🔥 Roast Me", self)
        roast_act.triggered.connect(self.roast_requested.emit)
        menu.addAction(roast_act)

        dance_act = QAction("🕺 Dance for Me", self)
        dance_act.triggered.connect(lambda: self.say("Let's party! Grooving right on your screen!", Mood.LOVE, "anim:dance"))
        menu.addAction(dance_act)

        stretch_act = QAction("🧘 Stretch With Me", self)
        stretch_act.triggered.connect(lambda: self.say("Arms up! Deep breath and stretch!", Mood.HAPPY, "anim:stretch"))
        menu.addAction(stretch_act)

        wave_act = QAction("👋 Wave Hello", self)
        wave_act.triggered.connect(lambda: self.say("Waving right at you, bestie!", Mood.HAPPY, "anim:wave"))
        menu.addAction(wave_act)

        menu.addSeparator()

        deck_act = QAction("💬 Open Command Deck & Settings", self)
        deck_act.triggered.connect(self.open_deck_requested.emit)
        menu.addAction(deck_act)

        stop_act = QAction("🛑 Stop & Exit Hitasha", self)
        stop_act.triggered.connect(self.manual_stop)
        menu.addAction(stop_act)

        menu.exec(QCursor.pos())
