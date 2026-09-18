@echo off
title SANCHAY IAS - Launcher
echo ==========================================
echo  SANCHAY IAS - Starting Unified Server...
echo ==========================================
echo.

:: Kill anything on port 8001 first
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do taskkill /PID %%a /F >nul 2>&1

echo [1/1] Starting API and Web Server on port 8001...
start "" /B python api_server.py

:: Wait for server to start
timeout /t 3 /nobreak >nul

echo.
echo ==========================================
echo  DONE! Opening browser...
echo  App URL: http://localhost:8001/frontend/advisor_login.html
echo ==========================================
echo.

:: Open browser
start "" "http://localhost:8001/frontend/advisor_login.html"

echo Press any key to STOP the server and exit.
pause >nul

:: Cleanup on exit
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do taskkill /PID %%a /F >nul 2>&1
echo Server stopped. Goodbye!
