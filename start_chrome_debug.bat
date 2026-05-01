@echo off
echo Closing Chrome...

:: Kill Chrome by full executable path - leaves WhatsApp untouched
taskkill /F /FI "IMAGENAME eq chrome.exe" /FI "STATUS eq RUNNING" 2>nul

:: Backup: kill by module path (only Google Chrome, not Electron apps)
wmic process where "CommandLine like '%%Google/Chrome%%' or ExecutablePath like '%%Google\\\\Chrome%%'" delete 2>nul

timeout /t 3 /nobreak >nul

echo Starting Chrome on debug port 9333...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9333 ^
  --user-data-dir="C:\ChromeDebugProfile" ^
  --no-first-run ^
  --no-default-browser-check ^
  --disable-background-mode ^
  --disable-extensions

echo Chrome ready on port 9333.