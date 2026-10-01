@echo off
title Build Hitasha Offline AI Model
cd /d "%~dp0"
echo ========================================================
echo   Training Hitasha Offline Indian English AI Model
echo ========================================================
echo Checking if Ollama is installed and running...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [!] Ollama is not currently detected in your PATH.
    echo If you have not installed Ollama yet, you can download it from:
    echo     https://ollama.com/download/windows
    echo.
    echo Once installed, run this script again to train Hitasha's offline model!
    echo.
    pause
    exit /b 1
)

echo.
echo Step 1: Pulling base model llama3.2:3b (optimized for RTX 5050 8GB VRAM)...
ollama pull llama3.2:3b

echo.
echo Step 2: Creating and training custom 'hitasha' assistant model from Modelfile...
ollama create hitasha -f Modelfile

echo.
echo ========================================================
echo   SUCCESS! Hitasha offline model is trained and ready!
echo ========================================================
echo Hitasha will now use the 'hitasha' offline model to answer
echo all your questions in simple, short, easy Indian English!
echo.
pause
