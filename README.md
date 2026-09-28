# DeltaB

A personal finance application built as a production-style system: deployed across isolated environments, instrumented for debugging, broken on purpose, and recovered.

> The hosted environments are no longer running. Everything below describes the system as it was built and operated between September 2025 and March 2026, and every claim is traceable to code in this repository.

---

## Why it exists

Most side projects are built to work. This one was built to be operated. The budgeting features are real and usable, but the point of the project was the operational layer around them: structured logging you can actually trace a request through, a schema that refuses to hold inconsistent financial data, and a deployment path where failures surface at startup instead of in production.

Django · PostgreSQL (Supabase) · Render · Terraform · Docker · Kubernetes · Better Stack

---

## Observability

The two middleware classes in [`DeltaBApp/middleware/`](DeltaBApp/middleware/) are where most of the debugging value lives. Both attach a UUID request ID and emit structured JSON, shipped to Better Stack via `logtail`.

**[`performance.py`](DeltaBApp/middleware/performance.py)** records per request:

- Wall-clock duration in milliseconds
- SQL query count, by diffing `connection.queries` across the request
- Any individual query over a 50 ms threshold, logged at `WARNING` with the statement text
- Unhandled exceptions, with the request ID attached via `process_exception`

**[`memory_usage.py`](DeltaBApp/middleware/memory_usage.py)** records the RSS delta across each request using `psutil`, so memory-heavy request paths are visible rather than inferred.

Together these answer the three questions that actually come up when an endpoint is slow: is it the database, is it the number of round trips, or is it the application. Logging is configured in [`DeltaB/settings.py`](DeltaB/settings.py) using `python-json-logger`, with a console handler and a Better Stack handler on the root logger.

---

## Data integrity

The schema is deliberately strict. The goal is that invalid financial state is rejected by PostgreSQL, not caught by application code.

**Constraints** in [`DeltaBApp/models.py`](DeltaBApp/models.py):

- `CheckConstraint` on `Budget.limit` (`limit >= 0`) — negative budgets cannot be stored
- Uniqueness on `Category` (`user`, `type`, `name`), `Budget` (`month`, `year`, `category`), and `AccountBalanceHistory` (`account`, `date`)
- Foreign keys throughout with deliberate `CASCADE` / `SET_NULL` behavior — ownership relationships cascade, provenance links (`uploadsource`, `institution` on a statement) null out so history survives a parent delete
- `NOT NULL` on every required relation

**Atomicity.** Any operation that writes both a `Transaction` and its `Entry` rows runs inside `transaction.atomic()`. There are nine such blocks in [`DeltaBApp/views.py`](DeltaBApp/views.py). The bank statement flow is the important one:

1. Upload creates `PendingTransaction` and `PendingEntry` rows
2. User assigns category and transaction type
3. Pending records are deleted, finalized `Transaction` and `Entry` rows are created, account balances are updated, and transfers are paired

All of that is one transaction. A failure at step 6 leaves no trace of steps 3 through 5.

---

## Incident postmortem

[`docs/POSTMORTEM_001.md`](docs/POSTMORTEM_001.md) documents a real data-consistency bug and its fix.

Bulk statement imports of 20+ rows ran in autocommit inside a loop. A network drop mid-loop committed transaction headers without their corresponding entries, leaving account balances wrong with no error surfaced. Root cause was three-part: no atomicity, N+1 round trips to Supabase, and transfer-matching `SELECT`s inside the loop. The fix was a bulk refactor wrapped in `transaction.atomic()`, stateful transfer pairing inside the same block, and replacing bare `except` clauses with real tracebacks so a failing row identifies itself.

The prevention item from that postmortem is now a rule the codebase follows: any function writing both a `Transaction` and an `Entry` is wrapped in `atomic()`.

---

## Failure testing and recovery

Failures were induced deliberately to confirm the system fails safely rather than silently.

| Induced failure | Expected | Observed |
|---|---|---|
| Process killed mid-write | Full rollback, no partial commit | Confirmed — no orphaned transaction headers |
| Invalid database credentials | Startup failure | App refuses to start |
| Missing critical config | Startup failure | `Config.validate()` raises before Django initializes |
| Unrecognized `APP_ENV` | Startup failure | `RuntimeError` at import time |
| Database restore from backup | No corruption | Restored cleanly |

Fail-fast is enforced in [`DeltaB/settings.py`](DeltaB/settings.py): `Config.validate()` checks `SECRET_KEY`, `DATABASE_URL`, and all three Supabase keys before anything else loads, and an `APP_ENV` outside `staging | production | development` raises immediately. A misconfigured deploy dies at boot with a named cause instead of throwing 500s under traffic.

---

## CI/CD

Three workflows in [`.github/workflows/`](.github/workflows/).

**[`deploy.yml`](.github/workflows/deploy.yml)** — on push to `main`:

1. **Migration safety gate.** `makemigrations --check --dry-run` fails the build if models and migrations have drifted, which prevents deploying code whose schema was never generated.
2. **Test step** against a `postgres:15` service container (see Known gaps).
3. **Cold-start health check.** `curl` against the staging `/health/` endpoint with `--connect-timeout 60` and retries, because Render's free tier sleeps between requests. A non-200 fails the build before anything deploys.
4. **Deploy hook** fired only on success.

**[`lint.yml`](.github/workflows/lint.yml)** — Ruff on every push and pull request.

**[`ping_server.yml`](.github/workflows/ping_server.yml)** — scheduled warm-up every 14 minutes during business hours, to keep free-tier instances from cold-starting for a visitor.

---

## Infrastructure and environments

[`tf-infra/`](tf-infra/) provisions both halves of the stack:

- **Supabase provider** — the PostgreSQL project, region, and organization
- **Render provider** — the web service, its full environment variable set, and deploy triggers (`auto_deploy = false`; deploys were gated by the pipeline above)

Staging and production were fully isolated: separate databases, separate credentials, separate secrets. Schema changes landed in staging first, and a staging failure could not reach production data.

[`k8s/`](k8s/) holds a 3-replica `Deployment` and a `LoadBalancer` `Service` for running the containerized app on a cluster.

---

## Running it locally

```bash
cp .env.example .env     # fill in database and Supabase values
./setup.sh               # docker compose up --build, then migrate
```

Then visit `http://localhost:8000`.

To populate a database with realistic data:

```bash
python manage.py seed_demo            # seed accounts, transactions, budgets, goals
python manage.py seed_demo --dry-run  # same, rolled back at the end
```

The seeder runs under `@transaction.atomic`, so `--dry-run` genuinely leaves the database untouched.

The project also ships a read-only demo mode, used when the app was publicly reachable. [`demo_read_only`](DeltaBApp/decorators.py) rejects `POST`/`PUT`/`PATCH`/`DELETE` from the `demo_user` account with a 403 for AJAX calls and a redirect plus warning for form posts, so a seeded environment can be explored without being modified.

---

## Features

- Accounts grouped under institutions, with typed account categories
- Manual transaction entry and bank statement upload
- A pending-transaction review step before anything enters reporting
- Double-entry style modeling: a `Transaction` header with one or more `Entry` rows, supporting transfers and multi-entry splits
- Automatic transfer detection and pairing
- Per-category monthly budgets with historical summaries
- Account balance history, bills, reminders, tasks, and savings goals

---

## Known gaps

Listed because a project that claims to be production-style should be honest about where it isn't.

- **No automated test coverage.** `DeltaBApp/tests.py` is empty. The pipeline's test step and its `postgres:15` service container are scaffolding waiting for a suite — right now the step passes because there is nothing to run. This is the top item.
- **The Dockerfile runs Django's development server.** `CMD` is `manage.py runserver`, not `gunicorn`. The Render start command used gunicorn, so the deployed app was fine, but the container image is not production-grade and the build is single-stage.
- **Log level does not vary by environment.** The ternary in `settings.py` resolves to `INFO` on both branches.
- **The database retry loop in `settings.py` is dead code** — its `try` block is empty and breaks immediately.
- **Backups were the Supabase platform default**, not a tested, scheduled restore procedure of my own. One manual restore was performed and verified.
- **One postmortem.** More failure classes are worth documenting in the same format.
- **The pipeline assumes live hosting.** `deploy.yml`'s health check and `ping_server.yml`'s warm-up both target environments that no longer exist, so both will fail until the hosting is restored or those steps are removed.

---

## Architecture diagram

See [`SYSTEM_ARCHITECHTURE.md`](SYSTEM_ARCHITECHTURE.md).
