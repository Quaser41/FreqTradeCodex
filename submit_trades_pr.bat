@echo off
setlocal

REM Create a pull request with tradesv3.dryrun sqlite files in this folder

set "BRANCH=trade-sqlite-upload"
set "BASE=main"
set "FILE_PATTERN=tradesv3.dryrun*.sqlite"

cd /d "%~dp0"


where git >nul 2>&1 || (echo Git not found & pause & exit /b)
where gh  >nul 2>&1 || (echo GitHub CLI not found & pause & exit /b)

git checkout -B "%BRANCH%" || (echo Failed to checkout branch & pause & exit /b 1)

dir %FILE_PATTERN% >nul 2>&1 || (echo No SQLite files found & pause & exit /b)

for %%F in (%FILE_PATTERN%) do (
    if exist "%%F" git add -f "%%F"
)

git commit -m "Add tradesv3 dryrun sqlite data" || (echo Commit failed & pause & exit /b 1)

git push -u origin "%BRANCH%" || (echo Push failed & pause & exit /b 1)

gh pr create ^
    --title "Add tradesv3 dryrun sqlite data" ^
    --body  "Uploading tradesv3.dryrun sqlite files for review and improvement." ^
    --base  "%BASE%" ^
    --head  "%BRANCH%" || (echo Pull request creation failed & pause & exit /b 1)

echo.
echo Pull request submitted.
pause
endlocal
