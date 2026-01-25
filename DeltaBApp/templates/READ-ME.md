# Deltab — Production Personal Finance System

Deltab is a production-grade personal finance web application that allows users to import bank transactions, track spending, manage account balances, set category-based budgets, and monitor financial activity over time with strong data integrity guarantees.

This project was intentionally designed to demonstrate production system ownership: deployment, database safety, observability, failure handling, and recovery.

---

## Live Environments

- **Production:** https://deltab.onrender.com  
- **Staging:** https://deltab-staging.onrender.com  

Each environment has:
- Separate PostgreSQL databases
- Separate secrets and environment variables
- Independent deployments

All changes are tested in staging before production release.

---

## Architecture Overview

**Application**
- Django (monolithic web service)
- PostgreSQL (Supabase-managed)
- Hosted on Render
- File storage via Supabase object storage

**Key Properties**
- Persistent user data
- Strong relational schema
- Explicit transaction boundaries
- Environment-based configuration

---

## Core Features

- Manual and imported transaction tracking
- Double-entry-style transaction modeling (entries per transaction)
- Account balance tracking with history
- Category-based budgets
- Pending transaction review workflow
- Bills and reminders
- Savings goals (in progress)

---

## Database Design & Safety

The database schema is designed to protect data integrity even if the application misbehaves.

### Schema Integrity
- NOT NULL constraints on critical fields
- Unique constraints (e.g. budgets per month/category, account balance per date)
- Explicit foreign keys across all relations
- Intentional cascade behavior (CASCADE vs SET NULL)

### Example Safety Patterns
- Users own all financial entities (hard isolation)
- Transactions decompose into Entries for atomic balance updates
- AccountBalanceHistory prevents duplicate records per day

### Migrations
- All schema changes are applied via Django migrations
- No manual production DB changes
- Migrations validated in staging before production

---

## Transaction Safety

Multi-step financial operations are wrapped in `transaction.atomic()` blocks.

### Example:
When converting a pending transaction into a finalized transaction:
- PendingTransaction is deleted
- PendingEntry rows are deleted
- Transaction row is created
- Entry rows are created
- Account balances are updated

If any step fails, the entire operation is rolled back, guaranteeing:
- No partial writes
- No balance corruption

This ensures ACID compliance, particularly atomicity and consistency.

---

## Configuration Discipline

Configuration is entirely environment-driven.

- Required environment variables are explicitly defined
- Application fails fast if critical config is missing
- Environment flag determines staging vs production behavior
- Secrets (DB credentials, Django secret key) are isolated per environment

Failing at startup is preferred over undefined runtime behavior.

---

## Observability

### Logging
- Structured JSON logs
- Request/response logging
- Per-request unique request IDs
- Memory usage tracking per request
- SQL query count and slow query detection

### Performance Monitoring
- Request latency tracking
- Slow endpoint identification
- Slow SQL query logging with thresholds

### Error Visibility
- Full exception tracebacks logged
- Errors captured with contextual request data

This allows debugging issues without SSH access to production hosts.

---

## Failure Testing & Recovery

The system is intentionally tested against failure scenarios in staging.

### Failure Scenarios
- Application terminated mid-database write
- Database connection misconfiguration
- Invalid or missing environment configuration

### Recovery Procedures
- Redeploy known-good application version
- Restore database from Supabase backup
- Verify data integrity and service health

Backups are not assumed safe until restore is verified.

---

## Postmortems

Operational failures are documented with:
- What happened
- Root cause
- Detection method
- Preventive measures

This encourages continuous improvement and operational maturity.

---

## What This Project Demonstrates

- Production system ownership
- Safe handling of financial data
- Strong relational schema design
- ACID-compliant database operations
- Observability-first debugging
- Environment isolation and config hygiene
- Failure recovery and data protection

---

## Future Improvements

- Automated backup restore verification
- Background job processing for imports
- Read replicas for analytics
- Budget forecasting and goal automation