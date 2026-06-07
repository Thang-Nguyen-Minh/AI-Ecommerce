# USER-SERVICE API Test Commands

## ✅ Quick Start

### Option 1: PowerShell (Recommended for Windows)
```powershell
powershell -ExecutionPolicy Bypass .\test-user-service.ps1
```

### Option 2: Simple Test Script
```powershell
powershell -ExecutionPolicy Bypass .\test-api-simple.ps1
```

---

## 📋 Manual Test Commands (Copy & Paste)

### 1. Health Check
```bash
curl -X GET http://localhost:8001/users/health/
```

### 2. Register User
```bash
curl -X POST http://localhost:8001/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "SecurePass@123",
    "password2": "SecurePass@123"
  }'
```

**Response contains:**
- `tokens.access` - JWT access token (use for requests)
- `tokens.refresh` - JWT refresh token
- `user` - User profile object

### 3. Login User
```bash
curl -X POST http://localhost:8001/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass@123"
  }'
```

### 4. Get User Profile (Authenticated)
Replace `YOUR_ACCESS_TOKEN` with token from registration/login:
```bash
curl -X GET http://localhost:8001/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Update Profile
```bash
curl -X PUT http://localhost:8001/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Name",
    "phone": "+84901234567"
  }'
```

### 6. Add Address
```bash
curl -X POST http://localhost:8001/users/me/addresses/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Delivery Address",
    "phone": "+84901234567",
    "street": "123 Main Street",
    "district": "District 1",
    "city": "Ho Chi Minh City",
    "postal_code": "700000",
    "country": "Vietnam",
    "is_default": true
  }'
```

### 7. Get Addresses
```bash
curl -X GET http://localhost:8001/users/me/addresses/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 8. Update Address
```bash
curl -X PUT http://localhost:8001/users/me/addresses/{address_id}/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Address",
    "phone": "+84987654321"
  }'
```

### 9. Set Default Address
```bash
curl -X POST http://localhost:8001/users/me/addresses/{address_id}/set-default/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 10. Delete Address
```bash
curl -X DELETE http://localhost:8001/users/me/addresses/{address_id}/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 11. Change Password
```bash
curl -X POST http://localhost:8001/users/me/change-password/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "SecurePass@123",
    "new_password": "NewSecurePass@456",
    "new_password2": "NewSecurePass@456"
  }'
```

### 12. Logout (Blacklist Token)
```bash
curl -X POST http://localhost:8001/auth/logout/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

### 13. User Stats (Admin Only)
```bash
curl -X GET http://localhost:8001/users/stats/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### 14. List Users (Admin Only)
```bash
curl -X GET http://localhost:8001/users/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

---

## 🔐 Authentication

- **Default Role:** customer
- **Access Token Lifetime:** 60 minutes
- **Refresh Token Lifetime:** 7 days
- **Token Format:** Bearer token in Authorization header
- **Header Format:** `Authorization: Bearer <access_token>`

---

## 📊 API Response Examples

### Success Response (201 Created)
```json
{
  "message": "Đăng ký thành công!",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "role": "customer",
    "is_active": true,
    "addresses": []
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLC...",
    "refresh": "eyJ0eXAiOiJKV1QiLC..."
  }
}
```

### Error Response (400 Bad Request)
```json
{
  "username": [
    "Trường này là bắt buộc."
  ],
  "email": [
    "Email này đã được sử dụng."
  ]
}
```

---

## 🧪 Test Scenarios

### Scenario 1: Complete User Workflow
1. Register → Get token
2. Login → Verify token
3. Update profile
4. Add address
5. Set default address
6. Logout

### Scenario 2: Address Management
1. Add multiple addresses
2. List addresses
3. Update an address
4. Set one as default
5. Delete an address

### Scenario 3: Security
1. Register user
2. Change password with old password
3. Attempt login with old password (should fail)
4. Login with new password
5. Logout

---

## 🌐 Service Ports

| Service | Port | URL |
|---------|------|-----|
| user-service | 8001 | http://localhost:8001 |
| product-service | 8002 | http://localhost:8002 |
| cart-service | 8003 | http://localhost:8003 |
| order-service | 8004 | http://localhost:8004 |
| payment-service | 8005 | http://localhost:8005 |
| shipping-service | 8006 | http://localhost:8006 |
| ai-service | 8007 | http://localhost:8007 |
| Neo4j | 7474 | http://localhost:7474 |

---

## 🐛 Troubleshooting

### "Authorization header must contain two space-delimited values"
- Make sure token format is: `Bearer <token>` (space between Bearer and token)

### "Table 'user_db.users_user' doesn't exist"
- Run migrations: `.\migrate.bat`

### "No installed app with label 'admin'"
- Admin app was removed (not needed for API-only services)

### "Connection refused"
- Check if Docker services are running: `docker ps`
- Check logs: `.\logs-user.bat`

---

## 📝 Notes

- Replace `YOUR_ACCESS_TOKEN` with actual token from registration/login response
- Replace `{address_id}` with actual address ID from GET addresses response
- All dates are in ISO 8601 format
- Phone numbers should include country code
