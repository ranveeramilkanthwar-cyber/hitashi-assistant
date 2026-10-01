@echo off
title Hitasha Control Center
cd /d "%~dp0"
echo ========================================================
echo   Starting Hitasha Control Center (Windows App)
echo ========================================================
start "" "%~dp0.venv\Scripts\pythonw.exe" control_center.py
echo Hitasha Control Center is now running on your desktop!
exit
