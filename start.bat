@echo off
REM Start Freqtrade main script
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python freqtrade\main.py %*
pause
