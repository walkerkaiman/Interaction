@echo off
echo ========================================
echo Interaction Project Validation
echo ========================================
echo.

set "errors=0"

REM Check for required directories
echo Checking project structure...

if not exist "backend\" (
    echo [ERROR] backend/ directory not found
    set /a errors+=1
) else (
    echo [OK] backend/ directory exists
)

if not exist "web-frontend\" (
    echo [ERROR] web-frontend/ directory not found
    set /a errors+=1
) else (
    echo [OK] web-frontend/ directory exists
)

if not exist "config\" (
    echo [ERROR] config/ directory not found
    set /a errors+=1
) else (
    echo [OK] config/ directory exists
)

REM Check for required files
echo.
echo Checking required files...

if not exist "backend\src\index.ts" (
    echo [ERROR] backend\src\index.ts not found
    set /a errors+=1
) else (
    echo [OK] backend\src\index.ts exists
)

if not exist "backend\package.json" (
    echo [ERROR] backend\package.json not found
    set /a errors+=1
) else (
    echo [OK] backend\package.json exists
)

if not exist "web-frontend\package.json" (
    echo [ERROR] web-frontend\package.json not found
    set /a errors+=1
) else (
    echo [OK] web-frontend\package.json exists
)

if not exist "loading.html" (
    echo [ERROR] loading.html not found
    set /a errors+=1
) else (
    echo [OK] loading.html exists
)

if not exist "start_interaction.bat" (
    echo [ERROR] start_interaction.bat not found
    set /a errors+=1
) else (
    echo [OK] start_interaction.bat exists
)

REM Check for unwanted files
echo.
echo Checking for unwanted files...

if exist "package.json" (
    echo [WARNING] Root-level package.json found - this should not exist
    echo           Dependencies should be in backend/package.json and web-frontend/package.json
)

if exist "package-lock.json" (
    echo [WARNING] Root-level package-lock.json found - this should not exist
)

if exist "node_modules" (
    echo [WARNING] Root-level node_modules/ found - this should not exist
    echo           Node modules should be in backend/node_modules/ and web-frontend/node_modules/
)

REM Check backend build
echo.
echo Checking backend build...

if not exist "backend\dist\index.js" (
    echo [WARNING] backend\dist\index.js not found - backend needs to be built
    echo           Run: cd backend && npm run build
) else (
    echo [OK] backend\dist\index.js exists
)

REM Check for required backend dependencies
echo.
echo Checking backend dependencies...

if not exist "backend\node_modules\multer" (
    echo [WARNING] multer dependency not found - backend may not start properly
    echo           Run: cd backend && npm install
) else (
    echo [OK] multer dependency exists
)

REM Check for required API endpoints
echo.
echo Checking API endpoints...

powershell -Command "try { (Invoke-WebRequest -Uri 'http://localhost:8000/api/status' -TimeoutSec 3).StatusCode } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Backend server not running - cannot check API endpoints
    echo           Start the server first to validate API endpoints
) else (
    echo [OK] Backend server is running
    
    powershell -Command "try { (Invoke-WebRequest -Uri 'http://localhost:8000/api/log_levels' -TimeoutSec 3).StatusCode } catch { exit 1 }" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] /api/log_levels endpoint not found - Console page may not work
    ) else (
        echo [OK] /api/log_levels endpoint working
    )
)

REM Check frontend build
echo.
echo Checking frontend build...

if not exist "web-frontend\dist\index.html" (
    echo [WARNING] web-frontend\dist\index.html not found - frontend needs to be built
    echo           Run: cd web-frontend && npm run build
) else (
    echo [OK] web-frontend\dist\index.html exists
)

REM Check for build configuration issues
echo.
echo Checking build configurations...

if exist "web-frontend\package.json" (
    findstr /C:"tsc -b" "web-frontend\package.json" >nul 2>&1
    if not errorlevel 1 (
        echo [WARNING] Frontend package.json contains 'tsc -b' which may cause build issues
        echo           Consider using 'vite build' instead
    ) else (
        echo [OK] Frontend build script looks correct
    )
)

echo.
echo ========================================
echo Error count: %errors%

if %errors% equ 0 (
    echo [SUCCESS] Project structure is valid!
    echo You can now run start_interaction.bat
) else (
    echo [FAILED] Found %errors% error(s)
    echo Please fix the errors above before running the application.
)

echo ========================================
pause 