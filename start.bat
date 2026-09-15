@echo off
if not exist venv (
    echo Setup has not been run yet. First run: setup.bat
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python main.py %*
pause
