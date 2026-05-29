# INFRA-OPS-SPEC — Bhog (AI Indian-nutrition coach)

**Audience:** fresh backend/infra engineer building the Phase-2 backend spine. Build from this without asking questions.
**Status:** LOCKED. Every decision below traces to a D-ID / REQ-ID / sibling spec. Anything genuinely unresolved is marked `OPEN — needs founder`.
**Scope (this doc):** repo structure, dependency management, secrets, CI/CD, hosting setup, health endpoints, region-pin compliance assertion, observability wiring, local-dev runbook.
**Out of scope (cross-linked, do NOT duplicate):**
- API route contracts, request/response shapes → `API-SPEC.md`
- DB schema, tables, columns, migrations content → `DATA-SPEC.md` (or `API-SPEC.md` if merged)
- DPDP cron logic, consent ledger, hard-delete, export → `COMPLIANCE-SPEC.md`
- `ai_provider.py` internals, prompt versioning, eval rubric content → `01-AI-SPEC.md`

Ground-truth priority honored: `CLAUDE.md` > `01-CONTEXT.md` (D-01..D-19) > `.planning/decisions/*` (incl D-CEO-01..03) > `01-AI-SPEC.md` > `REQUIREMENTS.md` > `ARCHITECTURE.md` (superseded banner honored).

---

## 0. Stack Versions (locked, do not bump without an ADR)

| Layer | Pin | Source |
|---|---|---|
| Python | **3.12** | CLAUDE.md, INFRA-05 |
| Package manager | **uv** (commit `pyproject.toml` + `uv.lock`) | audit lock |
| FastAPI | 0.128.x | CLAUDE.md, INFRA-05 |
| Pydantic | v2 (2.x) | CLAUDE.md |
| SQLAlchemy | 2.0 async + `asyncpg` | CLAUDE.md, INFRA-05 |
| Alembic | latest | INFRA-05/06 |
| Compute | **Render free, Singapore** (no CC) | D-01 |
| DB | **Supabase Postgres, Mumbai free** (no CC) | D-02, INFRA-06 |
| Object storage | **Cloudflare R2, `jurisdiction=india`** (no CC) | D-04, INFRA-07 |
| Auth | **Firebase Phone OTP** (no CC) | D-05 |
| Cron | **GitHub Actions scheduled workflows** (NOT APScheduler) | D-03, ARCHITECTURE banner |
| Backend error monitor | **`sentry-sdk[fastapi]`** (Phase-2 Wk1) | audit lock; ALPHA-04 (mobile half deferred) |
| AI tracing | **Arize Phoenix** + OpenInference | 01-AI-SPEC §5/§7 |

> **Render, not Fly.io / Railway.** ARCHITECTURE.md and 01-AI-SPEC §5/§7 say "Fly.io bom1" / "Railway" / "Fly.io sidecar" — those are **SUPERSEDED by D-01** (Fly + Railway both require a credit card in 2026; zero-CC is a hard constraint). Wherever a read source says Fly/Railway, substitute **Render free Singapore**. Compute living in Singapore (not Mumbai) is an **intentional, disclosed** DPDP trade-off — see §7.

---

## 1. Repo Structure — MONOREPO

**Locked:** single repo, two siblings — `server/` (FastAPI) and `mobile/` (Expo). This matches the ARCHITECTURE topology and is a hard dependency for CI path-filters (§5) and the eval gate (`prompts/**`, `providers/**`, `services/advice_*`).

```
ai-calorie-weight-loss/                 # repo root (current git root)
├── server/                             # FastAPI backend (Phase 2 builds this)
│   ├── app/
│   │   ├── main.py                     # app factory + lifespan (Phoenix init, region-pin assert)
│   │   ├── config.py                   # pydantic_settings.BaseSettings — ALL env/secret reads here
│   │   ├── deps.py                     # auth dep (firebase verify), db session dep
│   │   ├── healthz.py                  # /healthz + /readyz routers (§6)
│   │   ├── api/                        # routes — see API-SPEC.md for contracts
│   │   ├── services/                   # vision_pipeline, advice_engine, advice_rubric, ...
│   │   ├── providers/                  # ONLY dir allowed to import provider SDKs (ruff TID251)
│   │   ├── schemas/                    # Pydantic v2 request/response
│   │   ├── models/                     # SQLAlchemy 2.0 ORM (separate from schemas/ — anti-pattern #17)
│   │   ├── prompts/                    # version-stamped vision_v1.py / advice_v1.py
│   │   └── observability/              # phoenix_init.py, cost_log.py, latency_log.py
│   ├── alembic/                        # migrations (env.py async)
│   ├── tests/                          # unit / integration / fixtures
│   ├── pyproject.toml                  # COMMITTED
│   ├── uv.lock                         # COMMITTED
│   ├── .env.example                    # COMMITTED (no real values)
│   ├── .env                            # GITIGNORED
│   ├── Dockerfile                      # Render build (uv sync)
│   └── render.yaml                     # Render blueprint (push-from-GitHub)
├── mobile/                             # Expo app — Phase 3+. See sibling mobile specs.
│   ├── eas.json                        # EAS profiles — Phase 3 (TODOS.md item 5)
│   └── ...
├── data/                              # MOVE existing root data/ → server/app/data/ at Phase-2 Wk1
│   │                                  #   dish_decomposition.json, ifct_lookup.json,
│   │                                  #   veg_protein_prices_schema.sql, photos/, CURATION-CHECKLIST.md
├── evals/                             # KEEP at repo root (CI path-filter target evals/**)
│   ├── gate_0a_vision.py              # AI-SPEC §5 — required CI check
│   ├── gate_0b_advice.py
│   ├── datasets/  results/  promptfoo/
├── .github/workflows/                 # CREATE Phase-2 Wk1 (§5)
│   ├── evals.yml                      # eval merge gate
│   ├── cron-keepalive.yml             # Render /healthz + Supabase keep-alive
│   └── cron-price-anomaly.yml         # D-16 monthly anomaly
├── .planning/  CLAUDE.md  DESIGN.md  TODOS.md
```

### Migration action (Phase-2 Wk1, first PR)
The repo today has `data/` and `evals/` at root and **no** `server/` or `mobile/`. The first Phase-2 PR:
1. Creates `server/` and scaffolds `server/app/...` per above.
2. **Moves** `data/*` → `server/app/data/*` (these are runtime lookup tables the FastAPI app loads: `dish_decomposition.json`, `ifct_lookup.json`; `veg_protein_prices_schema.sql` becomes an Alembic migration per D-17).
3. **Leaves** `evals/` at repo root — `evals/**` is a CI path-filter (§5) and its datasets are not loaded by the running app. `git mv` for history preservation.

> `data/` ships **inside** `server/app/data/` (small, ~40KB JSON + 50-dish table) so there is no Week-1 data-loading runbook — matches ARCHITECTURE "Structure Rationale". `evals/` stays out of the deployed image.

---

## 2. Dependency Management — uv

**Locked:** `uv` for all Python deps. Python **3.12**.

- `server/pyproject.toml` + `server/uv.lock` are **both committed**. The lockfile is the reproducibility contract — Render and CI install from it.
- Install / sync everywhere via **`uv sync`** (Render build, GitHub Actions, local dev). `uv sync` installs the locked set, including the project itself, into `.venv`.
- Add a dep: `uv add "fastapi==0.128.*"`; dev-only: `uv add --dev pytest`. This rewrites `pyproject.toml` + `uv.lock` — commit both.
- Run anything in the env: `uv run <cmd>` (e.g. `uv run uvicorn app.main:app`, `uv run alembic upgrade head`, `uv run pytest`).
- **Do NOT** commit `.venv/`. **Do NOT** use `pip install` ad-hoc — it desyncs the lockfile (drift = irreproducible Render build).

Baseline deps (non-exhaustive; AI-SPEC §3/§5 lists the AI/eval set — do not duplicate here):
`fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `httpx`, `boto3` (R2), `firebase-admin`, `Pillow`, `tenacity`, `sentry-sdk[fastapi]`.

---

## 3. Secrets Matrix (locked)

**Rule:** every secret is read **only** in `server/app/config.py` via `pydantic_settings.BaseSettings`. No `os.environ[...]` scattered in services (AI-SPEC §3 layout). Nothing secret is ever committed; `.env` is gitignored, `.env.example` is committed with placeholder values.

| Secret / env name | Purpose | Local (`server/.env`, gitignored) | Render (Singapore web service) | GitHub Actions (repo secrets) | EAS (mobile, Phase 3) |
|---|---|---|---|---|---|
| `ENV` | `dev` \| `prod` (gates Ollama, Phoenix endpoint) | `dev` | `prod` | `ci` (for eval runs) | — |
| `DATABASE_URL` | Supabase Mumbai async Postgres DSN (`postgresql+asyncpg://...`) | local PG or Supabase dev DSN | **Render env var** | not needed (evals mock DB) | — |
| `SUPABASE_PROJECT_REF` | Mumbai project ref — region-pin allow-list (§6, COMP-01) | dev ref | **Render env var** | — | — |
| `R2_ACCOUNT_ID` | Cloudflare account id (builds `.in.r2.cloudflarestorage.com`) | dev | **Render env var** | — | — |
| `R2_ENDPOINT_URL` | Must be `https://<acct>.in.r2.cloudflarestorage.com` (jurisdictional) | dev | **Render env var** | — | — |
| `R2_ACCESS_KEY_ID` | R2 S3 access key | dev key | **Render secret file/env** | — | — |
| `R2_SECRET_ACCESS_KEY` | R2 S3 secret | dev key | **Render secret** | — | — |
| `R2_BUCKET` | `ai-coach-meals-prod` (jurisdiction=india) | dev bucket | **Render env var** | — | — |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | firebase-admin token verify (`verify_id_token`) | local file path | **Render Secret File** (mounted JSON) | — | — |
| `GEMINI_API_KEY` | Google AI Studio — production vision/text-paid-fallback | dev key | **Render secret** | — | — |
| `GROQ_API_KEY` | Groq Llama 3.3 — production text primary | dev key | **Render secret** | — | — |
| `OPENROUTER_API_KEY` | OpenRouter fallback chain | dev key | **Render secret** | — | — |
| `OPENAI_API_KEY` | GPT-4o-mini last-resort paid vision | dev key | **Render secret** | — | — |
| `EVAL_GEMINI_API_KEY` | **SEPARATE eval-only Gemini key** — keeps eval RPD off production budget (AI-SPEC §5 judge note) | optional | — | **GitHub repo secret** | — |
| `PHOENIX_OTLP_ENDPOINT` | tracing exporter target | `http://localhost:6006/v1/traces` | Phoenix endpoint (§7) | — | — |
| `SENTRY_DSN` | backend Sentry | optional (off in dev) | **Render env var** | — | — |
| `PHOENIX_BASIC_AUTH` | founder-only Phoenix UI gate | — | **Render secret** (if Phoenix hosted) | — | — |
| `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` | Play Internal Testing submit | — | — | — | **EAS secret** (Phase 3, TODOS.md item 5) |
| `ANDROID_SIGNING_*` | app signing custody | — | — | — | **EAS-managed + founder escrow** (TODOS.md item 5) |

Key locks:
- **`EVAL_GEMINI_API_KEY` is a distinct key from `GEMINI_API_KEY`.** Eval/CI uses the eval key; production uses the prod key. They never cross. The eval key lives **only** in GitHub repo secrets; the prod key lives **only** in Render. (AI-SPEC §5: "separate API key from production to keep eval RPD off production budget".)
- **`FIREBASE_SERVICE_ACCOUNT_JSON` is a Render Secret File**, not an inline env var (multi-line JSON; secret-file mounting avoids escaping bugs). Same option for `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` on EAS.
- **No credit card anywhere in Phase 0-2.** Every service above is on a no-CC free tier (D-01, D-02, D-04, D-05).
- EAS secrets are **deferred to Phase 3** (mobile build). Listed here only for completeness; do not provision in Phase 2.

`.env.example` (committed) lists every `dev`/`prod` row above with empty or placeholder values and a comment per line. The running app fails fast at boot if a required prod secret is missing (Pydantic Settings raises).

---

## 4. CI/CD Timing — split the "no CI/CD until month 4" rule

`CLAUDE.md` currently says: *"Manual builds V1, no CI/CD until month 4 (founder discipline)."* That rule is now **split**:

- **Backend CI (eval gates + cron) stands up at Phase-2 Week 1** — see §5. Rationale: the eval gate (AI-SPEC §5) and the Render/Supabase keep-alive crons (D-03, D-02) are infrastructure the backend cannot run safely without. These are not "build pipelines," they are correctness + uptime gates.
- **Mobile EAS Build CI/CD stays deferred to Phase 3/4** (TODOS.md item 5). No EAS automation in Phase 2.
- **Render deploy itself is push-from-GitHub** (Render watches the connected branch and builds on push) — this is Render-native, not a GitHub Actions pipeline, so it does not violate the "manual builds" spirit; it is just the no-CC deploy path.

### CLAUDE.md update (apply this exact edit during Phase-2 Wk1)
Replace the line `- Manual builds V1, no CI/CD until month 4 (founder discipline)` under the Mobile section with:
> `- Mobile EAS builds remain manual through Phase 2; mobile EAS CI/CD deferred to Phase 3/4 (TODOS.md item 5). Backend GitHub Actions (eval-gate + keep-alive + price-anomaly crons) stand up at Phase-2 Week 1 — see .planning/handoff/INFRA-OPS-SPEC.md §4/§5.`

---

## 5. GitHub Actions Workflows (create Phase-2 Wk1)

All workflows install via `uv sync`. Python 3.12. Three workflow files:

### 5a. `evals.yml` — eval merge gate (AI-SPEC §5)
- **Trigger:** `pull_request` with `paths:` filter — `prompts/**`, `providers/**`, `services/advice_*`, `services/vision_*`, `evals/**` (paths are repo-relative; with the monorepo they resolve to `server/app/prompts/**` etc — set the filter accordingly: `server/app/prompts/**`, `server/app/providers/**`, `server/app/services/advice_*`, `server/app/services/vision_*`, `evals/**`).
- **Jobs (required checks — PR cannot merge if any Critical dimension fails):**
  - `uv run pytest evals/gate_0a_vision.py --fail-under-bucket=0.70`
  - `uv run pytest evals/gate_0b_advice.py --fail-under=0.70`
  - `uv run promptfoo eval -c evals/promptfoo/vision_v1.yaml` and `.../advice_v1.yaml`
  - `uv run ruff check --select TID251` (provider-SDK-import lint) + the `gsd-no-pii-in-advice-prompt` rule (G11 / M10 hard gate — 0 violations).
- **Secret:** `EVAL_GEMINI_API_KEY` (repo secret, eval-only). Never the prod key.
- This is the operationalization of REQ INFRA-01 lint enforcement + AI-SPEC §5 CI integration. Branch protection on `main` marks these as required.

### 5b. `cron-keepalive.yml` — two scheduled jobs (D-03, D-02)
Both pinned to the **D-03 active window 04:30–16:30 UTC (10:00–22:00 IST)**. Off-window requests intentionally pay Render's ~60s cold start (D-03b handles UX, mobile-side, Phase 3).

| Job | Schedule (cron, UTC) | Action | Why |
|---|---|---|---|
| `render-keepalive` | every 10 min **within 04:30–16:30 UTC** → `cron: "*/10 4-16 * * *"` (the 04:30 floor is enforced in-job with a guard that skips runs before 04:30; GitHub cron has no sub-hour offset) | `curl -fsS https://<render-app>.onrender.com/healthz` | D-03: keeps Render free awake during the 14h Indian meal window; ~420h/mo, under 750h free cap. **Hits `/healthz` — shallow, no DB round-trip** (§6). |
| `supabase-keepalive` | every 6h → `cron: "0 */6 * * *"` | trivial `SELECT 1` against `DATABASE_URL` (or Supabase REST ping) | D-02: Supabase free auto-pauses after 1 week idle. Disable this job when paid tier kicks in. |

> GitHub Actions cron only supports 5-field UTC cron (no minute-offset windows). Implement the 04:30 floor and 16:30 ceiling as the hour range `4-16` plus an in-job `if` that exits early when the current UTC minute/hour falls outside `04:30–16:30`. Document the math inline (D-03: ~420h/mo, ~300h headroom).

### 5c. `cron-price-anomaly.yml` — monthly veg-protein anomaly (D-16)
- **Schedule:** monthly → `cron: "0 6 1 * *"` (1st of month, 06:00 UTC / 11:30 IST).
- **Action:** SQL job compares current `veg_protein_prices` rows vs the prior quarter snapshot; if any item moved **>15%**, ping founder (WhatsApp/email) for an early manual refresh (D-16 catches festival / tomato-onion shocks). Quarterly manual refresh is a founder calendar task, not a workflow.
- Depends on the `veg_protein_prices` table (D-17) existing — so this workflow lands after the Alembic migration for that table.

> Workflow YAML is planner/executor discretion (D-CONTEXT "Claude's Discretion" — standard pattern). The **triggers, schedules, target endpoints, and the D-03 window are locked above.**

---

## 6. Health Endpoints + Region-Pin Compliance Assertion

### 6a. `/healthz` vs `/readyz` (cross-link: API-SPEC.md)
| Endpoint | Depth | DB round-trip? | Used by | Returns |
|---|---|---|---|---|
| `GET /healthz` | **shallow liveness** | **No** | `render-keepalive` cron (§5b), Render platform | `200 {"status":"ok"}` always-if-process-up |
| `GET /readyz` | **deep readiness** | **Yes** — per dependency | manual / dashboard / deploy smoke check | `200` if all deps OK; `503 {"checks":{...}}` if any fail |

`/readyz` probes each dependency and reports per-dep status: **Postgres** (`SELECT 1`), **R2** (HEAD bucket / list-objects with `max_keys=1`), **Firebase** (admin SDK initialized / public-key fetch reachable). A single failure → overall `503` with the failing check named. `/healthz` deliberately does **none** of this so the keep-alive cron never wakes/holds a DB connection and never flaps on a transient dep blip. (INFRA-05 mandates `/healthz`; `/readyz` is the deeper companion.)

### 6b. COMP-01 region-pin = boot-time assertion (ABORT BOOT on mismatch)
Per **COMP-01** (DPDP Act 2023 region pinning verified by automated check at boot; deploy fails if mismatch) and **D-04 / D-02**, the FastAPI `lifespan` startup runs `assert_region_pin()` **before serving traffic**. On any mismatch it **raises and aborts boot** (process exits non-zero → Render marks deploy failed). This is the single enforcement point; cross-link `COMPLIANCE-SPEC.md` for the DPDP policy rationale.

Assertion (in `server/app/main.py` lifespan, reading `config.py`):
1. **R2 jurisdiction:** `settings.R2_ENDPOINT_URL` host **must match** `*.in.r2.cloudflarestorage.com` (the `.in.` jurisdictional endpoint per D-04). A bare `*.r2.cloudflarestorage.com` (Mumbai PoP, no jurisdiction) **fails** — that does NOT satisfy DPDP residency (D-04, anti-pattern #2).
2. **Supabase Mumbai:** `settings.SUPABASE_PROJECT_REF` (and the host in `DATABASE_URL`) **must be in an env allow-list** of known-Mumbai project refs (`settings.ALLOWED_SUPABASE_REFS`, comma-separated). Any other ref → fail. (Supabase region is not in the DSN, so the pin is an explicit founder-maintained allow-list of the Mumbai project ref.)
3. **Compute = Singapore is intentionally EXEMPT and disclosed.** Render runs in Singapore (D-01); this is a known, privacy-policy-disclosed cross-border processing posture (D-01 DPDP monitoring contract + COMPLIANCE-SPEC.md). The assertion pins **storage** (R2) and **DB** (Supabase) to India; it does **not** assert compute region. Document this exemption inline in `assert_region_pin()` so a future reader does not "fix" it.

```python
# server/app/main.py (sketch — full impl in API/backend build)
def assert_region_pin(settings) -> None:
    host = urlparse(settings.R2_ENDPOINT_URL).hostname or ""
    if not host.endswith(".in.r2.cloudflarestorage.com"):
        raise RuntimeError(f"COMP-01: R2 endpoint not india-jurisdictional: {host!r}")
    allowed = {r.strip() for r in settings.ALLOWED_SUPABASE_REFS.split(",") if r.strip()}
    if settings.SUPABASE_PROJECT_REF not in allowed:
        raise RuntimeError(f"COMP-01: Supabase ref {settings.SUPABASE_PROJECT_REF!r} not in Mumbai allow-list")
    # NOTE: compute region (Render=Singapore) is INTENTIONALLY not asserted (D-01, disclosed).
```

### 6c. Required test (ship with the assertion)
Add `server/tests/unit/test_region_pin.py` that **injects a wrong endpoint and expects boot to abort**:
- `assert_region_pin(settings_with R2_ENDPOINT_URL="https://acct.r2.cloudflarestorage.com")` → raises `RuntimeError` matching `COMP-01`.
- `assert_region_pin(settings_with SUPABASE_PROJECT_REF="some-singapore-ref")` (not in allow-list) → raises.
- happy path (`.in.r2...` + allow-listed ref) → returns `None`. (Satisfies COMP-01 "deploy fails if mismatch" with a regression guard.)

---

## 7. Observability

### 7a. Backend Sentry — pulled forward to Phase-2 Week 1
`ALPHA-04` originally schedules "Sentry + PostHog" at alpha (Phase 4). **Split:** the **backend** `sentry-sdk[fastapi]` is pulled forward to **Phase-2 Week 1** (init in `main.py`, `SENTRY_DSN` env, `ENV`-tagged). Rationale: backend crashes during spine build need traces from day 1. **Mobile Sentry + PostHog stay at Phase 4** (ALPHA-04) — they are mobile concerns and Phase 2 ships no mobile code.

### 7b. AI tracing = Arize Phoenix (AI-SPEC §5/§7)
- `server/app/observability/phoenix_init.py` called once in `lifespan`; OpenInference instruments `google-genai`, `groq`, `openai` SDKs. `cost_log.py` writes one `ai_call_log` Postgres row per call (gate-evaluating ledger; Phoenix is observability).
- **Hosting note (supersession):** AI-SPEC §7 says "Phoenix self-hosted on Fly.io sidecar." Fly.io is superseded (D-01). For **Phase 1/2**, Phoenix runs **locally** (`python -m phoenix.server.main serve`, port 6006) during prompt iteration and eval review — the prod `PHOENIX_OTLP_ENDPOINT` defaults to localhost and Phase-2 prod traces are reviewed against the locally-run collector / batched exports. A persistent always-on hosted Phoenix on Render (extra service, possibly CC-gated) is **OPEN — needs founder** (see §9). This does not block Phase-2 spine: cost gate uses the Postgres `ai_call_log` ledger, which is independent of where the Phoenix UI runs.

---

## 8. Local-Dev Runbook

Backend, from a clean clone (no CC, ~5 min):

```bash
git clone <repo-url> && cd ai-calorie-weight-loss/server
uv sync                                  # creates .venv from uv.lock (Python 3.12)
cp .env.example .env                     # fill in dev values (or point DATABASE_URL at local Postgres)
uv run alembic upgrade head              # apply migrations to the DB in DATABASE_URL
uv run uvicorn app.main:app --reload     # boot — region-pin assert runs; serves on :8000
# verify:
curl -fsS localhost:8000/healthz         # {"status":"ok"}
curl -s   localhost:8000/readyz          # per-dependency status
# optional, for prompt/eval work:
python -m phoenix.server.main serve      # Phoenix UI on :6006
uv run pytest                            # unit + integration
```

`ENV=dev` gates Ollama-dev provider and points `PHOENIX_OTLP_ENDPOINT` at localhost. A wrong R2 endpoint or non-allow-listed Supabase ref in `.env` will **abort boot** (§6b) — that is expected; fix `.env`.

---

## 9. Hosting Setup Checklist (all no-CC, Phase-2 Wk1)

Do these in order. None require a credit card.

1. **Supabase (D-02, INFRA-06):** create free project, **region = Mumbai (`ap-south-1`)**. Copy project ref → `SUPABASE_PROJECT_REF` + `ALLOWED_SUPABASE_REFS`. Copy async DSN → `DATABASE_URL` (`postgresql+asyncpg://`). Note: auto-pauses after 1 week idle → handled by `supabase-keepalive` cron (§5b).
2. **Cloudflare R2 (D-04, INFRA-07):** create bucket **with jurisdiction = `india`** (NOT just Mumbai PoP — anti-pattern #2). Bucket `ai-coach-meals-prod`. Endpoint = `https://<account_id>.in.r2.cloudflarestorage.com` → `R2_ENDPOINT_URL`. Create scoped API token → `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY`. Lifecycle rule: delete 90 days after soft-delete tombstone (DPDP — see COMPLIANCE-SPEC.md).
3. **Firebase (D-05):** create project, enable Phone auth. Download service-account JSON → mount as Render **Secret File** → `FIREBASE_SERVICE_ACCOUNT_JSON`.
4. **Render (D-01):** create **free web service, region = Singapore**, connect GitHub repo, **root dir = `server/`**, build = `uv sync`, start = `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set all `prod` env vars + secret files from §3. Push-to-deploy from the connected branch. Free service sleeps after 15 min idle (~60s wake) — mitigated by `render-keepalive` cron (§5b).
5. **GitHub repo secrets:** add `EVAL_GEMINI_API_KEY` (eval-only) for `evals.yml`. Enable branch protection on `main` marking the §5a eval jobs as required checks.
6. **AI provider keys:** Google AI Studio (`GEMINI_API_KEY`), Groq (`GROQ_API_KEY`), OpenRouter (`OPENROUTER_API_KEY`), OpenAI (`OPENAI_API_KEY`) — all set as Render secrets. (AI provider routing itself = AI-SPEC §3, not this doc.)

---

## OPEN — needs founder
- **Always-on hosted Phoenix collector for production traces.** AI-SPEC §7 assumed a Fly.io sidecar (superseded by D-01). Whether to (a) run a second Render free service for Phoenix, (b) accept local-only Phoenix + Postgres `ai_call_log` ledger through Phase 2/alpha, or (c) defer hosted Phoenix to the Phase-4 trigger that also lifts Render to paid — is unresolved. Cost gate is unaffected (uses Postgres ledger). Founder picks before Phase-4 alpha.

---

## Cross-references
- `API-SPEC.md` — route contracts incl `/healthz`, `/readyz`, `/uploads/presign`, `/meals/analyze`.
- `COMPLIANCE-SPEC.md` — DPDP region rationale, consent ledger, 30-day hard-delete cron, export (COMP-01..09).
- `01-AI-SPEC.md` — `ai_provider.py`, prompt versioning, eval rubric D1-D12, guardrails G1-G12, monitoring M1-M10, Phoenix (§5/§7).
- `.planning/decisions/2026-05-28-D-01-to-D-19.md` + `...-D-CEO-01-to-03.md` — locked decisions.
- `.planning/research/ARCHITECTURE.md` — topology (superseded-banner items honored: Render not Railway, GitHub-Actions cron not APScheduler).
- `CLAUDE.md` §"no CI/CD until month 4" — updated per §4.
- `TODOS.md` item 5 — EAS Build distribution pipeline (Phase 3 EAS secrets).
