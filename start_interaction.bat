@echo off
echo Starting Interaction System...
echo.

REM Check if backend source file exists
if not exist "backend\src\index.ts" (
    echo ERROR: Backend source file not found at backend\src\index.ts
    echo Please ensure the main server file is in the correct location.
    pause
    exit /b 1
)

REM Install backend dependencies
echo Building backend...
cd backend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)

call npm run build
if errorlevel 1 (
    echo ERROR: Failed to build backend
    pause
    exit /b 1
)

REM Verify the build output exists
if not exist "dist\index.js" (
    echo ERROR: Backend build output not found at dist\index.js
    echo The TypeScript compilation may have failed.
    pause
    exit /b 1
)

REM Go to frontend, install dependencies, and build
echo Building frontend...
cd ..\web-frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies
    pause
    exit /b 1
)

call npm install zustand
if errorlevel 1 (
    echo ERROR: Failed to install zustand
    pause
    exit /b 1
)

call npm run build
if errorlevel 1 (
    echo ERROR: Failed to build frontend
    pause
    exit /b 1
)

REM Verify the frontend build output exists
if not exist "dist\index.html" (
    echo ERROR: Frontend build output not found at dist\index.html
    echo The Vite build may have failed.
    pause
    exit /b 1
)

REM Get the local IP address using PowerShell
for /f "delims=" %%i in ('powershell -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -eq 'Dhcp' } | Select-Object -First 1 -ExpandProperty IPAddress"') do set IP=%%i
if "%IP%"=="" set IP=localhost

REM Check if loading screen exists
if not exist "%~dp0loading.html" (
    echo ERROR: Loading screen not found at loading.html
    pause
    exit /b 1
)

REM Go back to backend and start the server in a new window (background)
echo Starting backend server...
cd ..\backend
start cmd /c "npm start"

REM Wait a moment for the server to start
timeout /t 3

REM Check if server is actually running
echo Checking if server is running...
powershell -Command "try { (Invoke-WebRequest -Uri 'http://localhost:8000/api/status' -TimeoutSec 5).StatusCode } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Server may not be running yet, but continuing...
) else (
    echo Server is responding correctly
)

REM Open the loading screen after server is starting
echo Opening loading screen...
start "" "%~dp0loading.html"

echo.
echo ========================================
echo Loading screen opened! 
echo Backend server is starting in the background.
echo The application will be available at: http://localhost:8000
echo ======================================== 