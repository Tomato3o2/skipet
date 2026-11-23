@echo off
cd /d "%~dp0"
echo Starting Sakuyi Pet ... (keep this window open, close it to quit the pet)
where py >nul 2>nul
if %errorlevel%==0 (
    py sakuyi_pet.py
) else (
    python sakuyi_pet.py
)
if errorlevel 1 (
    echo.
    echo ================================================
    echo  Start FAILED. Read the error message above.
    echo  If it says "No module named PyQt5", open cmd and run:
    echo      pip install PyQt5
    echo ================================================
    pause
)
