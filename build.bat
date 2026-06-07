@echo off
REM Build all service images (fast - uses base images)

echo.
echo ========================================
echo Building service images...
echo ========================================
docker-compose build

if %ERRORLEVEL% NEQ 0 (
    echo Error building service images
    exit /b 1
)

echo.
echo ========================================
echo Success! Service images built.
echo ========================================
