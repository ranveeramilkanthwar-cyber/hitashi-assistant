@echo off
title Hitasha Desktop Companion
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [Hitasha] Virtual environment not found. Creating one...
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
)

echo [Hitasha] Launching your Jarvis desktop companion...
start "" ".venv\Scripts\pythonw.exe" main.py
exit
