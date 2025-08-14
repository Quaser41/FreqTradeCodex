@echo off
REM Start Freqtrade main script using local virtual environment
cd /d "%~dp0"

REM Use Python from the .venv folder
set "PYTHON=.venv\Scripts\python.exe"

"%PYTHON%" -m pip install --upgrade pip
"%PYTHON%" -m pip install -r requirements.txt
"%PYTHON%" -m freqtrade %*

pause
