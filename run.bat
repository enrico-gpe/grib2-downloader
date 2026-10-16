@echo off
TITLE GRIB2-Downloader Launcher
cd /d %~dp0

echo [INFO] Checking Python environment...

:: Check if the virtual environment exists
if not exist "venv" (
echo [INFO] Virtual environment 'venv' not found. Creating a new one...
python -m venv venv
if errorlevel 1 (
echo [ERROR] Failed to create virtual environment. Ensure Python is installed and added to your system PATH.
pause
exit /b 1
)
)

:: Activate the virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate

:: Install requirements if requirements.txt exists
if exist "requirements.txt" (
echo [INFO] Checking and installing dependencies from requirements.txt...
pip install -r requirements.txt --quiet
)

:: Launch the application
echo [INFO] Starting GRIB2-Downloader...
python main.py

:: Keep window open if an error occurs
if errorlevel 1 (
echo.
echo [ERROR] The application exited with an error.
pause
)