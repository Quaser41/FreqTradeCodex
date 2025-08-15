@echo off
REM Update repository to the latest changes
cd /d "%~dp0"

echo Fetching latest changes...
git fetch --all

git checkout develop
git reset --hard origin/develop

echo Rebasing local changes onto remote...
git pull --rebase

echo Update complete.
pause
