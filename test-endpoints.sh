#!/bin/bash

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8001"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     USER-SERVICE API ENDPOINT TESTS       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"

# 1. Health Check
echo -e "\n${YELLOW}[1] Health Check${NC}"
curl -s -X GET "$BASE_URL/users/health/" \
  -H "Content-Type: application/json" | jq .

# 2. Register User
echo -e "\n${YELLOW}[2] Register User${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser_'$(date +%s)'",
    "email": "test_'$(date +%s)'@example.com",
    "full_name": "Test User",
    "password": "SecurePass@123",
    "password2": "SecurePass@123"
  }')
echo "$REGISTER_RESPONSE" | jq .

# Extract tokens
ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.tokens.access')
REFRESH_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.tokens.refresh')
USERNAME=$(echo "$REGISTER_RESPONSE" | jq -r '.user.username')

echo -e "${GREEN}✓ Access Token: ${ACCESS_TOKEN:0:30}...${NC}"
echo -e "${GREEN}✓ Username: $USERNAME${NC}"

# 3. Login
echo -e "\n${YELLOW}[3] Login User${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$USERNAME\",
    \"password\": \"SecurePass@123\"
  }")
echo "$LOGIN_RESPONSE" | jq .

# 4. Get Profile
echo -e "\n${YELLOW}[4] Get Current User Profile${NC}"
curl -s -X GET "$BASE_URL/users/me/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" | jq .

# 5. Update Profile
echo -e "\n${YELLOW}[5] Update User Profile${NC}"
curl -s -X PUT "$BASE_URL/users/me/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated User Name",
    "phone": "+84901234567"
  }' | jq .

# 6. Add Address
echo -e "\n${YELLOW}[6] Add Delivery Address${NC}"
ADDRESS_RESPONSE=$(curl -s -X POST "$BASE_URL/users/me/addresses/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
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
  }')
echo "$ADDRESS_RESPONSE" | jq .

ADDRESS_ID=$(echo "$ADDRESS_RESPONSE" | jq -r '.id')

# 7. Get Addresses
echo -e "\n${YELLOW}[7] List User Addresses${NC}"
curl -s -X GET "$BASE_URL/users/me/addresses/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" | jq .

# 8. Update Address
echo -e "\n${YELLOW}[8] Update Address${NC}"
curl -s -X PUT "$BASE_URL/users/me/addresses/$ADDRESS_ID/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Delivery Address",
    "phone": "+84987654321"
  }' | jq .

# 9. Set Default Address
echo -e "\n${YELLOW}[9] Set Default Address${NC}"
curl -s -X POST "$BASE_URL/users/me/addresses/$ADDRESS_ID/set-default/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" | jq .

# 10. Change Password
echo -e "\n${YELLOW}[10] Change Password${NC}"
curl -s -X POST "$BASE_URL/users/me/change-password/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "SecurePass@123",
    "new_password": "NewSecurePass@456",
    "new_password2": "NewSecurePass@456"
  }' | jq .

# 11. User Stats (Admin)
echo -e "\n${YELLOW}[11] User Statistics (Requires Admin)${NC}"
curl -s -X GET "$BASE_URL/users/stats/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" | jq .

# 12. List Users (Admin)
echo -e "\n${YELLOW}[12] List All Users (Requires Admin)${NC}"
curl -s -X GET "$BASE_URL/users/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" | jq .

# 13. Logout
echo -e "\n${YELLOW}[13] Logout (Blacklist Token)${NC}"
curl -s -X POST "$BASE_URL/auth/logout/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh\": \"$REFRESH_TOKEN\"
  }" | jq .

echo -e "\n${GREEN}✓ All tests completed!${NC}"
