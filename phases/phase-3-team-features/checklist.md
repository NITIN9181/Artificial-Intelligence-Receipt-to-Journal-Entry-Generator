
# Phase 3 — Build Checklist

## 💰 FREE TIER REQUIREMENTS

**Total Monthly Cost: $0**

All services used in this phase are completely free.

## Prerequisites
- [ ] Supabase Free tier active (monitor usage at supabase.com/dashboard)
- [ ] Ollama running locally or on free cloud instance
- [ ] No paid subscriptions required

## Database
- [ ] User roles migration applied
- [ ] PENDING_REVIEW status added to enum
- [ ] Export history table created (optional)
- [ ] RLS policies updated for role-based access
- [ ] Database size under 500MB (Supabase Free limit)
- [ ] Indexes added on role and status columns

## Backend
- [ ] Role-checking middleware functional on all endpoints
- [ ] Approval workflow: submit → PENDING_REVIEW → approve/reject
- [ ] Review comments stored and retrievable
- [ ] CSV export endpoint functional
- [ ] Excel export endpoint functional (using openpyxl or pandas)
- [ ] GnuCash SQLite export endpoint functional (optional)
- [ ] Batch export with date filtering working
- [ ] No external API dependencies

## Frontend
- [ ] Role-based navigation renders correctly per role
- [ ] Approval queue page lists PENDING_REVIEW receipts
- [ ] Approve/reject with comments functional
- [ ] Export modal with format selection (CSV/Excel/GnuCash)
- [ ] Date range picker for bulk exports
- [ ] Export preview functionality
- [ ] Download progress indicator
- [ ] Export history log in browser

## Integration
- [ ] Full approval workflow: Preparer uploads → submits → Reviewer approves → posts
- [ ] CSV export opens correctly in Excel, Google Sheets, LibreOffice
- [ ] Excel export includes proper formatting and headers
- [ ] GnuCash import works correctly (if implemented)
- [ ] Exported data includes all required fields (date, account, debit, credit, description)

## Monitoring (Free Tier Limits)
- [ ] Set up Supabase usage alerts (Dashboard → Settings → Billing → Usage Alerts)
- [ ] Monitor database size monthly
- [ ] Monitor bandwidth usage (5GB limit)
- [ ] Plan upgrade path if approaching limits

