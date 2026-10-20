@echo off
title JobGetter dashboard
cd /d "%~dp0"
echo Starting the JobGetter dashboard. Keep this window open while you use it.
echo Close this window to stop the dashboard.
start "" http://localhost:5050
".venv\Scripts\python.exe" app.py
pause
