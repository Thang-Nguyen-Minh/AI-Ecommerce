# USER-SERVICE API Test Commands (PowerShell - Windows)
# Run: powershell -ExecutionPolicy Bypass .\test-user-service.ps1

$BASE_URL = "http://localhost:8001"
$timestamp = Get-Date -Format "yyyyMMddHHmmss"

Write-Host "`n╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     USER-SERVICE API ENDPOINT TESTS       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# 1. Health Check
Write-Host "[1] Health Check" -ForegroundColor Yellow
Invoke-WebRequest -Uri "$BASE_URL/users/health/" `
  -Method GET -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json

# 2. Register User
Write-Host "`n[2] Register User" -ForegroundColor Yellow
$username = "testuser_$timestamp"
$email = "test_$timestamp@example.com"
$registerBody = @{
    username    = $username
    email       = $email
    full_name   = "Test User"
    password    = "SecurePass@123"
    password2   = "SecurePass@123"
} | ConvertTo-Json

$registerResp = Invoke-WebRequest -Uri "$BASE_URL/auth/register/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $registerBody `
    -UseBasicParsing

$registerData = $registerResp.Content | ConvertFrom-Json
Write-Host ($registerData | ConvertTo-Json)
$accessToken = $registerData.tokens.access
$refreshToken = $registerData.tokens.refresh
Write-Host "✓ Access Token: $($accessToken.Substring(0,30))..." -ForegroundColor Green
Write-Host "✓ Username: $username" -ForegroundColor Green

# 3. Login
Write-Host "`n[3] Login User" -ForegroundColor Yellow
$loginBody = @{
    username = $username
    password = "SecurePass@123"
} | ConvertTo-Json

$loginResp = Invoke-WebRequest -Uri "$BASE_URL/auth/login/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $loginBody `
    -UseBasicParsing
Write-Host ($loginResp.Content | ConvertFrom-Json | ConvertTo-Json)

# 4. Get Profile
Write-Host "`n[4] Get Current User Profile" -ForegroundColor Yellow
$headers = @{ "Authorization" = "Bearer $accessToken" }
$profileResp = Invoke-WebRequest -Uri "$BASE_URL/users/me/" `
    -Method GET `
    -Headers $headers `
    -UseBasicParsing
Write-Host ($profileResp.Content | ConvertFrom-Json | ConvertTo-Json)

# 5. Update Profile
Write-Host "`n[5] Update User Profile" -ForegroundColor Yellow
$updateBody = @{
    full_name = "Updated User Name"
    phone     = "+84901234567"
} | ConvertTo-Json

$updateResp = Invoke-WebRequest -Uri "$BASE_URL/users/me/" `
    -Method PUT `
    -ContentType "application/json" `
    -Body $updateBody `
    -Headers $headers `
    -UseBasicParsing
Write-Host ($updateResp.Content | ConvertFrom-Json | ConvertTo-Json)

# 6. Add Address
Write-Host "`n[6] Add Delivery Address" -ForegroundColor Yellow
$addressBody = @{
    full_name   = "Delivery Address"
    phone       = "+84901234567"
    street      = "123 Main Street"
    district    = "District 1"
    city        = "Ho Chi Minh City"
    postal_code = "700000"
    country     = "Vietnam"
    is_default  = $true
} | ConvertTo-Json

$addressResp = Invoke-WebRequest -Uri "$BASE_URL/users/me/addresses/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $addressBody `
    -Headers $headers `
    -UseBasicParsing
$addressData = $addressResp.Content | ConvertFrom-Json
Write-Host ($addressData | ConvertTo-Json)
$addressId = $addressData.id

# 7. Get Addresses
Write-Host "`n[7] List User Addresses" -ForegroundColor Yellow
$addressListResp = Invoke-WebRequest -Uri "$BASE_URL/users/me/addresses/" `
    -Method GET `
    -Headers $headers `
    -UseBasicParsing
Write-Host ($addressListResp.Content | ConvertFrom-Json | ConvertTo-Json)

# 8. Update Address
Write-Host "`n[8] Update Address" -ForegroundColor Yellow
$updateAddrBody = @{
    full_name = "Updated Delivery Address"
    phone     = "+84987654321"
} | ConvertTo-Json

$updateAddrResp = Invoke-WebRequest -Uri "$BASE_URL/users/me/addresses/$addressId/" `
    -Method PUT `
    -ContentType "application/json" `
    -Body $updateAddrBody `
    -Headers $headers `
    -UseBasicParsing
Write-Host ($updateAddrResp.Content | ConvertFrom-Json | ConvertTo-Json)

# 9. Set Default Address
Write-Host "`n[9] Set Default Address" -ForegroundColor Yellow
$defaultResp = Invoke-WebRequest -Uri "$BASE_URL/users/me/addresses/$addressId/set-default/" `
    -Method POST `
    -Headers $headers `
    -UseBasicParsing
Write-Host ($defaultResp.Content | ConvertFrom-Json | ConvertTo-Json)

# 10. Change Password
Write-Host "`n[10] Change Password" -ForegroundColor Yellow
$passBody = @{
    old_password  = "SecurePass@123"
    new_password  = "NewSecurePass@456"
    new_password2 = "NewSecurePass@456"
} | ConvertTo-Json

$passResp = Invoke-WebRequest -Uri "$BASE_URL/users/me/change-password/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $passBody `
    -Headers $headers `
    -UseBasicParsing
Write-Host ($passResp.Content | ConvertFrom-Json | ConvertTo-Json)

# 11. User Stats (Admin)
Write-Host "`n[11] User Statistics" -ForegroundColor Yellow
try {
    $statsResp = Invoke-WebRequest -Uri "$BASE_URL/users/stats/" `
        -Method GET `
        -Headers $headers `
        -UseBasicParsing
    Write-Host ($statsResp.Content | ConvertFrom-Json | ConvertTo-Json)
} catch {
    Write-Host "Note: User needs admin role to access stats" -ForegroundColor Yellow
}

# 12. List Users (Admin)
Write-Host "`n[12] List All Users" -ForegroundColor Yellow
try {
    $usersResp = Invoke-WebRequest -Uri "$BASE_URL/users/" `
        -Method GET `
        -Headers $headers `
        -UseBasicParsing
    Write-Host ($usersResp.Content | ConvertFrom-Json | ConvertTo-Json)
} catch {
    Write-Host "Note: User needs admin role to list users" -ForegroundColor Yellow
}

# 13. Delete Address
Write-Host "`n[13] Delete Address" -ForegroundColor Yellow
$deleteResp = Invoke-WebRequest -Uri "$BASE_URL/users/me/addresses/$addressId/" `
    -Method DELETE `
    -Headers $headers `
    -UseBasicParsing
Write-Host "Deleted (HTTP $($deleteResp.StatusCode))" -ForegroundColor Green

# 14. Logout
Write-Host "`n[14] Logout (Blacklist Token)" -ForegroundColor Yellow
$logoutBody = @{
    refresh = $refreshToken
} | ConvertTo-Json

$logoutResp = Invoke-WebRequest -Uri "$BASE_URL/auth/logout/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $logoutBody `
    -Headers $headers `
    -UseBasicParsing
Write-Host ($logoutResp.Content | ConvertFrom-Json | ConvertTo-Json)

Write-Host "`n╔════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   ✓ All tests completed successfully!      ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════╝`n" -ForegroundColor Green
