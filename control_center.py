"""
Hitasha Control Center - Windows Desktop Application
A modern, sleek Windows 11 style control panel to Start, Stop, Monitor, and Configure
Hitasha 3D AI Assistant.
"""

import os
import sys
import time
import winreg
import subprocess
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor, QPixmap, QPainter, QBrush, QPen
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QDialog, QLineEdit,
    QComboBox, QSlider, QCheckBox, QSystemTrayIcon, QMenu,
    QGraphicsDropShadowEffect, QMessageBox, QTabWidget, QGridLayout,
    QProgressBar, QSizePolicy
)

try:
    import psutil
except ImportError:
    psutil = None

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PNG = os.path.join(PROJECT_DIR, "assets", "hitasha_icon.png")
ICON_ICO = os.path.join(PROJECT_DIR, "assets", "hitasha_icon.ico")
PYTHON_EXE = os.path.join(PROJECT_DIR, ".venv", "Scripts", "python.exe")
PYTHONW_EXE = os.path.join(PROJECT_DIR, ".venv", "Scripts", "pythonw.exe")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.json")


def is_hitasha_running():
    """Returns (is_running, pids, total_ram_mb, avg_cpu, uptime_seconds)."""
    if not psutil:
        return False, [], 0, 0, 0

    pids = []
    total_rss = 0
    total_cpu = 0
    oldest_create_time = None

    for p in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            cmdline = p.info.get('cmdline') or []
            cmd_str = " ".join(cmdline).lower()
            name = (p.info.get('name') or '').lower()

            if 'python' in name and 'main.py' in cmd_str:
                if not any(m in cmd_str for m in ['control_center', 'manager']):
                    pid = p.info['pid']
                    pids.append(pid)
                    try:
                        mem = p.memory_info().rss
                        total_rss += mem
                        cpu = p.cpu_percent(interval=None)
                        total_cpu += cpu
                        ctime = p.info.get('create_time')
                        if ctime:
                            if oldest_create_time is None or ctime < oldest_create_time:
                                oldest_create_time = ctime
                    except Exception:
                        pass
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    uptime_sec = 0
    if oldest_create_time:
        uptime_sec = max(0, int(time.time() - oldest_create_time))

    ram_mb = round(total_rss / (1024 * 1024), 1)
    return len(pids) > 0, pids, ram_mb, round(total_cpu, 1), uptime_sec


def get_autostart_status():
    """Checks if Hitasha is set to run on Windows startup."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, "HitashaAssistant")
            return bool(val)
    except FileNotFoundError:
        return False
    except Exception:
        return False


def set_autostart_status(enable: bool):
    """Enables or disables Hitasha run on Windows startup."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                cmd = f'"{PYTHONW_EXE}" "{os.path.join(PROJECT_DIR, "main.py")}"'
                winreg.SetValueEx(key, "HitashaAssistant", 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, "HitashaAssistant")
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"[Autostart Error] {e}")
        return False


def create_desktop_shortcut():
    """Creates a Windows desktop shortcut with icon."""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        desktop_dir = shell.SpecialFolders("Desktop")
        shortcut_path = os.path.join(desktop_dir, "Hitasha Control Center.lnk")

        vbs_launcher = os.path.join(PROJECT_DIR, "Start_Control_Center.vbs")
        
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = "wscript.exe"
        shortcut.Arguments = f'"{vbs_launcher}"'
        shortcut.WorkingDirectory = PROJECT_DIR
        shortcut.Description = "Hitasha 3D AI Assistant Control Center"
        if os.path.exists(ICON_ICO):
            shortcut.IconLocation = f"{ICON_ICO},0"
        shortcut.save()
        return True, shortcut_path
    except Exception as e:
        return False, str(e)


# Background Worker for Start / Stop / Restart actions
class ActionWorker(QThread):
    finished_signal = pyqtSignal(str, bool, str)  # action, success, message

    def __init__(self, action_name):
        super().__init__()
        self.action_name = action_name

    def run(self):
        try:
            if self.action_name == "start":
                from launch import launch
                success, pids = launch()
                msg = f"Started successfully (PID: {pids})" if success else "Failed to start"
                self.finished_signal.emit("start", success, msg)

            elif self.action_name == "stop":
                from stop import stop_hitasha
                count = stop_hitasha()
                self.finished_signal.emit("stop", True, f"Terminated {count} instance(s)")

            elif self.action_name == "restart":
                from stop import stop_hitasha
                stop_hitasha()
                time.sleep(1.5)
                from launch import launch
                success, pids = launch()
                msg = f"Restarted successfully (PID: {pids})" if success else "Failed to restart"
                self.finished_signal.emit("restart", success, msg)

            elif self.action_name == "voice_test":
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 185)
                    engine.say("Namaste! Hitasha system is fully operational and ready to assist you.")
                    engine.runAndWait()
                    self.finished_signal.emit("voice_test", True, "Voice test completed successfully")
                except Exception as e:
                    self.finished_signal.emit("voice_test", False, str(e))

        except Exception as e:
            self.finished_signal.emit(self.action_name, False, str(e))


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hitasha Configuration & Preferences")
        self.setFixedSize(520, 560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1117;
                color: #e6edf3;
                font-family: 'Segoe UI', Inter, sans-serif;
            }
            QLabel {
                color: #e6edf3;
                font-size: 13px;
                font-weight: 500;
            }
            QLineEdit, QComboBox {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                color: #e6edf3;
                padding: 8px 12px;
                font-size: 13px;
                selection-background-color: #1f6feb;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #58a6ff;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QCheckBox {
                color: #e6edf3;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #30363d;
                background-color: #161b22;
            }
            QCheckBox::indicator:checked {
                background-color: #238636;
                border-color: #2ea043;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #21262d;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #58a6ff;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 1px solid #58a6ff;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #238636;
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
            QPushButton#btnCancel {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
            }
            QPushButton#btnCancel:hover {
                background-color: #30363d;
            }
        """)

        from src.config import load_config
        self.config = load_config()

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("⚙️ Hitasha Assistant Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #58a6ff;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Assistant Name
        grid.addWidget(QLabel("Assistant Name:"), 0, 0)
        self.name_edit = QLineEdit(self.config.get("assistant_name", "Hitasha"))
        grid.addWidget(self.name_edit, 0, 1)

        # Personality
        grid.addWidget(QLabel("Personality:"), 1, 0)
        self.personality_combo = QComboBox()
        self.personality_combo.addItems(["jarvis", "sassy", "smart", "chill", "roast"])
        self.personality_combo.setCurrentText(self.config.get("personality", "jarvis"))
        grid.addWidget(self.personality_combo, 1, 1)

        # Response Style
        grid.addWidget(QLabel("Response Style:"), 2, 0)
        self.style_combo = QComboBox()
        self.style_combo.addItems(["simple_indian_english", "standard_english", "casual_hindi_english"])
        self.style_combo.setCurrentText(self.config.get("response_style", "simple_indian_english"))
        grid.addWidget(self.style_combo, 2, 1)

        # Gemini API Key
        grid.addWidget(QLabel("Gemini API Key:"), 3, 0)
        self.api_key_edit = QLineEdit(self.config.get("gemini_api_key", ""))
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Optional - powers cloud AI vision")
        grid.addWidget(self.api_key_edit, 3, 1)

        # Voice Enabled Checkbox
        self.voice_check = QCheckBox("Enable Voice Speech (TTS)")
        self.voice_check.setChecked(self.config.get("voice_enabled", True))
        grid.addWidget(self.voice_check, 4, 0, 1, 2)

        # Always on top
        self.top_check = QCheckBox("Keep 3D Avatar Always On Top")
        self.top_check.setChecked(self.config.get("always_on_top", True))
        grid.addWidget(self.top_check, 5, 0, 1, 2)

        # Sound effects
        self.sfx_check = QCheckBox("Sound Effects & Audio Cues")
        self.sfx_check.setChecked(self.config.get("sound_effects", True))
        grid.addWidget(self.sfx_check, 6, 0, 1, 2)

        # Voice Rate
        grid.addWidget(QLabel("Speech Rate (Speed):"), 7, 0)
        rate_layout = QHBoxLayout()
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(120, 260)
        self.rate_slider.setValue(self.config.get("voice_rate", 185))
        self.rate_label = QLabel(f"{self.rate_slider.value()} WPM")
        self.rate_slider.valueChanged.connect(lambda v: self.rate_label.setText(f"{v} WPM"))
        rate_layout.addWidget(self.rate_slider)
        rate_layout.addWidget(self.rate_label)
        grid.addLayout(rate_layout, 7, 1)

        layout.addLayout(grid)
        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save Settings")
        self.btn_save.clicked.connect(self.save_settings)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def save_settings(self):
        from src.config import save_config
        self.config["assistant_name"] = self.name_edit.text().strip() or "Hitasha"
        self.config["personality"] = self.personality_combo.currentText()
        self.config["response_style"] = self.style_combo.currentText()
        self.config["gemini_api_key"] = self.api_key_edit.text().strip()
        self.config["voice_enabled"] = self.voice_check.isChecked()
        self.config["always_on_top"] = self.top_check.isChecked()
        self.config["sound_effects"] = self.sfx_check.isChecked()
        self.config["voice_rate"] = self.rate_slider.value()
        save_config(self.config)
        self.accept()


class HitashaControlCenter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hitasha Control Center")
        self.setFixedSize(680, 720)
        self.is_busy = False

        if os.path.exists(ICON_PNG):
            self.setWindowIcon(QIcon(ICON_PNG))
        elif os.path.exists(ICON_ICO):
            self.setWindowIcon(QIcon(ICON_ICO))

        self.setup_ui()
        self.setup_tray()

        # Timer to poll Hitasha state every 1 second
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.update_status_loop)
        self.poll_timer.start(1000)

        # Initial log
        self.log("Hitasha Control Center loaded successfully.", "INFO")
        self.update_status_loop()

    def setup_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        central.setStyleSheet("background-color: #0b0f17; font-family: 'Segoe UI', Inter, sans-serif;")

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(22, 20, 22, 20)
        main_layout.setSpacing(16)

        # 1. Header with logo and subtitle
        header_layout = QHBoxLayout()
        
        # Logo icon
        logo_label = QLabel()
        if os.path.exists(ICON_PNG):
            pixmap = QPixmap(ICON_PNG).scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        header_layout.addWidget(logo_label)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        app_title = QLabel("HITASHA CONTROL CENTER")
        app_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #f0f6fc; letter-spacing: 1px;")
        app_sub = QLabel("3D Jarvis Desktop Companion & Virtual Assistant Management")
        app_sub.setStyleSheet("font-size: 12px; color: #8b949e; font-weight: 500;")
        title_col.addWidget(app_title)
        title_col.addWidget(app_sub)
        header_layout.addLayout(title_col)

        header_layout.addStretch()

        # Version Pill Badge
        ver_badge = QLabel("v2.5 ACTIVE")
        ver_badge.setStyleSheet("""
            background-color: rgba(31, 111, 235, 0.2);
            color: #58a6ff;
            border: 1px solid rgba(88, 166, 255, 0.3);
            border-radius: 12px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(ver_badge)
        main_layout.addLayout(header_layout)

        # 2. Status Card
        self.status_card = QFrame()
        self.status_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #131922, stop:1 #16202e);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
            }
        """)
        status_card_layout = QVBoxLayout(self.status_card)
        status_card_layout.setContentsMargins(18, 16, 18, 16)
        status_card_layout.setSpacing(12)

        # Top row of status card: dot indicator + text status
        status_top = QHBoxLayout()
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("font-size: 20px; color: #8b949e; margin-right: 4px;")
        self.status_text = QLabel("CHECKING STATUS...")
        self.status_text.setStyleSheet("font-size: 15px; font-weight: 700; color: #c9d1d9;")
        
        status_top.addWidget(self.status_dot)
        status_top.addWidget(self.status_text)
        status_top.addStretch()

        self.uptime_badge = QLabel("Uptime: --:--:--")
        self.uptime_badge.setStyleSheet("font-size: 12px; color: #8b949e; font-family: 'Consolas', monospace;")
        status_top.addWidget(self.uptime_badge)
        status_card_layout.addLayout(status_top)

        # Metrics grid (PIDs, RAM, CPU)
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(12)

        self.metric_pids = self.create_metric_widget("PROCESS ID(S)", "None")
        self.metric_ram = self.create_metric_widget("MEMORY (RAM)", "0 MB")
        self.metric_cpu = self.create_metric_widget("CPU USAGE", "0 %")

        metrics_layout.addWidget(self.metric_pids)
        metrics_layout.addWidget(self.metric_ram)
        metrics_layout.addWidget(self.metric_cpu)
        status_card_layout.addLayout(metrics_layout)

        main_layout.addWidget(self.status_card)

        # 3. Main Action Buttons (START / STOP / RESTART)
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background: #111620;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 14px;
            }
        """)
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(16, 16, 16, 16)
        actions_layout.setSpacing(12)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        # Start Button
        self.btn_start = QPushButton("🚀 START HITASHA")
        self.btn_start.setFixedHeight(54)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #10b981, stop:1 #059669);
                color: #ffffff;
                font-size: 15px;
                font-weight: 800;
                letter-spacing: 0.5px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34d399, stop:1 #10b981);
            }
            QPushButton:disabled {
                background: #1b232f;
                color: #484f58;
                border: 1px solid #21262d;
            }
        """)
        self.btn_start.clicked.connect(self.on_start_clicked)
        btn_row.addWidget(self.btn_start, 3)

        # Stop Button
        self.btn_stop = QPushButton("⏹️ STOP HITASHA")
        self.btn_stop.setFixedHeight(54)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f43f5e, stop:1 #e11d48);
                color: #ffffff;
                font-size: 15px;
                font-weight: 800;
                letter-spacing: 0.5px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fb7185, stop:1 #f43f5e);
            }
            QPushButton:disabled {
                background: #1b232f;
                color: #484f58;
                border: 1px solid #21262d;
            }
        """)
        self.btn_stop.clicked.connect(self.on_stop_clicked)
        btn_row.addWidget(self.btn_stop, 3)

        # Restart Button
        self.btn_restart = QPushButton("🔄 RESTART")
        self.btn_restart.setFixedHeight(54)
        self.btn_restart.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_restart.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0284c7, stop:1 #0369a1);
                color: #ffffff;
                font-size: 14px;
                font-weight: 700;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #38bdf8, stop:1 #0284c7);
            }
            QPushButton:disabled {
                background: #1b232f;
                color: #484f58;
                border: 1px solid #21262d;
            }
        """)
        self.btn_restart.clicked.connect(self.on_restart_clicked)
        btn_row.addWidget(self.btn_restart, 2)

        actions_layout.addLayout(btn_row)

        # Quick Utility Buttons
        tools_row = QHBoxLayout()
        tools_row.setSpacing(10)

        self.btn_settings = self.create_tool_button("⚙️ Config Settings", self.on_settings_clicked)
        self.btn_voice_test = self.create_tool_button("🔊 Test Voice", self.on_voice_test_clicked)
        self.btn_shortcut = self.create_tool_button("📌 Desktop Shortcut", self.on_create_shortcut_clicked)
        
        tools_row.addWidget(self.btn_settings)
        tools_row.addWidget(self.btn_voice_test)
        tools_row.addWidget(self.btn_shortcut)

        actions_layout.addLayout(tools_row)
        main_layout.addWidget(actions_frame)

        # 4. Settings & Autostart Quick Bar
        quick_bar = QHBoxLayout()
        self.autostart_checkbox = QCheckBox("Launch Hitasha automatically when Windows starts")
        self.autostart_checkbox.setStyleSheet("""
            QCheckBox {
                color: #8b949e;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #30363d;
                background-color: #161b22;
            }
            QCheckBox::indicator:checked {
                background-color: #10b981;
                border-color: #34d399;
            }
        """)
        self.autostart_checkbox.setChecked(get_autostart_status())
        self.autostart_checkbox.stateChanged.connect(self.on_autostart_toggled)
        quick_bar.addWidget(self.autostart_checkbox)
        quick_bar.addStretch()

        self.btn_clear_logs = QPushButton("Clear Console")
        self.btn_clear_logs.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8b949e;
                font-size: 11px;
                border: 1px solid #21262d;
                border-radius: 6px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                color: #f0f6fc;
                background: #161b22;
            }
        """)
        self.btn_clear_logs.clicked.connect(self.clear_logs)
        quick_bar.addWidget(self.btn_clear_logs)

        main_layout.addLayout(quick_bar)

        # 5. Live Console / Event Log Pane
        console_frame = QFrame()
        console_frame.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
        """)
        console_layout = QVBoxLayout(console_frame)
        console_layout.setContentsMargins(12, 10, 12, 10)
        console_layout.setSpacing(6)

        console_header = QHBoxLayout()
        console_title = QLabel("LIVE ACTIVITY & SYSTEM LOG")
        console_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #58a6ff; letter-spacing: 0.5px;")
        console_header.addWidget(console_title)
        console_header.addStretch()
        
        self.log_count_label = QLabel("0 events")
        self.log_count_label.setStyleSheet("font-size: 11px; color: #484f58; font-family: monospace;")
        console_header.addWidget(self.log_count_label)
        console_layout.addLayout(console_header)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("""
            QTextEdit {
                background-color: #07090e;
                border: none;
                color: #c9d1d9;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        console_layout.addWidget(self.log_view)
        main_layout.addWidget(console_frame, 1)

    def create_metric_widget(self, label_text, default_value):
        w = QFrame()
        w.setStyleSheet("""
            QFrame {
                background-color: rgba(22, 27, 34, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #8b949e; letter-spacing: 0.5px;")
        val = QLabel(default_value)
        val.setStyleSheet("font-size: 14px; font-weight: 700; color: #58a6ff; font-family: 'Consolas', monospace;")
        layout.addWidget(lbl)
        layout.addWidget(val)
        w.val_label = val
        return w

    def create_tool_button(self, text, callback):
        btn = QPushButton(text)
        btn.setFixedHeight(36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #21262d;
                color: #ffffff;
                border-color: #58a6ff;
            }
        """)
        btn.clicked.connect(callback)
        return btn

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        if os.path.exists(ICON_PNG):
            self.tray.setIcon(QIcon(ICON_PNG))
        elif os.path.exists(ICON_ICO):
            self.tray.setIcon(QIcon(ICON_ICO))
        self.tray.setToolTip("Hitasha Control Center")

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #161b22;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #1f6feb;
            }
        """)

        start_act = menu.addAction("🚀 Start Hitasha")
        start_act.triggered.connect(self.on_start_clicked)

        stop_act = menu.addAction("⏹️ Stop Hitasha")
        stop_act.triggered.connect(self.on_stop_clicked)

        restart_act = menu.addAction("🔄 Restart Hitasha")
        restart_act.triggered.connect(self.on_restart_clicked)

        menu.addSeparator()

        show_act = menu.addAction("🖥️ Show Control Center")
        show_act.triggered.connect(self.show_window)

        menu.addSeparator()

        quit_act = menu.addAction("❌ Exit Control Center")
        quit_act.triggered.connect(self.quit_app)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger or reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        # Minimize to tray instead of hard quit so the user can easily reopen it
        if self.tray.isVisible():
            self.hide()
            self.tray.showMessage(
                "Hitasha Control Center",
                "App minimized to Windows system tray. Click to reopen anytime!",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            event.accept()

    def log(self, message: str, level: str = "INFO"):
        now = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "INFO": "#8b949e",
            "OK": "#34d399",
            "WARN": "#fbbf24",
            "ERR": "#f87171",
            "ACTION": "#38bdf8"
        }
        color = color_map.get(level, "#c9d1d9")
        log_line = f'<span style="color:#484f58;">[{now}]</span> <b style="color:{color};">[{level}]</b> {message}'
        self.log_view.append(log_line)
        
        # update counter
        count = int(self.log_count_label.text().split()[0]) + 1
        self.log_count_label.setText(f"{count} events")

    def clear_logs(self):
        self.log_view.clear()
        self.log_count_label.setText("0 events")

    def update_status_loop(self):
        if self.is_busy:
            return

        is_running, pids, ram_mb, cpu_pct, uptime_sec = is_hitasha_running()

        if is_running:
            self.status_dot.setText("●")
            self.status_dot.setStyleSheet("font-size: 22px; color: #10b981; margin-right: 4px;")
            self.status_text.setText("RUNNING ON DESKTOP")
            self.status_text.setStyleSheet("font-size: 15px; font-weight: 800; color: #34d399;")

            pids_str = ", ".join(map(str, pids))
            self.metric_pids.val_label.setText(pids_str)
            self.metric_ram.val_label.setText(f"{ram_mb} MB")
            self.metric_cpu.val_label.setText(f"{cpu_pct} %")

            # Format uptime
            hours = uptime_sec // 3600
            minutes = (uptime_sec % 3600) // 60
            seconds = uptime_sec % 60
            self.uptime_badge.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.uptime_badge.setStyleSheet("font-size: 12px; color: #10b981; font-family: 'Consolas', monospace;")

            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.btn_restart.setEnabled(True)
            self.tray.setToolTip(f"Hitasha: Running (RAM: {ram_mb} MB)")

        else:
            self.status_dot.setText("○")
            self.status_dot.setStyleSheet("font-size: 22px; color: #f43f5e; margin-right: 4px;")
            self.status_text.setText("OFFLINE / STOPPED")
            self.status_text.setStyleSheet("font-size: 15px; font-weight: 800; color: #fb7185;")

            self.metric_pids.val_label.setText("None")
            self.metric_ram.val_label.setText("0 MB")
            self.metric_cpu.val_label.setText("0 %")
            self.uptime_badge.setText("Uptime: --:--:--")
            self.uptime_badge.setStyleSheet("font-size: 12px; color: #64748b; font-family: 'Consolas', monospace;")

            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.btn_restart.setEnabled(False)
            self.tray.setToolTip("Hitasha: Stopped")

    def on_start_clicked(self):
        self.set_busy_state("Starting Hitasha...")
        self.log("Sending command to start Hitasha 3D Companion...", "ACTION")
        self.worker = ActionWorker("start")
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def on_stop_clicked(self):
        self.set_busy_state("Stopping Hitasha...")
        self.log("Sending stop signal to Hitasha...", "ACTION")
        self.worker = ActionWorker("stop")
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def on_restart_clicked(self):
        self.set_busy_state("Restarting Hitasha...")
        self.log("Restarting Hitasha companion...", "ACTION")
        self.worker = ActionWorker("restart")
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def on_voice_test_clicked(self):
        self.log("Testing speech output via text-to-speech engine...", "ACTION")
        self.worker = ActionWorker("voice_test")
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def set_busy_state(self, message):
        self.is_busy = True
        self.status_dot.setText("◐")
        self.status_dot.setStyleSheet("font-size: 22px; color: #f59e0b; margin-right: 4px;")
        self.status_text.setText(message.upper())
        self.status_text.setStyleSheet("font-size: 15px; font-weight: 800; color: #fbbf24;")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_restart.setEnabled(False)

    def on_worker_finished(self, action, success, message):
        self.is_busy = False
        level = "OK" if success else "ERR"
        self.log(f"{action.capitalize()}: {message}", level)

        if action in ["start", "restart"] and success:
            if self.tray.isVisible():
                self.tray.showMessage(
                    "Hitasha Started",
                    "Hitasha 3D AI companion is now floating on your desktop!",
                    QSystemTrayIcon.MessageIcon.Information,
                    2500
                )
        elif action == "stop" and success:
            if self.tray.isVisible():
                self.tray.showMessage(
                    "Hitasha Stopped",
                    "Hitasha companion stopped cleanly.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )

        self.update_status_loop()

    def on_settings_clicked(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.log("Configuration updated and saved to config.json.", "OK")
            # If running, notify that restart might be required
            is_running, _, _, _, _ = is_hitasha_running()
            if is_running:
                self.log("Tip: Restart Hitasha to apply new voice or LLM settings.", "WARN")

    def on_autostart_toggled(self, state):
        enable = bool(state == Qt.CheckState.Checked.value)
        success = set_autostart_status(enable)
        if success:
            action_str = "Enabled" if enable else "Disabled"
            self.log(f"{action_str} automatic startup with Windows.", "OK")
        else:
            self.log("Failed to modify Windows startup registry.", "ERR")

    def on_create_shortcut_clicked(self):
        success, res = create_desktop_shortcut()
        if success:
            self.log(f"Desktop shortcut created: {res}", "OK")
            QMessageBox.information(
                self,
                "Desktop Shortcut Created",
                f"Hitasha Control Center shortcut was placed directly on your Desktop:\n\n{res}"
            )
        else:
            self.log(f"Failed to create desktop shortcut: {res}", "ERR")
            QMessageBox.warning(self, "Shortcut Error", f"Could not create shortcut: {res}")


# Global mutex handle to prevent garbage collection
_instance_mutex = None

def ensure_single_instance():
    global _instance_mutex
    try:
        import win32event
        import win32api
        import winerror
        _instance_mutex = win32event.CreateMutex(None, False, "Global\\HitashaControlCenterMutex")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            print("[Control Center] Another instance is already running.")
            sys.exit(0)
    except Exception as e:
        print(f"[Mutex Warning] {e}")


def main():
    ensure_single_instance()

    # Enable high-DPI scaling
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Hitasha Control Center")
    app.setQuitOnLastWindowClosed(False)

    window = HitashaControlCenter()
    
    # Center on screen
    screen = app.primaryScreen()
    if screen:
        geo = screen.availableGeometry()
        x = (geo.width() - window.width()) // 2
        y = (geo.height() - window.height()) // 2
        window.move(max(0, x), max(0, y))

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
