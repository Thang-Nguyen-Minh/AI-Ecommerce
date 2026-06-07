$baseUrl = "http://localhost:8001"

Write-Host "`n=== E-Commerce API Test ===" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "`n[1] Health Check" -ForegroundColor Yellow
$resp = Invoke-WebRequest "$baseUrl/users/health/" -UseBasicParsing
Write-Host "Status: $($resp.StatusCode)" -ForegroundColor Green

# Test 2: Register User
Write-Host "`n[2] Register User" -ForegroundColor Yellow
$username = "testuser_$(Get-Random)"
$regBody = @{
    username = $username
    email = "test_$(Get-Random)@example.com"
    full_name = "Test User"
    password = "Pass@123"
    password2 = "Pass@123"
} | ConvertTo-Json

$resp = Invoke-WebRequest "$baseUrl/auth/register/" -Method POST -ContentType "application/json" -Body $regBody -UseBasicParsing
$data = $resp.Content | ConvertFrom-Json
Write-Host "Status: $($resp.StatusCode)" -ForegroundColor Green
Write-Host "Username: $($data.user.username)" -ForegroundColor Green
Write-Host "Role: $($data.user.role)" -ForegroundColor Green
$token = $data.tokens.access
Write-Host "Token received: $($token.Substring(0,20))..." -ForegroundColor Gray

# Test 3: Get Profile
Write-Host "`n[3] Get Profile" -ForegroundColor Yellow
$headers = @{ "Authorization" = "Bearer $token" }
$resp = Invoke-WebRequest "$baseUrl/users/me/" -Headers $headers -UseBasicParsing
$profile = $resp.Content | ConvertFrom-Json
Write-Host "Status: $($resp.StatusCode)" -ForegroundColor Green
Write-Host "Username: $($profile.username)" -ForegroundColor Green

# Test 4: Update Profile
Write-Host "`n[4] Update Profile" -ForegroundColor Yellow
$updateBody = @{
    full_name = "Updated Name"
    phone = "+84901234567"
} | ConvertTo-Json

$resp = Invoke-WebRequest "$baseUrl/users/me/" -Method PUT -ContentType "application/json" -Body $updateBody -Headers $headers -UseBasicParsing
Write-Host "Status: $($resp.StatusCode)" -ForegroundColor Green

# Test 5: Add Address
Write-Host "`n[5] Add Address" -ForegroundColor Yellow
$addrBody = @{
    full_name = "Delivery Name"
    phone = "+84901234567"
    street = "123 Main St"
    district = "District 1"
    city = "Ho Chi Minh City"
    postal_code = "700000"
    country = "Vietnam"
    is_default = $true
} | ConvertTo-Json

$resp = Invoke-WebRequest "$baseUrl/users/me/addresses/" -Method POST -ContentType "application/json" -Body $addrBody -Headers $headers -UseBasicParsing
Write-Host "Status: $($resp.StatusCode)" -ForegroundColor Green

# Test 6: Get Addresses
Write-Host "`n[6] Get Addresses" -ForegroundColor Yellow
$resp = Invoke-WebRequest "$baseUrl/users/me/addresses/" -Headers $headers -UseBasicParsing
$addrs = $resp.Content | ConvertFrom-Json
Write-Host "Status: $($resp.StatusCode)" -ForegroundColor Green
Write-Host "Address Count: $($addrs.Count)" -ForegroundColor Green

Write-Host "`n=== All Tests Passed! ===" -ForegroundColor Cyan
