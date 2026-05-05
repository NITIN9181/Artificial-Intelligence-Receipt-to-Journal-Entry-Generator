# Phase 1 — Build Checklist

Tick off in strict order. Do not start the next section until all items in the current section pass.

## Infrastructure
- [ ] Supabase project created, connection string saved
- [ ] Render Web Service created, env vars configured
- [ ] Vercel project linked to repo
- [ ] UptimeRobot configured to ping /api/v1/health every 14 minutes

## Database
- [x] Alembic migration 001_initial_schema runs clean
- [x] Alembic migration 002_seed_defaults runs clean
- [x] All 5 RLS policies verified in Supabase dashboard
- [x] Audit log trigger verified: INSERT/UPDATE/DELETE on receipts writes to audit_logs

## Backend
- [x] B1: Config + Auth middleware — JWT rejection tested
- [x] B2: ReceiptExtraction schema — all 5 validators at 100% coverage
- [x] B3: LLM client — NVIDIA NIM path tested with real receipt image
- [x] B3: LLM client — Ollama fallback path tested locally
- [x] B3: Exponential backoff tested (mock 429 responses)
- [x] B3: json-repair path tested with malformed LLM output
- [x] B4: All receipt endpoints return correct status codes
- [x] B4: State machine rejects invalid transitions (e.g., POSTED → EXTRACTING)
- [x] B5: Bookkeeping engine balanced for all 4 payment methods
- [x] B5: Bookkeeping engine quarantines unbalanced entries
- [x] B5: JE-YYYY-XXXXX numbering verified
- [x] B6: Journal entry list pagination + all filters work
- [x] B6: Reversal creates correct mirror entry
- [x] B7: No stack traces in production error responses
- [x] GET /api/v1/health returns 200 with db + llm_provider

## Frontend
### Design System Integration
- [x] D1: Load custom fonts (Manrope, Inter, Space Grotesk) in `layout.tsx`
- [x] D2: Map Stitch "Atmospheric Intelligence" color tokens to `globals.css` (@theme)
- [x] D3: Implement Glassmorphism layers (Z-Index 1, 2, 3) in global utility classes
- [x] D4: Rewrite `UploadPage` (`page.tsx`) to match Stitch HTML structure exactly

### Features
- [x] F1: Login + signup with Supabase magic link
- [x] F2: apiClient injects JWT on every request
- [x] F3: Upload zone drag-and-drop + mobile camera
- [x] F3: Client-side compression verified (> 5MB image → compressed)
- [x] F3: 20 receipts/day counter visible in dashboard
- [x] F4: Review page split-panel renders on desktop + mobile
- [x] F4: Confidence indicators render correct colors
- [x] F4: Real-time receipt math validation fires on amount edit
- [x] F4: "Approve & Post" disabled while validation errors active
- [x] F4: T-Account preview shows amber footer on imbalance
- [x] F4: Queue position polling works (5s interval)
- [x] F5: Journal entries list with pagination + filters
- [x] F6: Toasts fire for success, error, rate-limit events
- [x] F7: Settings page — add/rename COA entries

## End-to-End
- [ ] Playwright: full upload → extract → review → approve → POSTED flow passes
- [ ] Manual test: handwritten receipt triggers low-confidence indicators
- [ ] Manual test: NVIDIA NIM rate limit triggers queue indicator, not crash
