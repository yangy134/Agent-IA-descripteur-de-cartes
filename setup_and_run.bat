@echo off
rem ------------------------------------------------------------
rem GeoAI-Carto automatic setup and run script
rem ------------------------------------------------------------
rem Create a virtual environment if it does not exist
if not exist .venv (
    echo Creating virtual environment... && python -m venv .venv
) else (
    echo Virtual environment already exists.
)

rem Activate the virtual environment
call .venv\Scripts\activate.bat

rem Upgrade pip (optional but recommended)
python -m pip install --upgrade pip

rem Install required packages
if exist requirements.txt (
    echo Installing dependencies from requirements.txt ...
    pip install -r requirements.txt
) else (
    echo ERROR: requirements.txt not found. Please ensure it exists in the repository root.
    exit /b 1
)

rem Run the main script. If you pass a path as the first argument, it will be used as --image.
rem Otherwise, the script will ask for the image path interactively.
if "%~1"=="" (
    python main.py
) else (
    python main.py --image "%~1"
)

rem Deactivate virtual environment
deactivate
