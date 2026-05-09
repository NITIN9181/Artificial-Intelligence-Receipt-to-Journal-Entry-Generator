# 🧾 AI Receipt to Journal Entry Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-316192.svg)](https://www.postgresql.org/)

**Transform receipt images into validated, double-entry bookkeeping journal entries using multimodal LLMs — at zero monthly cost.**

This is a production-grade accounting automation tool that takes unstructured receipt images (JPEG, PNG, HEIC, PDF) and converts them into mathematically balanced, double-entry general ledger records using AI (Meta Llama 4 Maverick via NVIDIA NIM API). Every entry undergoes Pydantic schema validation and hard assertion checks (debits must equal credits) before human review and final posting.

---

## 📋 Table of Contents

- [Who Is This For?](#-who-is-this-for)
- [Key Features](#-key-features)
- [Demo & Quick Start](#-demo--quick-start)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Database Setup](#database-setup)
- [Configuration](#-configuration)
- [Running Locally](#-running-locally)
- [API Quick Reference](#-api-quick-reference)
- [Development](#-development)
- [Deployment](#-deployment)
  - [Vercel + Render + Supabase](#vercel--render--supabase)
- [Self-Hosting (Zero External APIs)](#-self-hosting-zero-external-apis)
- [Free Tier Constraints & Mitigation](#-free-tier-constraints--mitigation)
- [Testing](#-testing)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 🎯 Who Is This For?

- **Freelancers and solo business owners** who need simple, automated bookkeeping
- **Bookkeepers at small accounting firms** looking to reduce manual data entry
- **Startup finance teams** wanting to streamline expense tracking
- **Developers** interested in accounting automation or multimodal LLM applications

---

## ✨ Key Features

### 📤 Smart Receipt Ingestion
- **Drag-and-drop, file picker, or live mobile camera capture**
- Client-side image compression (5MB limit, WebP conversion)
- Thumbnail preview immediately after upload
- Supports JPEG, PNG, HEIC, and PDF formats

### 🤖 AI-Powered Data Extraction
- **Multimodal LLM extraction** via NVIDIA NIM (Llama 4 Maverick 17B)
- Extracts: vendor, date, currency, subtotal, tax, tip, total, payment method, line items
- **Per-field confidence scoring** with color-coded review indicators
- Automatic JSON repair and markdown stripping from LLM output
- Local Ollama fallback for offline/self-hosted operation

### 👤 Human-in-the-Loop Review
- **Split-panel UI**: receipt image (with pan/zoom) alongside editable extraction form
- Color-coded confidence indicators (yellow/orange/red for low confidence)
- Real-time math validation as user edits fields
- "Regenerate from Image" button for fresh LLM extraction

### 📊 Double-Entry Bookkeeping Engine
- **Automatic journal entry generation** with debit/credit balancing
- Default Chart of Accounts (18 accounts: Assets, Liabilities, Equity, Revenue, Expenses)
- Smart vendor-to-category mapping (20+ default mappings)
- Payment method routing: Cash → 1010, Card → 2010, Check → 1020, Unknown → 2000
- **Hard assertion**: unbalanced entries are quarantined, never posted

### 📖 Journal Entry Management
- **Immutable ledger**: posted entries cannot be deleted, only reversed
- Reversals create mirror entries with full audit trail
- Filterable, paginated list view with CSV and PDF export
- Entry numbering format: `JE-YYYY-XXXXX`

### 🔒 Audit & Compliance
- **Full audit trail** via database triggers on all mutations
- Row-Level Security (RLS) isolating user data
- 7-year data retention for tax compliance
- PII protection: card numbers redacted by LLM prompt, signed image URLs with 1-hour expiry

### 💰 Free Tier Optimized
- **Designed for zero monthly cost** on free tiers
- Rate limiting with exponential backoff and queue management
- Local Ollama fallback for offline/self-hosted operation
- Automatic resource cleanup and compression

---

## 🚀 Demo & Quick Start

**Get your first journal entry in 5 minutes:**

1. **Sign up** for free accounts:
   - [Supabase](https://supabase.com) (Database + Auth + Storage)
   - [NVIDIA NIM](https://build.nvidia.com) (LLM API)
   - [Render](https://render.com) (Backend hosting)
   - [Vercel](https://vercel.com) (Frontend hosting)

2. **Clone and configure**:
   ```bash
   git clone https://github.com/yourusername/ai-receipt-journal.git
   cd ai-receipt-journal
   # Follow installation steps below
   ```

3. **Upload a receipt** → Review extracted data → Generate journal entry → Post to ledger ✅

> **Note**: For a completely self-hosted setup with zero external dependencies, see [Self-Hosting](#-self-hosting-zero-external-apis).

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│  Next.js 15 App Router + React Server Components + TanStack    │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTPS (JWT Bearer Auth)
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│  Python 3.12 + FastAPI + SQLAlchemy + asyncpg                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Receipt API  │  │ Journal API  │  │  Admin API   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                 │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ NVIDIA NIM   │   │  PostgreSQL  │   │   Supabase   │
│ Llama 4      │   │  Database    │   │   Storage    │
│ Maverick 17B │   │  (Supabase)  │   │  (Images)    │
└──────────────┘   └──────────────┘   └──────────────┘
        │
        │ (Fallback)
        ▼
┌──────────────┐
│    Ollama    │
│ Qwen2.5-VL   │
│ (Local)      │
└──────────────┘
```

### Receipt Status State Machine

```
UPLOADED → EXTRACTING → EXTRACTED → REVIEWED → POSTED
   ↓            ↓            ↓
EXTRACTION_FAILED  VALIDATION_FAILED  REJECTED
```

---

## 🛠️ Technology Stack

| Layer | Technology | Hosting |
|-------|-----------|---------|
| **Frontend** | Next.js 15 (App Router, React Server Components) | Vercel Hobby (free) |
| **Backend** | FastAPI (Python 3.12) | Render Web Service (free) |
| **LLM Inference** | NVIDIA NIM API (Llama 4 Maverick 17B) | Free tier (20 req/min) |
| **Local Fallback** | Ollama (Qwen2.5-VL 7B, Llama 3.2 Vision) | Self-hosted |
| **Database** | PostgreSQL 16 | Supabase Free (500 MB) |
| **File Storage** | Supabase Storage | Free tier (1 GB) |
| **Authentication** | Supabase Auth | Free tier |
| **State Management** | TanStack Query v5, Zustand | — |
| **Forms** | React Hook Form + Zod | — |

### Database Schema Overview

- **`users`** — Extended Supabase Auth profiles with role management
- **`receipts`** — Receipt images, extraction data, confidence scores, raw LLM output, status state machine
- **`chart_of_accounts`** — Default + user-customizable COA
- **`vendor_category_mappings`** — Smart vendor-to-account mapping
- **`journal_entries`** — Immutable ledger entries with balancing constraints
- **`journal_entry_lines`** — Individual debit/credit lines
- **`audit_logs`** — Full mutation history via triggers

---

## 📦 Installation

### Prerequisites

- **Node.js 20+** and npm/yarn/pnpm
- **Python 3.12+** and pip
- **Docker** (optional, for local Postgres/Ollama)
- **Ollama** (optional, for local LLM fallback)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment** (see [Configuration](#-configuration)):
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Configure environment**:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your Supabase keys
   ```

### Database Setup

1. **Create Supabase project** at [supabase.com](https://supabase.com)

2. **Get connection details**:
   - Project URL: `https://xxxxx.supabase.co`
   - Anon/Public Key: `eyJhbGc...`
   - Service Role Key: `eyJhbGc...` (keep secret!)
   - Database URL: `postgresql://postgres:[password]@db.xxxxx.supabase.co:5432/postgres`

3. **Run migrations** (from backend directory):
   ```bash
   alembic upgrade head
   ```

4. **Seed default data**:
   - Default Chart of Accounts (18 accounts)
   - Vendor category mappings (20+ mappings)
   - These are automatically seeded via migration `002_seed_defaults.py`

> ⚠️ **Security Warning**: Enable Row-Level Security (RLS) in Supabase dashboard for all tables. The migrations include RLS policies, but verify they're active.

---

## ⚙️ Configuration

### Backend Environment Variables (`.env`)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@db.supabase.co:5432/postgres` |
| `SUPABASE_URL` | Supabase project URL | `https://xxxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (secret!) | `eyJhbGc...` |
| `SUPABASE_ANON_KEY` | Anonymous/public key | `eyJhbGc...` |
| `NVIDIA_NIM_API_KEY` | NVIDIA NIM API key | `nvapi-...` |
| `OLLAMA_HOST` | Ollama server URL (optional) | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name (optional) | `qwen2.5-vl:7b` |
| `JWT_SECRET` | JWT signing secret | `your-secret-key` |

### Frontend Environment Variables (`.env.local`)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | `https://xxxxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anonymous/public key | `eyJhbGc...` |
| `FASTAPI_BASE_URL` | Backend API URL | `https://your-app.onrender.com` |

> ⚠️ **Security**: Never commit `.env` or `.env.local` files. Use `.env.example` templates.

---

## 🏃 Running Locally

### Start Backend

```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`

API docs: `http://localhost:8000/docs`

### Start Frontend

```bash
cd frontend
npm run dev
# or
yarn dev
# or
pnpm dev
```

Frontend will be available at `http://localhost:3000`

### Optional: Start Ollama (Local LLM)

```bash
# Install Ollama from https://ollama.ai
ollama pull qwen2.5-vl:7b
ollama serve
```

Ollama will be available at `http://localhost:11434`

---

## 📡 API Quick Reference

Base URL: `http://localhost:8000/api/v1` (local) or `https://your-app.onrender.com/api/v1` (production)

Authentication: `Authorization: Bearer <JWT_TOKEN>`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (no auth required) |
| `/receipts/upload` | POST | Upload receipt image |
| `/receipts/{id}/extract` | POST | Extract data from receipt using LLM |
| `/receipts/{id}` | GET | Get receipt details |
| `/receipts/{id}/correct` | PUT | Correct extracted data |
| `/receipts/{id}/journalize` | POST | Generate journal entry from receipt |
| `/journal-entries` | GET | List journal entries (paginated, filterable) |
| `/journal-entries/{id}` | GET | Get journal entry details |
| `/journal-entries/{id}/reverse` | POST | Reverse a posted journal entry |
| `/journal-entries/export/csv` | GET | Export entries to CSV |
| `/journal-entries/export/pdf` | GET | Export entries to PDF |
| `/admin/users` | GET | List users (admin only) |
| `/admin/usage` | GET | Get usage statistics (admin only) |

### Example: Upload and Extract Receipt

```bash
# 1. Upload receipt
curl -X POST http://localhost:8000/api/v1/receipts/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@receipt.jpg"

# Response: {"receipt_id": "123e4567-e89b-12d3-a456-426614174000"}

# 2. Extract data
curl -X POST http://localhost:8000/api/v1/receipts/123e4567-e89b-12d3-a456-426614174000/extract \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response: {"status": "extracted", "data": {...}, "confidence_scores": {...}}

# 3. Generate journal entry
curl -X POST http://localhost:8000/api/v1/receipts/123e4567-e89b-12d3-a456-426614174000/journalize \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response: {"journal_entry_id": "JE-2026-00001", "status": "posted"}
```

---

## 🧪 Development

### Run Tests

**Backend:**
```bash
cd backend
pytest --cov=app --cov-report=html
# Coverage report: htmlcov/index.html
```

**Frontend:**
```bash
cd frontend
npm run test
# or
yarn test
```

### Linting & Type Checking

**Backend:**
```bash
cd backend
# Linting
ruff check .
# Type checking
mypy app
# Format
black app
```

**Frontend:**
```bash
cd frontend
# Linting
npm run lint
# Type checking
npm run type-check
# Format
npm run format
```

### Load Testing

```bash
cd backend/tests/load
k6 run load_test.js
```

### E2E Testing

```bash
cd frontend
npx playwright test
# View report
npx playwright show-report
```

---

## 🚢 Deployment

### Vercel + Render + Supabase

This is the recommended free-tier deployment stack.

#### 1. Deploy Database (Supabase)

1. Create project at [supabase.com](https://supabase.com)
2. Note your project URL and API keys
3. Run migrations from local machine:
   ```bash
   cd backend
   DATABASE_URL="postgresql://..." alembic upgrade head
   ```

#### 2. Deploy Backend (Render)

1. Create account at [render.com](https://render.com)
2. Create new **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.12
5. Add environment variables from `.env.example`
6. Deploy

> ⚠️ **Free Tier Note**: Render free tier sleeps after 15 minutes of inactivity. Use [UptimeRobot](https://uptimerobot.com) to ping your backend every 14 minutes to keep it awake.

#### 3. Deploy Frontend (Vercel)

**Option A: One-Click Deploy**

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/ai-receipt-journal)

**Option B: CLI Deploy**

```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```

**Configuration:**
- Add environment variables in Vercel dashboard
- Set `FASTAPI_BASE_URL` to your Render backend URL
- Framework Preset: Next.js
- Build Command: `npm run build`
- Output Directory: `.next`

---

## 🏠 Self-Hosting (Zero External APIs)

Run the entire stack locally with Docker Compose, replacing all cloud services:

- **NVIDIA NIM** → Ollama (Qwen2.5-VL 7B)
- **Supabase Postgres** → Docker Postgres 16
- **Supabase Storage** → MinIO
- **Render/Vercel** → Local FastAPI + Next.js dev server

### Docker Compose Setup

1. **Create `docker-compose.yml`** (in project root):

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: receipts
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/receipts
      OLLAMA_HOST: http://ollama:11434
      OLLAMA_MODEL: qwen2.5-vl:7b
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - ollama
      - minio

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
  minio_data:
  ollama_data:
```

2. **Start services**:

```bash
docker-compose up -d
```

3. **Pull Ollama model**:

```bash
docker exec -it <ollama_container_id> ollama pull qwen2.5-vl:7b
```

4. **Run migrations**:

```bash
docker exec -it <backend_container_id> alembic upgrade head
```

5. **Access application**:
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - MinIO Console: `http://localhost:9001`

### Self-Hosting Benefits

✅ **Zero monthly cost** (only electricity)  
✅ **Complete data privacy** (no external APIs)  
✅ **No rate limits** (except hardware constraints)  
✅ **Offline operation** (no internet required)  
✅ **Full control** over models and infrastructure

---

## 💸 Free Tier Constraints & Mitigation

| Service | Limit | Mitigation Strategy |
|---------|-------|---------------------|
| **NVIDIA NIM** | 20 req/min | `asyncio.Semaphore(5)` caps concurrent requests, exponential backoff (3s, 9s, 27s), queue UI shows wait time |
| **Render** | 750 hrs/mo, sleeps after 15min | UptimeRobot ping every 14 min, stateless API design |
| **Supabase Postgres** | 500 MB | Alert at 400 MB, auto-cleanup of old receipts, WebP compression |
| **Supabase Storage** | 1 GB | Client-side compression (5MB limit), 90-day auto-delete policy |
| **Vercel Hobby** | 10s timeout, 100 GB bandwidth | Stateless API routes, CDN caching, optimized images |

### Rate Limit Handling

The backend implements sophisticated rate limit handling:

1. **Semaphore**: Max 5 concurrent LLM requests
2. **Exponential Backoff**: 3s → 9s → 27s on 429 errors
3. **Queue Management**: Users see position in queue and estimated wait time
4. **Automatic Retry**: Failed requests auto-retry up to 3 times
5. **Fallback**: Switches to Ollama if NVIDIA NIM is unavailable

---

## 🧪 Testing

### Test Coverage Targets

- **Backend Unit Tests**: ≥90% route coverage, 100% validator coverage
- **Frontend Unit Tests**: ≥80% component coverage
- **Integration Tests**: All critical user flows
- **E2E Tests**: Upload → Extract → Review → Post flow

### Running Tests

**Backend (pytest):**
```bash
cd backend
pytest --cov=app --cov-report=html --cov-report=term
# View coverage: open htmlcov/index.html
```

**Frontend (Jest + React Testing Library):**
```bash
cd frontend
npm run test:coverage
# View coverage: open coverage/lcov-report/index.html
```

**E2E (Playwright):**
```bash
cd frontend
npx playwright test
npx playwright show-report
```

**Load Testing (k6):**
```bash
cd backend/tests/load
k6 run --vus 10 --duration 30s load_test.js
```

### CI/CD

GitHub Actions workflow runs on every push:
- Linting (ruff, eslint)
- Type checking (mypy, tsc)
- Unit tests (pytest, jest)
- Integration tests (Docker Postgres + Ollama)
- E2E tests (Playwright)

---

## 🗺️ Roadmap

### Phase 2: Enhanced Ingestion
- ✅ Bulk upload (drag multiple files)
- ⏳ CSV/PDF export improvements
- ⏳ Email forwarding ingestion (receipts@yourdomain.com)
- ⏳ Mobile app camera integration

### Phase 3: Team Features
- ⏳ Multi-user approval workflows
- ⏳ Role-based access control (Viewer, Preparer, Reviewer, Admin)
- ⏳ Team activity dashboard
- ⏳ Slack/Teams notifications

### Phase 4: Integrations
- ⏳ QuickBooks Online integration
- ⏳ Xero integration
- ⏳ Multi-currency support
- ⏳ GnuCash export

### Phase 5: Advanced Features
- ⏳ React Native mobile app
- ⏳ OCR preprocessing (Tesseract)
- ⏳ Analytics dashboard (spending trends, category breakdown)
- ⏳ Recurring expense detection
- ⏳ Budget tracking and alerts

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

### Pull Request Process

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Code Style

**Python:**
- Follow PEP 8
- Use `black` for formatting
- Use `ruff` for linting
- Use `mypy` for type checking
- Add docstrings to all functions

**TypeScript/React:**
- Follow Airbnb style guide
- Use ESLint + Prettier
- Use TypeScript strict mode
- Add JSDoc comments for complex functions

### Commit Conventions

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add bulk upload support
fix: correct debit/credit calculation
docs: update README with Docker instructions
test: add unit tests for journal entry validation
refactor: extract LLM client to separate module
```

### Testing Requirements

- All new features must include unit tests
- Integration tests for API endpoints
- E2E tests for critical user flows
- Maintain ≥90% backend coverage, ≥80% frontend coverage

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

This project wouldn't be possible without these amazing technologies:

- **[NVIDIA NIM](https://build.nvidia.com)** — Free-tier multimodal LLM API (Llama 4 Maverick 17B)
- **[Supabase](https://supabase.com)** — Open-source Firebase alternative (Postgres + Auth + Storage)
- **[Ollama](https://ollama.ai)** — Local LLM runtime for self-hosting
- **[Meta Llama](https://llama.meta.com)** — Open-source foundation models
- **[FastAPI](https://fastapi.tiangolo.com)** — Modern Python web framework
- **[Next.js](https://nextjs.org)** — React framework for production
- **[Vercel](https://vercel.com)** — Frontend hosting platform
- **[Render](https://render.com)** — Backend hosting platform

### Special Thanks

- The accounting community for feedback on double-entry bookkeeping requirements
- Open-source contributors who built the libraries this project depends on
- Early testers who helped identify bugs and UX improvements

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ai-receipt-journal/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ai-receipt-journal/discussions)
- **Email**: support@yourdomain.com

---

<div align="center">

**Built with ❤️ for accountants, by developers**

[⭐ Star this repo](https://github.com/yourusername/ai-receipt-journal) if you find it useful!

</div>
