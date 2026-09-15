@echo off
echo Installing YouTube Content Factory...
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python not found. Install it from https://www.python.org/downloads/
    echo IMPORTANT: check "Add Python to PATH" during install.
    pause
    exit /b 1
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Installing dependencies, this can take a couple of minutes...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ============================================================
    echo  Some packages failed to install - see the errors above.
    echo  Copy the error text and send it back for help.
    echo ============================================================
    echo.
    pause
    exit /b 1
)
echo Dependencies installed successfully.

if not exist .env (
    copy .env.example .env >nul
    echo Created .env file
)

findstr /R "^GEMINI_API_KEY=..*" .env >nul 2>nul
if errorlevel 1 (
    echo.
    echo You need a free Gemini API key.
    echo Get one here: https://aistudio.google.com/app/apikey
    set /p key="Paste your key here (or press Enter to add it later): "
    if not "%key%"=="" (
        powershell -Command "(Get-Content .env) -replace '^GEMINI_API_KEY=.*', 'GEMINI_API_KEY=%key%' | Set-Content .env"
        echo Key saved to .env
    ) else (
        echo No key set - add it to .env later by editing the file.
    )
)

echo.
echo Setup complete!
echo Next, run: start.bat
pause
