@echo off
title Stop Hitasha 3D Assistant
cd /d "%~dp0"
echo ========================================================
echo   Stopping Hitasha Desktop Companion...
echo ========================================================
"%~dp0.venv\Scripts\python.exe" stop.py
echo Hitasha has been cleanly stopped.
exit
