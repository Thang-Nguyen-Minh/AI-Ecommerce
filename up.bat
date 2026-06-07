@echo off
REM Start the entire system

echo.
echo ========================================
echo Starting ecom-final system...
echo ========================================
docker-compose up -d

echo.
echo ========================================
echo System is running!
echo ========================================
echo.
echo Frontend:    http://localhost
echo API Health:  http://localhost/health
echo Neo4j UI:    http://localhost:7474
echo.
