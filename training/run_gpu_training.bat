@echo off
title Fine-Tune Hitasha AI on RTX 5050 GPU
cd /d "%~dp0.."
echo ========================================================
echo   HITASHA GPU FINE-TUNING RUNNER (RTX 5050 8GB VRAM)
echo ========================================================
echo.
echo Step 1: Checking Python & GPU dependencies...
"%~dp0..\.venv\Scripts\python.exe" -c "import torch; assert torch.cuda.is_available(), 'CUDA required'; print('CUDA GPU OK:', torch.cuda.get_device_name(0))" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] PyTorch with CUDA is not detected yet in your virtual environment.
    echo.
    echo Installing PyTorch with CUDA 12.4 support (takes a few minutes)...
    "%~dp0..\.venv\Scripts\pip.exe" install torch --index-url https://download.pytorch.org/whl/cu124
    echo.
    echo Installing Transformers, PEFT, TRL, Accelerate and BitsAndBytes...
    "%~dp0..\.venv\Scripts\pip.exe" install transformers datasets peft accelerate trl bitsandbytes
)

echo.
echo Step 2: Compiling latest master dataset (6,000+ web + curated instruction pairs)...
"%~dp0..\.venv\Scripts\python.exe" training\gather_and_build_dataset.py

echo.
echo Step 3: Launching 4-bit QLoRA GPU Training on RTX 5050...
"%~dp0..\.venv\Scripts\python.exe" training\train_gpu.py --epochs 3 --batch_size 2

echo.
echo ========================================================
echo   Training Completed!
echo ========================================================
pause
