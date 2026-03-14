# DeltaB – Budget & Transaction Management System

## Overview ##

DeltaB is a personal finance web application that allows users to track bank transactions, account balances, budgets, and financial goals. This system emphasizes data integrity, observability, and operational discipline, and was intentionally designed to be deployed, broken, recovered, and documented like a real production service.

**Production URL:** https://deltab.onrender.com  
**Staging URL:** https://deltab-staging.onrender.com

-----

## Why This Project Matters

DeltaB was designed not just as a budgeting application, but as a **production-style system**. The project focuses on:

- Infrastructure reliability
- Observability and operational debugging
- Strict database integrity
- Safe transaction processing

The goal was to build a system that could be **deployed, broken, diagnosed, and recovered** like a real service.

---

## Key Engineering Highlights

- **Infrastructure as Code:** Entire cloud stack provisioned with Terraform for reproducible environments.
- **CI/CD Safety Gates:** GitHub Actions pipeline validates migrations, runs tests against ephemeral PostgreSQL containers, and verifies service health before deployment.
- **Structured Observability:** JSON structured logging with request IDs, latency tracking, SQL query metrics, and memory profiling.
- **Atomic Financial Transactions:** Multi-step financial writes protected by `transaction.atomic()` to guarantee data consistency.
- **Staging/Production Parity:** Fully isolated environments with separate databases, credentials, and environment configs.

---

## CI/CD Pipeline & Automated Validation

Every push to main triggers a robust GitHub Actions pipeline designed to prevent regression and deployment failure:

- Migration Safety Gate: Uses makemigrations --check --dry-run to ensure the local schema matches the codebase before deployment.
- Ephemeral Testing: Spins up a PostgreSQL 15 service container in the runner to execute the test suite in a clean environment.
- Cold-Start Health Checks: A custom curl-based health check wakes up the staging instance and verifies a 200 OK from the /health/ endpoint before the final production deploy hook is triggered.

---

## Infrastructure as Code (IaC)

The entire cloud stack is managed via Terraform, ensuring environment parity:

- Supabase Provider: Manages the relational database lifecycle and organization settings.
- Render Provider: Defines the web service configuration, environment variables, and manual deployment triggers.

---

## Containerization & Local Development

- Docker: Multi-stage builds for a slim production-ready image.
- Kubernetes (K8s): Ready-to-deploy manifests including a 3-replica Deployment for high availability and a LoadBalancer Service.
- One-Command Setup: A setup.sh script automates the entire local bring-up, including Docker Compose builds and automatic database migrations.

---

## Observability

### Logging

- Structured JSON logs
- Request/response logging with user context
- Unique request IDs for traceability
- Persistent logs across restarts

### Performance Telemetry

Custom middleware records:

- Request latency
- SQL query count per request
- Slow SQL queries (>50ms)
- Memory usage changes per request

These metrics allow rapid identification of slow endpoints, inefficient queries, and memory-heavy request paths.

---

## Failure Testing & Recovery

### Intentional Failures Tested

- **Application killed during database write**
  - Result: transaction rollback, no partial data committed
- **Broken database connection**
  - Result: application fails to start
- **Bad configuration deployment**
  - Result: application fails to start

These failures validate that the system fails fast and safely.

### Recovery

- Application recovery via redeploy
- Git-based rollback supported
- Weekly PostgreSQL backups (Database successfully restored from backup without data corruption)

---

## Configuration Discipline

- All sensitive values (DB credentials, Django secret key, environment flags) are supplied via environment variables
- Invalid database credentials or missing critical configurations cause the application to fail at startup rather than at runtime
- Logging levels differ by environment (DEBUG in staging, INFO in production)

---

## Database Design & Safety

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

## Transaction Safety

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

## Environments

Two fully isolated environments are maintained:

- Each environment uses its own database, credentials, and secrets
- Environment behavior is controlled via environment variables
- Changes are validated in staging before posting to production
- Any failures in staging do not impact production data or availability

---

## Demo Mode Logic

Features a seed_demo.py utility that populates a view-only environment. This allows recruiters to explore the full dashboard and transaction history while a custom permission layer blocks write actions, protecting the integrity of the demo environment.

---

## Core Features

- User-managed financial accounts and institutions
- Transaction Upload (manual and bank statement upload)
- Pending transactions workflow before committing to reporting
- Double-entry style transaction modeling
- Budgeting per category and month
- Bills, reminders, tasks, and savings goals

---

## System Architecture

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
- BetterStack
- JSON Structured logs

---

## Postmortems

Formal postmortems are planned as part of ongoing operational maturity improvements. Future work includes documenting:
- Failure timeline
- Detection methods
- Root cause
- Preventative actions

---

## Future Improvements

- Automated backup and restore testing
- Formalized postmortem documentation
- Error aggregation (e.g., Sentry)
- CI-based migration checks
