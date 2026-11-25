@echo off
REM ============================================================
REM  Phishing AI Master 2 - Automatic Setup & Run
REM  Windows 11, Python 3.10
REM  Starts the API and the Web frontend automatically.
REM ============================================================

setlocal EnableDelayedExpansion

set "PROJECT_DIR=D:\openhands\projects\v2\phishing_ai_master"
set "VENDOR_DIR=D:\openhands\projects\v2\vendor_libs"

echo.
echo ============================================================
echo  Phishing AI Master 2 - Setup ^& Run
echo ============================================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10.
    pause
    exit /b 1
)
echo [OK] Python found.

REM --- Set environment ---
set "PYTHONPATH=%VENDOR_DIR%;%PROJECT_DIR%"
set "MODEL_PATH=%PROJECT_DIR%\models\versions\M1_LR_HARDNEG.joblib"
set "META_PATH=%PROJECT_DIR%\models\versions\metadata.json"
set "AB_TEST_ENABLED=1"
set "AB_TEST_SPLIT=0.5"
echo [OK] Environment configured.

REM --- Verify key packages ---
echo [INFO] Verifying packages...
python -c "import sklearn, pandas, numpy, fastapi; print('  OK')" 2>&1
if errorlevel 1 (
    echo [WARNING] Some packages missing. Install with: pip install -r requirements.txt
)

REM --- Run tests ---
echo.
echo [INFO] Running tests...
cd /d "%PROJECT_DIR%"
python -m pytest tests/ -q
if errorlevel 1 (
    echo [WARNING] Some tests failed. Continuing anyway.
) else (
    echo [OK] All tests passed.
)

REM --- Stop anything already on port 8000 (best effort) ---
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM --- Start API ---
echo.
echo [INFO] Starting FastAPI server on http://127.0.0.1:8000 ...
start "Phishing API" cmd /k "cd /d %PROJECT_DIR% && set PYTHONPATH=%VENDOR_DIR%;%PROJECT_DIR% && set MODEL_PATH=%PROJECT_DIR%\models\versions\M1_LR_HARDNEG.joblib && set META_PATH=%PROJECT_DIR%\models\versions\metadata.json && set AB_TEST_ENABLED=1 && set AB_TEST_SPLIT=0.5 && python -m uvicorn deployment.api.main:app --host 127.0.0.1 --port 8000"

REM --- Wait for API to be ready ---
echo [INFO] Waiting for API to be ready...
set "API_READY=0"
for /l %%i in (1,1,30) do (
    if "!API_READY!"=="0" (
        python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" >nul 2>&1
        if not errorlevel 1 set "API_READY=1"
        if "!API_READY!"=="0" timeout /t 1 /nobreak >nul
    )
)
if "!API_READY!"=="1" (
    echo [OK] API ready.
) else (
    echo [WARNING] API did not respond in time. Check the API window.
)

REM --- Start frontend ---
echo.
echo [INFO] Starting Web frontend on http://localhost:8501 ...
start "Phishing UI" cmd /k "cd /d %PROJECT_DIR%\deployment\frontend && set PYTHONPATH=%VENDOR_DIR%;%PROJECT_DIR% && python -m http.server 8501"

REM --- Open browser ---
timeout /t 2 /nobreak >nul
start "" "http://localhost:8501/index.html"

echo.
echo ============================================================
echo  Phishing AI Master 2 is running!
echo  API:      http://127.0.0.1:8000
echo  Frontend: http://localhost:8501/index.html
echo  API docs: http://127.0.0.1:8000/docs
echo ============================================================
echo.
echo Close the two console windows to stop the services.
pause