# AI Receipt → Journal Entry Generator

> Transform receipt images into validated, double-entry bookkeeping journal entries using multimodal AI — built for small businesses and accountants who want automation without sacrificing accuracy.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Live demo:** [artificial-intelligence-receipt-to.vercel.app](https://artificial-intelligence-receipt-to.vercel.app)
**API docs:** [ai-receipt-journal.onrender.com/docs](https://ai-receipt-journal.onrender.com/docs)

---

## About the Project

Manually transcribing paper receipts into accounting software is slow, error-prone, and one of the least enjoyable parts of bookkeeping. This app uses a vision LLM to extract every field from a receipt image — vendor, date, line items, tax, tip, total, and payment method — then constructs a balanced double-entry journal entry and posts it to a permanent ledger.

What makes it different is that it treats AI output as untrusted by design. Every extraction passes through a multi-stage JSON recovery pipeline and a strict Pydantic validation layer before it reaches the bookkeeping engine, which asserts `sum(debits) == sum(credits)` before any write. If an entry can't balance, the receipt is quarantined and never touches the ledger. POSTED entries are immutable — enforced at the application layer, in the schema, and by a database trigger.

![Demo](./docs/assets/hero.png)
<!-- Replace with a recorded demo GIF showing upload → extract → review → post for the best effect -->

---

## Features

- **Multimodal receipt extraction** — uploads JPEG, PNG, HEIC, or PDF (up to 20 MB) and extracts structured data using NVIDIA NIM or local Ollama vision models.
- **Bulk upload with batch tracking** — processes up to 20 receipts at once with real-time per-receipt status polling.
- **Strict double-entry engine** — builds balanced debit/credit lines and quarantines any receipt that fails the balance assertion.
- **Human-in-the-loop review** — provides a side-by-side image and editable data panel with per-field confidence scores and live balance validation before posting.
- **Immutable ledger with reversals** — prevents deletion of posted entries; corrections are made via mirror reversal entries that preserve the original.
- **Role-based approval workflow** — supports Preparer, Reviewer, and Admin roles with submit/approve/reject transitions and review comments.
- **Multi-format export** — streams the ledger as CSV or PDF, and exports single or multiple entries as GnuCash XML, CSV, or SQLite.
- **GnuCash integration** — imports an existing chart of accounts from GnuCash XML and maps internal account codes to GnuCash account paths.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Next.js 16 (App Router) | React framework with server components and routing |
| Frontend | React 19 + TypeScript 5 | UI library and type-safe components |
| Frontend | Tailwind CSS v4 + Radix UI | Styling and accessible UI primitives |
| Frontend | TanStack Query v5 | Server-state management and caching |
| Frontend | React Hook Form + Zod | Form handling and schema validation |
| Frontend | react-dropzone, react-zoom-pan-pinch | Drag-and-drop upload and receipt image viewer |
| Backend | FastAPI + Python 3.12 | Async REST API |
| Backend | SQLAlchemy 2 (async) | ORM with asyncpg / aiosqlite drivers |
| Backend | Pydantic v2 + pydantic-settings | Validation and configuration management |
| Backend | httpx + json-repair | LLM HTTP calls and JSON output recovery |
| Backend | Pillow | Image preprocessing and compression |
| Backend | ReportLab + pypdf | PDF ledger generation |
| Backend | APScheduler | Nightly usage monitoring |
| AI — cloud | NVIDIA NIM (`meta/llama-4-maverick-17b-128e-instruct`) | Vision LLM inference |
| AI — local | Ollama (`qwen2.5-vl:7b`) | Fully local inference, no data leaves the machine |
| Database | PostgreSQL (Supabase) | Production data store |
| Database | SQLite (aiosqlite) | Zero-setup local development |
| Storage | Supabase Storage | Receipt image storage with signed URLs (local FS fallback) |
| Migrations | Alembic | Versioned schema migrations |
| DevOps | Render + Vercel | Backend and frontend hosting |
| DevOps | Docker | Containerized builds for both services |
| Testing | pytest + pytest-asyncio | Backend unit and integration tests |
| Testing | Playwright | Frontend end-to-end tests |

---

## Getting Started

### Prerequisites

- **Python** 3.12+
- **Node.js** 20+
- A **Supabase** project, **or** use SQLite for fully local development
- An **NVIDIA NIM API key** from [build.nvidia.com](https://build.nvidia.com) (free tier available), **or** **Ollama** installed locally

### Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/ai-receipt-journal.git
cd ai-receipt-journal
```

**Backend:**

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # then edit .env with your values

uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

**Frontend:**

```bash
cd frontend
npm install
# create frontend/.env.local with the variables below
npm run dev
```

The app is available at `http://localhost:3000`.

### Local-only mode (no Supabase required)

Set these in `backend/.env` to run entirely locally — receipt images are stored in `backend/uploads/`:

```env
DATABASE_URL=sqlite+aiosqlite:///./receipts.db
SUPABASE_URL=http://localhost
SUPABASE_ANON_KEY=dummy
SUPABASE_SERVICE_ROLE_KEY=dummy
SUPABASE_JWT_SECRET=dummy
```

### Environment Variables

**Backend (`backend/.env`):**

| Variable | Description | Example | Required |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL or SQLite connection string | `postgresql+asyncpg://user:pass@host:5432/db` | Yes |
| `SUPABASE_URL` | Supabase project URL | `https://xyz.supabase.co` | Yes |
| `SUPABASE_ANON_KEY` | Supabase anon/public key | `eyJhbGc...` | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key for Storage (never expose in frontend) | `eyJhbGc...` | Yes |
| `SUPABASE_JWT_SECRET` | JWT secret from Supabase Dashboard → Settings → API | `super-secret-jwt` | Yes |
| `NVIDIA_NIM_API_KEY` | NVIDIA NIM API key (required unless using Ollama) | `nvapi-...` | Conditional |
| `LLM_MODEL` | Vision model name | `meta/llama-4-maverick-17b-128e-instruct` | Yes |
| `OLLAMA_HOST` | Set to use local Ollama instead of NIM | `http://localhost:11434` | No |
| `OLLAMA_MODEL` | Ollama model name | `qwen2.5-vl:7b` | No |
| `MAX_UPLOAD_SIZE_MB` | Maximum file size in MB | `20` | No (default `20`) |
| `MAX_RECEIPTS_PER_DAY` | Daily upload limit per user | `20` | No (default `20`) |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000,https://app.vercel.app` | No |
| `BACKEND_URL` | Public backend URL, used for local image URLs | `http://localhost:8000` | No |

**Frontend (`frontend/.env.local`):**

| Variable | Description | Example | Required |
|---|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Same as backend `SUPABASE_URL` | `https://xyz.supabase.co` | Yes |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Same as backend `SUPABASE_ANON_KEY` | `eyJhbGc...` | Yes |
| `NEXT_PUBLIC_API_URL` | Backend base URL | `http://localhost:8000` | Yes |

### Common Commands

```bash
# Backend — run dev server
uvicorn app.main:app --reload --port 8000

# Backend — run database migrations
alembic upgrade head

# Backend — run tests
pytest
pytest tests/test_bookkeeping.py    # a single test file
pytest -v --tb=short                # verbose output

# Frontend — dev server
npm run dev

# Frontend — production build
npm run build

# Frontend — lint
npm run lint

# Frontend — end-to-end tests
npx playwright test
```

---

## Project Structure

```
.
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py           # App entry: CORS, lifespan, routers, scheduler
│   │   ├── config.py         # pydantic-settings — all env vars
│   │   ├── database.py       # Async engine, session factory, get_db dependency
│   │   ├── auth.py           # Auth dependencies and role factories
│   │   ├── llm_client.py     # Unified NVIDIA NIM + Ollama client
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── routers/          # API endpoints (one file per resource)
│   │   └── services/         # Business logic (bookkeeping, extraction, exports)
│   ├── alembic/              # Database migrations (13 versions)
│   ├── tests/                # Pytest suite
│   └── requirements.txt
├── frontend/                 # Next.js frontend
│   ├── app/                  # App Router pages — (auth) and (dashboard) groups
│   ├── components/           # UI components (ui/, approval/, navigation/)
│   ├── lib/                  # API client, auth context, utilities
│   ├── types/                # Shared TypeScript types
│   ├── utils/                # Supabase client helpers
│   ├── middleware.ts         # Supabase session refresh
│   └── package.json
├── docs/                     # Setup guides and assets
├── scripts/                  # Deployment verification scripts
├── testing/                  # Manual and performance test assets
├── qa_test_data/             # Sample receipt images for QA
├── render.yaml               # Render deployment config (backend)
├── docker-compose.yml        # Local multi-service orchestration
└── LICENSE
```

---

## Architecture Overview

The system is a layered async web application split into a Next.js frontend and a FastAPI backend, backed by PostgreSQL (or SQLite locally) and an external vision LLM.

**Data flow — from upload to ledger:**

1. The user uploads a receipt via the frontend; `routers/receipts.py` validates the MIME type and size, stores the image through `services/storage.py`, and creates a `Receipt` row with status `UPLOADED`.
2. Triggering extraction sets the status to `EXTRACTING` and hands off to a FastAPI `BackgroundTask` that creates its own database session.
3. `services/extraction.py` calls `llm_client.py`, which routes to NVIDIA NIM or Ollama, then runs the raw output through a five-stage JSON recovery pipeline.
4. The parsed data is validated by the `ReceiptExtraction` Pydantic schema (`schemas/receipt.py`) and the status moves to `EXTRACTED`, `EXTRACTION_FAILED`, or `VALIDATION_FAILED`.
5. After human review and correction, `services/bookkeeping.py` builds balanced debit/credit lines, asserts the balance, generates a `JE-YYYY-XXXXX` entry number, and posts the entry — moving the receipt to `POSTED`.

**Notable patterns:**

- **Layered architecture** — routers handle HTTP, services hold business logic, models handle persistence. Services have no FastAPI dependencies and are independently testable.
- **REST API** — versioned under `/api/v1`, with a consistent typed `apiClient` wrapper on the frontend.
- **State machine** — receipt status transitions are declared in a single `VALID_TRANSITIONS` map and validated before every change.
- **Dependency injection** — database sessions and auth are injected via FastAPI's `Depends`.
- **Strategy pattern** — both storage (Supabase vs local FS) and LLM provider (NIM vs Ollama) are swappable behind a single interface.

---

## API Reference

All endpoints are versioned under `/api/v1`. Interactive documentation is available at `/docs`.

### Receipts — `/api/v1/receipts`

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/upload` | Upload a single receipt image or PDF | Yes |
| `POST` | `/bulk-upload` | Upload up to 20 receipts at once | Yes |
| `POST` | `/bulk-extract` | Trigger sequential extraction for a batch | Yes |
| `GET` | `` | List receipts for the current user | Yes |
| `GET` | `/{id}` | Get a single receipt with extracted data | Yes |
| `POST` | `/{id}/extract` | Trigger async LLM extraction | Yes |
| `PUT` | `/{id}/correct` | Submit human corrections | Yes |
| `POST` | `/{id}/journalize` | Create a journal entry and post to ledger | Yes |
| `POST` | `/{id}/submit` | Submit receipt for reviewer approval | Preparer |
| `POST` | `/{id}/approve` | Approve a pending receipt | Reviewer |
| `POST` | `/{id}/reject` | Reject a receipt with a comment | Reviewer |
| `GET` | `/pending-review` | List receipts awaiting review | Reviewer |
| `GET` | `/{id}/comments` | Get review comments for a receipt | Yes |
| `GET` | `/batch/{batch_id}` | Get aggregated batch status | Yes |

### Journal Entries — `/api/v1/journal-entries`

| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `` | Paginated, filterable ledger | Yes |
| `GET` | `/{id}` | Full entry with lines and receipt image | Yes |
| `DELETE` | `/{id}/reverse` | Create a reversal entry (original preserved) | Yes |
| `GET` | `/export/csv` | Stream the ledger as CSV | Yes |
| `GET` | `/export/pdf` | Stream the ledger as PDF | Yes |

### GnuCash — `/api/v1/gnucash`

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/mappings` | Create an account mapping | Preparer |
| `GET` | `/mappings` | List account mappings | Preparer |
| `PUT` | `/mappings/{id}` | Update an account mapping | Preparer |
| `DELETE` | `/mappings/{id}` | Delete an account mapping | Preparer |
| `POST` | `/journal-entries/{id}/export` | Export a single entry (xml/csv/sqlite) | Preparer |
| `POST` | `/journal-entries/export-multiple` | Export multiple entries | Preparer |
| `POST` | `/import-coa` | Import chart of accounts from GnuCash XML | Admin |

### Admin — `/api/v1/admin`

| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `/usage` | Database and request usage stats | Admin |
| `GET` | `/usage/flag` | Usage banner data for the frontend | Admin |
| `POST` | `/usage/snapshot` | Manually trigger a usage snapshot | Admin |
| `GET` | `/usage/history` | Historical usage snapshots | Admin |
| `GET` | `/stats` | System-wide statistics | Admin |
| `GET` | `/users` | List all users | Admin |
| `PUT` | `/users/{id}/role` | Update a user's role | Admin |

### Health & Auth — `/api/v1`

| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `/health` | Health check (DB + LLM status) | No |
| `GET` | `/auth/me` | Current user profile | Yes |

---

## Roadmap

- [x] Multimodal receipt extraction with NVIDIA NIM and Ollama
- [x] Double-entry bookkeeping engine with balance assertion and quarantine
- [x] Human review and correction workflow with confidence scores
- [x] Role-based approval workflow (Preparer / Reviewer / Admin)
- [x] CSV, PDF, and GnuCash export
- [ ] Re-enable Supabase JWT authentication (infrastructure wired, currently bypassed)
- [ ] Replace in-process background tasks with a Celery + Redis job queue
- [ ] Receipt duplicate detection before posting
- [ ] Full-text search and amount-range filtering across receipts
- [ ] CI/CD pipeline with automated linting, testing, and deployment

---

## Contributing

Contributions are welcome. The standard flow:

1. **Fork** the repository.
2. **Create a branch**: `git checkout -b feature/your-feature-name`.
3. **Make your changes** and add tests where appropriate.
4. **Run the checks** before submitting:
   ```bash
   # Backend
   cd backend && pytest

   # Frontend
   cd frontend && npm run lint && npx playwright test
   ```
5. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/).
6. **Push** to your fork and **open a Pull Request**.

Backend code uses `black` for formatting and `ruff` for linting. Frontend uses `eslint` with TypeScript strict mode and functional components. See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
