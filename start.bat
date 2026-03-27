@echo off
echo Starting TubeInsight AI...
echo.

:: Check if Ollama is running
echo Checking if Ollama is running...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [0/3] Starting Ollama server...
    start "Ollama Server" cmd /c "ollama serve"
    timeout /t 5 /nobreak >nul
) else (
    echo [0/3] Ollama already running
)

:: Start backend in new window
echo [1/3] Starting FastAPI backend on http://localhost:8000
start "TubeInsight Backend" cmd /c "uvicorn api:app --reload --host 0.0.0.0 --port 8000"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

:: Start frontend in new window
echo [2/3] Starting Next.js frontend on http://localhost:3000
start "TubeInsight Frontend" cmd /c "cd frontend && npm run dev"

echo.
echo All services starting...
echo Ollama:    http://localhost:11434
echo Backend:   http://localhost:8000
echo Frontend:  http://localhost:3000
echo.
echo Press Ctrl+C in each window to stop.
pause
