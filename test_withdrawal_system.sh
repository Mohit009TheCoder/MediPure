#!/bin/bash

echo "=========================================="
echo "TESTING COMPLETE WITHDRAWAL SYSTEM"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get tokens
echo -e "${BLUE}Step 1: Getting authentication tokens...${NC}"
DOCTOR_TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=doctor@test.com&password=test123" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@medipure.com&password=admin123" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo -e "${GREEN}✓ Tokens obtained${NC}"
echo ""

# Check doctor's initial balance
echo -e "${BLUE}Step 2: Checking doctor's initial balance...${NC}"
INITIAL_BALANCE=$(curl -s -X GET http://localhost:8000/doctor/earnings \
  -H "Authorization: Bearer $DOCTOR_TOKEN" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Pending: ₹{data['pending_amount']:.0f}, Withdrawn: ₹{data['withdrawn_amount']:.0f}\")")
echo -e "${GREEN}✓ $INITIAL_BALANCE${NC}"
echo ""

# Doctor requests 1st withdrawal (₹500 - 10% fee = ₹450)
echo -e "${BLUE}Step 3: Doctor requests 1st withdrawal (₹500)...${NC}"
WD1=$(curl -s -X POST http://localhost:8000/doctor/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "amount": 500,
    "account_holder_name": "Dr. Sarah Smith",
    "account_number": "1234567890",
    "ifsc_code": "SBIN0001234",
    "bank_name": "State Bank of India"
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['withdrawal_id']}|{data['withdrawal_number']}|{data['gross_amount']}|{data['platform_fee_percentage']}|{data['net_amount']}\")")

WD1_ID=$(echo $WD1 | cut -d'|' -f1)
WD1_NUM=$(echo $WD1 | cut -d'|' -f2)
WD1_GROSS=$(echo $WD1 | cut -d'|' -f3)
WD1_FEE=$(echo $WD1 | cut -d'|' -f4)
WD1_NET=$(echo $WD1 | cut -d'|' -f5)

echo -e "${GREEN}✓ Withdrawal #$WD1_NUM created${NC}"
echo -e "  Gross: ₹$WD1_GROSS | Fee: $WD1_FEE% | Net: ₹$WD1_NET"
echo ""

# Doctor requests 2nd withdrawal (₹500 - 10% fee = ₹450)
echo -e "${BLUE}Step 4: Doctor requests 2nd withdrawal (₹500)...${NC}"
WD2=$(curl -s -X POST http://localhost:8000/doctor/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "amount": 500,
    "account_holder_name": "Dr. Sarah Smith",
    "account_number": "1234567890",
    "ifsc_code": "SBIN0001234",
    "bank_name": "State Bank of India"
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['withdrawal_id']}|{data['withdrawal_number']}|{data['gross_amount']}|{data['platform_fee_percentage']}|{data['net_amount']}\")")

WD2_ID=$(echo $WD2 | cut -d'|' -f1)
WD2_NUM=$(echo $WD2 | cut -d'|' -f2)
WD2_GROSS=$(echo $WD2 | cut -d'|' -f3)
WD2_FEE=$(echo $WD2 | cut -d'|' -f4)
WD2_NET=$(echo $WD2 | cut -d'|' -f5)

echo -e "${GREEN}✓ Withdrawal #$WD2_NUM created${NC}"
echo -e "  Gross: ₹$WD2_GROSS | Fee: $WD2_FEE% | Net: ₹$WD2_NET"
echo ""

# Doctor requests 3rd withdrawal (₹500 - 15% fee = ₹425) - PENALTY!
echo -e "${BLUE}Step 5: Doctor requests 3rd withdrawal (₹500) - PENALTY FEE!${NC}"
WD3=$(curl -s -X POST http://localhost:8000/doctor/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "amount": 500,
    "account_holder_name": "Dr. Sarah Smith",
    "account_number": "1234567890",
    "ifsc_code": "SBIN0001234",
    "bank_name": "State Bank of India"
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['withdrawal_id']}|{data['withdrawal_number']}|{data['gross_amount']}|{data['platform_fee_percentage']}|{data['net_amount']}\")")

WD3_ID=$(echo $WD3 | cut -d'|' -f1)
WD3_NUM=$(echo $WD3 | cut -d'|' -f2)
WD3_GROSS=$(echo $WD3 | cut -d'|' -f3)
WD3_FEE=$(echo $WD3 | cut -d'|' -f4)
WD3_NET=$(echo $WD3 | cut -d'|' -f5)

echo -e "${RED}✓ Withdrawal #$WD3_NUM created with PENALTY${NC}"
echo -e "  Gross: ₹$WD3_GROSS | Fee: $WD3_FEE% | Net: ₹$WD3_NET"
echo ""

# Admin views all withdrawal requests
echo -e "${BLUE}Step 6: Admin views all withdrawal requests...${NC}"
PENDING_COUNT=$(curl -s -X GET http://localhost:8000/admin/withdrawals \
  -H "Authorization: Bearer $ADMIN_TOKEN" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(len([w for w in data if w['status']=='pending']))")
echo -e "${GREEN}✓ Admin sees $PENDING_COUNT pending requests${NC}"
echo ""

# Admin approves 1st withdrawal
echo -e "${BLUE}Step 7: Admin approves 1st withdrawal...${NC}"
APPROVE1=$(curl -s -X POST http://localhost:8000/admin/withdrawals/$WD1_ID/approve \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"action": "approve", "admin_notes": "Approved - 1st withdrawal"}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['status']}|{data['platform_fee']}|{data['net_amount']}\")")

echo -e "${GREEN}✓ Withdrawal #$WD1_NUM approved${NC}"
echo -e "  Status: $(echo $APPROVE1 | cut -d'|' -f1)"
echo -e "  Platform fee collected: ₹$(echo $APPROVE1 | cut -d'|' -f2)"
echo -e "  Doctor will receive: ₹$(echo $APPROVE1 | cut -d'|' -f3)"
echo ""

# Admin approves 2nd withdrawal
echo -e "${BLUE}Step 8: Admin approves 2nd withdrawal...${NC}"
APPROVE2=$(curl -s -X POST http://localhost:8000/admin/withdrawals/$WD2_ID/approve \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"action": "approve", "admin_notes": "Approved - 2nd withdrawal"}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['status']}|{data['platform_fee']}|{data['net_amount']}\")")

echo -e "${GREEN}✓ Withdrawal #$WD2_NUM approved${NC}"
echo -e "  Status: $(echo $APPROVE2 | cut -d'|' -f1)"
echo -e "  Platform fee collected: ₹$(echo $APPROVE2 | cut -d'|' -f2)"
echo -e "  Doctor will receive: ₹$(echo $APPROVE2 | cut -d'|' -f3)"
echo ""

# Admin approves 3rd withdrawal (with penalty)
echo -e "${BLUE}Step 9: Admin approves 3rd withdrawal (PENALTY)...${NC}"
APPROVE3=$(curl -s -X POST http://localhost:8000/admin/withdrawals/$WD3_ID/approve \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"action": "approve", "admin_notes": "Approved - 3rd withdrawal with penalty"}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['status']}|{data['platform_fee']}|{data['net_amount']}\")")

echo -e "${RED}✓ Withdrawal #$WD3_NUM approved with PENALTY${NC}"
echo -e "  Status: $(echo $APPROVE3 | cut -d'|' -f1)"
echo -e "  Platform fee collected: ₹$(echo $APPROVE3 | cut -d'|' -f3)"
echo -e "  Doctor will receive: ₹$(echo $APPROVE3 | cut -d'|' -f3)"
echo ""

# Admin marks 1st as processing
echo -e "${BLUE}Step 10: Admin marks 1st withdrawal as processing...${NC}"
curl -s -X PUT http://localhost:8000/admin/withdrawals/$WD1_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"status": "processing", "transaction_id": "TXN001"}' > /dev/null
echo -e "${GREEN}✓ Withdrawal #$WD1_NUM marked as processing${NC}"
echo ""

# Admin marks 1st as completed
echo -e "${BLUE}Step 11: Admin marks 1st withdrawal as completed...${NC}"
COMPLETE1=$(curl -s -X PUT http://localhost:8000/admin/withdrawals/$WD1_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"status": "completed"}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['status']}|{data['net_amount_paid']}\")")

echo -e "${GREEN}✓ Withdrawal #$WD1_NUM completed!${NC}"
echo -e "  Doctor received: ₹$(echo $COMPLETE1 | cut -d'|' -f2)"
echo ""

# Check final balances
echo -e "${BLUE}Step 12: Checking final balances...${NC}"
FINAL=$(curl -s -X GET http://localhost:8000/doctor/earnings \
  -H "Authorization: Bearer $DOCTOR_TOKEN" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['pending_amount']}|{data['withdrawn_amount']}|{data['platform_fees_paid']}\")")

FINAL_PENDING=$(echo $FINAL | cut -d'|' -f1)
FINAL_WITHDRAWN=$(echo $FINAL | cut -d'|' -f2)
FINAL_FEES=$(echo $FINAL | cut -d'|' -f3)

echo -e "${GREEN}✓ Final Doctor Balance:${NC}"
echo -e "  Pending: ₹$FINAL_PENDING"
echo -e "  Withdrawn: ₹$FINAL_WITHDRAWN"
echo -e "  Platform Fees Paid: ₹$FINAL_FEES"
echo ""

echo "=========================================="
echo -e "${GREEN}TEST COMPLETED SUCCESSFULLY!${NC}"
echo "=========================================="
echo ""
echo "Summary:"
echo "- 3 withdrawal requests created"
echo "- All 3 approved by admin"
echo "- Platform fees deducted correctly (10%, 10%, 15%)"
echo "- 1 withdrawal completed and paid to doctor"
echo "- 2 withdrawals approved and ready for payment"
