@echo off
echo ==========================================
echo   ClaraMente Local Development Setup
echo ==========================================

echo [1/2] Setting up Backend Service...
cd backend
python -m venv venv
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment created. Installing dependencies...
    pip install -r requirements.txt
    deactivate
    echo Backend setup complete.
) else (
    echo ERROR: Failed to create Python virtual environment.
    echo Please ensure Python 3.11+ is installed and in your PATH.
    pause
    exit /b 1
)
cd ..

echo [2/2] Setting up Frontend Service...
cd frontend
where npm >nul 2>nul
if %errorlevel% equ 0 (
    echo npm found. Installing Node modules...
    call npm install
    echo Frontend setup complete.
) else (
    echo ERROR: npm is not found.
    echo Please ensure Node.js (LTS) is installed and in your PATH.
    pause
    exit /b 1
)
cd ..

echo ==========================================
echo   Setup Finished!
echo   Please restart your IDE (VS Code) to apply changes.
echo ==========================================
pause
