# AI-PROVIDER-SPEC — Bhog (Phase 2 Backend Spine)

**Domain:** the `ai_provider.py` abstraction + prompt files + cost contract.
**Audience:** fresh engineer building Phase 2 with zero prior context. Every decision below is LOCKED. Build from it without asking.
**Last locked:** 2026-05-29.

**What this doc owns:** provider routing/fallback, per-provider retry, timeout topology, prompt files, the PII firewall (`AdvicePromptContext`), the cost/pricing contract, and the eval-only decomposition/alias data shapes.
**What this doc does NOT own (cross-linked):**
- DB table DDL (`ai_call_log`, `provider_quota`, `vision_cache`, `ai_provider_pricing`) → see **MODEL-SPEC.md**.
- HTTP route `POST /meals/analyze`, request/response envelopes, R2 presigned flow → see **API-SPEC.md**.
- The 4/4 rubric validator internals + guardrail wiring (G1–G12) → see AI-SPEC §6 (`.planning/phases/01-validation-gates-stack-lock/01-AI-SPEC.md`).
- Eval harness / Gate 0a+0b pytest scripts → see AI-SPEC §5.

**Source priority honored:** `CLAUDE.md` > `01-CONTEXT.md` (D-01..D-19) > `.planning/decisions/*` (incl. D-CEO-01..03) > `01-AI-SPEC.md` > `REQUIREMENTS.md` > `research/ARCHITECTURE.md` (superseded-banner items honored: Render not Railway; Gemini **2.5** not 2.0; GitHub-Actions cron not APScheduler; Firebase-ID-as-Bearer not app-JWT; Zustand+TanStack not Redux).

---

## 0. Decision Index (this doc → source)

| # | Decision (locked here) | Traces to |
|---|---|---|
| AP-01 | Two `Protocol`s: `VisionProvider`, `TextProvider`. SDK imports allowed ONLY under `providers/`. | INFRA-01; AI-SPEC §2,§3 |
| AP-02 | Vision fallback chain (4 links) + Text fallback chain (3 links), exact order. | INFRA-02, INFRA-03; CLAUDE.md routing block |
| AP-03 | Each provider file maps SDK errors to the SAME pair: `RateLimitError`, `ServerError`. | AI-SPEC §4 (line 446); audit blocker |
| AP-04 | Per-provider tenacity: `stop_after_attempt(2)`, `wait_exponential_jitter(0.5,4.0)`, `reraise=True`. Retries on `ServerError` + `ValidationError` ONLY. | AI-SPEC §3 line 278 (typo fixed 2026-05-29), §4 |
| AP-05 | Outer router walks the chain on `RateLimitError` OR exhausted-`ValidationError` only. NOT on `ServerError` (retried in-provider). | AI-SPEC §4b retry-logic; audit |
| AP-06 | Pre-call RPD check skips a provider at its daily ceiling (`provider_quota`). | AI-SPEC §4 State Mgmt; INFRA-04 |
| AP-07 | ONE aggregate `asyncio.wait_for` (~15s) wraps the whole vision+advice chain → status `'aggregate_timeout'`. | audit; AI-SPEC §4b latency |
| AP-08 | `ai_provider_pricing` table; cost computed at READ-TIME; `record_call` always passes `model`. | AI-SPEC §4b telemetry; D11/M3 |
| AP-09 | Budget = MONITORING-ONLY for V1 (alert at ≤₹15/user/mo). No runtime circuit-breaker. | D11, M3; audit |
| AP-10 | Prompt files `vision_v1.py`, `advice_v1.py`, `advice_v1_strict.py`; zero-shot vision, whitelist-embedded, temp 0.1/0.4; literal strings open until Gate 0a/0b. | ADVICE-04; AI-SPEC §4,§4b |
| AP-11 | `AdvicePromptContext` dataclass = the PII firewall (DPDP). | COMP-09; AI-SPEC §1 FM#3, §4b, G11 |
| AP-12 | Advice OUTPUT language = English + roman-script Indian terms. | AI-SPEC §6 G6/G7; this doc §6 |
| AP-13 | `dish_decomposition.json` = `{slug:[{ifct_code,grams_per_serving}]}`; `dish_aliases.json` = `{alias:slug}` EVAL-ONLY (no runtime fuzzy match). | D-07, D-08, TRACK-10; AI-SPEC §5 D1 |
| AP-14 | Daily-summary copy = DESCOPED to a later Phase-2 increment. | this doc §9 |
| AP-15 | Opus 4.7 ground-truth labeling prompt (Gate 0a), adapted from AI-SPEC §3 Appendix. | D-06, D-10; this doc §10 |

---

## 1. Module layout (LOCKED)

Build exactly this. `providers/` is the ONLY directory where AI SDK module imports may appear; everything else is lint-banned (`ruff --select TID251` banned-module-imports). This operationalizes INFRA-01 + AI-SPEC §1 Failure Mode #4.

```
server/app/
├── providers/                     # ← ONLY place SDK imports live (ruff-enforced)
│   ├── ai_provider.py             # Protocols + outer router + chain definitions
│   ├── errors.py                  # ProviderRateLimitError, ProviderServerError (shared)
│   ├── vision_gemini.py           # google-genai  — vision primary (free)
│   ├── vision_openrouter.py       # AsyncOpenAI @ openrouter — vision fallback 1 (free)
│   ├── vision_gemini_paid.py      # google-genai  — vision fallback 2 (paid)
│   ├── vision_gpt4o.py            # AsyncOpenAI (OpenAI) — vision fallback 3 (paid, last resort)
│   ├── text_groq.py               # AsyncGroq — text primary (free)
│   ├── text_openrouter.py         # AsyncOpenAI @ openrouter — text fallback 1 (free)
│   ├── text_gemini_paid.py        # google-genai text-only — text fallback 2 (paid)
│   └── dev/text_ollama.py         # DEV ONLY — lint-banned in prod import paths
├── prompts/
│   ├── vision_v1.py               # VERSION="v1"; build() -> (system, user)
│   ├── advice_v1.py               # VERSION="v1"; build(ctx: AdvicePromptContext) -> (system, user)
│   └── advice_v1_strict.py        # VERSION="v1-strict"; G5/G6 retry prompt
├── schemas/
│   ├── vision.py                  # VisionResult, DishItem, DishName Literal
│   ├── advice.py                  # Advice
│   └── advice_context.py          # AdvicePromptContext dataclass (PII firewall)
└── observability/
    └── cost_log.py                # record_call(...) — see §8
```

`prompts/*` each export a top-level `VERSION: str` constant + a `build(...)` function. The `VERSION` string is written into every `ai_call_log.prompt_version` row so a prompt regression on a Gate re-run is attributable to the exact version that changed (AI-SPEC §4b prompt-versioning). **Note:** ADVICE-04 originally named `prompts/advice_v0.json`; the format is now a versioned `.py` module — `advice_v1.py` supersedes the `.json` filename. REQ intent (semver prompt, version recorded per advice) is satisfied.

**Dev-iteration provider** (`dev/text_ollama.py`, `qwen2.5:7b`/`llama3.1:8b`) is gated by `settings.ENV == "dev"` AND a ruff rule (`--select TID252`) banning `from ollama import ...` outside `providers/dev/`. Ollama at `localhost:11434` does not exist on Render — importing it in a prod path hangs on `httpx.ConnectError` (AI-SPEC §3 pitfall 8). NEVER ship Ollama user-facing.

---

## 2. Provider chains (LOCKED — verbatim from CLAUDE.md routing block + INFRA-02/03)

**Vision chain** (`POST /meals/analyze` Stage 1):

| Link | File | Provider | Model ID | Tier | Skip-if |
|---|---|---|---|---|---|
| 1 | `vision_gemini.py` | Google AI Studio | `gemini-2.5-flash` | free | RPD ≥ ceiling |
| 2 | `vision_openrouter.py` | OpenRouter | `qwen/qwen2.5-vl-32b-instruct:free` | free | RPD ≥ ceiling |
| 3 | `vision_gemini_paid.py` | Google AI Studio | `gemini-2.5-flash` | paid | — |
| 4 | `vision_gpt4o.py` | OpenAI | `gpt-4o-mini` | paid (last resort) | — |

**Text/advice chain** (Stage 3):

| Link | File | Provider | Model ID | Tier | Skip-if |
|---|---|---|---|---|---|
| 1 | `text_groq.py` | Groq | `llama-3.3-70b-versatile` | free | RPD ≥ ceiling |
| 2 | `text_openrouter.py` | OpenRouter | `meta-llama/llama-3.3-70b-instruct:free` | free | RPD ≥ ceiling |
| 3 | `text_gemini_paid.py` | Google AI Studio | `gemini-2.5-flash` (text-only) | paid | — |

**Model config** (LOCKED, from AI-SPEC §4 table — do not freelance):

| Stage | temperature | max output tokens | structured-output mechanism |
|---|---|---|---|
| Vision (all 4 links) | `0.1` | `512` | Gemini: `response_mime_type='application/json'` + `response_schema=VisionResult`, `top_p=0.95`. OpenRouter Qwen: `response_format={"type":"json_object"}`. GPT-4o-mini: `response_format={"type":"json_schema","json_schema":...}`. |
| Advice (all 3 links) | `0.4` | `200` | Groq + OpenRouter Llama: `response_format={"type":"json_object"}` + prompt MUST contain literal "JSON". Gemini paid: `response_schema=Advice`. |

`max_*tokens` is ALWAYS set on every call — unbounded = unbounded INR. Lint: provider files flagged if the token-cap kwarg is missing.

**Provider switch is env-driven, not code (Anti-Pattern #18):** `AI_PROVIDER_VISION_PRIMARY` / `AI_PROVIDER_TEXT_PRIMARY` env vars select the head of each chain; the rest of the chain order is fixed. Config flag, not edit.

---

## 3. Error mapping contract (AP-03 — LOCKED)

Every provider file maps its SDK's raw exceptions to the SAME two shared types in `providers/errors.py`. This is what lets the outer router stay provider-agnostic.

```python
# server/app/providers/errors.py
class ProviderRateLimitError(Exception):
    """Mapped from any provider 429 / quota-exhausted. → outer router advances the chain."""
class ProviderServerError(Exception):
    """Mapped from any provider 5xx / transient transport. → retried IN-provider, never advances chain."""
```

Mapping table each provider file MUST implement (in its `except` block):

| Raw SDK signal | Mapped to | Who handles it |
|---|---|---|
| HTTP 429 / RESOURCE_EXHAUSTED / rate-limit | `ProviderRateLimitError` | **outer router** → next chain link |
| HTTP 5xx / timeout / connection reset | `ProviderServerError` | **in-provider tenacity** (retry once) |
| `pydantic.ValidationError` (schema miss) | re-raised as-is | **in-provider tenacity** (retry once); if exhausted → **outer router** → next link |
| HTTP 4xx other than 429 (e.g. 400 bad request) | re-raised as-is | bubbles up — this is a code bug, not a fallback case; fail loud |

> Implementation note: read `status_code` defensively — `code = getattr(e, "status_code", None) or 0`. Gemini surfaces 429 as `RESOURCE_EXHAUSTED`; map both the numeric 429 and that string token.

---

## 4. Per-provider retry (AP-04 — LOCKED, the line-278 fix)

Inside each provider file, wrap the single SDK call in a tenacity `AsyncRetrying` loop with EXACTLY these params:

```python
async for attempt in AsyncRetrying(
    stop=stop_after_attempt(2),                                  # 1 try + 1 retry — NOT 3
    wait=wait_exponential_jitter(initial=0.5, max=4.0),
    retry=retry_if_exception_type((ProviderServerError, ValidationError)),
    reraise=True,                                                # original exc, not RetryError
):
    with attempt:
        ...  # SDK call → map errors → Pydantic validate → record_call
```

- `stop_after_attempt(2)` is the corrected value (AI-SPEC §3 line 278 typo "3" → "2", fixed 2026-05-29 per decision-audit blocker #1). It matches the §4b prose "single retry → fallback". **Do not set 3.**
- `retry` set covers `ProviderServerError` (5xx) and `ValidationError` (schema miss) — retry the SAME provider for these.
- `ProviderRateLimitError` is NOT in the retry set → it escapes immediately to the outer router.
- `reraise=True` is mandatory so the outer router sees the real exception type, not tenacity's `RetryError` wrapper (AI-SPEC §3 pitfall 6).

---

## 5. Outer router (AP-05, AP-06, AP-07 — LOCKED)

`ai_provider.py` exposes two singletons satisfying the Protocols:

```python
class VisionProvider(Protocol):
    name: str
    async def identify(self, *, image_bytes: bytes) -> VisionResult: ...

class TextProvider(Protocol):
    name: str
    async def generate_advice(self, *, ctx: AdvicePromptContext) -> Advice: ...
```

**Router algorithm (both chains, identical shape):**

```
for link in CHAIN:                      # ordered list from §2
    if rpd_at_ceiling(link.provider):   # AP-06 — pre-call quota check, see below
        continue                        # skip silently; log skip reason
    try:
        result = await link.call(...)   # per-provider tenacity loop runs inside
        increment_rpd(link.provider)    # on success only
        return result
    except ProviderRateLimitError:
        continue                        # AP-05 — advance chain
    except ValidationError:
        continue                        # AP-05 — in-provider retry already exhausted → advance
    except ProviderServerError:
        raise                           # AP-05 — 5xx is in-provider's job; do NOT advance
# chain exhausted:
#   vision  → raise VisionUnavailable  → API returns HTTP 502 (see API-SPEC.md)
#   advice  → caller catches → Advice.fallback_for(dish) template (NEVER blocks macros)
```

**Advance-chain ONLY on `ProviderRateLimitError` OR exhausted-`ValidationError`.** `ProviderServerError` does NOT advance — it is the in-provider tenacity loop's responsibility, and if that loop exhausts it re-raises a 5xx which the router lets bubble (a 5xx storm across all providers is an incident, not a routine fallback).

**AP-06 pre-call RPD check:** before calling a link, read `provider_quota` (row keyed `(provider, date)`; schema in MODEL-SPEC.md) and compare `rpd_consumed` against the provider's ceiling:

| Provider | RPD ceiling (free) | Source |
|---|---|---|
| `gemini_2_5_flash_free` | 500 | CLAUDE.md / Gemini rate-limits 2026 |
| `openrouter_*_free` | 1000 (≥$10 credit) / 50 (<$10) — configure per account; default 50 conservative | CLAUDE.md |
| `groq_llama_3_3_70b_free` | 1000 | CLAUDE.md / Groq rate-limits |

At ceiling → `continue` (skip the link, advance to next). Increment `rpd_consumed` on success ONLY. Reset daily (date key rolls). No Redis at Phase 1 scale (100 users) — single Postgres row read/increment is fine; revisit at Phase 3 if contention surfaces (AI-SPEC §4 State Mgmt). Per-minute RPM is NOT pre-checked in V1 — 429 from RPM bursts is handled reactively by `ProviderRateLimitError` → chain advance.

**AP-07 aggregate timeout (single source of truth for "too slow"):** wrap the ENTIRE vision→gather(macros,advice) sequence in ONE `asyncio.wait_for(..., timeout=AGGREGATE_TIMEOUT_S)` where `AGGREGATE_TIMEOUT_S = 15.0`. On `asyncio.TimeoutError`:
- write an `ai_call_log` row with `status='aggregate_timeout'` (this exact literal — MODEL-SPEC.md enumerates it),
- return macros-if-ready + `Advice.fallback_for(...)`; if vision itself didn't finish → HTTP 502 `{"error":"vision_unavailable","retry_after":30}` (API-SPEC.md).

This 15s aggregate cap sits ABOVE the per-stage soft timeouts kept from AI-SPEC §4 (`VISION_TIMEOUT_S=5.0`, `ADVICE_TIMEOUT_S=6.0`). Per-stage timeouts give clean fallback boundaries; the aggregate cap is the hard ceiling that protects the 8s-P95 SLA from a pathological multi-fallback tail (worst case 5s vision + 6s advice + fallback hops). The 8s P95 target (TRACK-08, D12) holds because Stage 2+3 run in parallel and the long multi-hop tail is rare.

**`status` enum written to `ai_call_log`** (LOCKED set; MODEL-SPEC.md §4 `ai_call_status_t` owns the column — must match exactly): `ok`, `validation_error`, `rate_limited`, `server_error`, `timeout` (single-provider call timeout), `aggregate_timeout` (whole-pipeline `wait_for` cap, AP-07), `fallback_template` (advice fell back to template). 7 values. G3 reconciliation 2026-05-29: this is the canonical set; MODEL renamed its earlier `fallback_used` → `fallback_template` to match this literal.

---

## 6. Prompt files (AP-10, AP-12 — strategy LOCKED, literal strings OPEN until Gate)

Strategy is locked; only the literal prompt text is open and gets finalized at Gate 0a (vision) and Gate 0b WoZ corpus (advice). Engineer: build the modules with the locked shape; fill strings from the Gate artifacts.

### `prompts/vision_v1.py`
- `VERSION = "v1"`.
- `build() -> tuple[str, str]` returns `(system_prompt, user_prompt)`. No per-user data (vision is image-only).
- **Strategy LOCKED:** zero-shot (no in-context examples — the 50-dish `DishName` Literal IS the constraint; few-shot bloats tokens with no measured Gate 0a gain, AI-SPEC §4b). 50-dish whitelist embedded at build time (~600 tokens, static). Temperature `0.1`.
- User prompt ≈ "What dish is this? Estimate portion in grams. Output JSON matching schema." (~50 tokens).
- **OPEN — finalized at Gate 0a:** exact whitelist slug ordering + exact system wording. The 50 dishes are enumerated in TRACK-06; slugify to snake_case for the `DishName` Literal.

### `prompts/advice_v1.py`
- `VERSION = "v1"`.
- `build(ctx: AdvicePromptContext) -> tuple[str, str]`. The ONLY accepted input type is `AdvicePromptContext` (§7) — this is the PII firewall.
- **Strategy LOCKED:** system prompt = role + invariants + "Respond with valid JSON matching this schema:" preamble + the 4 rubric requirements (R1 specific food, R2 quantity, R3 ₹ cost, R4 log-ref). Temperature `0.4`. Per AI-SPEC §4b "Advice: 3 inline few-shot examples" — 3 static rubric-pattern examples baked in, sourced from the Gate 0b WoZ corpus.
- **OUTPUT language LOCKED (AP-12):** advice text is **English with roman-script Indian food terms** ("Add 50g paneer", "1 katori dal", "2 roti"). NOT Devanagari, NOT Hinglish sentences. Rationale: the G6 (CDSCO banned-words) and G7 (cultural-fit banned-foods) regex guardrails are English-token regexes (AI-SPEC §6) — emitting non-English advice text would blind those guardrails. Roman-script Indian nouns (paneer/dal/chana/sattu/katori) are fine; they are not in any banned set. (The cold-start UX *banner* copy in D-03b is Hinglish — that is mobile-side UI string, NOT advice-engine output; different surface, out of scope here.)
- **OPEN — finalized at Gate 0b WoZ corpus:** the 3 few-shot example strings + exact system wording.

### `prompts/advice_v1_strict.py`
- `VERSION = "v1-strict"`.
- Used by the G5/G6 single-retry path: when the 4/4 rubric validator OR banned-words regex rejects the first advice, regenerate with this prompt which appends "your previous response missed rubric R{N} / contained banned token {X}; regenerate satisfying all constraints." (AI-SPEC §6 G5, G6).
- Same `AdvicePromptContext` input; same language rule (AP-12).
- **OPEN — finalized alongside `advice_v1.py`** at Gate 0b.

> Banned-words regexes themselves (G6 medical, G7 cultural, G8 diet, G9 goal-directional) live in `services/advice_engine.py` / `advice_rubric.py`, NOT in the prompt files — see AI-SPEC §6 and (validator internals) the advice-engine spec. This doc only fixes that advice OUTPUT stays English so those regexes remain sound.

---

## 7. `AdvicePromptContext` — the PII firewall (AP-11 — LOCKED)

This typed dataclass is the structural DPDP guarantee (COMP-09; AI-SPEC §1 Failure Mode #3; G11). `build_advice_prompt` accepts ONLY this type — `name`, `phone`, `exact_dob`, `email` are NOT fields on it, so the type system makes leaking them a compile-time impossibility. A ruff custom rule (`gsd-no-pii-in-advice-prompt`, G11) additionally bans the substrings `user.name`, `user.phone`, `user.date_of_birth`, `user.email` anywhere under `services/advice_*`, `prompts/advice_*`, `providers/text_*` — CI-blocking, target M10 = 0 violations.

```python
# server/app/schemas/advice_context.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

DietPreference = Literal["veg", "non_veg", "vegan", "egg_veg", "lactose_intolerant"]
Goal = Literal["muscle_gain"]                 # V1 only; weight_loss is V1.1 (out of scope)
BudgetBucket = Literal["100_150", "150_250", "250_plus"]   # ONBOARD-01 buckets

@dataclass(frozen=True)
class MealLogRow:
    # one row of the last-3-day SQL log; NO photo URL, NO free-text, NO PII
    date_iso: str                  # "2026-05-26"
    meal_slot: Literal["breakfast", "lunch", "dinner", "snack"]
    dish_slug: str                 # from DishName Literal
    portion_g: int
    kcal: int
    protein_g: int
    carbs_g: int
    fat_g: int

@dataclass(frozen=True)
class VegProteinRef:
    # pulled from veg_protein_prices table (D-17); global-avg in V1 (per-region V1.5)
    food_name: str
    protein_per_100g: float
    cost_per_g_protein_inr: float

@dataclass(frozen=True)
class AdvicePromptContext:
    # ── identity: DE-IDENTIFIED ONLY ──
    de_identified_user_id: str          # opaque user_id; never the phone-derived id
    # ── goal + targets (ONBOARD-02) ──
    goal: Goal
    target_kcal: int
    target_protein_g: int               # ISSN 1.8 g/kg default
    diet_preference: DietPreference
    budget_bucket: BudgetBucket
    budget_remaining_today_inr: int     # for D6 budget-fit check
    # ── current meal (from VisionResult) ──
    current_dish_slug: str
    current_kcal: int
    current_protein_g: int
    # ── day-so-far totals ──
    day_kcal_so_far: int
    day_protein_so_far: int
    # ── last-3-day log (SQL LIMIT 9; AI-SPEC §4b) ──
    recent_log: list[MealLogRow]
    # ── ₹/g veg-protein reference (ADVICE-02, ADVICE-05) ──
    veg_protein_ref: list[VegProteinRef]
```

**FORBIDDEN fields (never add):** `name`, `phone`, `email`, `date_of_birth`, raw `firebase_uid`, photo URL, free-text health notes. Pass age only as `goal`/`target_*` are derived server-side BEFORE building the context — the LLM never sees DOB. `recent_log` is built from `SELECT ... FROM meal_photo WHERE user_id=? AND created_at > now()-interval '3 days' LIMIT 9` (bounded by SQL, not token-counting; AI-SPEC §4b). This is NOT RAG — no embeddings, no vector store.

---

## 8. Cost + pricing contract (AP-08, AP-09 — LOCKED)

### `record_call` (every provider call writes one row)
LOCKED signature change from AI-SPEC §4b: `model` is **required** (drop the `model=None` default) so cost can always be computed at read-time.

```python
# server/app/observability/cost_log.py
async def record_call(
    *, provider: str, model: str,            # model REQUIRED (was =None — AP-08)
    prompt_version: str, latency_ms: int,
    input_tokens: int, output_tokens: int,
    status: str = "ok",                      # enum: §5 status set
) -> None:
    # INSERT one row into ai_call_log. Cost is NOT stored — computed at READ-TIME
    # by joining ai_provider_pricing (so historical re-pricing stays correct). MODEL-SPEC.md owns DDL.
    ...
```

### `ai_provider_pricing` table (NEW — AP-08; DDL in MODEL-SPEC.md)
Columns: `provider`, `model`, `price_in_per_mtok_inr`, `price_out_per_mtok_inr`, `effective_from` (date). Cost is computed at READ-TIME by joining `ai_call_log` to the pricing row whose `effective_from` is the latest `<= ai_call_log.ts` for that `(provider, model)`. Read-time computation means a later price correction re-prices history correctly — never store a frozen cost on the call row.

**FX assumption (LOCKED, document in seed migration):** USD→INR provider prices are converted at **₹85 / $1** (May 2026 reference). The pricing rows store INR directly (already-converted). When the FX rate moves materially (>10%), insert NEW pricing rows with a new `effective_from` — do NOT mutate existing rows (history integrity).

Seed `ai_provider_pricing` (from AI-SPEC §4b cost table; free tiers = 0):

| provider | model | in ₹/Mtok | out ₹/Mtok | note |
|---|---|---|---|---|
| `gemini_2_5_flash_free` | `gemini-2.5-flash` | 0 | 0 | free tier |
| `gemini_2_5_flash_paid` | `gemini-2.5-flash` | ≈₹0.08/call equiv | — | ~₹0.08/vision call (AI-SPEC) |
| `groq_llama_3_3_70b_free` | `llama-3.3-70b-versatile` | 0 | 0 | free tier |
| `openrouter_qwen_vl_free` | `qwen/qwen2.5-vl-32b-instruct:free` | 0 | 0 | free |
| `openrouter_llama_free` | `meta-llama/llama-3.3-70b-instruct:free` | 0 | 0 | free |
| `gpt_4o_mini_paid` | `gpt-4o-mini` | ~₹12.75 (=$0.15×85) | ~₹51 (=$0.60×85) | last-resort paid |

> Paid Gemini/Groq exact per-Mtok INR are OPEN — fill at first paid-burst from the providers' 2026 price pages × ₹85. Free-tier rows (the V1 routine path) are 0 and complete; this does NOT block the build.

### Budget enforcement = MONITORING-ONLY (AP-09 — LOCKED)
For V1 (20–100 users) budget is **observe + alert only** — **NO runtime circuit-breaker, NO request-blocking on spend.** A circuit-breaker at this scale is over-engineering (the free-tier routine path is ≈₹0/mo; AI-SPEC §4b).
- Daily SQL rollup feeds D11/M3: cost/active-user 30-day rolling, target **≤₹15/user/month**.
- Alert (not block) at the M3/F7 thresholds: >₹20/user 7-day rolling → investigate within 24h; >₹25 → page (AI-SPEC §6 F7, §7 alert table).
- Surfaced via founder-only `/admin/cost` endpoint (daily rollup) + the Phoenix dashboard.
- Provider-fallback rate (M4/F8) >15% sustained → investigate (Gemini RPD ceiling hit OR primary quality regression).

---

## 9. Daily-summary copy = DESCOPED (AP-14)

The daily-summary text generation (the third Groq advice call counted in the AI-SPEC §4b volume math, "2 meal-advice + 1 daily summary") is **descoped from the first Phase-2 increment** and moved to a later Phase-2 increment. Reason: it is not on the core photo→macros→advice trust loop (ADVICE-01..06); the RETAIN-02 8pm push can ship with a templated string in the first increment and gain LLM-generated summary copy later. When built, it reuses `text_provider.generate_advice` machinery with a distinct `prompt_version` (`daily_summary_v1`) and the SAME `AdvicePromptContext` PII firewall. No new provider, no new chain. This narrows the first increment to vision + inline advice only.

---

## 10. Eval-only data shapes (AP-13, AP-15 — LOCKED)

### `data/dish_decomposition.json` (D-07, D-08, TRACK-10)
Shape LOCKED as `{slug: [{ifct_code, grams_per_serving}]}`:

```json
{
  "paneer_butter_masala": [
    {"ifct_code": "D012", "grams_per_serving": 80},
    {"ifct_code": "A045", "grams_per_serving": 60},
    {"ifct_code": "F003", "grams_per_serving": 15},
    {"ifct_code": "C021", "grams_per_serving": 5}
  ],
  "dal_tadka": [ ... ]
}
```
- `slug` = a member of the `DishName` Literal (50 dishes, TRACK-06).
- `ifct_code` = IFCT 2017 raw-ingredient code; macros looked up DETERMINISTICALLY (no LLM math — D-07, Anti-Pattern #4). `grams_per_serving` is the founder-curated reference portion (scaled by `portion_g` at runtime).
- Macros = `Σ (ifct_macro_per_100g × grams_per_serving/100)`. This is the entire Stage 2; `lookup_dish_macros()` is a plain SQL/dict function, NOT an LLM call, NOT a tool exposed to the LLM (AI-SPEC §4 Tool Use = None).
- Built via the D-08 cascade (NIN dataset → scrape Tarla Dalal/Unlock.fit → Opus 4.7 draft → founder verifies grams). 50 dishes, committed at Gate 0a.

### `data/dish_aliases.json` (AP-13 — EVAL-ONLY)
Shape LOCKED as `{alias: slug}`:

```json
{ "pbm": "paneer_butter_masala", "butter paneer": "paneer_butter_masala", "dal fry": "dal_tadka" }
```
- **EVAL-ONLY. NO runtime fuzzy matching in V1.** At runtime the `DishName` Literal forces Gemini to emit an exact whitelist slug or fail Pydantic validation — there is no fuzzy/alias resolution on the hot path (Literal exact-key by design; AI-SPEC §4b vision schema).
- `dish_aliases.json` is consumed ONLY by the Gate 0a eval harness (AI-SPEC §5 D1) to normalize a founder ground-truth label that used a colloquial name to the canonical slug before string-compare. It never touches `vision_pipeline.py`.

### Opus 4.7 ground-truth labeling prompt (AP-15 — Gate 0a, D-06/D-10)
LOCKED: ground-truth labeler = **Claude Opus 4.7** (existing subscription, zero incremental cost), NOT Gemini (avoids circular bias with the Gemini-2.5-Flash-under-test — D-10). Adapt the AI-SPEC §3 Appendix labeling prompt for Opus:
- Opus emits **dish-name (slug) + portion estimate (grams) ONLY** — never macros (D-07: macros are deterministic IFCT lookup).
- Output JSON: `{ground_truth_dishes:[{name, portion_g}], reference_object:'coin'|'palm'|'spoon'|'none', notes}`.
- Founder MANUALLY verifies EVERY label (not spot-check — D-10 mitigation), cross-checked against IFCT 2017 + Tarla Dalal + Munmun Ganeriwal/Ryan Fernando recipes.
- Macros for the ground-truth row are then computed by the SAME deterministic `dish_decomposition.json` × IFCT pipeline at the labeled `portion_g`.
- V1.5 RD-audit trigger: if Gate 0a passes but real-user accuracy in Phase 6 alpha drops <75%, book the reserved ₹1,500–3,000 RD consult (D-10).

> The literal Opus prompt text is finalized at Gate 0a kickoff (founder discretion per CONTEXT "Claude's Discretion"; already drafted in AI-SPEC §3 Appendix). Strategy is locked here.

---

## 11. Library pins (LOCKED — AI-SPEC §3)

```
google-genai >=1.33,<2     # Gemini 2.5 Flash multimodal + response_schema; use .aio.* async
groq         >=0.11,<1     # AsyncGroq llama-3.3-70b-versatile; JSON mode needs "JSON" in prompt
openai       >=1.55,<2     # ONLY for OpenRouter base_url + gpt-4o-mini paid fallback
ollama       >=0.4,<1      # DEV ONLY, lint-banned in prod paths
pydantic     >=2.7,<3
tenacity     >=9,<10
httpx        >=0.27,<1     # shared AsyncClient per provider, created at startup
python       3.12
```

**Build pitfalls (carry from AI-SPEC §3 — do not relearn):**
1. Gemini `response_schema` rejects `Any`/untyped dict/untagged Union → every field concrete type; nullable = `X | None` + `Field(default=None)`. Verify `VisionResult.model_json_schema()` before first run.
2. Groq JSON mode silently 400s if the literal token "JSON" is absent from the prompt → always include "Respond with valid JSON matching this schema:".
3. Never `asyncio.run()` inside a FastAPI handler → use `await asyncio.gather/wait_for`.
4. Pass image to Gemini as `Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg")` — NOT `from_uri` with an R2 presigned URL (DPDP region ambiguity + latency). Backend downloads bytes via shared `httpx.AsyncClient` first (API-SPEC.md owns the R2 GET).
5. Use `client.aio.models.generate_content(...)` (async namespace) — sync call inside `async def` blocks the event loop.
6. tenacity `reraise=True` always (see §4).
7. On `ValidationError`, `logger.exception(...)` with `response.text[:500]` + model + prompt_version — never silent-swallow (invisible accuracy regression).

---

## 12. Cross-references

| Need | Doc |
|---|---|
| DDL for `ai_call_log`, `provider_quota`, `vision_cache`, `ai_provider_pricing` | **MODEL-SPEC.md** |
| `POST /meals/analyze` route, request/response envelope, R2 presigned GET, HTTP 502/413 contract | **API-SPEC.md** |
| 4/4 rubric validator internals, guardrails G1–G12, online/offline flywheel | AI-SPEC §6 |
| Eval harness, Gate 0a/0b pytest, datasets, LLM-judge calibration | AI-SPEC §5 |
| 50-dish whitelist enumeration | REQUIREMENTS.md TRACK-06 |
| `veg_protein_prices` table schema | decisions/2026-05-28-D-01-to-D-19.md (D-15..D-18) + MODEL-SPEC.md |

---

## 13. Open items (needs founder / later Gate — NOT build blockers for the free-tier routine path)

| Item | Resolves at | Why not blocking |
|---|---|---|
| Exact vision system-prompt + 50-slug ordering | Gate 0a | Strategy + schema locked; strings are fill-in |
| Exact advice system-prompt + 3 few-shot strings | Gate 0b WoZ corpus | Strategy + `AdvicePromptContext` locked |
| Exact `advice_v1_strict.py` retry wording | Gate 0b | Mechanism (G5/G6 retry) locked |
| Paid Gemini/Groq exact per-Mtok INR | first paid burst | Free-tier rows (V1 path) are 0 and complete; read-time pricing |
| OpenRouter RPD ceiling (50 vs 1000) | founder confirms credit level | Default 50 (conservative) ships safely; bump when ≥$10 credit |
