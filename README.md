# AI Receipt to Journal Entry Generator

## Project Overview
This project is an AI-powered application that extracts data from receipts and automatically generates double-entry bookkeeping journal entries. It handles receipt uploads, parses line items via LLMs (like Nvidia NIM and Ollama), validates the data, and securely posts balanced journal entries.

## Tech Stack
| Component | Technology |
|---|---|
| Frontend | Next.js 15 App Router, React, Tailwind CSS, Zustand, Zustand |
| Backend | FastAPI, Python, SQLAlchemy, asyncpg |
| Database | PostgreSQL (Supabase) |
| Auth | Supabase Auth (JWT) |
| LLM | Nvidia NIM / Ollama |

## Local Setup Instructions
Please refer to `docs/local-setup.md` for detailed instructions on how to run this project locally using Docker Compose.
