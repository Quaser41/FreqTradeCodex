@echo off
REM Start Freqtrade main script
cd /d "%~dp0"
python freqtrade\main.py %*
