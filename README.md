# Deltab – Budget & Transaction Management System

## Overview ##

Deltab is a personal finance web application that allows users to track bank transactions, account balances, budgets, and financial goals. This system emphasizes data integrity, observability, and operational discipline, and was intentionally designed to be deployed, broken, recovered, and documented like a real production service.

**Production URL:** https://deltab.onrender.com  
**Staging URL:** https://deltab-staging.onrender.com

-----

## System Architecture ##

### Application Layer
- Django (Python)
- REST-style CRUD endpoints
- Custom user model
- Middleware-based logging and performance procedures

### Data Layer
- PostgreSQL (Supabase)
- Separate databases for staging and production
- Strict relational schema with foreign keys and uniqueness constraints

### Hosting & Deployment
- Render (application hosting)
- Supabase (managed PostgreSQL + file storage)
- Environment-based configuration (staging vs production)

### Logging
- Better Stack
- JSON Structured logs

---

## Core Features ##

- User-managed financial accounts and institutions
- Transaction Upload (manual and bank statement upload)
- Pending transactions workflow before committing to reporting
- Double-entry style transaction modeling
- Budgeting per category and month
- Bills, reminders, tasks, and savings goals

---

## Environments ##

Two fully isolated environments are maintained:

- Each environment uses its own database, credentials, and secrets
- Environment behavior is controlled via environment variables
- Changes are validated in staging before posting to production
- Any failures in staging do not impact production data or availability

---

## Configuration Discipline

- All sensitive values (DB credentials, Django secret key, environment flags) are supplied via environment variables
- Invalid database credentials or missing critical configurations cause the application to fail at startup rather than at runtime
- Logging levels differ by environment (DEBUG in staging, INFO in production)

---

## Database Design & Safety ##

The database schema is intentionally strict to enforce data integrity.

### Schema Integrity

- **NOT NULL constraints** on required fields
- **UNIQUE constraints** where appropriate:
  - Category names per user and type
  - Monthly budgets per category
  - Account balance history per account/date
- **Foreign keys** used throughout with intentional cascade behavior
- **Check constraints** (e.g., budget limits must be non-negative)

### Key Models

- Users (custom user model)
- Bank Institutions > Accounts
- Transactions > Entries (supports transfers and multi-entry transactions)
- Budgets, Monthly Summaries (Budget History), Account Balance History
- Tasks, Reminders, Goals

### Migrations

- All schema changes are managed via Django migrations
- No manual schema changes are made in production
- Migrations are tested in staging before being deployed to production

Even if the application encounters errors, the database schema prevents invalid or inconsistent financial data.

---

## Transaction Safety ##

Several multi-step write operations are wrapped in `transaction.atomic()` blocks.

### Example: Bank Statement Upload → Final Transaction

1. Bank statement upload creates a `PendingTransaction` and `PendingEntry`
2. User assigns category and transaction type
3. System deletes pending records
4. System creates a finalized `Transaction`
5. Corresponding `Entry` records are created
6. Account balances are updated
7. Transfers are detected and paired automatically when applicable

All steps occur inside atomic transactions. If any step fails, no partial data is committed, ensuring consistency.

---

## Observability ##

### Logging

- Structured JSON logs
- Persistent logs across restarts
- Request/response logging with user context
- Unique request IDs for traceability

### Performance & Resource Tracking

Custom middleware logs:
- Request latency
- SQL query count per request
- Slow SQL queries (>50ms)
- Memory usage changes per request

This enables identification of:
- Slow endpoints
- Inefficient queries
- Memory-heavy request paths

### Error Visibility

- Full exception tracebacks logged
- Errors correlated to request IDs
- Context-rich logs allow debugging without SSH access

---

## Failure Testing & Recovery ##

### Intentional Failures Tested

- **Application killed during database write**
  - Result: transaction rollback, no partial data commited
- **Broken database connection**
  - Result: application fails to start
- **Bad configuration deployment**
  - Result: applications fails to start

These failures validate that the system fails fast and safely.

### Recovery

- Application recovery via redeploy
- Git-based rollback supported
- Weekly PostgreSQL backups (Database successfully restored from backup without data corruption)

---

## Postmortems ##

Formal postmortems are planned as part of ongoing operational maturity improvements. Future work includes documenting:
- Failure timeline
- Detection methods
- Root cause
- Preventative actions

---

## Why This Project Matters ##

This project was built to demonstrate the ability to:
- Design safe relational schemas
- Protect data using transactions and constraints
- Operate multiple production environments
- Observe and debug systems using logs and metrics
- Intentionally break production systems and recover safely

---

## Future Improvements ##

- Automated backup and restore testing
- Formalized postmortem documentation
- Error aggregation (e.g., Sentry)
- CI-based migration checks
