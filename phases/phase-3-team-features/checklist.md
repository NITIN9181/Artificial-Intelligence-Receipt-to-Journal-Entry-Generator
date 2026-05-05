# Phase 3 — Build Checklist

## Prerequisites
- [ ] Supabase upgraded to Pro ($25/mo)
- [ ] NVIDIA NIM paid tier active OR Ollama cluster deployed
- [ ] QuickBooks Online developer account created

## Database
- [ ] User roles migration applied
- [ ] PENDING_REVIEW status added to enum
- [ ] QuickBooks tokens table created
- [ ] RLS policies updated for role-based access

## Backend
- [ ] Role-checking middleware functional on all endpoints
- [ ] Approval workflow: submit → PENDING_REVIEW → approve/reject
- [ ] Review comments stored and retrievable
- [ ] QuickBooks OAuth 2.0 flow: authorize → callback → store tokens
- [ ] QuickBooks COA sync (two-way)
- [ ] Push to QuickBooks endpoint functional
- [ ] Token refresh and error recovery working

## Frontend
- [ ] Role-based navigation renders correctly per role
- [ ] Approval queue page lists PENDING_REVIEW receipts
- [ ] Approve/reject with comments functional
- [ ] QuickBooks OAuth connect flow in Settings
- [ ] Connection status indicator accurate
- [ ] "Push to QuickBooks" button on posted entries
- [ ] Sync errors displayed clearly

## Integration
- [ ] Full approval workflow: Preparer uploads → submits → Reviewer approves → posts
- [ ] QuickBooks push creates matching entry in QBO
- [ ] COA sync reflects changes bidirectionally
