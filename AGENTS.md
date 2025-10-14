# NightLoom_worktree1 Development Guidelines

Auto-generated from feature plans. Last updated: 2025-10-15

## Active Technologies
- Python 3.12 backend with FastAPI / httpx / Pydantic / uv
- TypeScript 5 frontend with Next.js 14 / React 18 / Tailwind CSS / pnpm
- Testing stack: pytest + respx、Jest + Testing Library、Playwright

## Project Structure
```
backend/
├── src/
└── tests/

frontend/
├── src/
└── tests/ (unit, e2e)
```

## Commands
- Backend dev server: `cd backend && uv sync && uv run uvicorn app.main:app --reload`
- Backend tests: `uv run --extra dev pytest`
- Frontend dev server: `pnpm --filter nightloom-frontend dev`
- Frontend unit tests: `pnpm --filter nightloom-frontend test`
- Frontend e2e: `pnpm --filter nightloom-frontend test:e2e`

## Code Style
- Python: follow FastAPI + Pydantic conventions, type hints required
- TypeScript: Next.js App Router guidelines, Tailwind utility-first styling

## Recent Changes
- 001-initial-plan: NightLoom MVP 診断体験の計画を追加（FastAPI + Next.js14 構成）

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
