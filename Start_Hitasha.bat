@echo off
title Start Hitasha 3D Assistant
cd /d "%~dp0"
echo ========================================================
echo   Starting Hitasha - 3D Indian Girl AI Assistant
echo ========================================================
start "" "%~dp0.venv\Scripts\pythonw.exe" main.py
echo Hitasha is now floating on your screen!
exit
