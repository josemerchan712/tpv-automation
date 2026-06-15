# TPV-Automation — CLAUDE.md

## Project Overview

Point-of-sale (TPV) automation system. Backend exposes a REST API; frontend is a React SPA that consumes it.

**Stack:**
- Backend: Python / FastAPI + SQLite (via SQLAlchemy or raw `aiosqlite`)
- Frontend: React + Vite + Tailwind CSS
- Runtime: Node 20+ (frontend), Python 3.11+ (backend)

## Repository Layout (target)

```
TPV-automation/
├── backend/
│   ├── main.py            # FastAPI app entry point
│   ├── database.py        # SQLite connection / engine setup
│   ├── models/            # SQLAlchemy ORM models
│   ├── schemas/           # Pydantic request/response schemas
│   ├── routers/           # APIRouter modules (products, orders, ...)
│   └── tests/             # pytest suites
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Route-level views
│   │   ├── api/           # Fetch wrappers / React Query hooks
│   │   └── store/         # Global state (Zustand or Context)
│   └── tests/             # Vitest / React Testing Library
├── .claude/
│   ├── agents/
│   └── skills/
└── CLAUDE.md
```

## Dev Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev          # Vite dev server on :5173
npm run build
npm run test
```

## Architecture Decisions

- **SQLite** — single-file DB, no external service required for development or self-hosted deployments.
- **FastAPI** — async-first, auto-generates OpenAPI docs at `/docs`.
- **Vite** — fast HMR; proxies `/api` to the FastAPI server in dev mode (`vite.config.ts`).
- **Tailwind** — utility-first; no separate CSS files unless truly necessary.

## Coding Conventions

- Backend: snake_case everywhere; Pydantic v2 schemas; dependency injection via `Depends`.
- Frontend: PascalCase components, camelCase elsewhere; TypeScript strict mode.
- No `any` types in TypeScript; use proper generics or `unknown`.
- All API calls go through `src/api/`; components never call `fetch` directly.
- Keep routers thin — business logic belongs in service functions, not route handlers.

## Key Domain Concepts

| Term | Meaning |
|------|---------|
| **Producto** | Item available for sale (name, price, stock, category) |
| **Pedido** | A customer order (header + line items) |
| **LineaPedido** | One line of a Pedido: product × quantity × unit price snapshot |
| **Caja** | Cash register session (open/close with totals) |
| **Ticket** | Printable receipt generated for a closed order |

## Custom Agents & Skills

- **code-reviewer** (`.claude/agents/code-reviewer.md`) — run after writing any non-trivial code.
- **planning** skill (`.claude/skills/planning.md`) — generate a file-level plan before implementing a feature.
- **brainstorming** skill (`.claude/skills/brainstorming.md`) — explore 3-4 approaches with trade-offs before committing to one.

## Security Notes

- Never store plain-text passwords; use `passlib` with bcrypt if auth is added.
- Parameterized queries only — no string interpolation in SQL.
- CORS origins must be explicit in production; `allow_origins=["*"]` is dev-only.
- Validate all user input at the API boundary via Pydantic; never trust frontend data.
