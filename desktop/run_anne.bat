@echo off
setlocal
cd /d "%~dp0.."

where py >nul 2>&1
if errorlevel 1 (
  echo Python 3.12+ is required. Install Python from python.org and try again.
  pause
  exit /b 1
)

py -m pip install -U google-genai
if errorlevel 1 (
  echo Failed to install google-genai.
  pause
  exit /b 1
)

py desktop\anne_tinker.py
if errorlevel 1 (
  echo ANNE stopped with an error.
  pause
)
