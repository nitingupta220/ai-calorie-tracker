# HANDOFF.md — Bhog Developer Handoff (START HERE)

> **You are a new engineer joining Bhog. Read this file first, top to bottom.** It tells you what the product is, what is already decided, which spec answers which question, the exact order to build Phase 2 in, and the short list of things only the founder can unblock. Everything below is LOCKED unless a line literally says `OPEN — needs founder`.
>
> **Authored:** 2026-05-29 · **Phase context:** Phase 1 (validation gates + stack lock) is the active gating phase; the six domain specs in this folder define Phase 2 (backend spine) + Phase 3 (mobile). The spine can be built in parallel with founder gate-fieldwork.

---

## (a) Product summary + the locked stack

**Bhog** (codename `ai-calorie-weight-loss`) is an AI nutrition + advice app for urban Indian youth (18–30). A user photographs their Indian meal and immediately gets accurate macros plus one specific, budget-aware, veg-protein-gap-closing next action grounded in their own recent log — so they trust the app more than their ₹3,000/mo gym trainer. The wedge is food-photo logging; the moat is Indian-context advice rendered **inline on every meal result**, never as a separate screen. V1 ships as an Android Expo app + FastAPI backend, free-first multi-provider AI, serving muscle-gain (V1) and weight-loss (V1.1) within a single youth persona. Positioned as "trainer replacement at ₹299/mo." Solo bootstrap founder, ~₹0 → ₹1,700/mo budget ceiling, 14-week target to launch.

**Locked stack (authority: `CLAUDE.md`):**

| Layer | Locked choice |
|---|---|
| Mobile | Expo SDK 54 / RN 0.81 (New Arch on) · expo-router ~5 · TanStack Query v5 (server state) + Zustand v5 (client state; Redux banned) · expo-camera / expo-image-manipulator / expo-image-picker · @react-native-firebase/auth 21.x (phone OTP, custom dev client) · expo-notifications + FCM v1 · react-native-mmkv |
| Backend | Python 3.12 · FastAPI 0.128 · Pydantic v2 · SQLAlchemy 2.0 async + asyncpg · Alembic · httpx · Pillow · firebase-admin · tenacity · **uv** (commit `pyproject.toml` + `uv.lock`) |
| Compute | **Render free, Singapore** (D-01 — overrides Fly.io/Railway in older docs; both require a CC, zero-CC is a hard constraint) |
| DB | **Supabase Postgres, Mumbai (`ap-south-1`)** (D-02) — in-country, DPDP residency |
| Object storage | **Cloudflare R2, `jurisdiction=india`** bucket via `<acct>.in.r2.cloudflarestorage.com` (D-04) — not just the Mumbai PoP |
| Auth | **Firebase phone OTP**; the Firebase ID token is the `Bearer` credential directly (D-05) — **no app-minted JWT** |
| AI vision | Gemini **2.5** Flash (free) → OpenRouter Qwen2.5-VL-32B (free) → Gemini paid → GPT-4o-mini paid. **Never Gemini 2.0** (retires 2026-03-03) |
| AI text | Groq Llama-3.3-70B (free) → OpenRouter Llama (free) → Gemini paid |
| Cron | **GitHub Actions scheduled workflows**, NOT in-process APScheduler (Render free sleeps) — D-03, ARCHITECTURE banner |
| Nutrition | IFCT 2017 + `data/dish_decomposition.json` + founder portion table; **macros are deterministic IFCT aggregates, never LLM math** (D-07) |
| Push / Payments | FCM v1 + Expo Push (Phase 3) · Razorpay UPI Autopay (Phase 3+ only) |
| Observability | backend `sentry-sdk[fastapi]` (Phase-2 Wk1) · Arize Phoenix + OpenInference AI tracing · `ai_call_log` Postgres cost ledger |

> **Five superseded-banner overrides you must internalize** (newer docs already honor them; if an older doc disagrees, the override wins): Render not Railway/Fly · Gemini **2.5** not 2.0 · GitHub-Actions cron not APScheduler · **Firebase-ID-token-as-Bearer** not app-JWT · **Zustand + TanStack** not Redux.

---

## (b) Which spec answers which question + canonical-doc map

### The six domain specs (this folder — `.planning/handoff/`)

| If you need to know… | Read | Owns |
|---|---|---|
| The Postgres schema — every table, column, enum, FK, Alembic order, append-only triggers, DPDP cascade topology | **`MODEL-SPEC.md`** | 13-table inventory, native ENUM catalog, hard-delete cascade, append-only enforcement |
| The HTTP contract — routes, request/response Pydantic shapes, error envelope, auth dependency, upload pipeline | **`API-SPEC.md`** | Presign-first upload, frozen error enum, `current_user` dep, Phase-2 route set |
| `ai_provider.py` internals — provider chains, retry/timeout topology, prompts, the PII firewall, cost contract | **`AI-PROVIDER-SPEC.md`** | Vision/text fallback chains, tenacity params, `AdvicePromptContext`, `ai_provider_pricing` |
| Repo structure, uv, secrets matrix, CI/CD, hosting setup, health endpoints, region-pin, local-dev runbook | **`INFRA-OPS-SPEC.md`** | Monorepo layout, secrets matrix, 3 GitHub Actions workflows, `assert_region_pin()` |
| DPDP delete/export/consent behavior, banned-words lint, cross-border disclosure, migration runbook | **`COMPLIANCE-SPEC.md`** | Hard-delete cascade behavior, consent ledger contract, COMP-08 string lint, WhatsApp consent |
| The mobile app — routes, state split, libs, upload/correction/offline pipelines (Phase 3) | **`FRONTEND-HANDOFF.md`** | expo-router layout, TanStack/Zustand split, §8 correction payload contract (the one P2 dependency) |

**Spec dependency direction:** `MODEL-SPEC` is the schema root. `API-SPEC` references tables by name. `AI-PROVIDER-SPEC` is the analyze black box. `COMPLIANCE-SPEC` consumes the consent/delete schema. `INFRA-OPS-SPEC` is where everything runs. `FRONTEND-HANDOFF` consumes API + MODEL + COMPLIANCE contracts. On any conflict, **MODEL-SPEC wins for schema, API-SPEC wins for routes, COMPLIANCE wins for consent enum** — all three are reconciled to agree.

### Canonical docs the specs build on (read for the "why")

| Doc | Path | What it is |
|---|---|---|
| Project charter | `.planning/PROJECT.md` | Persona, value prop, scope discipline, success definition |
| Requirements | `.planning/REQUIREMENTS.md` | 67 REQ-IDs (INFRA-, AUTH-, ONBOARD-, TRACK-, HISTORY-, ADVICE-, RETAIN-, COMP-, ALPHA-, GATE-, LAUNCH-). Specs trace to these |
| Roadmap | `.planning/ROADMAP.md` | Phase 1→5 with per-phase REQ mapping + success criteria. **Phase 2 = the backend spine you build** |
| AI design contract | `.planning/phases/01-validation-gates-stack-lock/01-AI-SPEC.md` | Vision/advice pipeline §3-§7, guardrails G1–G12, rubric, eval harness, Gate 0a/0b pytest, monitoring M1–M10 |
| Decision context | `.planning/phases/01-validation-gates-stack-lock/01-CONTEXT.md` | D-01..D-19 rationale (the engineering decisions) |
| Discussion log | `.planning/phases/01-validation-gates-stack-lock/01-DISCUSSION-LOG.md` | How the decisions were argued (background) |
| Decisions ledger | `.planning/decisions/` — `README.md` (index), `2026-05-28-D-01-to-D-19.md`, `2026-05-28-D-CEO-01-to-03.md` | ADR-lite entries; D-CEO-01/02/03 = WhatsApp pre-install, own-rank streak pill, budget optimizer |
| Design system | `DESIGN.md` (repo root) | Coach Dark tokens, type (Inter + IBM Plex Mono), mascot (Bali), advice-block + disclaimer rendering, locked invariants |
| Open work | `TODOS.md` (repo root) | Outstanding tasks incl. item 5 (EAS Build distribution, Phase 3) |
| Architecture | `.planning/research/ARCHITECTURE.md` | Topology + Patterns 1–6 + Anti-Patterns. **Read its top SUPERSEDED banner** before trusting any line |
| Mockups (web HTML reference only) | `~/.gstack/projects/ai-calorie-weight-loss/designs/00{1..5}-*/finalized.html` | 001 camera · 002 home/today · 003 meal-detail · 004 onboarding · 005 budget-optimizer. **Port layout + tokens, not the HTML** (see FRONTEND-HANDOFF §4, §10) |
| Runtime data | `data/dish_decomposition.json`, `data/ifct_lookup.json`, `data/veg_protein_prices_schema.sql`, `data/photos/` | Move to `server/app/data/` in the first PR (INFRA-OPS §1). `veg_protein_prices_schema.sql` becomes an Alembic migration verbatim |

---

## (c) Recommended BUILD ORDER — Phase 2 backend spine

Phase 2 delivers the photo→macros→advice vertical slice with DPDP plumbing baked in. Build in this order; each step is mergeable and testable on its own. **All steps run independent of founder gate-fieldwork** (section d) — the spine does not wait on the gates; the gates validate the spine.

**Week 1 — baseline migration + skeleton (no AI yet)**
1. **Repo move + scaffold** (INFRA-OPS §1): `git mv data/ → server/app/data/`, keep `evals/` at root, scaffold `server/app/{main,config,deps}.py` + `api/ services/ providers/ schemas/ models/ prompts/ observability/`. Commit `pyproject.toml` + `uv.lock`. Apply the `CLAUDE.md` "no CI/CD" line edit (INFRA-OPS §4).
2. **Config + secrets + region-pin** (INFRA-OPS §3, §6b): `config.py` via `pydantic_settings`; `assert_region_pin()` in lifespan (ABORT BOOT on non-`india` R2 or non-Mumbai Supabase ref) + `test_region_pin.py`. Wire backend Sentry (ENV-tagged).
3. **Alembic baseline migration** (MODEL-SPEC §4, §5, §7): create all 15 native ENUM types first, then the Phase-2 baseline tables `0001`→`0007` — `users, meal_photo, consent_log, correction_event, daily_summary, ai_call_log, provider_quota, vision_cache, veg_protein_prices, consent_audit, ai_provider_pricing, whatsapp_session(stub)`. **`consent_log` and `correction_event` ship append-only with full provenance + wide enums NOW** (DPDP-verifiable / V1.5 corpus replayability). Add the append-only guard trigger with the `app.allow_purge` GUC carve-out. **Do NOT** run `0008 push_event/streak_event` or `0009 weight_log` — those are Phase 3 (and `weight_log` is OPEN).
   - **The seven intra-spec reconciliations (G1–G7) are ALREADY CLOSED in the spec files (2026-05-29) — build directly, no reconciliation work needed.** The locked outcomes are baked into the ENUM/column defs above and recorded in section (2): G1 `consent_type_t` = 8 values `{photo, profile, analytics, ai_training, whatsapp_preinstall, leaderboard, age_18plus, disclaimer_ack}` (consents/acks only; profile fields on `users`, DSR events in `consent_audit`); G3 `ai_call_status_t` uses `fallback_template` (+`timeout`,`aggregate_timeout`); G4 `meal_status_t` includes `analyzing`; G5 `users.is_adult` boolean persisted; G2 `/readyz` uses INFRA-OPS env names; G6 DSR routes = `DELETE /me` + `GET /me/export`; G7 `consent_log` is `ON DELETE SET NULL` (survives PII-stripped). Just implement what the specs now say.
4. **Health + GitHub Actions crons** (INFRA-OPS §5, §6a): `/healthz` (shallow, no DB) + `/readyz` (deep); `evals.yml` merge gate, `cron-keepalive.yml` (D-03 04:30–16:30 UTC window), `cron-price-anomaly.yml`. Enable branch protection.

**Week 1–2 — the spine's load-bearing trio (build in this sub-order)**
5. **`ai_provider.py` abstraction** (AI-PROVIDER-SPEC §1–§8): two `Protocol`s, vision + text fallback chains, shared error mapping (`ProviderRateLimitError`/`ProviderServerError`), per-provider tenacity `stop_after_attempt(2)`, outer-router advance rules, pre-call RPD check vs `provider_quota`, aggregate `wait_for(15s)`, `record_call` → `ai_call_log`, read-time cost via `ai_provider_pricing`. PII firewall = `AdvicePromptContext`. `ruff TID251` bans SDK imports outside `providers/`. Prompt modules with locked shape; literal strings filled from Gate 0a/0b artifacts.
6. **Presign upload + auth** (API-SPEC §1, §3, §5.1): `current_user` dep (Firebase verify per-request + soft-delete 403 + 18+ 403); `POST /uploads/presign` (content-type + ≤600KB + 300s pinned, insert `meal_photo status=pending`); orphan-janitor cron.
7. **Analyze pipeline** (API-SPEC §5.2 + AI-PROVIDER-SPEC §5): `POST /meals/{key}/analyze` → fetch R2 bytes → Pillow validate + **authoritative EXIF strip** + 600KB re-check → vision → deterministic IFCT macro aggregate (Stage 2, no LLM math) ∥ advice (6s timeout, never blocks macros) → persist + `ai_call_log`. `PATCH /meals/{id}` appends `correction_event`; `GET /meals` fixed last-3-day window. Frozen `MealResponse` + error envelope. **Daily-summary copy is descoped to a later P2 increment** (AI-PROVIDER §9) — first increment = vision + inline advice only.

**Week 2–3 — DPDP plumbing (COMPLIANCE-SPEC)**
8. **DSR endpoints + purge** (COMPLIANCE §4, §5; API-SPEC §5.5, §5.6): `DELETE /me` soft-delete + `delete_requested` ledger row + 403 lockout; `/internal/compliance/purge` (token-gated, idempotent, R2-first then ordered child→parent deletes, `consent_log` PII-strip-not-delete, `consent_audit` receipt); `GET /me/export` inline JSON; `dpdp-purge.yml` (22:00 UTC) + 24h WhatsApp-TTL step; `test_hard_delete.py` 31-day-backdate fixture. Disclaimer + banned-words constants modules; COMP-08 string-lint CI step. Author `dpdp-migration-runbook.md`.

**Week 3 — evals wired (close the loop)**
9. **Eval gate green** (AI-SPEC §5; INFRA-OPS §5a): `gate_0a_vision.py` + `gate_0b_advice.py` + promptfoo + `ruff TID251` + PII lint (G11/M10 = 0) all required checks on the eval-path-filter. This is where the founder's Gate 0a/0b artifacts (section d) plug into the spine you built.

> **Phase-2 exit = ROADMAP Phase 2 success criteria** (photo→macros→inline-advice in 8s P95 single response; 50-dish whitelist + IFCT decomposition; 4/4 rubric gate + 429-fallback verified; DPDP boot check + consent/correction/soft-delete live + hard-delete cron green; Firebase OTP verify + delete-my-data with audit). Mobile (FRONTEND-HANDOFF) starts at the Phase 2→3 boundary.

---

## (d) WHAT THE FOUNDER STILL OWES — gate fieldwork (parallel to the spine)

These gate Phase-1 validation and unblock the *content* the spine consumes (prompt strings, the 50 dishes, the API key). **They do NOT block building the spine** — the architecture, schema, routes, chains, and DPDP plumbing are all locked and buildable today. They are founder-only because they require real photos, real users, real labeling judgment, and account ownership. (Per the brief, these are fieldwork, not technical gaps.)

| Gate | Founder owes | Unblocks |
|---|---|---|
| **Gate 0a** (vision accuracy) | Verify `data/dish_decomposition.json` → v1.0 (founder confirms grams per the D-08 cascade) · 30 stratified meal photos (10 single / 10 mixed / 10 thali, D-09) · obtain the production **Gemini API key**. ≥70% dish-name match + ≥60% macros within ±35% per bucket | Final 50-slug ordering + vision system-prompt strings (AI-PROVIDER §6, §13); `gate_0a_vision.py` green; the live vision link |
| **Gate 0b** (advice quality) | Run 14 days of own meals through the pipeline; produce the **4/4 advice rubric WoZ corpus**; ≥70% of replies score 4/4 (specific food + quantity + ₹ cost + log reference) | Advice system-prompt + 3 few-shot strings + `advice_v1_strict` retry wording (AI-PROVIDER §6); `gate_0b_advice.py` green |
| **Gate 0c** (demand) | 20 named Trial Users on WhatsApp · ≥10 verbal commitments · **≥3 verbatim price/WTP quotes** | Phase 4 alpha recruitment; pricing validation (no code dependency) |
| **Gate 0d** (distribution) | Purchase **Google Play Developer account** ($25) + submit identity verification (3–7 day clock — start before Phase 2 ends) | Phase 4 Play Internal Testing + Production submission |

**Also founder-confirm before the relevant phase (technical defaults already chosen, so non-blocking):** OpenRouter free-tier RPD ceiling (50 vs 1000 — default 50 ships safe) · email transport for export/delete (Resend recommended) · WhatsApp consent posture (YES-gate recommended) · `weight_log` table shape (standalone proposed) · hosted Phoenix for prod traces (Phase-4 decision). See section (2) for why none of these block Phase 2.

---

## (e) Colleague onboarding checklist

Work top to bottom. Steps 1–4 are reading; 5–8 are hands-on; 9 onward is building.

1. **Read this file** (HANDOFF.md) fully — you are here.
2. **Read `.planning/PROJECT.md` + `.planning/REQUIREMENTS.md` + `.planning/ROADMAP.md` Phase 2** — the what and the why; note the REQ-IDs Phase 2 owns.
3. **Read the SUPERSEDED banner in `.planning/research/ARCHITECTURE.md`** — internalize the five overrides (Render / Gemini 2.5 / GH-Actions cron / Firebase-Bearer / Zustand+TanStack) so older lines don't mislead you.
4. **Read the six specs in dependency order:** `MODEL-SPEC` → `API-SPEC` → `AI-PROVIDER-SPEC` → `COMPLIANCE-SPEC` → `INFRA-OPS-SPEC` → `FRONTEND-HANDOFF` (last; it's Phase 3). Skim the decisions ledger for any D-ID a spec leans on.
5. **Skim `01-AI-SPEC.md` §3–§7** (the AI pipeline contract the AI-PROVIDER-SPEC operationalizes) and `DESIGN.md` (tokens + invariants).
6. **Provision the no-CC stack** (INFRA-OPS §9, in order): Supabase Mumbai → R2 `india` bucket → Firebase project → Render free Singapore (root dir `server/`) → GitHub repo secrets + branch protection → AI provider keys.
7. **Run the local-dev runbook** (INFRA-OPS §8): `uv sync` → `cp .env.example .env` → `uv run alembic upgrade head` → `uv run uvicorn app.main:app --reload` → `curl /healthz`. A wrong R2/Supabase ref aborting boot is *expected* — that's the region pin working.
8. **Confirm with the founder** which Gate 0a/0b artifacts (section d) are ready, so you know whether you're filling prompt strings now or stubbing them.
9. **Start the Phase-2 build order** (section c) — first PR = repo-move + scaffold + Alembic baseline (incl. append-only `correction_event` + `consent_log`). Open a PR per build-order step; the `evals.yml` gate must stay green.

---

## (2) COMPLETENESS CRITIC — is any during-Phase-2 decision still undocumented?

**Verdict: HANDOFF-READY.** A competent backend engineer can start and complete the Phase-2 spine today without asking the founder a single *technical* question. Every during-phase-2 decision surfaced by the audit is locked in one of the six specs; the only remaining items are (i) founder *fieldwork* for the gates (not technical gaps, explicitly excluded by the brief) and (ii) a small set of decisions with safe, documented defaults whose resolution is non-blocking for Phase 2. Detail follows; this critic section is reproduced as structured output.

### Reconciliation checks I ran across the six specs (all PASS)

- **`correction_event` payload (the one cross-team contract):** API-SPEC §5.3 PATCH body ⊆ MODEL-SPEC §3.3 columns ⊆ FRONTEND-HANDOFF §8 mutation shape. All three agree (`dish_name`, `portion_g`, `macros{kcal,protein_g,carbs_g,fat_g}`), append-only, MODEL-SPEC named the canonical source on field-name conflict. **Closed.**
- **`consent_type` enum:** COMPLIANCE §3.1 (12 values: 8 onboarding toggles + 4 system events) vs MODEL-SPEC §3.2/§4 (`consent_type_t` 7 values). **See gap G1 below — this is the one real naming divergence.**
- **Auth model:** API-SPEC §1 (Firebase-ID-as-Bearer, implicit lazy-create, no app-JWT) = FRONTEND-HANDOFF §1 = AI-PROVIDER honored. **Consistent.**
- **Cron strategy:** orphan-janitor (API), keepalive/price-anomaly (INFRA), dpdp-purge + 24h-WhatsApp (COMPLIANCE) all GitHub Actions, not APScheduler. **Consistent.**
- **Region pin:** API-SPEC §5.8 `/readyz` checks ≈ INFRA-OPS §6b `assert_region_pin()` ≈ COMPLIANCE §7. **See gap G2 — a cosmetic field-name drift, not a behavior gap.**
- **`ai_call_log` status enum + `aggregate_timeout`:** MODEL-SPEC §3.6/§4 vs AI-PROVIDER §5. **See gap G3 — a literal-string drift the dev must reconcile, both specs flag it.**
- **DSR user-facing route paths:** API-SPEC §4/§5.5/§5.6 (`DELETE /me`, `GET /me/export`) vs COMPLIANCE §4.1/§5.1/§9 (`POST /compliance/delete`, `POST /compliance/export`). **See gap G6 — a real route divergence, not cosmetic; resolved by the "API-SPEC wins for routes" rule. The internal cron endpoint `/internal/compliance/purge` is consistent across both.**

### Reconciliations G1–G7 — RESOLVED 2026-05-29 (closed in the spec files, not deferred)

The completeness critic surfaced 7 intra-spec divergences. **All are now reconciled and written into the spec files** (no longer "dev closes in PR-1"). Locked outcomes:

- **G1 — `consent_type` enum (DPDP never-widen).** RESOLVED: `consent_type_t` = **8 values** `{photo, profile, analytics, ai_training, whatsapp_preinstall, leaderboard, age_18plus, disclaimer_ack}` (MODEL-SPEC §3.2/§4; COMPLIANCE §3.1 rewritten to match). `consent_log` holds **consents/acknowledgements only**, `action ∈ {grant, revoke}`. Profile fields (`budget_bucket/diet_preference/goal`) are NOT consents — they live on `users` under the single `profile` consent. DSR events (`delete_requested/export_generated/hard_deleted`) are NOT consents — they go to `consent_audit.event_type` (`audit_event_t`). Onboarding subset = `{photo, profile, analytics, ai_training, age_18plus, disclaimer_ack}`.
- **G2 — `/readyz` region env names.** RESOLVED: canonical = INFRA-OPS `R2_ENDPOINT_URL` + `SUPABASE_PROJECT_REF` + `ALLOWED_SUPABASE_REFS`; COMPLIANCE §7 rewritten to use them.
- **G3 — `ai_call_log.status` literal.** RESOLVED: `ai_call_status_t` = `{ok, rate_limited, server_error, validation_error, timeout, aggregate_timeout, fallback_template}` (7); MODEL renamed `fallback_used`→`fallback_template` to match AI-PROVIDER §5; `timeout` (single-provider) + `aggregate_timeout` (pipeline) both kept.
- **G4 — `meal_photo.status`.** RESOLVED: `meal_status_t` = `{pending, analyzing, done, failed}` (`analyzing` added to MODEL §3.4/§4 to match API-SPEC; also lets the orphan janitor distinguish crashed-mid-analyze from never-analyzed).
- **G5 — `users.is_adult`.** RESOLVED: `is_adult BOOLEAN NOT NULL` persisted on `users` (MODEL §3.1), computed from DOB at signup; `current_user` reads the stored verdict (matches API-SPEC §1 step 5).
- **G6 — DSR routes.** RESOLVED: user-facing = **`DELETE /me`** + **`GET /me/export`** (API-SPEC owns routes); COMPLIANCE §4.1/§5.1 rewritten to reference them; `/internal/compliance/purge` stays the internal cron endpoint.
- **G7 — `consent_log` hard-delete behavior (found during reconciliation).** RESOLVED: `consent_log.user_id` is **`ON DELETE SET NULL`** (NOT cascade) so the row survives PII-stripped — `user_id_hash` (written at INSERT) is the retained DPDP §6 consent proof. Fixes MODEL's earlier internal §3.2-vs-§6 contradiction; cascade design reconciled across MODEL §6 + COMPLIANCE §4.3 (explicit ordered service deletes, R2-first, CASCADE children + SET NULL consent_log/ai_call_log; the earlier `ON DELETE RESTRICT` + `audit_event`-table proposal is superseded).

**No during-phase-2 decision is left to founder judgment, and no intra-spec divergence remains open.** The audit's during-phase-2 surface (provider chains, retry/timeout, schema, cascade, consent ledger, region pin, error envelope, upload pipeline, cost contract, eval gate) is fully covered and self-consistent across the six specs. The dev builds directly from the specs as written.

### Genuinely still-open items that are correctly deferred (NOT Phase-2 technical gaps)

These are explicitly defaulted in their specs and either land after Phase 2 or carry a safe ship-now default — listing them so nothing is silently dropped:

- OpenRouter free-tier RPD ceiling 50 vs 1000 (AI-PROVIDER §13) — default 50 ships safe.
- Paid Gemini/Groq exact ₹/Mtok rows (AI-PROVIDER §8) — free-tier path rows are 0 and complete; fill at first paid burst.
- Email transport for export + delete confirmation (COMPLIANCE §5.3) — Resend recommended; coded behind `EmailTransport` Protocol; export returns inline JSON in V1 regardless.
- WhatsApp consent posture YES-gate vs footer-only (COMPLIANCE §2.1) — Phase 4 wire; stub-only in Phase 2.
- Fresh-OTP re-auth on delete (COMPLIANCE §4.1 / API §5.5) — default = any valid Bearer.
- Export allowed during the 30-day delete window (API §5.6) — default = allow until hard-delete.
- `weight_log` table shape (MODEL §3.14) — Phase 3, standalone-table default proposed.
- Hosted Phoenix for production traces (INFRA-OPS §9) — Phase-4 decision; cost gate uses the Postgres ledger meanwhile.
- `POST /auth/verify` explicit handshake, thumbnail presigned-GET, founder RBAC beyond env allowlist (API §7) — all Phase-3+ or defaulted.

These are the founder/later-gate items; none gate a competent dev from completing the Phase-2 spine.
