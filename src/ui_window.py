"""
Modern Desktop Popup UI for Hitasha (Jarvis Companion).
Features frameless glassmorphism, draggable window, animated 3D avatar stage,
live speech bubble, full chat history, quick action chips, voice input,
compact pet mode, and custom settings dialog.
"""

import os
import sys
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer, pyqtSignal, QUrl
from PyQt6.QtGui import (
    QColor, QFont, QIcon, QAction, QPainter, QBrush, QPen
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QScrollArea, QFrame,
    QDialog, QComboBox, QSlider, QCheckBox, QSystemTrayIcon, QMenu,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings

from .avatar import Mood
from .voice_engine import VoiceEngine
from .personality import PersonalityEngine
from .tools_engine import ToolsEngine
from .config import save_config
from .screen_observer import ScreenObserver
from .reminders_engine import RemindersEngine
from .screen_mate import ScreenMateWindow


class Custom3DPage(QWebEnginePage):
    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        if "hitasha:click" in message or "mochi:click" in message:
            self.parent_widget.avatar_clicked.emit()


class Avatar3DWidget(QWidget):
    avatar_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 250)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView(self)
        self.web_page = Custom3DPage(self)
        self.web_view.setPage(self.web_page)
        self.web_page.setBackgroundColor(QColor(0, 0, 0, 0))
        self.web_view.setStyleSheet("background: transparent; border: none;")

        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)

        html_path = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "assets", "character_3d.html"
        ))
        self.web_view.load(QUrl.fromLocalFile(html_path))
        layout.addWidget(self.web_view)

    def set_talking(self, talking: bool):
        self.web_view.page().runJavaScript(f"window.setTalking({'true' if talking else 'false'});")

    def set_mood(self, mood: str, duration_ms: int = 4000):
        self.web_view.page().runJavaScript(f"window.setMood('{mood}');")

    def set_listening(self, listening: bool):
        if listening:
            self.web_view.page().runJavaScript("window.setAnimation('think');")
        else:
            self.web_view.page().runJavaScript("window.setAnimation('idle');")

    def set_animation(self, anim: str):
        self.web_view.page().runJavaScript(f"window.setAnimation('{anim}');")


# Premium Modern Glassmorphic Dark Stylesheet
APP_STYLE = """
QMainWindow {
    background-color: transparent;
}

QWidget#CentralCard {
    background-color: #161724;
    border: 1.5px solid #2f324d;
    border-radius: 20px;
}

/* Custom Title Bar */
QWidget#TitleBar {
    background-color: #1c1d2e;
    border-top-left-radius: 20px;
    border-top-right-radius: 20px;
    border-bottom: 1px solid #26283d;
    padding: 6px 12px;
}

QLabel#TitleText {
    color: #f0f0ff;
    font-size: 13px;
    font-weight: bold;
    font-family: 'Segoe UI', sans-serif;
}

QLabel#StatusBadge {
    color: #00e5ff;
    font-size: 11px;
    font-weight: 600;
}

QPushButton.TitleBtn {
    background-color: transparent;
    color: #9094b8;
    border: none;
    font-size: 14px;
    font-weight: bold;
    border-radius: 6px;
    min-width: 28px;
    min-height: 28px;
    max-width: 28px;
    max-height: 28px;
}

QPushButton.TitleBtn:hover {
    background-color: #2b2e47;
    color: #ffffff;
}

QPushButton.TitleCloseBtn:hover {
    background-color: #e53935;
    color: #ffffff;
}

/* Speech Bubble */
QFrame#SpeechBubble {
    background-color: #212338;
    border: 1.5px solid #3c3f63;
    border-radius: 14px;
    padding: 8px 12px;
}

QLabel#SpeechLabel {
    color: #ffffff;
    font-size: 13px;
    font-weight: 500;
    font-family: 'Segoe UI', sans-serif;
}

/* Quick Action Chips */
QPushButton.ActionChip {
    background-color: #22243a;
    color: #d1d5ff;
    border: 1px solid #353857;
    border-radius: 12px;
    padding: 5px 10px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'Segoe UI', sans-serif;
}

QPushButton.ActionChip:hover {
    background-color: #7c4dff;
    color: #ffffff;
    border: 1px solid #9e75ff;
}

QPushButton.ActionChip:pressed {
    background-color: #651fff;
}

/* Chat History */
QScrollArea#ChatScrollArea {
    background-color: transparent;
    border: none;
}

QWidget#ChatContentWidget {
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #181928;
    width: 6px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #3e4266;
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #7c4dff;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Input Area */
QWidget#InputBar {
    background-color: #1c1e30;
    border: 1.5px solid #313552;
    border-radius: 15px;
    padding: 4px 6px;
}

QLineEdit#ChatInput {
    background-color: transparent;
    border: none;
    color: #ffffff;
    font-size: 13px;
    font-family: 'Segoe UI', sans-serif;
    padding-left: 6px;
}

QLineEdit#ChatInput:focus {
    outline: none;
}

QPushButton.SendBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c4dff, stop:1 #00e5ff);
    color: #ffffff;
    border: none;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
    min-width: 32px;
    min-height: 32px;
}

QPushButton.SendBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #956aff, stop:1 #33ecff);
}

QPushButton.MicBtn {
    background-color: #272a42;
    color: #00e5ff;
    border: 1px solid #3a3e63;
    border-radius: 12px;
    font-size: 14px;
    min-width: 32px;
    min-height: 32px;
}

QPushButton.MicBtn:hover {
    background-color: #00e5ff;
    color: #12131e;
}

QPushButton.MicBtnListening {
    background-color: #ff4081;
    color: #ffffff;
    border: 2px solid #ff80ab;
    border-radius: 12px;
    font-size: 14px;
    min-width: 32px;
    min-height: 32px;
}

QPushButton.MuteBtn {
    background-color: transparent;
    color: #9094b8;
    border: none;
    font-size: 14px;
    min-width: 28px;
    min-height: 28px;
}

QPushButton.MuteBtn:hover {
    color: #ffffff;
}
"""


class SettingsDialog(QDialog):
    """Configuration Dialog for Voice, Personality, and Gemini AI."""

    def __init__(self, config: dict, voice_engine: VoiceEngine, parent=None):
        super().__init__(parent)
        self.config = config
        self.voice_engine = voice_engine
        self.setWindowTitle("Hitasha Settings")
        self.setFixedSize(380, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #181928;
                color: #ffffff;
            }
            QLabel {
                color: #d1d5ff;
                font-size: 12px;
                font-weight: 500;
            }
            QLineEdit, QComboBox {
                background-color: #24273d;
                border: 1px solid #383c5e;
                border-radius: 8px;
                color: #ffffff;
                padding: 6px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #24273d;
                color: #ffffff;
                selection-background-color: #7c4dff;
            }
            QPushButton {
                background-color: #7c4dff;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #956aff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title_label = QLabel("✨ Hitasha AI Settings")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00e5ff;")
        layout.addWidget(title_label)

        # Assistant Name
        layout.addWidget(QLabel("Assistant Name:"))
        self.name_edit = QLineEdit(self.config.get("assistant_name", "Hitasha"))
        layout.addWidget(self.name_edit)

        # Personality Mode
        layout.addWidget(QLabel("Personality Style:"))
        self.personality_combo = QComboBox()
        self.personality_combo.addItem("🎩 Jarvis AI (Loyal, witty, hyper-intelligent assistant)", "jarvis")
        self.personality_combo.addItem("💅 Sassy Bestie (Playful teasing & banter)", "sassy")
        self.personality_combo.addItem("🔥 Roast Master (Spicy savage roasts)", "roast")
        self.personality_combo.addItem("☕ Chill Buddy (Cozy, supportive & wholesome)", "chill")
        self.personality_combo.addItem("🧠 Smart Aleck (Clever wit & facts)", "smart")
        current_pers = self.config.get("personality", "jarvis")
        for i in range(self.personality_combo.count()):
            if self.personality_combo.itemData(i) == current_pers:
                self.personality_combo.setCurrentIndex(i)
                break
        layout.addWidget(self.personality_combo)

        # Voice Selector
        layout.addWidget(QLabel("Voice Model (SAPI5):"))
        self.voice_combo = QComboBox()
        voices = self.voice_engine.get_available_voices()
        current_voice = self.config.get("voice_id", "")
        self.voice_combo.addItem("System Default Voice", "")
        for v in voices:
            self.voice_combo.addItem(v["name"], v["id"])
            if v["id"] == current_voice:
                self.voice_combo.setCurrentIndex(self.voice_combo.count() - 1)
        layout.addWidget(self.voice_combo)

        # Speech Rate
        layout.addWidget(QLabel("Speech Speed:"))
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(120, 260)
        self.rate_slider.setValue(self.config.get("voice_rate", 185))
        layout.addWidget(self.rate_slider)

        # Gemini API Key
        layout.addWidget(QLabel("Gemini API Key (Optional for unlimited AI chat):"))
        self.api_key_edit = QLineEdit(self.config.get("gemini_api_key", ""))
        self.api_key_edit.setPlaceholderText("Paste Google Gemini API Key here")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_key_edit)

        # Checkboxes
        self.sfx_check = QCheckBox("Sound Effects & Audio Cues")
        self.sfx_check.setChecked(self.config.get("sound_effects", True))
        self.sfx_check.setStyleSheet("color: #ffffff;")
        layout.addWidget(self.sfx_check)

        # Save Button
        save_btn = QPushButton("Save Preferences")
        save_btn.clicked.connect(self._on_save)
        layout.addWidget(save_btn)

    def _on_save(self):
        self.config["assistant_name"] = self.name_edit.text().strip() or "Hitasha"
        self.config["personality"] = self.personality_combo.currentData()
        self.config["voice_id"] = self.voice_combo.currentData()
        self.config["voice_rate"] = self.rate_slider.value()
        self.config["gemini_api_key"] = self.api_key_edit.text().strip()
        self.config["sound_effects"] = self.sfx_check.isChecked()

        save_config(self.config)
        self.accept()


class MainWindow(QMainWindow):
    """
    Main Floating Desktop Companion Window.
    """

    def __init__(self, config: dict):
        super().__init__()
        self.config = config

        # Engines
        self.voice_engine = VoiceEngine(self.config)
        self.personality = PersonalityEngine(self.config)
        self.tools = ToolsEngine(self.voice_engine)
        self.screen_observer = ScreenObserver(self.config)
        self.reminders = RemindersEngine(self.config, self.personality.memory, self)

        # Screen Mate: Floating, roaming, transparent 3D desktop companion
        self.screen_mate = ScreenMateWindow(self.config)
        self.screen_mate.mate_clicked.connect(self._on_avatar_clicked)
        self.screen_mate.open_deck_requested.connect(self._toggle_deck_visibility)
        self.screen_mate.watch_screen_requested.connect(self._action_watch_screen)
        self.screen_mate.mic_listen_requested.connect(self._toggle_voice_listen)
        self.screen_mate.send_message_requested.connect(self._handle_user_message)
        self.screen_mate.roast_requested.connect(self._action_roast)
        self.screen_mate.power_toggled.connect(self._on_power_toggled)
        self.reminders.reminder_triggered.connect(self._on_proactive_reminder)

        # Proactive Continuous Screen Reading Loop
        self.last_observed_title = ""
        self.last_observed_app = ""
        self.last_observed_time = 0
        self.screen_watch_timer = QTimer(self)
        self.screen_watch_timer.timeout.connect(self._on_proactive_screen_tick)
        self.screen_watch_timer.start(25000)

        # Window Flags: Frameless & Stays on top
        self.setWindowTitle("Hitasha • Jarvis Assistant")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Window |
            (Qt.WindowType.WindowStaysOnTopHint if self.config.get("always_on_top", True) else Qt.WindowType.Widget)
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(390, 680)

        # Dragging support
        self.drag_position = QPoint()
        self.is_sleeping = False

        # Connect Signals
        self._connect_signals()

        # Build UI
        self._init_ui()
        self._init_tray()
        self._check_system_status()

        # Initial Welcome Dialogue & Launch Screen Mate
        self.screen_mate.show()
        QTimer.singleShot(600, self._initial_greeting)

    def _connect_signals(self):
        # Voice signals
        self.voice_engine.speech_started.connect(self._on_speech_started)
        self.voice_engine.speech_finished.connect(self._on_speech_finished)
        self.voice_engine.listening_started.connect(self._on_listening_started)
        self.voice_engine.listening_finished.connect(self._on_listening_finished)
        self.voice_engine.speech_recognized.connect(self._handle_user_message)
        self.voice_engine.error_occurred.connect(self._on_voice_error)

        # Tools signals
        self.tools.timer_finished.connect(self._on_timer_finished)
        self.tools.action_completed.connect(self._on_action_completed)

    def _init_ui(self):
        self.setStyleSheet(APP_STYLE)

        # Central Card Container
        self.central_card = QWidget(self)
        self.central_card.setObjectName("CentralCard")
        card_layout = QVBoxLayout(self.central_card)
        card_layout.setContentsMargins(0, 0, 0, 10)
        card_layout.setSpacing(8)

        # 1. Sleek Title Bar
        self.title_bar = QWidget()
        self.title_bar.setObjectName("TitleBar")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(12, 6, 8, 6)

        # Status Dot & Title
        self.status_dot = QLabel("🟢")
        self.title_label = QLabel(f"{self.config.get('assistant_name', 'Hitasha')} • Jarvis Assistant")
        self.title_label.setObjectName("TitleText")

        # Window Controls
        self.pin_btn = QPushButton("📌")
        self.pin_btn.setProperty("class", "TitleBtn")
        self.pin_btn.setToolTip("Toggle Always on Top")
        self.pin_btn.clicked.connect(self._toggle_always_on_top)

        self.compact_btn = QPushButton("🔘")
        self.compact_btn.setProperty("class", "TitleBtn")
        self.compact_btn.setToolTip("Compact Pet Mode")
        self.compact_btn.clicked.connect(self._toggle_compact_mode)

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setProperty("class", "TitleBtn")
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self._open_settings)

        self.min_btn = QPushButton("─")
        self.min_btn.setProperty("class", "TitleBtn")
        self.min_btn.setToolTip("Minimize to Tray")
        self.min_btn.clicked.connect(self.hide)

        self.close_btn = QPushButton("✕")
        self.close_btn.setProperty("class", "TitleBtn TitleCloseBtn")
        self.close_btn.setToolTip("Close App")
        self.close_btn.clicked.connect(QApplication.instance().quit)

        title_layout.addWidget(self.status_dot)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self.mate_btn = QPushButton("🚶")
        self.mate_btn.setProperty("class", "TitleBtn")
        self.mate_btn.setToolTip("Free Roam Screen Mate (Walks & Hovers on Desktop)")
        self.mate_btn.clicked.connect(self._toggle_screen_mate)

        self.sleep_btn = QPushButton("💤")
        self.sleep_btn.setProperty("class", "TitleBtn")
        self.sleep_btn.setToolTip("Manual Sleep / Wake (Hitasha Power Nap)")
        self.sleep_btn.clicked.connect(self._toggle_sleep)

        self.stop_btn = QPushButton("🛑")
        self.stop_btn.setProperty("class", "TitleBtn TitleCloseBtn")
        self.stop_btn.setToolTip("Stop Hitasha Desktop App")
        self.stop_btn.clicked.connect(self._stop_hitasha)

        title_layout.addWidget(self.pin_btn)
        title_layout.addWidget(self.mate_btn)
        title_layout.addWidget(self.sleep_btn)
        title_layout.addWidget(self.compact_btn)
        title_layout.addWidget(self.settings_btn)
        title_layout.addWidget(self.min_btn)
        title_layout.addWidget(self.stop_btn)
        title_layout.addWidget(self.close_btn)

        card_layout.addWidget(self.title_bar)

        # 2. Avatar Display Stage
        self.stage_container = QWidget()
        stage_layout = QVBoxLayout(self.stage_container)
        stage_layout.setContentsMargins(10, 2, 10, 4)
        stage_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.avatar = Avatar3DWidget(self)
        self.avatar.avatar_clicked.connect(self._on_avatar_clicked)
        stage_layout.addWidget(self.avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Live Speech Bubble (Right under avatar)
        self.speech_bubble = QFrame()
        self.speech_bubble.setObjectName("SpeechBubble")
        bubble_layout = QHBoxLayout(self.speech_bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)

        self.speech_text = QLabel("Waking up and checking on my favorite human! ✨")
        self.speech_text.setObjectName("SpeechLabel")
        self.speech_text.setWordWrap(True)
        self.speech_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bubble_layout.addWidget(self.speech_text)

        stage_layout.addWidget(self.speech_bubble)
        card_layout.addWidget(self.stage_container)

        # 3. Quick Action Chips (Horizontal Scroll or Flex Row)
        chips_container = QWidget()
        chips_layout = QHBoxLayout(chips_container)
        chips_layout.setContentsMargins(10, 0, 10, 2)
        chips_layout.setSpacing(6)

        actions = [
            ("👁️ Watch", self._action_watch_screen),
            ("🚶 Roam", self._action_roam),
            ("✨ Hover", self._action_hover),
            ("📝 Notes", self._action_notes),
            ("🔥 Roast", self._action_roast),
            ("🕺 Dance", self._action_dance),
            ("🚶 Walk", self._action_walk),
            ("👋 Wave", self._action_wave),
            ("🤣 Joke", self._action_joke),
            ("🔮 8-Ball", self._action_8ball),
            ("📸 Snap", self._action_screenshot),
            ("💻 PC Stats", self._action_vitals),
        ]
        for label, callback in actions:
            btn = QPushButton(label)
            btn.setProperty("class", "ActionChip")
            btn.clicked.connect(callback)
            chips_layout.addWidget(btn)

        card_layout.addWidget(chips_container)

        # 4. Scrollable Chat History Feed
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setObjectName("ChatScrollArea")
        self.chat_scroll.setWidgetResizable(True)

        self.chat_content = QWidget()
        self.chat_content.setObjectName("ChatContentWidget")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(12, 4, 12, 4)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_content)
        card_layout.addWidget(self.chat_scroll)

        # 5. Interactive Input Bar
        input_container = QWidget()
        input_wrap = QHBoxLayout(input_container)
        input_wrap.setContentsMargins(12, 2, 12, 4)

        self.input_bar = QWidget()
        self.input_bar.setObjectName("InputBar")
        bar_layout = QHBoxLayout(self.input_bar)
        bar_layout.setContentsMargins(6, 4, 6, 4)
        bar_layout.setSpacing(6)

        # Mic Button
        self.mic_btn = QPushButton("🎙️")
        self.mic_btn.setProperty("class", "MicBtn")
        self.mic_btn.setToolTip("Click to Speak (Speech-to-Text)")
        self.mic_btn.clicked.connect(self._toggle_voice_listen)

        # Text Input
        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("ChatInput")
        self.chat_input.setPlaceholderText("Talk with Hitasha, say 'Hey Hitasha', ask for a roast...")
        self.chat_input.returnPressed.connect(self._on_send_clicked)

        # Mute Voice Button
        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setProperty("class", "MuteBtn")
        self.mute_btn.setToolTip("Mute/Unmute Speech Voice")
        self.mute_btn.clicked.connect(self._toggle_voice_mute)

        # Send Button
        self.send_btn = QPushButton("➤")
        self.send_btn.setProperty("class", "SendBtn")
        self.send_btn.clicked.connect(self._on_send_clicked)

        bar_layout.addWidget(self.mic_btn)
        bar_layout.addWidget(self.chat_input)
        bar_layout.addWidget(self.mute_btn)
        bar_layout.addWidget(self.send_btn)

        input_wrap.addWidget(self.input_bar)
        card_layout.addWidget(input_container)

        self.setCentralWidget(self.central_card)

        # Restore window position if saved
        pos = self.config.get("window_pos", [1200, 350])
        self.move(pos[0], pos[1])

    def _check_system_status(self):
        """Detects whether Local GPU model or Online AI is active and updates badge."""
        is_gpu, gpu_desc = self.personality.local_llm.check_connection()
        if is_gpu:
            self.status_dot.setText("🟣")
            self.status_dot.setToolTip(f"RTX 5050 GPU Active • {gpu_desc}")
        elif self.personality.gemini_client:
            self.status_dot.setText("🟢")
            self.status_dot.setToolTip("Online • Gemini AI & Indian Female Voice Active")
        else:
            self.status_dot.setText("🟡")
            self.status_dot.setToolTip("Offline Mode • Local Desi Banter & SAPI5/Edge Active")

    def _toggle_sleep(self):
        """Manual Sleep / Wake toggle for entire assistant."""
        if hasattr(self, "screen_mate"):
            self.screen_mate.toggle_power()

    def _on_power_toggled(self, is_on: bool):
        """Called when Screen Mate power button is toggled ON / OFF."""
        self.is_sleeping = not is_on
        if is_on:
            self.avatar.set_animation("idle")
            self.sleep_btn.setText("💤")
            self.sleep_btn.setToolTip("Standby / Power Nap")
            if hasattr(self, 'screen_watch_timer'):
                self.screen_watch_timer.start(25000)
            self.voice_engine.speak("Arre yaar, I'm back ON duty! Watching your screen and ready to chat!")
        else:
            if hasattr(self, 'screen_watch_timer'):
                self.screen_watch_timer.stop()
            self.voice_engine.stop_speaking()
            self.avatar.set_animation("sleep")
            self.sleep_btn.setText("⚡")
            self.sleep_btn.setToolTip("Wake Up Hitasha")

    def _on_proactive_screen_tick(self):
        """Continuous screen reader loop. Proactively reacts to the user's active window."""
        if not hasattr(self, 'screen_mate') or not self.screen_mate.is_active or self.is_sleeping:
            return
        if self.voice_engine.is_speaking or self.voice_engine.is_listening:
            return

        import time
        now = time.time()
        win_info = self.screen_observer.get_active_window_info()
        curr_title = win_info.get("title", "")
        curr_app = win_info.get("app_name", "")

        # Ignore our own app windows
        if not curr_title or "hitasha" in curr_title.lower() or "character_3d" in curr_title.lower():
            return

        window_changed = (curr_title != self.last_observed_title or curr_app != self.last_observed_app)
        time_elapsed = now - self.last_observed_time

        # React if window changed (after at least 35s since last observation) or after 85s continuous activity
        if (window_changed and time_elapsed >= 35) or (time_elapsed >= 85):
            self.last_observed_title = curr_title
            self.last_observed_app = curr_app
            self.last_observed_time = now

            comment, mood = self.screen_observer.watch_and_comment()
            if comment:
                self._bot_say(comment, mood)

    def _stop_hitasha(self):
        """Clean manual stop and app shutdown."""
        self._bot_say("Alvida dost! Hitasha stopping now. See you soon! 👋", Mood.HAPPY, "anim:wave")
        QTimer.singleShot(1200, QApplication.instance().quit)

    def _init_tray(self):
        """System tray icon integration."""
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self._create_tray_pixmap())

        menu = QMenu()
        show_action = QAction("👁️ Toggle Command Deck", self)
        show_action.triggered.connect(self._toggle_deck_visibility)

        mate_action = QAction("🚶 Toggle Screen Mate", self)
        mate_action.triggered.connect(self._toggle_screen_mate)

        sleep_action = QAction("💤 Sleep / ⚡ Wake", self)
        sleep_action.triggered.connect(self._toggle_sleep)

        roast_action = QAction("🔥 Roast Me", self)
        roast_action.triggered.connect(lambda: (self.showNormal(), self._action_roast()))

        snap_action = QAction("📸 Screenshot", self)
        snap_action.triggered.connect(self._action_screenshot)

        stop_action = QAction("🛑 Stop Hitasha", self)
        stop_action.triggered.connect(self._stop_hitasha)

        menu.addAction(show_action)
        menu.addAction(mate_action)
        menu.addAction(sleep_action)
        menu.addSeparator()
        menu.addAction(roast_action)
        menu.addAction(snap_action)
        menu.addSeparator()
        menu.addAction(stop_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _create_tray_pixmap(self):
        from PyQt6.QtGui import QPixmap
        pix = QPixmap(32, 32)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(124, 77, 255))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(2, 2, 28, 28)
        p.setBrush(QColor(0, 229, 255))
        p.drawEllipse(8, 10, 5, 5)
        p.drawEllipse(19, 10, 5, 5)
        p.end()
        return QIcon(pix)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    # --- Dragging & Window Interaction ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            # Save position
            self.config["window_pos"] = [self.x(), self.y()]
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = QPoint()
        save_config(self.config)

    # --- Message Handling ---
    def _initial_greeting(self):
        name = self.config.get("assistant_name", "Hitasha")
        welcome = f"Namaste dost! {name} is right here on your desktop! Always watching your screen and ready to chat! ✨"
        self._bot_say(welcome, Mood.HAPPY, "anim:wave")

    def _on_send_clicked(self):
        text = self.chat_input.text().strip()
        if not text:
            return
        self.chat_input.clear()
        self._handle_user_message(text)

    def _handle_user_message(self, text: str):
        # 1. Add user bubble to chat
        self._add_chat_bubble(text, is_user=True)
        self.avatar.set_mood(Mood.THINKING)

        # 2. Generate response via Personality Engine
        reply, mood, action_code = self.personality.generate_response(text)

        # 3. Execute tool action, animation, or screen mate action
        if action_code:
            if action_code.startswith("anim:"):
                anim_name = action_code.split(":", 1)[1]
                self.avatar.set_animation(anim_name)
                if hasattr(self, 'screen_mate') and self.screen_mate.isVisible():
                    self.screen_mate.set_animation(anim_name)
            elif action_code == "action:screen_watch":
                comment, watch_mood = self.screen_observer.watch_and_comment()
                reply = f"{reply}\n{comment}"
                mood = watch_mood
            elif action_code == "mate:walk_left":
                if hasattr(self, 'screen_mate'):
                    if not self.screen_mate.isVisible():
                        self.screen_mate.show()
                    self.screen_mate.walk_to_x(max(50, self.screen_mate.x() - 350))
            elif action_code == "mate:walk_right":
                if hasattr(self, 'screen_mate'):
                    if not self.screen_mate.isVisible():
                        self.screen_mate.show()
                    self.screen_mate.walk_to_x(self.screen_mate.x() + 350)
            elif action_code == "mate:roam":
                if hasattr(self, 'screen_mate'):
                    if not self.screen_mate.isVisible():
                        self.screen_mate.show()
                    self.screen_mate.roam_screen()
            elif action_code == "mate:hover":
                if hasattr(self, 'screen_mate'):
                    if not self.screen_mate.isVisible():
                        self.screen_mate.show()
                    if not self.screen_mate.is_hovering:
                        self.screen_mate.toggle_hover()
            elif action_code == "mate:land":
                if hasattr(self, 'screen_mate') and self.screen_mate.is_hovering:
                    self.screen_mate.toggle_hover()
            else:
                action_msg, action_mood = self.tools.execute_action(action_code)
                reply = f"{reply}\n{action_msg}"
                mood = action_mood

        # 4. Speak & update UI
        self._bot_say(reply, mood)

    def _bot_say(self, text: str, mood: str = Mood.HAPPY, anim_name: str | None = None):
        self.speech_text.setText(text)
        self.avatar.set_mood(mood)
        self._add_chat_bubble(text, is_user=False)
        self.voice_engine.speak(text)
        if hasattr(self, 'screen_mate') and self.screen_mate.isVisible():
            self.screen_mate.say(text, mood, anim_name)

    def _on_avatar_clicked(self):
        import random
        pokes = [
            ("Hey! Don't poke my glass visor, that tickles! 😆", Mood.LAUGHING),
            ("Careful! Clicking me increases my sass levels by 15%! 💅", Mood.SASSY),
            ("Aww, petting your favorite desktop companion? Purring in binary... ✨", Mood.LOVE),
            ("Boop! Visor tapped! What can your bestie do for you? 💖", Mood.LOVE),
            ("I was resting my digital eyelids! Just kidding, always here for you!", Mood.HAPPY)
        ]
        quote, mood = random.choice(pokes)
        self.voice_engine.play_sound("pop")
        self._bot_say(quote, mood)

    def _add_chat_bubble(self, text: str, is_user: bool):
        bubble_frame = QFrame()
        b_layout = QHBoxLayout(bubble_frame)
        b_layout.setContentsMargins(0, 2, 0, 2)

        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        if is_user:
            msg_label.setStyleSheet("""
                background-color: #2e2850;
                color: #ffffff;
                border: 1px solid #4a3f7a;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
            """)
            b_layout.addStretch()
            b_layout.addWidget(msg_label)
        else:
            msg_label.setStyleSheet("""
                background-color: #1f2238;
                color: #e0e4ff;
                border: 1px solid #33385c;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
            """)
            b_layout.addWidget(msg_label)
            b_layout.addStretch()

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble_frame)

        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    # --- Voice Engine Callbacks ---
    def _on_speech_started(self, text: str):
        self.avatar.set_talking(True)
        if hasattr(self, 'screen_mate') and self.screen_mate.isVisible():
            self.screen_mate.set_talking(True)

    def _on_speech_finished(self):
        self.avatar.set_talking(False)
        if hasattr(self, 'screen_mate') and self.screen_mate.isVisible():
            self.screen_mate.set_talking(False)

    def _toggle_voice_listen(self):
        if self.voice_engine.is_listening:
            return
        self.voice_engine.listen_once()

    def _on_listening_started(self):
        self.mic_btn.setProperty("class", "MicBtnListening")
        self.mic_btn.setStyleSheet("background-color: #ff4081; color: white;")
        self.avatar.set_listening(True)
        self.speech_text.setText("Listening carefully... Speak now, friend! 🎙️")
        if hasattr(self, 'screen_mate') and self.screen_mate.isVisible():
            self.screen_mate.say("Listening... Speak now, dost! 🎙️", Mood.THINKING)
            self.screen_mate.set_animation("think")

    def _on_listening_finished(self):
        self.mic_btn.setProperty("class", "MicBtn")
        self.mic_btn.setStyleSheet("")
        self.avatar.set_listening(False)
        if hasattr(self, 'screen_mate') and self.screen_mate.isVisible():
            self.screen_mate.set_animation("idle")

    def _on_voice_error(self, err_msg: str):
        self._bot_say(err_msg, Mood.SASSY)

    def _toggle_voice_mute(self):
        current = self.config.get("voice_enabled", True)
        self.config["voice_enabled"] = not current
        self.mute_btn.setText("🔇" if not self.config["voice_enabled"] else "🔊")
        save_config(self.config)
        if not self.config["voice_enabled"]:
            self.voice_engine.stop_speaking()

    # --- Tool Callbacks ---
    def _on_timer_finished(self, msg: str):
        self.showNormal()
        self.activateWindow()
        self._bot_say(msg, Mood.SHOCKED)

    def _on_action_completed(self, msg: str, mood: str):
        self._bot_say(msg, mood)

    # --- Quick Action Chip Handlers ---
    def _action_watch_screen(self):
        self._handle_user_message("Watch screen with me")

    def _action_roam(self):
        self._handle_user_message("Roam screen")

    def _action_hover(self):
        self._handle_user_message("Hover")

    def _action_roast(self):
        self._handle_user_message("Roast me")

    def _action_dance(self):
        self._handle_user_message("Dance")

    def _action_walk(self):
        self._handle_user_message("Walk around")

    def _action_wave(self):
        self._handle_user_message("Wave at me")

    def _action_joke(self):
        self._handle_user_message("Tell me a joke")

    def _action_8ball(self):
        self._handle_user_message("Magic 8-Ball fortune")

    def _action_trivia(self):
        self._handle_user_message("Trivia quiz")

    def _action_screenshot(self):
        self._handle_user_message("Take a screenshot")

    def _action_notes(self):
        self._handle_user_message("Show my notes")

    def _action_vitals(self):
        self._handle_user_message("How's my PC doing?")

    # --- Title Bar Actions ---
    def _toggle_always_on_top(self):
        current = self.config.get("always_on_top", True)
        self.config["always_on_top"] = not current
        save_config(self.config)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.config["always_on_top"])
        self.show()

    def _toggle_compact_mode(self):
        """Toggles between expanded companion deck and compact pet widget."""
        is_compact = self.config.get("compact_mode", False)
        self.config["compact_mode"] = not is_compact
        save_config(self.config)

        if self.config["compact_mode"]:
            self.chat_scroll.hide()
            self.input_bar.parentWidget().hide()
            self.resize(380, 360)
            self.compact_btn.setText("🔲")
            self.compact_btn.setToolTip("Expand Companion Deck")
        else:
            self.chat_scroll.show()
            self.input_bar.parentWidget().show()
            self.resize(390, 680)
            self.compact_btn.setText("🔘")
            self.compact_btn.setToolTip("Compact Pet Mode")

    def _toggle_screen_mate(self):
        """Toggles between Command Deck and Desktop Screen Mate."""
        if self.screen_mate.isVisible():
            self.screen_mate.hide()
        else:
            self.screen_mate.show()
            self.screen_mate.say("Hitasha is out on your desktop! Walking and hovering with you!", Mood.HAPPY, "anim:wave")

    def _toggle_deck_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()

    def _on_proactive_reminder(self, msg: str, mood: str, anim: str):
        self._bot_say(msg, mood, anim_name=anim.split(":", 1)[1] if ":" in anim else None)

    def _open_settings(self):
        dlg = SettingsDialog(self.config, self.voice_engine, self)
        if dlg.exec():
            # Refresh personality and title
            name = self.config.get("assistant_name", "Hitasha")
            self.title_label.setText(f"{name} • Jarvis Assistant")
            self.personality.refresh_gemini()
            if hasattr(self, 'screen_observer'):
                self.screen_observer.refresh_gemini()
            self.voice_engine.play_sound("pop")
