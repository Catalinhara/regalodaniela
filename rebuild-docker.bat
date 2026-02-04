@echo off
echo ========================================
echo ClaraMente - Docker Rebuild Script
echo ========================================
echo.

echo [1/4] Stopping existing containers...
docker-compose down
echo.

echo [2/4] Rebuilding containers (this may take a few minutes)...
docker-compose build --no-cache
echo.

echo [3/4] Starting services...
docker-compose up -d
echo.

echo [4/4] Waiting for services to start...
timeout /t 5 /nobreak >nul
echo.

echo ========================================
echo Services Status:
echo ========================================
docker-compose ps
echo.

echo ========================================
echo Application URLs:
echo ========================================
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

echo ========================================
echo To view logs, run:
echo   docker-compose logs -f
echo ========================================
echo.

pause
