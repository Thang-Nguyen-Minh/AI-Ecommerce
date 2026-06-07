@echo off
REM Build base images (Django + AI)
REM Chỉ cần chạy 1 lần

echo.
echo ========================================
echo Building Django base image...
echo ========================================
docker build -t ecom-django-base:latest ./base-images/django-base/

if %ERRORLEVEL% NEQ 0 (
    echo Error building Django base image
    exit /b 1
)

echo.
echo ========================================
echo Building AI base image (may take 10-15 minutes)...
echo ========================================
docker build -t ecom-ai-base:latest ./base-images/ai-base/

if %ERRORLEVEL% NEQ 0 (
    echo Error building AI base image
    exit /b 1
)

echo.
echo ========================================
echo Success! Base images built.
echo ========================================
