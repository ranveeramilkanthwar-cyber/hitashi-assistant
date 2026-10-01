"""
Main entry point for Hitasha - 3D Jarvis Desktop Companion & Assistant.
"""

import sys
import os

# CRITICAL: QtWebEngineWidgets must be imported and AA_ShareOpenGLContexts must be set
# BEFORE creating the QApplication instance on Windows.
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

if hasattr(Qt.ApplicationAttribute, "AA_ShareOpenGLContexts"):
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

from src.config import load_config
from src.ui_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Hitasha Desktop Companion")
    app.setQuitOnLastWindowClosed(False)  # Stays alive in system tray or screen mate

    # Load persistent config
    config = load_config()

    # MainWindow acts as the backend controller (voice, vision, LLM, reminders)
    # The 3D character ScreenMateWindow is displayed exclusively on the desktop.
    window = MainWindow(config)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
