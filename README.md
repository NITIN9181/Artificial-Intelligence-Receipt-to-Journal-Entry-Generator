# AI Receipt → Journal Entry Generator

> Transform receipt images into validated, double-entry bookkeeping journal entries using multimodal AI.

Upload a photo of any receipt — the system extracts every line item, validates the math, constructs balanced debit/credit entries, and posts them to a permanent ledger. Built for small businesses and accountants who want automation without sacrificing accuracy.

**Live demo:** [artificial-intelligence-receipt-to.vercel.app](https://artificial-intelligence-receipt-to.vercel.app)  
**API docs:** [ai-receipt-journal.onrender.com/docs](https://ai-receipt-journal.onrender.com/docs)

---

## How it works

```
Upload receipt image
        │
        ▼
Vision LLM extracts structured data
(vendor, date, line items, tax, tip, total, payment method)
        │
        ▼
Side-by-side review panel — edit anything before posting
        │
        ▼
Double-entry engine builds balanced debit/credit lines
(asserts sum(debits) == sum(credits) before any write)
        │
        ▼
Entry posted to permanent ledger → export as CSV / PDF / GnuCash XML
```

---

## Features

**Receipt processing**
- Drag-and-drop upload — JPEG, PNG, HEIC, PDF up to 20 MB
- Bulk upload up to 20 receipts at once with batch tracking
- Async LLM extraction with real-time status polling
- Per-field confidence scores so you know what to double-check
- Human correction panel before journalizing

**Accounting engine**
- Strict double-entry bookkeeping — every entry is balanced or rejected
- Unbalanced entries quarantine the receipt and never touch the ledger
- POSTED entries are immutable — only reversals allowed
- DB-level trigger prevents deletion of posted entries
- Automatic account assignment based on payment method and vendor category

**Approval workflow**
- Three roles: Preparer → Reviewer → Admin
- Preparers submit receipts for review; reviewers approve or reject with comments
- Full audit log of every status change

**Exports**
- Ledger export as CSV or PDF
- GnuCash XML, CSV, or SQLite export (single entry or bulk)
- Import your existing GnuCash chart of accounts to auto-map accounts

**AI providers — your choice**
- Cloud: NVIDIA NIM (free tier available at [build.nvidia.com](https://build.nvidia.com))
- Local: Ollama — no data leaves your machine

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4 |
| Backend | FastAPI, Python 3.12, SQLAlchemy (async), Pydantic v2 |
| Database | PostgreSQL (Supabase) or SQLite for local dev |
| AI — cloud | NVIDIA NIM (`meta/llama-4-maverick-17b-128e-instruct`) |
| AI — local | Ollama (`qwen2.5-vl:7b`) |
| Storage | Supabase Storage (local filesystem fallback) |
| Deployment | Render (backend) + Vercel (frontend) |
| Migrations | Alembic |
| Scheduling | APScheduler (nightly usage monitoring) |

---

## Project structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, startup, scheduler
│   │   ├── auth.py              # Auth (anonymous bypass for local dev)
│   │   ├── config.py            # Pydantic settings — all env vars
│   │   ├── database.py          # Async SQLAlchemy engine
│   │   ├── llm_client.py        # Unified NVIDIA NIM + Ollama client
│   │   ├── models/              # ORM models (receipt, journal, user, usage, gnucash)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # API endpoints
│   │   │   ├── receipts.py      # Upload, extract, correct, journalize, approve/reject
│   │   │   ├── journal_entries.py  # Ledger list, get, reverse, export
│   │   │   ├── gnucash.py       # Account mappings, GnuCash export/import
│   │   │   ├── admin.py         # Usage stats, user management
│   │   │   └── health.py        # Health check, /auth/me
│   │   └── services/
│   │       ├── extraction.py    # LLM orchestration + state machine
│   │       ├── bookkeeping.py   # Double-entry engine
│   │       ├── storage.py       # Supabase Storage / local fallback
│   │       ├── bulk_processor.py
│   │       ├── export_csv.py
│   │       ├── export_pdf.py
│   │       ├── gnucash_exporter.py
│   │       └── usage_monitor.py
│   ├── alembic/                 # 13 database migrations
│   ├── tests/                   # Pytest suite
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── (auth)/login/        # Login page
│   │   └── (dashboard)/
│   │       ├── dashboard/       # KPI overview
│   │       ├── upload/          # Drag-and-drop uploader
│   │       ├── review/[id]/     # Receipt review + edit
│   │       ├── journal-entries/ # Ledger table
│   │       ├── approval-queue/  # Reviewer workflow
│   │       ├── submissions/     # Preparer's receipts
│   │       ├── admin/users/     # User management
│   │       └── settings/
│   ├── components/              # UI components (Radix UI + Tailwind)
│   ├── lib/                     # API client, auth context
│   └── types/                   # TypeScript types
├── render.yaml                  # Render deployment config
└── README.md
```

---

## Running locally

### Prerequisites

- Python 3.12+
- Node.js 20+
- A Supabase project **or** use SQLite (see [Local-only mode](#local-only-mode-no-supabase-needed) below)
- An NVIDIA NIM API key from [build.nvidia.com](https://build.nvidia.com) (free tier available), **or** Ollama installed locally

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values — see Environment variables below

uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
# Create frontend/.env.local (see Environment variables below)

npm run dev
```

App available at `http://localhost:3000`.

### Local-only mode (no Supabase needed)

Set these in `backend/.env` to run entirely locally with no external services:

```env
DATABASE_URL=sqlite+aiosqlite:///./receipts.db
SUPABASE_URL=http://localhost
SUPABASE_ANON_KEY=dummy
SUPABASE_SERVICE_ROLE_KEY=dummy
SUPABASE_JWT_SECRET=dummy
```

Receipt images will be stored in `backend/uploads/` and served at `http://localhost:8000/uploads/`.

---

## Environment variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL (`postgresql+asyncpg://...`) or SQLite (`sqlite+aiosqlite:///./receipts.db`) |
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Supabase service role key — used for Storage. **Never expose in frontend.** |
| `SUPABASE_JWT_SECRET` | ✅ | JWT secret from Supabase Dashboard → Settings → API |
| `NVIDIA_NIM_API_KEY` | ✅* | NVIDIA NIM API key. Required unless using Ollama. **Never expose in frontend.** |
| `LLM_MODEL` | ✅ | Model name, e.g. `meta/llama-4-maverick-17b-128e-instruct` |
| `OLLAMA_HOST` | ❌ | Set to `http://localhost:11434` to use local Ollama instead of NIM |
| `OLLAMA_MODEL` | ❌ | Ollama model name, e.g. `qwen2.5-vl:7b` |
| `BACKEND_URL` | ❌ | Public URL of the backend, used for image URLs |
| `CORS_ORIGINS` | ❌ | Comma-separated allowed origins (e.g. `http://localhost:3000,https://yourapp.vercel.app`) |
| `MAX_UPLOAD_SIZE_MB` | ❌ | Max file size in MB (default: `20`) |
| `MAX_RECEIPTS_PER_DAY` | ❌ | Daily upload limit per user (default: `20`) |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | ✅ | Same as backend `SUPABASE_URL` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ | Same as backend `SUPABASE_ANON_KEY` |
| `NEXT_PUBLIC_API_URL` | ✅ | Backend URL, e.g. `http://localhost:8000` |

---

## API reference

### Receipts — `/api/v1/receipts`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload a single receipt image or PDF |
| `POST` | `/bulk-upload` | Upload up to 20 receipts at once |
| `POST` | `/bulk-extract` | Trigger extraction for a batch |
| `GET` | `` | List receipts (filterable by status) |
| `GET` | `/{id}` | Get a single receipt with extracted data |
| `POST` | `/{id}/extract` | Trigger async LLM extraction |
| `PUT` | `/{id}/correct` | Submit human corrections |
| `POST` | `/{id}/journalize` | Create journal entry and post to ledger |
| `POST` | `/{id}/submit` | Submit for reviewer approval |
| `POST` | `/{id}/approve` | Approve receipt (reviewer role) |
| `POST` | `/{id}/reject` | Reject receipt with comment |
| `GET` | `/pending-review` | List receipts awaiting review |
| `GET` | `/{id}/comments` | Get review comments |
| `GET` | `/batch/{batch_id}` | Get batch upload status |

### Journal Entries — `/api/v1/journal-entries`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `` | Paginated, filterable ledger |
| `GET` | `/{id}` | Full entry with debit/credit lines + receipt image |
| `DELETE` | `/{id}/reverse` | Create reversal entry (original is preserved) |
| `GET` | `/export/csv` | Stream ledger as CSV |
| `GET` | `/export/pdf` | Stream ledger as PDF |

### GnuCash — `/api/v1/gnucash`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/mappings` | Create account mapping |
| `GET` | `/mappings` | List account mappings |
| `PUT` | `/mappings/{id}` | Update account mapping |
| `DELETE` | `/mappings/{id}` | Delete account mapping |
| `POST` | `/journal-entries/{id}/export` | Export single entry (xml / csv / sqlite) |
| `POST` | `/journal-entries/export-multiple` | Export multiple entries |
| `POST` | `/import-coa` | Import chart of accounts from GnuCash XML (admin) |

### Admin — `/api/v1/admin`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/usage` | Database and request usage stats |
| `GET` | `/usage/flag` | Usage banner data for frontend |
| `POST` | `/usage/snapshot` | Manually trigger a usage snapshot |
| `GET` | `/usage/history` | Historical usage snapshots |
| `GET` | `/stats` | System-wide statistics |
| `GET` | `/users` | List all users |
| `PUT` | `/users/{id}/role` | Update user role |

### Other

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check (DB + LLM status) |
| `GET` | `/api/v1/auth/me` | Current user profile |

---

## How the double-entry engine works

Every receipt produces exactly two types of journal entry lines:

**Debits** (what you spent money on):
- Main expense line → account from vendor lookup (falls back to `5999 Miscellaneous Expense`)
- Tax line → `2100 Sales Tax Payable` (if tax > 0)
- Tip line → `5300 Meals & Entertainment` (if tip > 0)

**Credit** (how you paid):
- Cash → `1010 Cash`
- Card → `2010 Credit Card Liability`
- Check → `1020 Checking Account`
- Unknown → `2000 Accounts Payable`

The engine asserts `sum(debits) == sum(credits)` before writing anything. If this assertion fails, the receipt is quarantined and never enters the ledger.

---

## Receipt state machine

```
UPLOADED → EXTRACTING → EXTRACTED → REVIEWED → POSTED (terminal)
                      ↘                       ↘ QUARANTINED (terminal, balance failure)
                        EXTRACTION_FAILED      ↘ PENDING_REVIEW → REVIEWED
                        (retryable)                             ↘ REJECTED (terminal)
                      ↘
                        VALIDATION_FAILED → REVIEWED
```

---

## Using a local LLM (Ollama)

For full privacy — no data leaves your machine:

```bash
# Install Ollama from https://ollama.ai
ollama pull qwen2.5-vl:7b
```

Then in `backend/.env`:

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-vl:7b
# Leave NVIDIA_NIM_API_KEY blank or remove it
```

The backend automatically switches to Ollama when `OLLAMA_HOST` is set.

---

## Deployment

### Backend → Render

1. Push to GitHub
2. Create a new **Web Service** on [render.com](https://render.com) and connect your repo
3. Render auto-detects `render.yaml` and configures the service
4. Add environment variables in the Render dashboard
5. Use the **Session pooler** connection string from Supabase (port 5432, not 6543)

### Frontend → Vercel

1. Import your repo on [vercel.com](https://vercel.com)
2. Set root directory to `frontend`
3. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_URL` → your Render backend URL

### Supabase setup

1. Create a project at [supabase.com](https://supabase.com)
2. Run migrations:
   ```bash
   cd backend && alembic upgrade head
   ```
3. Create a storage bucket named `receipts` (set to private)
4. Add a storage policy to allow signed URL access:
   ```sql
   CREATE POLICY "Allow signed URL access"
   ON storage.objects FOR SELECT TO public
   USING (bucket_id = 'receipts');
   ```
5. If you get FK errors on the `users` table, remove the Supabase auth trigger:
   ```sql
   ALTER TABLE users DROP CONSTRAINT IF EXISTS users_id_fkey;
   ```

---

## Running tests

```bash
# Backend
cd backend
pytest                              # all tests
pytest tests/test_bookkeeping.py    # bookkeeping engine only
pytest -v --tb=short                # verbose output

# Frontend (end-to-end)
cd frontend
npx playwright test
```

---

## License

MIT
