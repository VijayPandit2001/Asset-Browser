@echo off
REM Install dependencies and run Asset Browser

echo Setting up and running Asset Browser...

REM Run setup script
python setup.py

REM Run the application
if exist ".venv\Scripts\python.exe" (
    echo Starting Asset Browser with virtual environment...
    .venv\Scripts\python.exe main.py %*
) else (
    echo Starting Asset Browser with system Python...
    python main.py %*
)

pause
