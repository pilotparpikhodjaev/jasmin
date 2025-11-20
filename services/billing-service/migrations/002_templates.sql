CREATE TABLE IF NOT EXISTS templates (
    id UUID PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES accounts (id),
    name TEXT NOT NULL,
    channel TEXT NOT NULL,
    category TEXT,
    content TEXT NOT NULL,
    variables JSONB,
    status TEXT NOT NULL DEFAULT 'pending',
    admin_comment TEXT,
    last_submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_templates_account ON templates (account_id);
CREATE INDEX IF NOT EXISTS idx_templates_status ON templates (status);

