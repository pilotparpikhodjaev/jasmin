#!/bin/bash

# API Gateway Test Script
# Usage: ./test_api.sh

set -e

API_URL="${API_URL:-http://localhost:8080}"
EMAIL="${TEST_EMAIL:-admin@example.com}"
PASSWORD="${TEST_PASSWORD:-password123}"

echo "🧪 Testing API Gateway at $API_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
response=$(curl -s "$API_URL/health")
if echo "$response" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "$response"
    exit 1
fi
echo ""

# Test 2: Login
echo -e "${YELLOW}Test 2: Login${NC}"
login_response=$(curl -s -X POST "$API_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

if echo "$login_response" | grep -q "token"; then
    echo -e "${GREEN}✅ Login successful${NC}"
    TOKEN=$(echo "$login_response" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
    echo "Token: ${TOKEN:0:50}..."
else
    echo -e "${RED}❌ Login failed${NC}"
    echo "$login_response"
    exit 1
fi
echo ""

# Test 3: Get User Info
echo -e "${YELLOW}Test 3: Get User Info${NC}"
user_response=$(curl -s -X GET "$API_URL/api/auth/user" \
    -H "Authorization: Bearer $TOKEN")

if echo "$user_response" | grep -q "email"; then
    echo -e "${GREEN}✅ Get user info successful${NC}"
    echo "$user_response" | python3 -m json.tool || echo "$user_response"
else
    echo -e "${RED}❌ Get user info failed${NC}"
    echo "$user_response"
fi
echo ""

# Test 4: Get Balance
echo -e "${YELLOW}Test 4: Get Balance${NC}"
balance_response=$(curl -s -X GET "$API_URL/api/user/get-limit" \
    -H "Authorization: Bearer $TOKEN")

if echo "$balance_response" | grep -q "balance"; then
    echo -e "${GREEN}✅ Get balance successful${NC}"
    echo "$balance_response" | python3 -m json.tool || echo "$balance_response"
else
    echo -e "${RED}❌ Get balance failed${NC}"
    echo "$balance_response"
fi
echo ""

# Test 5: Check SMS
echo -e "${YELLOW}Test 5: Check SMS${NC}"
check_response=$(curl -s -X GET "$API_URL/api/message/sms/check?message=Test%20message" \
    -H "Authorization: Bearer $TOKEN")

if echo "$check_response" | grep -q "parts_count"; then
    echo -e "${GREEN}✅ Check SMS successful${NC}"
    echo "$check_response" | python3 -m json.tool || echo "$check_response"
else
    echo -e "${RED}❌ Check SMS failed${NC}"
    echo "$check_response"
fi
echo ""

# Test 6: Normalize SMS
echo -e "${YELLOW}Test 6: Normalize SMS${NC}"
normalize_response=$(curl -s -X POST "$API_URL/api/message/sms/normalizer" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello "World" — this is a test…"}')

if echo "$normalize_response" | grep -q "normalized_message"; then
    echo -e "${GREEN}✅ Normalize SMS successful${NC}"
    echo "$normalize_response" | python3 -m json.tool || echo "$normalize_response"
else
    echo -e "${RED}❌ Normalize SMS failed${NC}"
    echo "$normalize_response"
fi
echo ""

# Test 7: Send SMS (will fail without billing service)
echo -e "${YELLOW}Test 7: Send SMS (expected to fail without billing service)${NC}"
send_response=$(curl -s -X POST "$API_URL/api/message/sms/send" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "mobile_phone": "998901234567",
        "message": "Test message",
        "from": "TestSender"
    }')

if echo "$send_response" | grep -q "request_id"; then
    echo -e "${GREEN}✅ Send SMS successful${NC}"
    echo "$send_response" | python3 -m json.tool || echo "$send_response"
else
    echo -e "${YELLOW}⚠️  Send SMS failed (expected without billing service)${NC}"
    echo "$send_response"
fi
echo ""

# Test 8: List Operators (Admin)
echo -e "${YELLOW}Test 8: List Operators (Admin)${NC}"
operators_response=$(curl -s -X GET "$API_URL/api/admin/operators" \
    -H "Authorization: Bearer $TOKEN")

if echo "$operators_response" | grep -q "total"; then
    echo -e "${GREEN}✅ List operators successful${NC}"
    echo "$operators_response" | python3 -m json.tool || echo "$operators_response"
else
    echo -e "${YELLOW}⚠️  List operators failed (may require admin role)${NC}"
    echo "$operators_response"
fi
echo ""

# Test 9: Logout
echo -e "${YELLOW}Test 9: Logout${NC}"
logout_response=$(curl -s -X POST "$API_URL/api/auth/logout" \
    -H "Authorization: Bearer $TOKEN")

if echo "$logout_response" | grep -q "logged out"; then
    echo -e "${GREEN}✅ Logout successful${NC}"
else
    echo -e "${YELLOW}⚠️  Logout response: $logout_response${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ API Gateway tests completed!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📝 Notes:"
echo "  - Some tests may fail without billing-service running"
echo "  - Admin endpoints require admin role"
echo "  - SMS sending requires billing-service and jasmin running"
echo ""
echo "🚀 Next steps:"
echo "  1. Implement billing-service"
echo "  2. Implement routing-service"
echo "  3. Start Jasmin SMS Gateway"
echo "  4. Run full integration tests"

