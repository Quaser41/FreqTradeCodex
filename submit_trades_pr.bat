@echo off
setlocal

REM Create a pull request with tradesv3.dryrun sqlite files in this folder

set "BRANCH=trade-sqlite-upload"
set "BASE=main"
set "FILE_PATTERN=tradesv3.dryrun*.sqlite"

cd /d "%~dp0"

git checkout -B "%BRANCH%" || goto :eof

for %%F in (%FILE_PATTERN%) do (
    if exist "%%F" git add -f "%%F"
)

git commit -m "Add tradesv3 dryrun sqlite data" || goto :eof

git push -u origin "%BRANCH%" || goto :eof

gh pr create ^
    --title "Add tradesv3 dryrun sqlite data" ^
    --body  "Uploading tradesv3.dryrun sqlite files for review and improvement." ^
    --base  "%BASE%" ^
    --head  "%BRANCH%" || goto :eof

echo.
echo Pull request submitted.
endlocal
