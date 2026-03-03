# Incident Postmortem: 002 - Atomic Integrity & Statement Processing Latency
**Date:** 2026-03-02  
**Status:** Resolved  
**Severity:** High (Risk of Data Inconsistency)

## Summary
During large bank statement imports (50+ rows), the system experienced high latency. A network flicker during a non-atomic loop caused "Partial Commits"—where Transactions were created without corresponding Entries—leading to corrupted user balances.

## Root Cause Analysis
1. **Lack of Atomicity:** The original `createtransaction` function operated in "Autocommit" mode. If a failure occurred mid-loop, the database saved the Transaction header but failed to save the money-moving Entries.
2. **N+1 Round-trips:** Each manual or imported transaction required multiple sequential `INSERT` statements. Over the network to Supabase, this caused a linear increase in response time.
3. **Complex Pairing Logic:** The transfer matching logic (`matchtransaction`) added additional `SELECT` overhead within the loop, further slowing down the process.

## Resolution (The "Bulk" Refactor)
- **Transactional Integrity:** Wrapped the new `create_bulk_transactions` in `db_transaction.atomic()`. This guarantees that if a transfer fails to pair or an entry fails to write, the entire set is rolled back.
- **Stateful Pairing:** Optimized the `TRANSFER_TYPES` logic to handle "Matched" vs "Unmatched" imports. If a match is found, the system now updates the existing transaction's paired state within the same atomic block.
- **Traceback Visibility:** Replaced bare excepts with `Exception as e` and `traceback.print_exc()` to ensure that if a bulk upload fails, the specific row and reason are visible in logs.

## Prevention & Operational Maturity
1. **Atomic-First Design:** Established a rule that any function creating both a `Transaction` and an `Entry` must be wrapped in `transaction.atomic()`.
2. **Batch Processing Documentation:** Documented the transition from individual `.save()` calls to bundled atomic writes in `Architecture_Overview.md`.
3. **Observability:** Better Stack alerts now monitor for "Incomplete Transactions" (headers without entries) to ensure the atomic blocks are performing as expected.