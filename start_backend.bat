@echo off
cd /d "%~dp0"

REM --- Create virtual environment if missing ---
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM --- Activate virtual environment ---
call .venv\Scripts\activate.bat

REM --- Install / update dependencies ---
echo Installing backend dependencies...
pip install -r backend/requirements.txt

REM --- Copy .env from example if missing ---
if not exist ".env" (
    echo Copying .env.example to .env...
    copy .env.example .env
    echo.
    echo  IMPORTANT: Edit .env and set OPENAI_API_KEY before continuing.
    echo.
    pause
)

REM --- Seed the database (idempotent) ---
echo Seeding database...
python -m backend.db.seed

REM --- Start API server ---
echo.
echo  Backend API: http://localhost:8000
echo  API docs:    http://localhost:8000/docs
echo.
uvicorn backend.main:app --reload --port 8000
