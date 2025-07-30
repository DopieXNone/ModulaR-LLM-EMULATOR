@echo off
echo ====================================
echo ModulaR LLM EMULATOR - Windows Setup
echo ====================================
echo.

:: Check if winget is available
winget --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: winget is not available on this system.
    echo Install winget or update Windows to continue.
    pause
    exit /b 1
)

echo [1/4] Installing Python...
winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo WARNING: Error installing Python or already installed.
)

echo.
echo [2/4] Installing Ollama...
winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo WARNING: Error installing Ollama or already installed.
)

echo.
echo [3/4] Updating PATH and starting Ollama service...
:: Add Python to PATH if not present
setx PATH "%PATH%;%USERPROFILE%\AppData\Local\Programs\Python\Python312;%USERPROFILE%\AppData\Local\Programs\Python\Python312\Scripts" >nul 2>&1

:: Start Ollama service in background
echo Starting Ollama service...
start /b ollama serve >nul 2>&1

:: Wait for Ollama to be ready
echo Waiting for Ollama service to start...
timeout /t 5 /nobreak >nul

echo.
echo [4/4] Downloading deepseek-r1:1.5b model...
ollama pull deepseek-r1:1.5b
if errorlevel 1 (
    echo ERROR: Unable to download deepseek-r1:1.5b model
    echo Verify that Ollama is installed correctly.
)

echo.
echo [5/5] Installing Python libraries...
python -m pip install --upgrade pip
python -m pip install requests colorama flask keyboard

echo.
echo ====================================
echo ModulaR LLM EMULATOR Setup Complete!
echo ====================================
echo.
echo Installed programs:
echo - Python 3.12
echo - Ollama
echo - Model: deepseek-r1:1.5b
echo.
echo Installed Python libraries:
echo - requests
echo - colorama  
echo - flask
echo - keyboard
echo.
echo Notes:
echo - datetime, json, subprocess, importlib, typing, msvcrt are built-in modules
echo - Ollama service has been started in background
echo.
pause
