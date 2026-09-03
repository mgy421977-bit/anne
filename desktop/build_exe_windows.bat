@echo off
setlocal
cd /d "%~dp0.."

if not exist .venv\Scripts\python.exe (
  echo Run install_windows.bat first.
  pause
  exit /b 1
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pyinstaller

REM IMPORTANT: add src to PyInstaller's analysis path so the bundled EXE contains ANNE.
python -m PyInstaller --noconfirm --clean --onefile --windowed --paths "%CD%\src" --name ANNE_Tinker desktop\anne_tinker.py

if errorlevel 1 goto :fail

echo.
echo ========================================
echo ANNE_Tinker.exe created successfully.
echo Location: dist\ANNE_Tinker.exe
echo ========================================
echo.
pause
exit /b 0

:fail
echo.
echo Build failed.
echo.
pause
exit /b 1
