# Architecture Research

> ⚠️ **PARTIALLY SUPERSEDED — read `.planning/phases/01-validation-gates-stack-lock/01-CONTEXT.md` (D-01..D-19 + D-CEO-01..03) and `CLAUDE.md` FIRST.**
> This is a point-in-time research artifact (2026-05-27). The following items are STALE and overridden by later locked decisions — do NOT plan against them:
> - **Compute:** "FastAPI on Railway / Railway Postgres / railway.toml" → **Render free tier, Singapore region** per D-01. Both Railway AND Fly.io eliminated — each requires a credit card in 2026, failing the zero-CC bootstrap constraint. Render free has no CC requirement. The Mumbai-compute latency win (sub-20ms) is a **deferred Phase-4 migration trigger only**, never the V1 plan. **Every "Railway" / "Mumbai-edge compute" / "Fly.io" mention in the diagram, component table, scaling table, anti-patterns, and India-specific table below is STALE — read it as "Render free, Singapore."**
> - **Vision model:** "Gemini 2.0 Flash (15 RPM / 1500 RPD)" → **Gemini 2.5 Flash** (10 RPM / 250K TPM / 500 RPD) per CLAUDE.md + D-stack. 2.0 retires 2026-03-03.
> - **Cron:** "in-process APScheduler" for hard-delete / keep-alive / push → **GitHub Actions scheduled workflows** per D-03 (Render free sleeps; in-process cron will NOT fire). APScheduler only valid once on always-on paid compute.
> - **Auth wire:** "HTTPS (JWT)" / app-minted JWT → **Firebase ID token used directly as Bearer**, verified per-request via `firebase-admin.verify_id_token` per D-05 (no separate app JWT).
> - **State mgmt:** "Zustand/Redux" → **Zustand + TanStack Query** (Redux is anti-pattern #12).
> The *component topology, two-step vision pipeline, ai_provider.py abstraction, presign-first upload, and append-only event-log patterns* below remain VALID. Treat infra/provider/cron/auth specifics as superseded.

**Domain:** AI-powered Indian-context nutrition coach (mobile + backend, vision + advice LLM)
**Researched:** 2026-05-27
**Confidence:** HIGH (stack locked in design doc + standard 2026 mobile-AI patterns)
**Superseded-banner added:** 2026-05-29 per /plan-eng-review + bhog-decision-audit workflow (blocker #1)

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       MOBILE CLIENT (React Native + Expo)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │ Camera   │ │ Macros   │ │ History  │ │ Streak / │ │ Correction   │    │
│  │ Capture  │ │ Card +   │ │ (last 3d)│ │ Push UI  │ │ Edit UI      │    │
│  │ + Compr. │ │ Advice   │ │          │ │          │ │              │    │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘    │
│       │            │            │            │              │            │
│  ┌────┴────────────┴────────────┴────────────┴──────────────┴────────┐   │
│  │   App State (Zustand/Redux) + React Query + Local SQLite cache    │   │
│  └─────────────────────────────────┬──────────────────────────────────┘   │
│                                    │                                     │
│  ┌─────────────────────────────────┴───────────────────────────────┐    │
│  │  Auth (Firebase phone OTP) │ Push (FCM) │ HTTPS API client       │    │
│  └─────────────────────────────────┬───────────────────────────────┘    │
└────────────────────────────────────┼─────────────────────────────────────┘
                                     │ HTTPS (JWT)
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI on Railway, Mumbai-adjacent)      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  API Layer (FastAPI routes + Pydantic v2 schemas + JWT verify)  │    │
│  └────┬────────────┬────────────┬────────────┬──────────────┬──────┘    │
│       │            │            │            │              │           │
│  ┌────┴────┐ ┌─────┴────┐ ┌─────┴────┐ ┌─────┴────┐ ┌──────┴───────┐    │
│  │ Upload  │ │ Vision   │ │ Advice   │ │ Daily    │ │ Compliance / │    │
│  │ Service │ │ Pipeline │ │ Engine   │ │ Summary  │ │ DSR Service  │    │
│  │ (R2     │ │ Service  │ │ Service  │ │ + Streak │ │ (consent,    │    │
│  │ presign)│ │          │ │          │ │ Service  │ │  delete)     │    │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘    │
│       │           │            │            │              │            │
│  ┌────┴───────────┴────────────┴────────────┴──────────────┴────────┐   │
│  │              ai_provider.py — Provider Abstraction Layer         │   │
│  │  VisionProvider {gemini_2_flash, openrouter_gemini, qwen_vl,     │   │
│  │                  gpt4o_mini}                                     │   │
│  │  TextProvider   {groq_llama, openrouter_free, ollama_local,      │   │
│  │                  gemini_flash_paid}                              │   │
│  │  Routing rules: free-first, 429-fallback, per-call timing log    │   │
│  └────┬─────────────────────────────────────────────────────────────┘   │
│       │                                                                  │
│  ┌────┴────────────────────────────────────────────────────────────┐    │
│  │ Dish Decomposition Layer (cooked → IFCT raw ingredients + qty)  │    │
│  │ IFCT 2017 macros aggregator + portion ground-truth table (50    │    │
│  │ pan-Indian dishes)                                              │    │
│  └────┬────────────────────────────────────────────────────────────┘    │
│       │                                                                  │
│  ┌────┴─────────┐ ┌──────────────┐ ┌────────────────┐ ┌──────────────┐  │
│  │ Postgres     │ │ Cron / APS-  │ │ Audit / Event  │ │ Metrics      │  │
│  │ (Railway,    │ │ Scheduler    │ │ Log (DPDP +    │ │ (Sentry +    │  │
│  │ Mumbai-edge) │ │ (8pm push,   │ │ training-      │ │ /metrics)    │  │
│  │              │ │ hard-delete) │ │ corpus events) │ │              │  │
│  └──────────────┘ └──────────────┘ └────────────────┘ └──────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
        │                  │                    │                 │
        ▼                  ▼                    ▼                 ▼
┌───────────────┐ ┌───────────────────┐ ┌──────────────┐ ┌───────────────┐
│ Cloudflare R2 │ │ AI Providers      │ │ Firebase     │ │ FCM (India    │
│ (Mumbai jur.) │ │ Google AI Studio  │ │ (phone OTP)  │ │ delivery)     │
│ photos/       │ │ Groq, OpenRouter, │ │              │ │ daily 8pm     │
│ thumbnails/   │ │ Ollama (dev)      │ │              │ │ push          │
└───────────────┘ └───────────────────┘ └──────────────┘ └───────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Mobile Camera + Compression** | Capture meal photo, downscale to ~1280px max edge, JPEG q=80, ~150-300KB. Show reference-object guidance overlay (coin/palm). | `expo-camera` + `expo-image-manipulator` |
| **App State + Cache** | Hold day's macros, last 3 days log offline, streak counter, pending uploads queue. | Zustand + React Query + `expo-sqlite` |
| **Upload Service (backend)** | Issue presigned PUT URL for R2; record `meal_photo` row with status=pending; verify upload completion. | FastAPI route + boto3 (R2 is S3-compatible) |
| **Vision Pipeline Service** | Take photo URL → call `VisionProvider` → parse dish JSON → invoke Dish Decomposition → aggregate macros → persist. | Async FastAPI worker (single-process v1; ARQ/Celery v1.5) |
| **ai_provider.py** | Single abstraction for vision + text. Free-first routing, 429 fallback, cost + latency log per call. | Python module, env-driven config |
| **Dish Decomposition Layer** | "Paneer butter masala" → {paneer 80g, tomato 50g, butter 10g, cashew 5g, cream 10g}. LLM-prompted with IFCT-anchored examples. | Prompt + IFCT 2017 lookup (sqlite or Postgres table) |
| **Advice Engine Service** | Build prompt with goal + target macros + last-3-day log + day-so-far + budget + veg/non-veg → text LLM → 1-2 sentence advice. | Groq Llama 3.3 → fallback chain |
| **Daily Summary + Streak Service** | At midnight IST (or first-open-next-day) compute day totals, gap vs target, streak update. | APScheduler in-process; cron job week 7+ |
| **Compliance / DSR Service** | Consent records, "delete my data" handler (soft-delete + 30d hard-delete cron), data export, training-opt-in flag. | FastAPI routes + scheduled job |
| **Push Scheduler (FCM)** | 8pm IST per-user push with personalized macro-gap copy. | APScheduler → FCM HTTP v1 API |
| **Postgres** | Source of truth: users, meal_photo, daily_summary, streak, push_event, consent_log, correction_event. | Railway managed Postgres |
| **Cloudflare R2 (Mumbai)** | Photo binary storage. Public bucket disabled; signed URL access only. | R2 with Mumbai jurisdiction tag |

## Recommended Project Structure

### Backend (`server/`)

```
server/
├── app/
│   ├── main.py                  # FastAPI app factory, CORS, middleware
│   ├── config.py                # Pydantic Settings (env-driven)
│   ├── deps.py                  # auth dep, db session dep
│   ├── api/
│   │   ├── auth.py              # phone OTP verify (Firebase admin SDK)
│   │   ├── uploads.py           # presigned R2 URL issuer
│   │   ├── meals.py             # POST /meals (trigger vision), GET log, PATCH correction
│   │   ├── advice.py            # GET /advice/today (re-render)
│   │   ├── summary.py           # GET /summary/today, /streak
│   │   ├── push.py              # device token registration
│   │   └── compliance.py        # consent, delete-my-data, export
│   ├── services/
│   │   ├── vision_pipeline.py   # orchestrates photo → dish → macros
│   │   ├── dish_decomposition.py# cooked-to-raw ingredient decomposition
│   │   ├── ifct_lookup.py       # IFCT 2017 macros per ingredient
│   │   ├── advice_engine.py     # advice prompt build + LLM call
│   │   ├── daily_summary.py     # day totals + gap vs target
│   │   ├── streak.py            # streak increment / reset logic
│   │   ├── push_scheduler.py    # 8pm cron + per-user copy
│   │   └── compliance_service.py# consent + delete pipeline
│   ├── providers/
│   │   ├── ai_provider.py       # VisionProvider + TextProvider + routing
│   │   ├── vision_gemini.py     # Google AI Studio + paid Gemini
│   │   ├── vision_openrouter.py # OpenRouter Gemini / Qwen 2.5 VL
│   │   ├── vision_gpt4o.py      # GPT-4o-mini fallback
│   │   ├── text_groq.py         # Groq Llama 3.3 70B free
│   │   ├── text_openrouter.py   # OpenRouter Llama / Mixtral free
│   │   ├── text_ollama.py       # local dev only
│   │   └── text_gemini.py       # paid Gemini Flash text
│   ├── storage/
│   │   ├── r2_client.py         # boto3 S3-compatible R2 client (Mumbai)
│   │   └── presign.py           # PUT/GET URL signing
│   ├── models/                  # SQLAlchemy 2.0 (or SQLModel) models
│   │   ├── user.py
│   │   ├── meal_photo.py
│   │   ├── daily_summary.py
│   │   ├── streak.py
│   │   ├── push_event.py
│   │   ├── correction_event.py  # training corpus signal
│   │   └── consent_log.py
│   ├── schemas/                 # Pydantic v2 request/response models
│   ├── prompts/
│   │   ├── vision_v0.py         # Appendix A prompt + in-context examples
│   │   ├── decomposition.py
│   │   └── advice.py
│   ├── data/
│   │   ├── ifct_2017.sqlite     # IFCT raw food DB (528 items)
│   │   └── dish_ground_truth.csv# 50-dish whitelist portion + ingredients table
│   └── workers/
│       ├── push_cron.py         # APScheduler
│       └── hard_delete_cron.py  # 30-day DPDP purge
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/                # 30 benchmark photos + true macros
├── alembic/                     # migrations
├── pyproject.toml
└── railway.toml
```

### Mobile (`mobile/`)

```
mobile/
├── app/                         # Expo Router v3 file-based routes
│   ├── (auth)/
│   │   ├── phone.tsx            # phone entry
│   │   └── otp.tsx              # OTP verify
│   ├── (onboarding)/
│   │   ├── goal.tsx             # muscle gain (V1) / weight loss (V1.1)
│   │   ├── body.tsx             # height/weight/age
│   │   ├── diet.tsx             # veg / non-veg / budget
│   │   └── consent.tsx          # DPDP consent screens
│   ├── (tabs)/
│   │   ├── home.tsx             # today's macros + advice + streak
│   │   ├── camera.tsx           # photo capture + reference-object overlay
│   │   ├── history.tsx          # last 3 days meals
│   │   └── settings.tsx         # delete-my-data + privacy policy
│   └── meal/[id].tsx            # meal detail + correction UI
├── src/
│   ├── components/
│   │   ├── MacrosCard.tsx       # ← advice rendered INLINE here (moat surface)
│   │   ├── AdviceInline.tsx
│   │   ├── StreakBadge.tsx
│   │   ├── CameraOverlay.tsx    # reference-object guidance
│   │   └── CorrectionSheet.tsx  # tap dish/macro to fix
│   ├── api/
│   │   ├── client.ts            # fetch wrapper + JWT
│   │   ├── meals.ts             # uploadPhoto, getMeal, correctMeal
│   │   └── summary.ts
│   ├── state/
│   │   ├── auth.ts              # zustand
│   │   ├── meals.ts             # react-query
│   │   └── streak.ts
│   ├── lib/
│   │   ├── compress.ts          # expo-image-manipulator pipeline
│   │   ├── upload.ts            # presigned PUT
│   │   ├── push.ts              # FCM token register
│   │   └── offline_queue.ts     # SQLite-backed pending uploads
│   └── theme/
├── app.json                     # Expo config (permissions, FCM)
├── eas.json                     # EAS Build profiles
└── package.json
```

### Structure Rationale

- **`server/app/providers/`:** AI provider abstraction is a first-class folder, not a util. Reflects the design-doc priority (free-first multi-provider routing is a core constraint, not an implementation detail).
- **`server/app/services/`:** Domain services thin; orchestrate provider + DB. Keeps API routes 5-10 lines each.
- **`server/app/prompts/`:** Prompts version-controlled as Python modules with explicit `VERSION = "v0"` strings. Prompt iteration is the actual product work in Phase 0-1.
- **`server/app/data/`:** Ship IFCT DB + 50-dish ground-truth table inside the repo. Small (~5MB); avoids week-1 data-loading runbook.
- **`mobile/src/components/MacrosCard.tsx` + `AdviceInline.tsx`:** Co-located by design — the moat lives here. If `AdviceInline` ever moves to its own tab, the moat collapses (per design doc P1).
- **`mobile/src/lib/offline_queue.ts`:** Solo-founder Indian-network reality. 24-hour queue, no offline writes beyond that (design doc constraint).

## Architectural Patterns

### Pattern 1: Provider Abstraction with Free-First Routing

**What:** Single `ai_provider.py` exposing `VisionProvider.identify(image_url, ...)` and `TextProvider.complete(messages, ...)`. Internal routing tries free tiers in order, falls back on 429 / rate-limit / timeout.

**When to use:** Always for vision + text in this product. The provider switch is the single most important architectural decision (vendor risk + cost mitigation).

**Trade-offs:**
- Pro: One config change moves from free to paid; vendor lock-in eliminated; fallback resilience.
- Con: Adds an indirection layer; per-call latency log + cost tracking needed to know which provider actually ran.

**Example:**

```python
# server/app/providers/ai_provider.py
class VisionProvider:
    async def identify(self, image_url: str, *, prompt_version="v0") -> VisionResult:
        for provider in self._route():  # ["gemini_free", "openrouter_gemini", "qwen_vl", "gpt4o_mini"]
            try:
                return await provider.call(image_url, prompt_version=prompt_version)
            except RateLimitError:
                self.metrics.record_429(provider.name)
                continue
            except TimeoutError:
                continue
        raise AllProvidersFailed()
```

### Pattern 2: Photo Upload via Presigned PUT (Client → R2 Direct)

**What:** Backend never proxies photo bytes. Mobile compresses → backend issues presigned PUT URL → mobile uploads directly to R2 Mumbai → mobile POSTs `{photo_key}` to backend → backend triggers vision pipeline.

**When to use:** Any mobile photo upload where backend bandwidth and request body limits matter. Critical on Railway $5/mo tier.

**Trade-offs:**
- Pro: Backend bandwidth ~0 for photos; faster perceived upload on Indian 4G; no FastAPI request-body limits.
- Con: Two-step flow (presign + confirm); orphan photos possible if confirm never lands — need janitor cron.

**Example:**

```python
# server/app/api/uploads.py
@router.post("/uploads/presign")
async def presign(user=Depends(current_user)):
    key = f"meals/{user.id}/{uuid4()}.jpg"
    url = r2_presign_put(key, expires=300, content_type="image/jpeg")
    await db.meal_photo.insert(user_id=user.id, key=key, status="pending")
    return {"upload_url": url, "key": key}
```

### Pattern 3: Inline Advice Rendered on Macros Card (Moat Surface Pattern)

**What:** Vision pipeline result and advice engine result resolve into a **single API response** (`MealResponse`) containing both macros and advice text. Mobile renders both in one `<MacrosCard />` — advice is a child element of the macros card, not a separate screen or modal.

**When to use:** Mandatory for this product per design doc P1. The advice cannot be lazy-loaded into a separate "Coach" tab or buried behind a button.

**Trade-offs:**
- Pro: Moat surfaces on every meal; users always see the value.
- Con: Advice call latency now blocks meal-result UI. Mitigate with: (a) parallel advice call after vision completes, (b) optimistic skeleton, (c) hard timeout 6s and ship macros-only fallback.

**Example:**

```python
# server/app/api/meals.py
@router.post("/meals/{photo_key}/analyze")
async def analyze_meal(photo_key: str, user=Depends(current_user)):
    vision = await vision_pipeline.run(photo_key)        # ~2-3s
    advice_task = asyncio.create_task(advice_engine.generate(user, vision))
    advice = await asyncio.wait_for(advice_task, timeout=6.0)
    return MealResponse(macros=vision.macros, dishes=vision.dishes, advice=advice)
```

### Pattern 4: Cooked-Dish Decomposition Layer

**What:** Vision returns dish name + portion (`paneer butter masala, 250g`). Decomposition layer calls a small LLM with IFCT-anchored prompt to break it into raw ingredients with weights, then aggregates macros from IFCT lookup table. NOT a free vision-to-macros call.

**When to use:** Always for cooked Indian dishes. IFCT 2017 is raw ingredients; cooked-dish accuracy requires this two-step.

**Trade-offs:**
- Pro: Macros grounded in IFCT (authoritative), not LLM hallucination; correction signals can fix decomposition weights (training data).
- Con: Extra LLM call; ground-truth table must be curated for the 50-dish whitelist (week-2 founder work).

**Example:**

```python
# server/app/services/dish_decomposition.py
async def decompose(dish_name: str, portion_g: int) -> list[Ingredient]:
    if dish_name in DISH_GROUND_TRUTH:                  # 50-dish curated table
        return scale(DISH_GROUND_TRUTH[dish_name], portion_g)
    raw = await text_provider.complete(DECOMPOSITION_PROMPT.format(dish=dish_name, g=portion_g))
    return parse_ingredients(raw)  # [{"name":"paneer","grams":80}, ...]
```

### Pattern 5: Correction Event as Training Signal

**What:** Every user edit to dish name / macros / portion is persisted as a `correction_event` row with `{before, after, photo_key, user_id, timestamp}`. Never overwritten. Becomes the V1.5 fine-tuning corpus.

**When to use:** Now, week 3, before there's any data to lose. Cheap to add early; expensive to retrofit.

**Trade-offs:**
- Pro: Builds the dataset moat from day 1; supports per-user accuracy improvement later; debug provenance for support cases.
- Con: ~2x writes per correction; storage growth (mitigated — text only).

### Pattern 6: Daily Push via Per-User Cron with Personalized Copy

**What:** APScheduler job runs every 5 minutes, queries users whose local 8pm-IST window opened, computes day-so-far macro gap, generates short personalized copy via text LLM, dispatches via FCM HTTP v1.

**When to use:** Week 7. Before this, the app has no return trigger and retention gate (5/20 D7) likely fails.

**Trade-offs:**
- Pro: Personalized per user (not broadcast); copy references their actual gap.
- Con: LLM call per user per day (~100 users × 1 = trivial); FCM batch API better at scale.

## Data Flow

### Primary Flow — Photo to Inline Advice

```
[User taps shutter in Camera tab]
    │
    ▼
[Mobile] expo-image-manipulator: 1280px max, JPEG q=80  (~200KB)
    │
    ▼
[Mobile → Backend]  POST /uploads/presign  → { upload_url, key }
    │
    ▼
[Mobile → R2 Mumbai]  PUT image bytes directly to presigned URL
    │
    ▼
[Mobile → Backend]  POST /meals/{key}/analyze
    │
    ▼
[Backend] vision_pipeline.run(key)
    │     ├─ ai_provider.VisionProvider.identify(r2_public_url)
    │     │       └─ Gemini 2.0 Flash (free) → Qwen 2.5 VL → GPT-4o-mini
    │     ├─ dish_decomposition.decompose(dish, portion_g)
    │     │       └─ ground-truth lookup OR LLM decomposition
    │     ├─ ifct_lookup.aggregate(ingredients)
    │     └─ db.meal_photo.update(macros, dishes, status=done)
    │
    ▼   (parallel)
[Backend] advice_engine.generate(user, vision_result)
    │     ├─ load user.last_3_days_log()
    │     ├─ build prompt: goal + target + budget + veg + day-so-far + last-3-days
    │     ├─ ai_provider.TextProvider.complete(prompt)  → Groq Llama 3.3 free
    │     └─ parse → 1-2 sentence advice text
    │
    ▼
[Backend → Mobile]  MealResponse { macros, dishes, advice, day_totals, streak }
    │
    ▼
[Mobile] render <MacrosCard> { macros + <AdviceInline> + day's running total }
                                            ↑ moat surface
```

### Correction Flow

```
[User taps dish name on MacrosCard]
    │
    ▼
[Mobile] <CorrectionSheet> opens, prefilled with current values
    │
    ▼
[Mobile → Backend]  PATCH /meals/{id}  { dish_name?, portion_g?, macros? }
    │
    ▼
[Backend]  ├─ insert correction_event { before, after, photo_key, user_id }  ← training corpus
           ├─ update meal_photo with corrected values
           ├─ recompute daily_summary for the day
           └─ return updated MealResponse
    │
    ▼
[Mobile] re-render MacrosCard with corrected values + recompute streak/totals
```

### Daily Push Flow (Retention Loop)

```
[APScheduler @ every 5min]  for user in users where now ≥ user.tz_8pm and not push_event_today:
    │
    ▼
[Backend]  ├─ compute today's macro_gap = target - day_so_far
           ├─ pick template: "protein gap" | "calorie behind" | "first log of day"
           ├─ text_provider.complete(push_copy_prompt)  → "You're at 48g protein, target 90g..."
           ├─ FCM send to user.fcm_token
           └─ insert push_event { user_id, ts, copy, gap_snapshot }
    │
    ▼
[FCM India edge → user device]  notification tap → deep-link to camera tab
```

### Account Deletion Flow (DPDP plumbing)

```
[User taps "Delete my data" in settings]
    │
    ▼
[Mobile → Backend]  DELETE /me  (soft-delete; any valid Firebase Bearer token — G6 / D-05)
    │
    ▼
[Backend]  ├─ users.soft_delete_at = now()
           ├─ insert consent_log { action: "delete_requested" }
           └─ return 202
    │
    ▼
[Cron: hard_delete @ daily 3am IST]  for user where soft_delete_at + 30d < now():
    ├─ R2: delete all objects under meals/{user_id}/
    ├─ Postgres: cascade delete user + meal_photo + summaries + streak + push_event
    ├─ Keep consent_log (proof of deletion) with PII-stripped user_id_hash
    └─ insert audit_event { type: "hard_deleted", user_id_hash, ts }
```

### State Management (mobile)

```
[Server: MealResponse]
    │ (react-query mutation onSuccess)
    ▼
[React Query cache: meals[date]]  ←─ optimistic update on correction
    │
    ▼
[<MacrosCard>, <HistoryList>, <StreakBadge>]  (re-render via useQuery)

[Zustand: { user, fcm_token, pending_uploads[] }]  ←─ persisted to SQLite
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-20 users (alpha, weeks 8-12) | **Render free web service (Singapore), per D-01** [~~Railway $5/mo~~ superseded]; cron via **GitHub Actions scheduled workflows** (D-03), NOT in-process APScheduler — free instance sleeps when idle; free AI tiers entirely. No queue. |
| 20-100 users (Phase 2, public) | Stay on Render free or step to a paid always-on instance if sleep latency bites [~~Railway $20/mo Pro~~ superseded]. Move push scheduler to dedicated worker (or keep on GitHub Actions). Add Redis for rate-limit cache (free providers). Keep single Postgres. |
| 100-1000 users | Split vision pipeline to ARQ/Celery worker (async meal processing). Add CDN for R2 GET. AI cost becomes top-line — tune routing weights. |
| 1000-10k users | Read replica Postgres. Per-region FCM batch sender. Consider self-hosted Qwen 2.5 VL on GPU to flatten vision cost curve. |
| 10k+ | Out of scope; revisit at PMF. |

### Scaling Priorities

1. **First bottleneck — AI provider rate limits, not infra.** Gemini free 15 RPM caps at ~50 active users analyzing photos simultaneously at lunch. Fix: provider routing weights + paid Gemini Flash burst.
2. **Second bottleneck — vision latency on Indian 4G.** 2-3s vision call + 1-2s advice = perceived 4-5s. Fix: parallel advice call (already in Pattern 3); 6s hard timeout with macros-only fallback.
3. **Third bottleneck — Railway Postgres connection pool.** FastAPI per-request connections drain quickly. Fix: SQLAlchemy async pool + pgbouncer side-car at week 9.
4. **Fourth bottleneck — push fan-out at 8pm IST.** All 100 users hit FCM in same 5-min window. Fix: FCM batch HTTP v1; spread within 7:55-8:10pm window.

## Anti-Patterns

### Anti-Pattern 1: Advice in a Separate "Coach" Tab

**What people do:** Build a `/coach` route with an "Ask Coach" button; meal results show macros only.
**Why it's wrong:** Design doc P1 — the moat collapses. Indian users have seen HealthifyMe Ria; siloed AI coach is the existing failure pattern. No friction = inline = moat.
**Do this instead:** `<AdviceInline />` is a child of `<MacrosCard />`. The two API results stream into one response shape.

### Anti-Pattern 2: Direct LLM Calls in API Routes

**What people do:** `await openai.chat.create(...)` inside `meals.py`.
**Why it's wrong:** Locks the product to one provider; free-tier routing is impossible; vendor pricing change is a code rewrite.
**Do this instead:** All LLM access through `ai_provider.py`. Routes call `VisionProvider`/`TextProvider`; never import provider SDKs in route files.

### Anti-Pattern 3: Vision-to-Macros in One Step (Skip Decomposition)

**What people do:** Trust Gemini to return final macros for "paneer butter masala 250g".
**Why it's wrong:** LLM macro estimates for cooked Indian dishes are hallucinated. IFCT 2017 is the only authoritative Indian food DB. Corrections cannot reuse single-step output.
**Do this instead:** Two-step: vision identifies (dish + portion + confidence) → decomposition → IFCT lookup → aggregate. Patterns 4 above.

### Anti-Pattern 4: Photo Bytes Through FastAPI

**What people do:** `POST /meals` with `multipart/form-data` and the backend uploads to R2.
**Why it's wrong:** Railway bandwidth wasted (you pay), per-request body limits, slow uploads on Indian 4G (double-hop client→server→R2).
**Do this instead:** Pattern 2 — presigned PUT direct to R2 Mumbai.

### Anti-Pattern 5: Storing PII (phone, weight) in R2 Photo Object Tags

**What people do:** Add `user_phone` as R2 object metadata for "convenience".
**Why it's wrong:** DPDP Act 2023 — PII outside DB is harder to delete on DSR request, and R2 object tags don't satisfy localization claims cleanly.
**Do this instead:** R2 stores only `meals/{user_id_uuid}/{photo_uuid}.jpg`. All PII in Postgres. Hard-delete cron walks Postgres → derives R2 keys → deletes both.

### Anti-Pattern 6: Mobile Computes Macros Locally

**What people do:** Ship IFCT DB to the device, do dish-to-macros on-device to "save API cost".
**Why it's wrong:** App binary bloats; updates require Play Store re-release; vision is server-side anyway; cannot capture corrections as training data.
**Do this instead:** All macro computation server-side. Mobile is render-only.

### Anti-Pattern 7: Skipping Correction Event Persistence Until V2

**What people do:** Apply edits in-place; "we'll add audit later for fine-tuning."
**Why it's wrong:** The data is generated at week 6+; if not captured then, the V1.5 fine-tuning corpus is gone forever (corrections un-replayable).
**Do this instead:** Pattern 5 — append-only `correction_event` table from day 1.

### Anti-Pattern 8: Single AI Provider for Both Vision and Text

**What people do:** Use GPT-4o for both (one API key, simpler).
**Why it's wrong:** Burns paid budget on text where Groq Llama free is ~equally good and 10x faster. Provider concentration risk.
**Do this instead:** Vision = Gemini family (best multimodal free tier). Text = Groq family (fastest, generous free). Different optimal frontiers.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Cloudflare R2 (Mumbai)** | boto3 S3-compatible client; presigned PUT/GET; bucket region tag = Asia (Mumbai). | R2 is S3-compatible; same SDK as AWS. Egress is free which matters for photo download to LLM. |
| **Google AI Studio (Gemini 2.0 Flash)** | REST via `google-genai` Python SDK; pass image as inline `inline_data` or as URL; structured JSON output via `response_schema`. | 15 RPM / 1500 RPD free. Watch for image-URL fetching being blocked from certain regions — fall back to inline bytes. |
| **Groq (Llama 3.3 70B)** | OpenAI-compatible REST; tokens-per-second very high (~500/s); generous free tier. | Use for advice text and push copy. Latency under 1s typical. |
| **OpenRouter** | OpenAI-compatible REST; single key routes to ~200 models including free Gemini, Qwen 2.5 VL, Llama, Mixtral. | Fallback layer; document model IDs in `ai_provider.py` so swaps are config-only. |
| **Ollama (local)** | HTTP at `localhost:11434`; OpenAI-compatible. | Dev-only. Used by founder for prompt iteration. Never enabled in prod env. |
| **Firebase (phone OTP)** | `firebase-admin` Python SDK verifies ID tokens; mobile uses `expo-firebase-recaptcha` or `@react-native-firebase/auth`. | Faster than MSG91 (no DLT registration wait). Phone OTP only; no email signup in V1. |
| **FCM (push)** | HTTP v1 API; service-account JWT; per-user `fcm_token` stored on backend. | India delivery: standard FCM works; no special region config. |
| **IFCT 2017** | Static SQLite or Postgres table; ~528 raw foods with macros per 100g. | Ship inside repo. Source: NIN ICMR 2017 release; ~5MB. |
| **Razorpay (Phase 3 only)** | Webhook + REST; subscription via Razorpay Subscriptions API. | Not in V1; account setup in week 13 as prep work. |
| **Sentry** | `sentry-sdk[fastapi]` + `@sentry/react-native`. | Free tier sufficient for alpha. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Mobile ↔ Backend | HTTPS JSON; JWT in `Authorization: Bearer`. | No GraphQL; REST is simpler for solo founder. |
| Backend route ↔ Service | Direct function call (same process). | No internal HTTP. Service layer is just Python. |
| Service ↔ `ai_provider` | Async function calls; provider implementation detail hidden. | The only place provider SDKs are imported. |
| `ai_provider` ↔ External AI | HTTPS REST per provider. | All retry/fallback logic lives in `ai_provider.py`, not in services. |
| Backend ↔ R2 | boto3 S3 client (presign on backend, PUT from mobile). | Backend never proxies photo bytes. |
| Backend ↔ FCM | HTTPS REST; service-account JWT. | One outbound call per push (or batch). |
| Cron worker ↔ DB | Same Postgres connection pool as API. | In-process APScheduler v1; separate process v1.5. |

## India-Specific Architectural Considerations

| Concern | Design Decision | Rationale |
|---------|----------------|-----------|
| **Data localization (DPDP Act 2023)** | Cloudflare R2 with `india` jurisdiction (PII + photos); **Postgres = Supabase Mumbai region** (DB stays in India). Compute = **Render free, Singapore** (D-01) — compute in Singapore is acceptable because PII at rest (DB + R2) is India-resident; only transient request processing transits Singapore. | Photos + PII stay in India region (R2 india + Supabase Mumbai). Document jurisdiction in privacy policy. ~~Railway Postgres region = closest to India~~ superseded — see D-01. |
| **Latency on Indian 4G** | Presigned PUT direct to R2 Mumbai (one hop, not two). Compress to 200KB max. Parallel vision + advice on backend. 6s hard timeout. | First-meal experience target: <8s shutter-to-macros. |
| **Free-tier rate limits** | Provider abstraction with 429 fallback; per-provider RPM tracked in Redis (Phase 2). | Gemini free 15 RPM caps ~50 simultaneous users at lunch peak; fallback chain prevents user-facing failure. |
| **DPDP consent ledger** | `consent_log` append-only table; consent screens version-stamped; PII-stripped audit kept post-delete. | Survives "delete my data" but proves consent existed — regulatory requirement. |
| **30-day hard-delete** | Soft-delete flag on user row; daily 3am cron walks `users.soft_delete_at + 30d < now()` and purges R2 + cascade-deletes Postgres rows. | DPDP Act compliance. Cron is idempotent and audited. |
| **Phone OTP not email** | Firebase phone OTP; no email/password in V1. | Indian youth signup norm; DLT-free path. |
| **₹-aware advice prompts** | Advice prompt includes budget + product ₹ tags (paneer ₹/100g, soya chunks ₹/100g). | Customer evidence: "wanted budget diets." Differentiator vs global apps. |
| **Veg-default content, non-veg tracking** | Vision recognizes non-veg dishes; advice engine prompt has `dietary_pref: veg|non-veg` flag that biases recommended foods. | Customer evidence: "Most India is vegetarian — they want veg sources of protein." |
| **FCM India delivery window** | 8pm IST per-user local time (not UTC); APScheduler runs every 5min and matches user TZ. | Indians dine 8-10pm IST; UTC scheduling would fire at 2:30pm IST. |
| **CDSCO/ASCI disclaimer** | Static disclaimer string baked into onboarding consent + meal-card footer + Play Store listing. | Avoids medical-device classification; ASCI advertising compliance. |
| **Indian-context dish DB** | IFCT 2017 + 50-dish ground-truth table shipped in repo. | No external food-DB dependency; offline-capable lookup; founder-curated and improvable. |
| **Cloudflare R2 over AWS S3** | R2 has free egress, Mumbai jurisdiction available, S3-compatible API. | AWS S3 Mumbai charges egress to LLM providers; R2 doesn't. Meaningful at 100+ users. |

## Suggested Build Order (Dependencies)

This order encodes "what must exist before what" — derived from data flow + risk gates in design doc.

### Phase 0 (weeks 0): Validation, no code
1. Gate 0a — vision prompt + 30 photos benchmark (validates VisionProvider before architecture exists)
2. Gate 0b — advice prompt + 14 days founder log (validates TextProvider before architecture exists)
3. Gate 0d — stack lock + `ai_provider.py` skeleton

### Phase 1 (weeks 1-2): Backend skeleton + vision spine
1. **Week 1:** FastAPI app + Postgres + auth (Firebase verify) + R2 client + presigned upload → first photo lives in R2.
2. **Week 2:** `ai_provider.py` with Gemini free + Groq free. Vision pipeline service. Dish decomposition layer. IFCT lookup. → End-to-end: photo URL → macros JSON.

**Dependency:** Vision pipeline must exist before advice engine can be tested with realistic inputs.

### Phase 2 (week 3): Advice engine
1. Advice engine service + prompt + last-3-days context fetch.
2. Correction event table + `PATCH /meals/{id}` endpoint.

**Dependency:** Last-3-days log requires vision pipeline writing `meal_photo` rows. Advice engine must precede mobile build to validate the API shape mobile will render.

### Phase 3 (weeks 4-6): Mobile client
1. **Week 4:** Expo scaffold + auth flow + onboarding (goal, body, diet, consent).
2. **Week 5:** Camera + compression + presigned upload + `MacrosCard` with inline advice.
3. **Week 6:** History view + correction sheet UI + manual-advice QA loop.

**Dependency:** Backend API must be stable enough by end of week 3 for mobile to consume without rebuild churn.

### Phase 4 (week 7): Retention loop
1. FCM token registration endpoint.
2. APScheduler push job + per-user copy generation.
3. Streak service + badge UI.

**Dependency:** Retention loop requires real meal data to personalize copy — must come after meal logging works end-to-end. Building it earlier produces broadcast copy.

### Phase 5 (week 8): Hardening
1. Offline queue (24h pending uploads).
2. Sentry integration.
3. Play Internal Testing build via EAS.

### Phase 6 (weeks 9-10): Alpha
1. 20 users + daily monitoring + iteration.

### Phase 7 (week 11): DPDP plumbing
1. Privacy policy + consent ledger + delete-my-data endpoint + hard-delete cron.

**Dependency:** Can be built earlier but only enforced before public launch. Internal alpha (closed group with explicit consent) is acceptable preceding this; public listing is not.

### Phase 8 (weeks 12-14): Retention gate + launch prep
1. Gate 7 evaluation, ASO, Razorpay account setup.

### Key cross-dependencies
- `ai_provider.py` is built once in week 0-2 and never rewritten. All later services consume it.
- Correction event persistence (week 3) must precede any user touching the app (week 9-10). If skipped early, the V1.5 training corpus is lost.
- Inline advice rendering (week 5) is the moat; if it slips to a "Coach tab" iteration, the product positioning collapses regardless of how well other phases ship.

## Sources

- `/home/nitin/Desktop/ai-calorie-weight-loss/.planning/PROJECT.md` — locked stack + constraints (HIGH)
- `/home/nitin/.gstack/projects/ai-calorie-weight-loss/nitin-unknown-design-20260527-181050.md` — design doc iteration 4, AI Provider Strategy section, weekly milestones, compliance section (HIGH)
- Standard 2026 React Native + Expo Router v3 mobile architecture (HIGH)
- FastAPI + SQLAlchemy 2.0 async standard patterns (HIGH)
- Cloudflare R2 S3-compatible API + Mumbai jurisdiction tagging — Cloudflare R2 docs (HIGH)
- Google AI Studio Gemini 2.0 Flash multimodal + `response_schema` structured output — Google AI docs (HIGH)
- Groq OpenAI-compatible API + Llama 3.3 70B free tier — Groq docs (HIGH)
- OpenRouter unified API + free models routing — OpenRouter docs (HIGH)
- IFCT 2017 (Indian Food Composition Tables) — NIN/ICMR 2017 (HIGH)
- DPDP Act 2023 data localization + 30-day deletion provisions — design-doc Compliance section (MEDIUM, founder-validated)
- FCM HTTP v1 API for India push delivery — Firebase docs (HIGH)

---
*Architecture research for: AI nutrition coach mobile app, Indian-context*
*Researched: 2026-05-27*
