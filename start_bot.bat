@echo off
echo ========================================
echo AI Fact Checker - Start & Update Script
echo ========================================

cd /d "%~dp0"

echo.
echo [1/5] Checking if bot is running...
tasklist | findstr python.exe >nul
if %ERRORLEVEL% EQU 0 (
    echo Bot is running. Stopping it...
    taskkill /F /IM python.exe
    timeout /t 2 /nobreak >nul
) else (
    echo Bot is not running.
)

echo.
echo [2/5] Backing up real config with API keys...
if exist tiktok_factcheck_config.json (
    copy tiktok_factcheck_config.json tiktok_factcheck_config_backup.json >nul
    echo Config backed up.
)

echo.
echo [3/5] Committing and pushing to GitHub...
git add .
git commit -m "Update: AI Fact Checker improvements"
git push -u origin master
if %ERRORLEVEL% EQU 0 (
    echo Successfully pushed to GitHub!
) else (
    echo Warning: Git push failed. Check your internet connection.
)

echo.
echo [4/5] Restoring API keys...
if exist tiktok_factcheck_config_backup.json (
    copy /Y tiktok_factcheck_config_backup.json tiktok_factcheck_config.json >nul
    del tiktok_factcheck_config_backup.json
    echo API keys restored.
)

echo.
echo [5/5] Starting the bot...
python tiktok_factcheck.py

pause
