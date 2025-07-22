@echo off
REM Install backend dependencies
cd backend
call npm install
call npm run build

REM Go to frontend, install dependencies, and build
cd ..\web-frontend
call npm install
call npm install zustand
call npm run build

REM Go back to backend and start the server in a new window (background)
cd ..\backend
start cmd /c "npm start"

REM Wait a moment for the server to start
timeout /t 3

REM Get the local IP address using PowerShell
for /f "delims=" %%i in ('powershell -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -eq 'Dhcp' } | Select-Object -First 1 -ExpandProperty IPAddress"') do set IP=%%i
if "%IP%"=="" set IP=localhost

REM Open the browser to the UI on the local network
start http://%IP%:8000/

echo All done! The backend server is running and the UI should open in your browser. 