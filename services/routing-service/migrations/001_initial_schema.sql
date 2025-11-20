-- Routing Service Initial Schema
-- Creates operators and MCC/MNC prefix tables with Uzbekistan data

-- Operators table
CREATE TABLE IF NOT EXISTS operators (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    mcc VARCHAR(3) NOT NULL,
    mnc VARCHAR(3) NOT NULL,
    smpp_connector_id VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'testing')),
    price_per_sms DECIMAL(10, 4) NOT NULL DEFAULT 0.0000,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    health_score INT NOT NULL DEFAULT 100 CHECK (health_score >= 0 AND health_score <= 100),
    priority INT NOT NULL DEFAULT 10,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- MCC/MNC Prefix mapping table
CREATE TABLE IF NOT EXISTS mcc_mnc_prefixes (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(5) NOT NULL,
    prefix VARCHAR(10) NOT NULL,
    mcc VARCHAR(3) NOT NULL,
    mnc VARCHAR(3) NOT NULL,
    operator_id INT NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (country_code, prefix)
);

-- Operator health metrics table
CREATE TABLE IF NOT EXISTS operator_health (
    operator_id INT PRIMARY KEY REFERENCES operators(id) ON DELETE CASCADE,
    dlr_rate DECIMAL(5, 2) NOT NULL DEFAULT 0.00 CHECK (dlr_rate >= 0 AND dlr_rate <= 100),
    avg_latency_ms INT NOT NULL DEFAULT 0,
    current_tps INT NOT NULL DEFAULT 0,
    error_rate DECIMAL(5, 2) NOT NULL DEFAULT 0.00 CHECK (error_rate >= 0 AND error_rate <= 100),
    health_score INT NOT NULL DEFAULT 100 CHECK (health_score >= 0 AND health_score <= 100),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_operators_status ON operators(status);
CREATE INDEX idx_operators_price ON operators(price_per_sms);
CREATE INDEX idx_mcc_mnc_prefix ON mcc_mnc_prefixes(country_code, prefix);
CREATE INDEX idx_mcc_mnc_operator ON mcc_mnc_prefixes(operator_id);

-- Insert Uzbekistan operators (MCC: 434)
-- Based on real Uzbekistan mobile operators

-- 1. Beeline (Unitel/Coscom) - MNC: 04, 07
INSERT INTO operators (name, country, mcc, mnc, smpp_connector_id, status, price_per_sms, currency, priority)
VALUES
    ('Beeline', 'Uzbekistan', '434', '04', 'smpp-beeline-uz', 'active', 50.00, 'UZS', 1);

-- 2. Ucell (Coscom) - MNC: 05, 07
INSERT INTO operators (name, country, mcc, mnc, smpp_connector_id, status, price_per_sms, currency, priority)
VALUES
    ('Ucell', 'Uzbekistan', '434', '05', 'smpp-ucell-uz', 'active', 55.00, 'UZS', 2);

-- 3. UMS (Uzdunrobita) - MNC: 01
INSERT INTO operators (name, country, mcc, mnc, smpp_connector_id, status, price_per_sms, currency, priority)
VALUES
    ('UMS', 'Uzbekistan', '434', '01', 'smpp-ums-uz', 'active', 60.00, 'UZS', 3);

-- 4. Perfectum Mobile (Mobiuz) - MNC: 06
INSERT INTO operators (name, country, mcc, mnc, smpp_connector_id, status, price_per_sms, currency, priority)
VALUES
    ('Perfectum Mobile', 'Uzbekistan', '434', '06', 'smpp-perfectum-uz', 'active', 65.00, 'UZS', 4);

-- Insert MCC/MNC prefixes for Uzbekistan operators
-- Country code: +998
-- Prefix allocation (2-digit after country code):

-- Beeline prefixes: 90, 91
INSERT INTO mcc_mnc_prefixes (country_code, prefix, mcc, mnc, operator_id)
SELECT '+998', '90', '434', '04', id FROM operators WHERE smpp_connector_id = 'smpp-beeline-uz'
UNION ALL
SELECT '+998', '91', '434', '04', id FROM operators WHERE smpp_connector_id = 'smpp-beeline-uz';

-- Ucell prefixes: 93, 94, 95, 97
INSERT INTO mcc_mnc_prefixes (country_code, prefix, mcc, mnc, operator_id)
SELECT '+998', '93', '434', '05', id FROM operators WHERE smpp_connector_id = 'smpp-ucell-uz'
UNION ALL
SELECT '+998', '94', '434', '05', id FROM operators WHERE smpp_connector_id = 'smpp-ucell-uz'
UNION ALL
SELECT '+998', '95', '434', '05', id FROM operators WHERE smpp_connector_id = 'smpp-ucell-uz'
UNION ALL
SELECT '+998', '97', '434', '05', id FROM operators WHERE smpp_connector_id = 'smpp-ucell-uz';

-- UMS prefixes: 88, 98, 99
INSERT INTO mcc_mnc_prefixes (country_code, prefix, mcc, mnc, operator_id)
SELECT '+998', '88', '434', '01', id FROM operators WHERE smpp_connector_id = 'smpp-ums-uz'
UNION ALL
SELECT '+998', '98', '434', '01', id FROM operators WHERE smpp_connector_id = 'smpp-ums-uz'
UNION ALL
SELECT '+998', '99', '434', '01', id FROM operators WHERE smpp_connector_id = 'smpp-ums-uz';

-- Perfectum Mobile prefixes: 33, 77
INSERT INTO mcc_mnc_prefixes (country_code, prefix, mcc, mnc, operator_id)
SELECT '+998', '33', '434', '06', id FROM operators WHERE smpp_connector_id = 'smpp-perfectum-uz'
UNION ALL
SELECT '+998', '77', '434', '06', id FROM operators WHERE smpp_connector_id = 'smpp-perfectum-uz';

-- Initialize operator health metrics
INSERT INTO operator_health (operator_id, dlr_rate, avg_latency_ms, current_tps, error_rate, health_score)
SELECT id, 95.00, 500, 0, 2.00, 95 FROM operators WHERE smpp_connector_id = 'smpp-beeline-uz'
UNION ALL
SELECT id, 93.00, 600, 0, 3.00, 93 FROM operators WHERE smpp_connector_id = 'smpp-ucell-uz'
UNION ALL
SELECT id, 90.00, 700, 0, 5.00, 90 FROM operators WHERE smpp_connector_id = 'smpp-ums-uz'
UNION ALL
SELECT id, 88.00, 800, 0, 6.00, 88 FROM operators WHERE smpp_connector_id = 'smpp-perfectum-uz';

-- Verify data
SELECT 'Operators created:' as info, COUNT(*) as count FROM operators;
SELECT 'Prefixes created:' as info, COUNT(*) as count FROM mcc_mnc_prefixes;
SELECT 'Health metrics created:' as info, COUNT(*) as count FROM operator_health;
