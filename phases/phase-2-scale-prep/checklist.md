# Phase 2 — Build Checklist

## Backend
- [ ] Bulk upload endpoint accepts up to 20 files
- [ ] Bulk upload processes sequentially (never parallel)
- [ ] CSV export endpoint returns streaming response
- [ ] PDF export endpoint returns formatted ledger
- [ ] Admin usage endpoint returns Postgres MB + daily requests
- [ ] Nightly usage check logs warning at 80% threshold
- [ ] Admin flag check on admin-only endpoints

## Frontend
- [ ] Multi-file upload queue shows per-receipt progress
- [ ] CSV export button triggers download from journal entries page
- [ ] PDF export button triggers formatted report download
- [ ] Dashboard KPI cards render: receipts/month, spend by category, avg processing time
- [ ] Admin banner appears when 80% threshold hit
- [ ] Banner links to export dialog pre-filtered to entries > 90 days old

## Integration
- [ ] Bulk upload → sequential extraction → all receipts reach EXTRACTED
- [ ] Export CSV matches journal entries data exactly
- [ ] PDF export is readable and correctly formatted
- [ ] Admin banner only visible to admin users
