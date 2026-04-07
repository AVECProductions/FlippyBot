# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FLIPPY** is an AI-powered Facebook Marketplace deal scanner. It scrapes listings using Playwright, runs them through a two-pass Google Gemini pipeline (quick triage → deep analysis), and surfaces high-value resale opportunities via UI and email notifications.

## Commands

### Backend (Django)

```bash
cd backend

# Install dependencies (first time or after requirements.txt changes)
pip install -r requirements.txt

# Run development server (port 8000)
python manage.py runserver

# Apply migrations
python manage.py migrate

# Create new migrations after model changes
python manage.py makemigrations

# Install Playwright browsers (required for scraping)
playwright install chromium
```

### Frontend (Vue 3 + Vite)

```bash
cd frontend

# Install dependencies
npm install

# Dev server with hot reload (port 5173)
npm run dev

# Type check
npm run type-check

# Run unit tests
npm run test:unit

# Run a single test file
npx vitest run src/path/to/test.spec.ts

# Lint
npm run lint

# Format
npm run format

# Production build
npm run build
```

## Architecture

### Two-Pass AI Analysis Pipeline

The core feature. Located in `backend/apps/scanners/services/`:

1. **Scraping** (`flippy_scanner_service.py`): Playwright scrapes Facebook Marketplace listings and stores them as `Listing` objects grouped in a `ScanBatch`.
2. **Pass 1 – Triage** (`two_pass_analysis_service.py`): Batches raw listings and sends them to Gemini with the agent's `triage_prompt`. Listings marked "interesting" proceed to pass 2.
3. **Pass 2 – Deep Analysis** (`llm_analysis_service.py`): Fetches full listing details + images for interesting listings and runs the agent's `analysis_prompt`. Results saved back to `Listing`.

### Agent System

Agents are database records (`apps/scanners/models.py` → `Agent` model), not hardcoded classes. Each agent has:
- `slug`: unique identifier used throughout the system
- `triage_prompt` / `analysis_prompt`: the actual prompts sent to Gemini
- `model`: which Gemini model version to use

`AgentBuilderService` (`services/agent_builder_service.py`) can generate prompts via AI given a description.

### Key Models

| Model | App | Purpose |
|-------|-----|---------|
| `Agent` | scanners | AI specialist configuration (prompts, model) |
| `ActiveScanner` | scanners | Query + locations + on/off state |
| `Listing` | listings | Marketplace listing + AI analysis results |
| `ScanBatch` | scanners | Groups listings from one scan run |
| `LLMUsage` | scanners | Per-call token usage and cost tracking |

### Frontend State Flow

```
Views → Pinia Stores → services/api.ts (axios) → Django REST API
```

- **Stores** (`src/stores/`): `auth`, `scanners`, `agents` — source of truth for app state
- **Views** (`src/views/`): Page-level components that read from stores
- **Components** (`src/components/features/`): Feature UI organized by domain (`agents/`, `scanners/`, `listings/`)
- **Types** (`src/types/`): TypeScript interfaces mirroring backend models

### API Structure

Backend URL routing: `mysite/urls.py` → `apps/api/urls.py` → per-app routers.

All API endpoints are under `/api/`. DRF ViewSets handle CRUD; custom actions handle scan triggers and analysis runs.

## Environment Variables

Backend requires a `.env` file in `backend/` with:
- `GEMINI_API_KEY` — Google Gemini API key
- `SENDGRID_API_KEY` — for email notifications
- `SECRET_KEY` — Django secret key
- `DATABASE_URL` — PostgreSQL URL (production); SQLite used in dev by default

## Deployment

- **Backend**: Railway (`backend/railway.json`) — runs `gunicorn mysite.wsgi`
- **Frontend**: Netlify (`frontend/netlify.toml`) — builds `dist/` and serves as SPA
- **Production API base URL**: `https://flippy-production-9afd.up.railway.app/api`
