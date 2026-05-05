# Phase 1 — Core Loop: Single User (Weeks 1–3)

## Goal

Build the end-to-end receipt → journal entry flow for a single authenticated user. Every feature must run at **zero monthly cost** on free-tier services.

## Scope

Upload → Extract → Review → Post

## Tech Stack (enforce exactly)

| Layer | Technology | Deployment |
|---|---|---|
| Frontend | Next.js 15 (App Router) | Vercel Hobby (free) |
| Backend | FastAPI (Python 3.12) | Render Web Service (free) |
| LLM | NVIDIA NIM — `meta/llama-4-maverick-17b-128e-instruct` | Free (20 req/min) |
| Database | Supabase Postgres | Free (500 MB) |
| File Storage | Supabase Storage | Free (1 GB) |
| Auth | Supabase Auth | Free |
| Local Fallback | Ollama | User-provided hardware |

## Constraints Enforced

- Maximum 20 receipts/day hard limit enforced in the UI (counter displayed in dashboard).
- No bulk processing; each receipt must be submitted individually.
- No email ingestion; no third-party integrations.
- Local Ollama optional fallback documented and tested.

## Free Tier Budget

- **NVIDIA NIM:** ~600 requests/day capacity; target 20/day.
- **Supabase Postgres:** < 10 MB for Phase 1 volume.
- **Render:** 750 hrs/month = perpetual uptime with UptimeRobot.

## Deliverables

- [ ] Working upload, extraction, review, and post flow
- [ ] Default COA and vendor mappings seeded
- [ ] Supabase Auth working with email/password + magic link
- [ ] Vercel + Render + Supabase all on free tier, fully functional
- [ ] UptimeRobot configured to keep Render service warm

## Global Rules (enforce throughout)

1. **Never expose secrets** — `NVIDIA_NIM_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY` never appear in Next.js client bundles, API responses, or logs.
2. **Bookkeeping assertion is sacred** — `sum(debits) == sum(credits)` must be enforced with a hard Python assertion AND a Postgres `CHECK` constraint. Both must fail independently.
3. **Status state machine is strict** — Any code path that could transition a receipt to a status not in the PRD diagram is a bug. Reject it with a 409.
4. **No raw 429s to the client** — Rate limit responses from NVIDIA NIM must be caught by the backend, queued, and communicated to the frontend as a queue position, not a raw error.
5. **Free tier first** — Every architectural decision must respect free-tier limits.
6. **Test before moving on** — Each backend task requires passing unit tests before the next task begins.
7. **Immutability of posted entries** — Physical `DELETE` on `journal_entries` where `status = 'POSTED'` must be blocked.
8. **PII protection** — LLM prompt redacts card numbers; Supabase Storage uses signed URLs with 1-hour expiry.
9. **Rollback safety** — Every Alembic migration must include a working `downgrade()` function.
10. **Environment parity** — Docker Compose config must work identically to cloud deployment.

## Reference Sections (PRD)

| Topic | PRD Section |
|---|---|
| Full DB schema + SQL | §6 |
| Seed data SQL | §7 |
| Trigger + RLS SQL | §8 |
| All API request/response schemas | §9 |
| Next.js directory structure + env vars | §10 |
| Exact UI colors, fonts, layout specs | §11 |
| LLM system prompt (copy verbatim) | §13 |
| Ollama fallback + LLMClient Python class | §14 |
| Rate limit UI copy and behavior | §15 |
| Free tier limits per service | §5 |
| Risk table | §18 |
| KPI targets | §19 |
