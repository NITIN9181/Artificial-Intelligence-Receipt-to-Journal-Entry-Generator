# Phase 2 — Build Checklist

## Backend
- [x] Bulk upload endpoint accepts up to 20 files
- [x] Bulk upload processes sequentially (never parallel)
- [x] CSV export endpoint returns streaming response
- [x] PDF export endpoint returns formatted ledger
- [x] Admin usage endpoint returns Postgres MB + daily requests
- [x] Nightly usage check logs warning at 80% threshold
- [x] Admin flag check on admin-only endpoints

## Frontend
- [x] Multi-file upload queue shows per-receipt progress
- [x] CSV export button triggers download from journal entries page
- [x] PDF export button triggers formatted report download
- [x] Dashboard KPI cards render: receipts/month, spend by category, avg processing time
- [x] Admin banner appears when 80% threshold hit
- [x] Banner links to export dialog pre-filtered to entries > 90 days old

## Integration
- [ ] Bulk upload → sequential extraction → all receipts reach EXTRACTED
- [ ] Export CSV matches journal entries data exactly
- [ ] PDF export is readable and correctly formatted
- [ ] Admin banner only visible to admin users

## Database Migrations
- [x] 004_add_admin_flag.py — `is_admin` on users table
- [x] 005_add_usage_snapshots.py — `usage_snapshots` table
- [x] 006_add_batch_id.py — `batch_id` on receipts table
- [ ] Alembic upgrade head run against live database (requires .env)
