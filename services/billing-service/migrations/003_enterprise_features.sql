-- Enterprise Features Migration
-- Adds: operators, nicknames, authentication, transactions, invoices, tariff plans

-- ============================================================================
-- OPERATORS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS operators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(64) NOT NULL UNIQUE,
    country CHAR(2) NOT NULL,
    mcc CHAR(3) NOT NULL,
    mnc CHAR(3) NOT NULL,
    price_per_sms NUMERIC(18, 6) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'UZS',
    priority INTEGER NOT NULL DEFAULT 100,
    weight INTEGER NOT NULL DEFAULT 100,
    status VARCHAR(32) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    health_check_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    health_check_interval INTEGER NOT NULL DEFAULT 60,
    smpp_config JSONB NOT NULL,
    jasmin_connector_id VARCHAR(64),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_operators_country ON operators(country);
CREATE INDEX idx_operators_mcc_mnc ON operators(mcc, mnc);
CREATE INDEX idx_operators_status ON operators(status);

-- ============================================================================
-- OPERATOR HEALTH METRICS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS operator_health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
    is_connected BOOLEAN NOT NULL DEFAULT FALSE,
    last_connected_at TIMESTAMPTZ,
    connection_uptime_seconds INTEGER DEFAULT 0,
    submit_sm_count INTEGER DEFAULT 0,
    submit_sm_resp_count INTEGER DEFAULT 0,
    delivery_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    submit_success_rate NUMERIC(5, 2) DEFAULT 0.0,
    delivery_rate NUMERIC(5, 2) DEFAULT 0.0,
    avg_submit_latency_ms NUMERIC(10, 2) DEFAULT 0.0,
    p95_submit_latency_ms NUMERIC(10, 2) DEFAULT 0.0,
    p99_submit_latency_ms NUMERIC(10, 2) DEFAULT 0.0,
    health_score NUMERIC(5, 2) DEFAULT 100.0,
    health_status VARCHAR(32) NOT NULL DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    recent_errors JSONB DEFAULT '[]'::jsonb,
    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_operator_health_operator_measured ON operator_health_metrics(operator_id, measured_at DESC);

-- ============================================================================
-- NICKNAMES (SENDER IDs) TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS nicknames (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    nickname VARCHAR(11) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    category VARCHAR(64),
    description TEXT,
    approved_by UUID REFERENCES accounts(id),
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(account_id, nickname)
);

CREATE INDEX idx_nicknames_account ON nicknames(account_id);
CREATE INDEX idx_nicknames_status ON nicknames(status);

-- ============================================================================
-- AUTHENTICATION TABLE (for email/password login)
-- ============================================================================
CREATE TABLE IF NOT EXISTS account_credentials (
    account_id UUID PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verified_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_account_credentials_email ON account_credentials(email);

-- ============================================================================
-- TRANSACTIONS TABLE (financial audit trail)
-- ============================================================================
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    type VARCHAR(32) NOT NULL CHECK (type IN ('charge', 'refund', 'topup', 'adjustment', 'commission')),
    amount NUMERIC(18, 6) NOT NULL,
    currency CHAR(3) NOT NULL,
    balance_before NUMERIC(18, 6) NOT NULL,
    balance_after NUMERIC(18, 6) NOT NULL,
    description TEXT,
    reference_type VARCHAR(64),
    reference_id UUID,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES accounts(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_transactions_account_created ON transactions(account_id, created_at DESC);
CREATE INDEX idx_transactions_reference ON transactions(reference_type, reference_id);

-- ============================================================================
-- TARIFF PLANS TABLE (volume discounts, custom pricing)
-- ============================================================================
CREATE TABLE IF NOT EXISTS tariff_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(32) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    pricing_rules JSONB NOT NULL,
    volume_discounts JSONB DEFAULT '[]'::jsonb,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tariff_plans_account ON tariff_plans(account_id);
CREATE INDEX idx_tariff_plans_status ON tariff_plans(status);

-- ============================================================================
-- INVOICES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(64) NOT NULL UNIQUE,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    subtotal NUMERIC(18, 6) NOT NULL,
    tax_rate NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
    tax_amount NUMERIC(18, 6) NOT NULL DEFAULT 0.0,
    total NUMERIC(18, 6) NOT NULL,
    currency CHAR(3) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'issued', 'paid', 'cancelled')),
    due_date TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    payment_method VARCHAR(64),
    payment_reference VARCHAR(255),
    line_items JSONB NOT NULL DEFAULT '[]'::jsonb,
    notes TEXT,
    pdf_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_invoices_account_period ON invoices(account_id, period_start DESC);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_number ON invoices(invoice_number);

-- ============================================================================
-- PAYMENT GATEWAY TRANSACTIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES invoices(id),
    gateway VARCHAR(64) NOT NULL,
    gateway_transaction_id VARCHAR(255),
    amount NUMERIC(18, 6) NOT NULL,
    currency CHAR(3) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded')),
    payment_method VARCHAR(64),
    gateway_response JSONB,
    error_message TEXT,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payment_transactions_account ON payment_transactions(account_id, created_at DESC);
CREATE INDEX idx_payment_transactions_gateway_id ON payment_transactions(gateway_transaction_id);
CREATE INDEX idx_payment_transactions_status ON payment_transactions(status);

-- ============================================================================
-- REVENUE SHARING TABLE (for resellers)
-- ============================================================================
CREATE TABLE IF NOT EXISTS revenue_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reseller_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    revenue_amount NUMERIC(18, 6) NOT NULL,
    commission_rate NUMERIC(5, 2) NOT NULL,
    commission_amount NUMERIC(18, 6) NOT NULL,
    currency CHAR(3) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'cancelled')),
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_revenue_shares_reseller ON revenue_shares(reseller_id, created_at DESC);
CREATE INDEX idx_revenue_shares_client ON revenue_shares(client_id);
CREATE INDEX idx_revenue_shares_status ON revenue_shares(status);

-- ============================================================================
-- DISPATCH TRACKING TABLE (for batch SMS)
-- ============================================================================
CREATE TABLE IF NOT EXISTS dispatches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispatch_id VARCHAR(255) NOT NULL UNIQUE,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    total_messages INTEGER NOT NULL DEFAULT 0,
    submitted_count INTEGER NOT NULL DEFAULT 0,
    delivered_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    pending_count INTEGER NOT NULL DEFAULT 0,
    total_cost NUMERIC(18, 6) NOT NULL DEFAULT 0.0,
    currency CHAR(3) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed', 'cancelled')),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dispatches_account ON dispatches(account_id, created_at DESC);
CREATE INDEX idx_dispatches_dispatch_id ON dispatches(dispatch_id);

-- ============================================================================
-- AUDIT LOG TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    actor_id UUID REFERENCES accounts(id),
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id UUID,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_account ON audit_logs(account_id, created_at DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- ============================================================================
-- RATE LIMITS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    limit_type VARCHAR(64) NOT NULL,
    max_requests INTEGER NOT NULL,
    window_seconds INTEGER NOT NULL,
    current_count INTEGER NOT NULL DEFAULT 0,
    window_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(account_id, limit_type)
);

CREATE INDEX idx_rate_limits_account ON rate_limits(account_id);

-- ============================================================================
-- Add missing columns to existing tables
-- ============================================================================

-- Add dispatch_id to sms_cdr
ALTER TABLE sms_cdr ADD COLUMN IF NOT EXISTS dispatch_id VARCHAR(255);
ALTER TABLE sms_cdr ADD COLUMN IF NOT EXISTS user_sms_id VARCHAR(255);
ALTER TABLE sms_cdr ADD COLUMN IF NOT EXISTS message_text TEXT;
ALTER TABLE sms_cdr ADD COLUMN IF NOT EXISTS country CHAR(2);
ALTER TABLE sms_cdr ADD COLUMN IF NOT EXISTS operator_id UUID REFERENCES operators(id);

CREATE INDEX IF NOT EXISTS idx_sms_cdr_dispatch ON sms_cdr(dispatch_id);
CREATE INDEX IF NOT EXISTS idx_sms_cdr_user_sms_id ON sms_cdr(user_sms_id);

-- Add rate limiting to accounts
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS rate_limit_rps INTEGER DEFAULT 50;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS allowed_ips TEXT[];

-- Add email to accounts (for backward compatibility)
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS email VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_email ON accounts(email) WHERE email IS NOT NULL;

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at
CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_operators_updated_at BEFORE UPDATE ON operators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nicknames_updated_at BEFORE UPDATE ON nicknames
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_account_credentials_updated_at BEFORE UPDATE ON account_credentials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tariff_plans_updated_at BEFORE UPDATE ON tariff_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_invoices_updated_at BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dispatches_updated_at BEFORE UPDATE ON dispatches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

