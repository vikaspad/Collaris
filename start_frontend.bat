@echo off
setlocal

cd /d "%~dp0frontend" || (
    echo ERROR: frontend folder not found.
    echo Expected path: %~dp0frontend
    pause
    exit /b 1
)

echo Installing frontend dependencies...
call npm install || (
    echo ERROR: npm install failed.
    pause
    exit /b 1
)

echo.
echo Frontend app: http://localhost:5173
echo.

call npm run dev

pause