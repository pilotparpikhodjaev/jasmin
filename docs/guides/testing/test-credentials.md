# Test Credentials

Database has been seeded with test accounts. Use these credentials to test the UIs.

## 🔑 Login Credentials

All accounts use the same password: **`password123`**

### 👤 Client Portal ([http://localhost:3001](http://localhost:3001))

**Email:** `client@example.com`
**Password:** `password123`
**Account:** Test Company (Client)
**Balance:** 50,000 UZS
**Credit Limit:** 10,000 UZS

### 🛡️ Admin Dashboard ([http://localhost:3002](http://localhost:3002))

**Email:** `admin@example.com`
**Password:** `password123`
**Account:** Admin User
**Balance:** 1,000,000 UZS

### 🔄 Reseller Account

**Email:** `reseller@example.com`
**Password:** `password123`
**Account:** Reseller LLC
**Balance:** 100,000 UZS
**Credit Limit:** 50,000 UZS

---

## 📊 Pre-loaded Test Data

### Operators (3)
- **Ucell** (MCC: 434, MNC: 05) - 50 UZS per SMS
- **Beeline** (MCC: 434, MNC: 04) - 45 UZS per SMS
- **Uzmobile** (MCC: 434, MNC: 07) - 48 UZS per SMS

### Approved Nicknames (Sender IDs)
- **TestCompany** - Business category
- **1234** - Short Code category

### Message History (3 test messages)
- Message to 998901234567 - **DELIVRD** (50 UZS)
- Message to 998907654321 - **DELIVRD** (45 UZS)
- Message to 998931234567 - **PENDING** (48 UZS)

---

## 🧪 Testing Features

### Client Portal Features:
1. ✅ Login with client@example.com
2. ✅ View balance (50,000 UZS)
3. ✅ Send SMS (use approved nicknames: TestCompany or 1234)
4. ✅ Check message preview before sending
5. ✅ View message history with filters
6. ✅ Track message status

### Admin Dashboard Features:
1. ✅ Login with admin@example.com
2. ✅ View dashboard with stats
3. ✅ Manage operators (CRUD operations)
4. ✅ View all accounts
5. ✅ Filter and search accounts
6. ✅ Monitor system health

---

## 🗄️ Database Access

**Connection String:**
```
postgresql://otp:otp-secret@localhost:5432/otp
```

**Docker exec:**
```bash
docker exec -it jasmin-postgres-1 psql -U otp -d otp
```

---

## 🔄 Re-seeding Data

To re-run the seed script:

```bash
docker exec -i jasmin-postgres-1 psql -U otp -d otp -f /tmp/seed.sql
```

Or from host machine:

```bash
docker cp services/billing-service/migrations/999_seed_test_data.sql jasmin-postgres-1:/tmp/seed.sql
docker exec -i jasmin-postgres-1 psql -U otp -d otp -f /tmp/seed.sql
```

---

## ⚠️ Security Note

**These are development/test credentials only!**

Before deploying to production:
1. Delete all test accounts
2. Create secure admin account with strong password
3. Enable email verification
4. Set up proper authentication (2FA recommended)
5. Configure rate limiting
6. Review and secure all API endpoints
