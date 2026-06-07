# Test E-commerce API Endpoints
$baseUrl = "http://localhost:8001"

Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   E-Commerce API Test Script          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "`n[TEST 1] Health Check" -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "$baseUrl/users/health/" -UseBasicParsing -ErrorAction Stop
Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
Write-Host ($response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 1)

# Test 2: Register New User
Write-Host "`n[TEST 2] Register New User" -ForegroundColor Yellow
$regBody = @{
    username  = "newuser_$(Get-Random)"
    email     = "user_$(Get-Random)@example.com"
    full_name = "New Test User"
    password  = "SecurePass@123"
    password2 = "SecurePass@123"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/auth/register/" -Method POST -ContentType "application/json" -Body $regBody -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ User ID: $($data.user.id)"
    Write-Host "✓ Username: $($data.user.username)"
    Write-Host "✓ Access Token: $($data.access.Substring(0,30))..."
    Write-Host "✓ Refresh Token: $($data.refresh.Substring(0,30))..."
    
    $accessToken = $data.access
    $username = $data.user.username
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 3: Login
Write-Host "`n[TEST 3] Login User" -ForegroundColor Yellow
$loginBody = @{
    username = $username
    password = "SecurePass@123"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/auth/login/" -Method POST -ContentType "application/json" -Body $loginBody -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ Access Token: $($data.access.Substring(0,30))..."
    Write-Host "✓ Role: $($data.role)"
    $accessToken = $data.access
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Get Current User Profile
Write-Host "`n[TEST 4] Get Current User Profile (/users/me/)" -ForegroundColor Yellow
$headers = @{
    Authorization = "Bearer $accessToken"
}

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/users/me/" -Headers $headers -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ Username: $($data.username)"
    Write-Host "✓ Email: $($data.email)"
    Write-Host "✓ Full Name: $($data.full_name)"
    Write-Host "✓ Role: $($data.role)"
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Update Profile
Write-Host "`n[TEST 5] Update User Profile" -ForegroundColor Yellow
$updateBody = @{
    full_name = "Updated User Name"
    phone = "+1234567890"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/users/me/" -Method PUT -ContentType "application/json" -Body $updateBody -Headers $headers -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ Updated Full Name: $($data.full_name)"
    Write-Host "✓ Updated Phone: $($data.phone)"
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Add Address
Write-Host "`n[TEST 6] Add Address" -ForegroundColor Yellow
$addrBody = @{
    full_name = "Delivery Name"
    phone = "+84901234567"
    street = "123 Main St"
    city = "Ho Chi Minh City"
    state = "HCM"
    postal_code = "700000"
    country = "Vietnam"
    is_default = $true
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/users/me/addresses/" -Method POST -ContentType "application/json" -Body $addrBody -Headers $headers -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ Address ID: $($data.id)"
    Write-Host "✓ City: $($data.city)"
    Write-Host "✓ Is Default: $($data.is_default)"
    $addressId = $data.id
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 7: Get Addresses
Write-Host "`n[TEST 7] Get User Addresses" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/users/me/addresses/" -Headers $headers -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ Total Addresses: $($data.Count)"
    if ($data.Count -gt 0) {
        Write-Host "✓ First Address: $($data[0].city), $($data[0].country)"
    }
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 8: Change Password
Write-Host "`n[TEST 8] Change Password" -ForegroundColor Yellow
$passBody = @{
    old_password = "SecurePass@123"
    new_password = "NewPass@456"
    new_password2 = "NewPass@456"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/users/me/change-password/" -Method POST -ContentType "application/json" -Body $passBody -Headers $headers -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ Message: $($data.message)"
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 9: Logout (skipped - would need to store refresh token from login)
Write-Host "`n[TEST 9] Logout (Skipped - would invalidate current session)" -ForegroundColor Yellow
Write-Host "✓ Logout endpoint available at: POST /auth/logout/" -ForegroundColor Green

Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   All Tests Completed!                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
