-- ============================================================================
-- SEED TEST DATA
-- Creates test accounts for development and testing
-- ============================================================================

-- NOTE: Password hashes are bcrypt(12) for 'password123'
-- To generate: python3 -c "import bcrypt; print(bcrypt.hashpw(b'password123', bcrypt.gensalt(12)).decode())"

-- ============================================================================
-- TEST ADMIN ACCOUNT
-- ============================================================================
INSERT INTO accounts (id, name, type, status, currency, profile, created_at, updated_at)
VALUES
(
    '00000000-0000-0000-0000-000000000001',
    'Admin User',
    'admin',
    'active',
    'UZS',
    '{}'::jsonb,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO account_credentials (account_id, email, password_hash, email_verified, failed_login_attempts, created_at, updated_at)
VALUES
(
    '00000000-0000-0000-0000-000000000001',
    'admin@example.com',
    '$2b$12$nM8JkoLKXCiVLPOKm.6wKOLQ79HIU0oMwcBBpjSXxSFlOkCLrv7sO', -- password123
    TRUE,
    0,
    NOW(),
    NOW()
)
ON CONFLICT (account_id) DO UPDATE SET password_hash = EXCLUDED.password_hash;

INSERT INTO account_balances (account_id, balance, credit_limit, currency, updated_at)
VALUES
(
    '00000000-0000-0000-0000-000000000001',
    1000000.000000,
    0.000000,
    'UZS',
    NOW()
)
ON CONFLICT (account_id) DO UPDATE SET balance = EXCLUDED.balance;

-- ============================================================================
-- TEST CLIENT ACCOUNT
-- ============================================================================
INSERT INTO accounts (id, name, type, status, currency, profile, created_at, updated_at)
VALUES
(
    '00000000-0000-0000-0000-000000000002',
    'Test Company',
    'client',
    'active',
    'UZS',
    '{}'::jsonb,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO account_credentials (account_id, email, password_hash, email_verified, failed_login_attempts, created_at, updated_at)
VALUES
(
    '00000000-0000-0000-0000-000000000002',
    'client@example.com',
    '$2b$12$DVvYCs3ek0b7oQbWZ78IOe0rwtlU7gNeX7EquMPvPLL50D//DF1Je', -- password123
    TRUE,
    0,
    NOW(),
    NOW()
)
ON CONFLICT (account_id) DO UPDATE SET password_hash = EXCLUDED.password_hash;

INSERT INTO account_balances (account_id, balance, credit_limit, currency, updated_at)
VALUES
(
    '00000000-0000-0000-0000-000000000002',
    50000.000000,
    10000.000000,
    'UZS',
    NOW()
)
ON CONFLICT (account_id) DO UPDATE SET balance = EXCLUDED.balance;

-- ============================================================================
-- TEST RESELLER ACCOUNT
-- ============================================================================
INSERT INTO accounts (id, name, type, status, currency, profile, created_at, updated_at)
VALUES
(
    '00000000-0000-0000-0000-000000000003',
    'Reseller LLC',
    'reseller',
    'active',
    'UZS',
    '{}'::jsonb,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO account_credentials (account_id, email, password_hash, email_verified, failed_login_attempts, created_at, updated_at)
VALUES
(
    '00000000-0000-0000-0000-000000000003',
    'reseller@example.com',
    '$2b$12$psW2bb7UJZbS.tkETRE1guzoljOjwuOYNbH/bahDZrNtvcDuYnHWe', -- password123
    TRUE,
    0,
    NOW(),
    NOW()
)
ON CONFLICT (account_id) DO UPDATE SET password_hash = EXCLUDED.password_hash;

INSERT INTO account_balances (account_id, balance, credit_limit, currency, updated_at)
VALUES
(
    '00000000-0000-0000-0000-000000000003',
    100000.000000,
    50000.000000,
    'UZS',
    NOW()
)
ON CONFLICT (account_id) DO UPDATE SET balance = EXCLUDED.balance;

-- ============================================================================
-- TEST OPERATORS (SMPP Connectors)
-- ============================================================================
INSERT INTO operators (name, country, mcc, mnc, smpp_connector_id, status, price_per_sms, currency, priority, created_at, updated_at)
VALUES
(
    'Ucell',
    'Uzbekistan',
    '434',
    '05',
    'ucell-uz',
    'active',
    50.0000,
    'UZS',
    10,
    NOW(),
    NOW()
),
(
    'Beeline',
    'Uzbekistan',
    '434',
    '04',
    'beeline-uz',
    'active',
    45.0000,
    'UZS',
    20,
    NOW(),
    NOW()
),
(
    'Uzmobile',
    'Uzbekistan',
    '434',
    '07',
    'uzmobile-uz',
    'active',
    48.0000,
    'UZS',
    15,
    NOW(),
    NOW()
)
ON CONFLICT (smpp_connector_id) DO NOTHING;

-- ============================================================================
-- TEST APPROVED NICKNAMES (Sender IDs)
-- ============================================================================
INSERT INTO nicknames (id, account_id, nickname, status, category, approved_at, created_at, updated_at)
VALUES
(
    '20000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000002',
    'TestCompany',
    'approved',
    'Business',
    NOW(),
    NOW(),
    NOW()
),
(
    '20000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000002',
    '1234',
    'approved',
    'Short Code',
    NOW(),
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- TEST SMS CDR (Message History)
-- ============================================================================
INSERT INTO sms_cdr (id, message_id, account_id, connector_id, msisdn, sender, status, parts, price, currency, submit_at, delivery_at, created_at)
VALUES
(
    '30000000-0000-0000-0000-000000000001',
    'msg-test-001',
    '00000000-0000-0000-0000-000000000002',
    'ucell-uz',
    '998901234567',
    'TestCompany',
    'DELIVRD',
    1,
    50.000000,
    'UZS',
    NOW() - INTERVAL '1 hour',
    NOW() - INTERVAL '55 minutes',
    NOW() - INTERVAL '1 hour'
),
(
    '30000000-0000-0000-0000-000000000002',
    'msg-test-002',
    '00000000-0000-0000-0000-000000000002',
    'beeline-uz',
    '998907654321',
    'TestCompany',
    'DELIVRD',
    1,
    45.000000,
    'UZS',
    NOW() - INTERVAL '2 hours',
    NOW() - INTERVAL '118 minutes',
    NOW() - INTERVAL '2 hours'
),
(
    '30000000-0000-0000-0000-000000000003',
    'msg-test-003',
    '00000000-0000-0000-0000-000000000002',
    'uzmobile-uz',
    '998931234567',
    '1234',
    'PENDING',
    1,
    48.000000,
    'UZS',
    NOW() - INTERVAL '10 minutes',
    NULL,
    NOW() - INTERVAL '10 minutes'
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- Admin Account:
--   Email: admin@example.com
--   Password: password123
--   Balance: 1,000,000 UZS
--
-- Client Account:
--   Email: client@example.com
--   Password: password123
--   Balance: 50,000 UZS
--   Credit: 10,000 UZS
--
-- Reseller Account:
--   Email: reseller@example.com
--   Password: password123
--   Balance: 100,000 UZS
--   Credit: 50,000 UZS
-- ============================================================================
