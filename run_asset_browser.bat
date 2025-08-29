@echo off
REM Batch script to run Asset Browser

echo Starting Asset Browser...

REM Check if virtual environment exists
if exist ".venv\Scripts\python.exe" (
    echo Using virtual environment...
    .venv\Scripts\python.exe main.py %*
) else (
    echo Virtual environment not found. Using system Python...
    python main.py %*
)

pause
