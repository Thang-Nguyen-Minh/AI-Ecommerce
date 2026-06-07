@echo off
REM USER-SERVICE API Test Commands (Windows Batch)
REM Run: test-user-service.bat

setlocal enabledelayedexpansion

set BASE_URL=http://localhost:8001
set /a TIMESTAMP=%RANDOM%

echo.
echo ╔════════════════════════════════════════════╗
echo ║     USER-SERVICE API ENDPOINT TESTS       ║
echo ╚════════════════════════════════════════════╝
echo.

REM 1. Health Check
echo [1] Health Check
powershell -Command "Invoke-WebRequest -Uri '%BASE_URL%/users/health/' | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json"

REM 2. Register User
echo.
echo [2] Register User
set USERNAME=testuser_%TIMESTAMP%
set EMAIL=test_%TIMESTAMP%@example.com

powershell -Command "^
  $body = @{ ^
    username = '%USERNAME%'; ^
    email = '%EMAIL%'; ^
    full_name = 'Test User'; ^
    password = 'SecurePass@123'; ^
    password2 = 'SecurePass@123' ^
  } | ConvertTo-Json; ^
  $resp = Invoke-WebRequest -Uri '%BASE_URL%/auth/register/' -Method POST -ContentType 'application/json' -Body $body -UseBasicParsing; ^
  $data = $resp.Content | ConvertFrom-Json; ^
  $data | ConvertTo-Json -Depth 2; ^
  Write-Host ('Access Token: ' + $data.tokens.access.Substring(0,30) + '...') -ForegroundColor Green ^
"

REM 3. Login
echo.
echo [3] Login User
powershell -Command "^
  $body = @{ ^
    username = '%USERNAME%'; ^
    password = 'SecurePass@123' ^
  } | ConvertTo-Json; ^
  $resp = Invoke-WebRequest -Uri '%BASE_URL%/auth/login/' -Method POST -ContentType 'application/json' -Body $body -UseBasicParsing; ^
  $resp.Content | ConvertFrom-Json | ConvertTo-Json -Depth 2 ^
"

REM 4. Get Profile (requires token from registration)
echo.
echo [4] Get User Profile
echo Note: Use access token from registration response with Authorization header

REM 5. Health Check Alternative (using curl syntax if available)
echo.
echo ═══════════════════════════════════════════════════════════════
echo ALTERNATIVE: Using curl commands (if curl is available)
echo ═══════════════════════════════════════════════════════════════
echo.
echo Test Health Check:
echo   curl -X GET http://localhost:8001/users/health/
echo.
echo Register User:
echo   curl -X POST http://localhost:8001/auth/register/ ^
echo     -H "Content-Type: application/json" ^
echo     -d "{\"username\":\"testuser\",\"email\":\"test@example.com\",\"full_name\":\"Test User\",\"password\":\"Pass@123\",\"password2\":\"Pass@123\"}"
echo.
echo Login:
echo   curl -X POST http://localhost:8001/auth/login/ ^
echo     -H "Content-Type: application/json" ^
echo     -d "{\"username\":\"testuser\",\"password\":\"Pass@123\"}"
echo.
echo Get Profile (with token):
echo   curl -X GET http://localhost:8001/users/me/ ^
echo     -H "Authorization: Bearer [YOUR_ACCESS_TOKEN]"
echo.

echo ✓ Test script completed!
echo.
pause
