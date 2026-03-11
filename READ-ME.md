# Deltab — Production Personal Finance System

Deltab is a production-grade personal finance web application that allows users to import bank transactions, track spending, manage account balances, set category based budgets, and monitor financial activity over time with strong data integrity guarantees.

This project was intentionally designed to demonstrate **production system ownership**: deployment, database safety, observability, failure handling, and recovery.

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
- Django
- PostgreSQL (Supabase)
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
- Double-entry-style transaction modeling
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
- Migrations are created locally and committed to source control
- Migrations run automatically during service startup
- No manual production DB changes
- Migrations validated in staging before production

A failed migration prevents the service from starting, avoiding schema drift.

---

## Transaction Safety & Rollback Verification

Multi-step financial operations are wrapped in `transaction.atomic()` blocks.

### Verified Rollback via Exception Injection

Rollback behavior was explicitly validated by **injecting controlled failures** during multi-step writes.

#### Example Scenario
During transfer import processing:
- A `Transaction` row is created
- An exception is intentionally raised before `Entry` creation and pending cleanup

Observed behavior:
- Transaction row was rolled back
- No Entry rows were created
- PendingTransaction rows were preserved
- Account balances remained unchanged

This confirmed that partial writes do not persist when failures occur inside atomic blocks.

### ACID Guarantees
- **Atomicity:** All-or-nothing writes
- **Consistency:** Schema constraints enforced by the database
- **Isolation:** Concurrent requests do not corrupt balances
- **Durability:** Committed data persists across restarts

---

## Configuration Discipline

Configuration is entirely environment-driven.

- Required environment variables are explicitly defined
- Configuration is validated at startup
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

### Verified Failure Scenarios

#### 1. Application Termination During Write
A long-running transaction was introduced inside an atomic block.  
The application service was terminated mid-request.

Result:
- Open database transaction was rolled back automatically
- No partial Transaction or Entry rows persisted
- Account balances were unchanged

#### 2. Database Connectivity Failure
Database connectivity is verified at application startup.

When database connectivity failed:
- The application refused to start
- No traffic was served
- No database writes occurred

This prevents the application from running in a degraded state.

#### 3. Invalid Configuration Deployment
When required environment variables were missing:
- Application startup failed immediately
- Deployment was rejected
- No runtime instability occurred

This prevents configuration drift from causing silent data corruption.

---

## Backup & Recovery

Database backups are performed via the managed PostgreSQL provider.

### Restore Validation
Backups are not assumed valid until restoration is verified.

Recovery procedures were tested by restoring backed-up data into a non-production environment and validating:
- Application startup
- Data integrity
- Relationship consistency
- Core application workflows

This ensures recoverability and protects against silent data loss.

---

## Postmortems

Operational failures are documented with:
- What happened
- Root cause
- Detection method
- Preventive measures

This promotes continuous improvement and operational maturity.

---

## What This Project Demonstrates

- Production system ownership
- Safe handling of financial data
- Strong relational schema design
- ACID-compliant database operations
- Explicit failure injection and recovery
- Observability-first debugging
- Environment isolation and config hygiene

---

## Future Improvements

- Automated backup restore verification
- Centralized error aggregation
- Background job processing for imports
- Read replicas for analytics
- Budget forecasting and goal automation