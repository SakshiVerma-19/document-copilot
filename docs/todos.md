# Document Copilot — Development Roadmap

> Tracks what needs to be built, in the order that unblocks the next thing.
> Each phase should end in a working, runnable state before the next one starts.
> Mark items `[x]` as you go.

---

## Phase 0 — Infrastructure (where we are now)

- [x] Repo structure created (`backend/`, `frontend/`, `docs/`, `data/`)
- [x] `uv` project + dev deps (`pytest`, `ruff`) in `backend/pyproject.toml`
- [x] `pnpm` project in `frontend/` with Vite + React + TypeScript
- [x] Tailwind CSS v4 + `@tailwindcss/vite` installed and wired into `vite.config.ts`
- [x] shadcn/ui initialized (Nova preset)
- [x] Alembic initialized (`alembic/`, `alembic.ini`)
- [x] Supabase project created, connection string confirmed working
- [x] `.env` files in place for both services (not committed)
- [x] Fix `alembic.ini` — replace hardcoded URL with `%(DATABASE_URL)s`; read actual URL from `app/config.py` in `alembic/env.py`
- [x] Confirm `uv run alembic upgrade head` runs clean against the Session-mode Supabase URL (pooler, port 5432)

---

## Phase 1 — Backend skeleton

Stand up a FastAPI app that starts, reads config, and responds to a health-check.

- [x] Install core runtime deps: `uv add fastapi "uvicorn[standard]" pydantic-settings structlog supabase openai sqlalchemy alembic httpx`
- [x] `app/config.py` — Pydantic `Settings` class; reads all env vars; fails fast if any required var is missing
- [x] `app/main.py` — FastAPI app creation, CORS middleware (from `settings.allowed_origins`), `GET /health` returning `{"status": "ok"}`
- [x] Verify `uv run uvicorn app.main:app --reload` starts without errors

---

## Phase 2 — Database schema + first migration

Define all tables; apply them to Supabase in one reviewed migration.

- [ ] `app/database/models.py` — SQLAlchemy declarative models:
  - `profiles` (user_id FK to Supabase auth, email, created_at)
  - `chat_threads` (id, user_id, title, created_at, updated_at)
  - `chat_messages` (id, thread_id, role, content JSON, created_at)
  - `message_citations` (id, message_id, chunk_id, excerpt, page, section)
  - `source_documents` (id, ticker, company, filing_type, fiscal_year, filing_date, accession_number, source_url, markdown_content, created_at)
  - `document_chunks` (id, document_id, chunk_index, text, token_count, metadata JSON, embedding vector(1536), search_vector tsvector)
- [ ] Wire `models.py` metadata into `alembic/env.py` for autogenerate
- [ ] `alembic/env.py` reads `DATABASE_URL` from `app/config.py` — no hardcoded credentials
- [ ] Generate initial migration: `uv run alembic revision --autogenerate -m "initial schema"`
- [ ] Review generated migration; manually add: `CREATE EXTENSION IF NOT EXISTS vector`, generated tsvector column, HNSW index on embedding, GIN index on search_vector, RLS enablement and user-scoped policies on all tables
- [ ] `uv run alembic upgrade head` — confirms schema applied cleanly

---

## Phase 3 — Auth layer

FastAPI verifies the Supabase JWT; every protected route knows who the user is.

- [ ] `app/database/supabase.py` — creates anon + service-role Supabase clients from config
- [ ] `app/auth/dependencies.py` — `get_current_user` FastAPI dependency: reads `Authorization: Bearer <token>`, calls Supabase Auth to verify, returns typed `AuthUser(id, email)`, raises 401 on failure
- [ ] Add `GET /me` behind `get_current_user`
- [ ] Manual smoke test: call `/me` with a valid Supabase session token

---

## Phase 4 — Frontend scaffolding + auth UI

A working React SPA that can log in and talk to the backend.

- [ ] Install: `pnpm add @supabase/supabase-js react-router-dom @ai-sdk/react ai`
- [ ] `src/lib/env.ts` — validates `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` at boot; throws if missing
- [ ] `src/lib/supabase.ts` — browser Supabase client singleton
- [ ] `src/lib/http.ts` — thin `fetch` wrapper: base URL, JSON headers, bearer token from Supabase session, timeout, typed `ApiError` with `isNetworkError` flag
- [ ] `src/lib/api.ts` — product-level call wrappers (threads list, create thread, message history)
- [ ] `src/App.tsx` — React Router routes: `/login`, `/chat`, `/chat/:threadId`
- [ ] `src/pages/LoginPage.tsx` — email + password form; calls Supabase `signInWithPassword`; redirects to `/chat` on success
- [ ] `src/components/AuthGuard.tsx` — wraps protected routes; redirects to `/login` if no session
- [ ] shadcn components to add: `button`, `input`, `form`, `card`, `toast`
- [ ] Verify: login, session stored, redirect works, `/me` returns 200 with the token

---

## Phase 5 — Chat threads UI + stubbed streaming endpoint

End-to-end skeleton: user can open/create threads; backend streams a stub reply.

**Backend:**
- [ ] `app/api/chat.py` — FastAPI router with: `GET /chat/threads`, `POST /chat/threads`, `GET /chat/threads/{id}/messages`, `POST /chat/stream` (stub for now)
- [ ] `app/database/chats.py` — async helpers: create/read threads and messages
- [ ] `app/chat/streaming.py` — AI SDK-compatible SSE event emitter helpers
- [ ] Wire router into `app/main.py`

**Frontend:**
- [ ] `src/pages/ChatPage.tsx` — sidebar (thread list), main chat area
- [ ] `src/components/chat/ChatThread.tsx` — message list, input bar
- [ ] `src/components/chat/Message.tsx` — renders user and assistant messages
- [ ] `useChat` from AI SDK pointed at `POST /chat/stream` with Supabase bearer token
- [ ] Verify: create thread, send message, see streamed stub reply in UI

---

## Phase 6 — Ingestion pipeline

Populate the database with the SEC corpus so retrieval has something to work with.

- [ ] `ingest/download.py` — downloads 10-K filings from EDGAR for Apple, Amazon, Alphabet, Microsoft, NVIDIA (2021–2025)
- [ ] `ingest/parse.py` — converts raw HTML filings to cleaned Markdown preserving section headers
- [ ] `ingest/chunk.py` — splits Markdown into overlapping chunks (~400 tokens, 50-token overlap); attaches metadata (ticker, company, filing_type, fiscal_year, page/section)
- [ ] `ingest/embed.py` — batches chunks through OpenAI `text-embedding-3-small`
- [ ] `ingest/writer.py` — upserts `source_documents` + `document_chunks` into Supabase
- [ ] `ingest/run.py` — orchestrates full pipeline; idempotent (skip already-ingested docs)
- [ ] Run pipeline; verify chunk + embedding counts in Supabase dashboard
- [ ] Confirm `document_chunks.search_vector` is populated

---

## Phase 7 — Retrieval

Hybrid semantic + lexical search with RRF fusion.

- [ ] `app/retrieval/queries.py` — `semantic_search(query_embedding, k)` via pgvector, `fulltext_search(query_text, k)` via Postgres `ts_rank`
- [ ] `app/retrieval/fusion.py` — Reciprocal Rank Fusion over two ranked lists
- [ ] `app/retrieval/retriever.py` — `DocumentRetriever.retrieve(query, k)`: embed query, run both searches, fuse, return typed `SourcePassage` list
- [ ] Unit tests for fusion logic (`tests/retrieval/test_fusion.py`)
- [ ] Integration test behind `@pytest.mark.integration` for end-to-end retrieval against Supabase

---

## Phase 8 — PydanticAI agent + real answers

Replace the stub with a grounded, cited assistant response.

- [ ] `uv add pydantic-ai`
- [ ] `app/assistant/outputs.py` — `Citation`, `SourcePassage`, `GroundedAnswer` Pydantic models
- [ ] `app/assistant/deps.py` — `DocumentAgentDeps` dataclass (user_id, thread_id, retriever, grounding_validator)
- [ ] `app/assistant/instructions.md` — system prompt: answer only from retrieved passages; cite every claim; say so if corpus is insufficient; never recommend stocks
- [ ] `app/assistant/agent.py` — PydanticAI agent with `search_filings`, `read_chunk`, `read_surrounding_chunks` tools
- [ ] `app/grounding/validator.py` — validates every citation maps to a retrieved passage; raises on violation
- [ ] `app/chat/orchestrator.py` — full turn: retrieve, agent run, validate grounding, stream, persist
- [ ] Wire orchestrator into `POST /chat/stream`
- [ ] Smoke test: "What was Apple's Services revenue in FY2024?" returns cited, grounded answer

---

## Phase 9 — Citations UI

Surface sources so analysts can verify in one click.

- [ ] `src/components/chat/CitationBadge.tsx` — inline [1] links in assistant message text
- [ ] `src/components/chat/SourcePanel.tsx` — slide-in drawer: company, filing type, fiscal year, section/page, verbatim excerpt, link to EDGAR URL
- [ ] `src/components/chat/EmptyState.tsx` — first-thread prompt with example questions from the client brief
- [ ] `src/components/chat/ErrorMessage.tsx` — friendly error display (auth expired, corpus miss, grounding failure)
- [ ] Parse structured citation parts from the AI SDK stream; render alongside text deltas

---

## Phase 10 — Polish, hardening, and deployment prep

- [ ] Error handling audit — all 401/403/404/502/500 cases return correct status + stream error event
- [ ] Streaming edge cases — connection drop mid-stream, partial message, grounding failure mid-generation
- [ ] RLS audit — confirm users cannot access each other's threads, messages, or citations via the API
- [ ] CORS — tighten `allowed_origins` to production frontend URL only
- [ ] Config hardening — `alembic.ini` URL uses `%(DATABASE_URL)s`; no secrets leak into logs
- [ ] Structured logging — `structlog` across all request-path modules; include `user_id`, `thread_id`, `latency_ms`
- [ ] Railway deployment: `pnpm build` for frontend, `uvicorn app.main:app` for backend, env vars in Railway dashboard, health check passes
- [ ] Pilot handoff — 5 senior analysts get access; collect feedback on answer quality, latency, citation UX

---

## Blocked / decisions pending

| Item | Blocker |
|---|---|
| Alembic migration | Need confirmed working Session-mode Supabase URL (pooler, port 5432) |
| Ingestion pipeline | Confirm EDGAR download strategy: full-text search API vs. bulk index download |
| Embedding model dimensions | Locked to `text-embedding-3-small` (1536 dims) — confirm before writing schema migration |
| AI SDK chat hook | Verify `useChat` / `DefaultChatTransport` API surface against installed `ai` package version before Phase 5 |
