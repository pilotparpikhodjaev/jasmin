# 🏦 Enterprise Billing Service

**Production-ready billing and account management service for Jasmin SMS Gateway**

## 📋 Overview

The Billing Service is the authoritative source for:
- **Account Management** - User accounts with authentication, balance, and hierarchy
- **Balance Tracking** - Real-time balance management with credit limits and ledger
- **CDR Storage** - Call Detail Records for all SMS messages with delivery tracking
- **Operator Management** - SMPP operator configurations with health monitoring
- **Template Management** - Message templates with moderation workflow
- **Dispatch Tracking** - Batch SMS tracking with status aggregation
- **Nickname Management** - Sender ID approval workflow
- **Transaction History** - Complete financial audit trail
- **Authentication** - Email/password login with bcrypt hashing

## 🚀 Quick Start

```bash
# Start services
docker-compose up -d

# Access API docs
open http://localhost:8081/docs
```

## 📊 Database Schema

**Core Tables:** accounts, account_credentials, account_balances, balance_ledger, api_keys, tariffs, sms_cdr

**Enterprise Tables:** operators, operator_health_metrics, nicknames, dispatches, transactions, audit_logs

## 🔧 API Endpoints (35+)

- **Authentication** (5): register, login, change-password, reset-password, verify-email
- **Operators** (7): CRUD + health + stats
- **Nicknames** (7): CRUD + moderation + approved list
- **Dispatches** (6): CRUD + status + messages
- **Accounts, CDR, Charges, Templates** (10+)

## 🎯 Status

✅ **ENTERPRISE-READY** - Version 1.0.0

See full documentation at http://localhost:8081/docs
