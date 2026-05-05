# Phase 2 — Scale Preparation (Weeks 4–6)

## Prerequisites

**Do NOT start Phase 2 until every Phase 1 checklist item is ticked and monitored in production.**

## Goal

Add bulk processing, exports, and basic analytics. All features must still respect the 5-concurrent semaphore. No parallelism.

## Constraints Enforced

- Bulk upload processes receipts **sequentially**, never in parallel, to respect `asyncio.Semaphore(5)`.
- Analytics aggregations computed client-side from cached TanStack Query data, not additional DB queries.
- Export generates files on-demand using streaming response; no background jobs.

## Deliverables

- [ ] Multi-file upload queue with per-receipt progress
- [ ] CSV export (raw data) and PDF export (formatted ledger report)
- [ ] Dashboard KPI cards: receipts this month, total spend by category, avg processing time
- [ ] Admin usage monitoring with 80% threshold banner
- [ ] Evaluate paid tier migration based on actual usage metrics
