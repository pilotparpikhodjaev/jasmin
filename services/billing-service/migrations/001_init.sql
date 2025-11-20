CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('admin', 'reseller', 'client')),
    status TEXT NOT NULL CHECK (status IN ('active', 'suspended')),
    currency CHAR(3) NOT NULL,
    parent_id UUID REFERENCES accounts (id),
    profile JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES accounts (id),
    token TEXT NOT NULL UNIQUE,
    label TEXT,
    allowed_ips TEXT[],
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS account_balances (
    account_id UUID PRIMARY KEY REFERENCES accounts (id),
    balance NUMERIC(18, 6) NOT NULL DEFAULT 0,
    credit_limit NUMERIC(18, 6) NOT NULL DEFAULT 0,
    currency CHAR(3) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS balance_ledger (
    id UUID PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES accounts (id),
    amount NUMERIC(18, 6) NOT NULL,
    currency CHAR(3) NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('debit', 'credit')),
    reason TEXT,
    reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_balance_ledger_account_created_at
    ON balance_ledger (account_id, created_at DESC);

CREATE TABLE IF NOT EXISTS tariffs (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts (id),
    mcc CHAR(3),
    mnc CHAR(3),
    connector_id TEXT,
    price_per_submit NUMERIC(18, 6) NOT NULL,
    currency CHAR(3) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sms_cdr (
    id UUID PRIMARY KEY,
    message_id TEXT NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts (id),
    connector_id TEXT,
    msisdn TEXT NOT NULL,
    sender TEXT,
    status TEXT NOT NULL,
    parts INTEGER NOT NULL DEFAULT 1,
    price NUMERIC(18, 6),
    currency CHAR(3),
    submit_at TIMESTAMPTZ NOT NULL,
    delivery_at TIMESTAMPTZ,
    error_code TEXT,
    dlr_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sms_cdr_account_created_at
    ON sms_cdr (account_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_sms_cdr_message_id
    ON sms_cdr (message_id);

