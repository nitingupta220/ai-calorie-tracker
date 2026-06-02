<!-- GSD:project-start source:PROJECT.md -->
## Project

**AI Personal Coach — Indian Youth (codename: ai-calorie-weight-loss)**

An AI-powered nutrition + advice app for urban Indian youth (18-30) that uses food-photo logging as the demo hook and renders Indian-context advice inline on every meal result. Positioned as "trainer replacement at ₹299/mo instead of ₹3,000/mo." V1 ships as a React Native (Expo) Android app with FastAPI backend, free-first multi-provider AI (Google AI Studio + Groq + OpenRouter + Ollama), and serves both muscle-gain and weight-loss goals within a single youth persona.

**Core Value:** A user can photograph their Indian meal and immediately get accurate macros + one specific, budget-aware, veg-protein-gap-closing next action grounded in their own recent log — so they trust the app more than their gym trainer.

### Constraints

- **Tech stack**: React Native + Expo + EAS Build (V1); FastAPI on Render free (Singapore, per D-01) + Supabase Mumbai Postgres; Cloudflare R2 with `jurisdiction=india` for photo storage; Firebase phone OTP — Reason: Render is the only no-credit-card FastAPI host in 2026 (Fly.io removed free, Railway requires CC); Supabase Mumbai + R2 india jurisdiction satisfy DPDP residency; Singapore compute disclosed in privacy policy; re-evaluate Mumbai compute at Phase 4-5 trigger
- **AI models**: Multi-provider abstraction via `ai_provider.py`; Phase 0 testing = 100% free tiers (Google AI Studio Gemini 2.5 Flash + Groq Llama 3.3 70B); Phase 1 alpha = free-first then paid; Phase 2+ = paid Gemini Flash primary, OpenRouter fallback — Reason: bootstrap budget, vendor-risk mitigation
- **Budget**: ~₹0 in Phase 0, ~₹0-200 across Phase 1 alpha (4 weeks), ~₹1,700/mo ceiling at 100 free users — Reason: solo bootstrap founder, no external funding
- **Timeline**: 14-week target to public launch; 10-12 weeks if founder has shipped React Native before, 14-20 weeks if first-time RN shipper — Reason: founder native-app fluency unknown
- **Compliance**: DPDP Act 2023 + CDSCO/ASCI advertising disclaimers — Reason: Indian regulatory obligations; medical-device territory must be avoided
- **Persona discipline**: V1 brand voice + onboarding + first growth loop locked to urban Indian youth 18-30; engine serves both muscle-gain (V1) and weight-loss (V1.1) goals — Reason: solo founder bandwidth; multi-persona V1 dilutes both
- **Regional scope discipline**: 50-dish pan-Indian whitelist, not unrestricted — Reason: scope discipline; ship 50 well
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Executive Summary
| Design doc said | Research says | Action |
|---|---|---|
| Gemini **2.0** Flash primary | Gemini 2.0 Flash **retires 2026-03-03** | Use **Gemini 2.5 Flash** as primary vision (same free tier, better quality) |
| **Railway** $5/mo backend | Railway and Fly.io both require a credit card in 2026 (fails zero-CC) | Locked **Render free tier (Singapore)** per D-01; Fly.io Mumbai = deferred Phase-4 migration target only |
| **Cloudflare R2 Mumbai edge** for DPDP | Mumbai is a *network PoP*, not a storage *jurisdiction* | Use R2 **`india` jurisdictional bucket** (explicit DPDP guarantee), accessed via `https://<acct>.in.r2.cloudflarestorage.com` |
## Recommended Stack
### Mobile (Android V1, iOS V2)
| Technology | Version | Purpose | Why |
|---|---|---|---|
| **Expo SDK** | **54** (current stable, Jan 2026) | RN framework + EAS Build + OTA updates | 83% of SDK 54 EAS builds use New Architecture (Fabric/TurboModules); managed workflow lets first-time RN shipper avoid Xcode/Gradle hell; OTA updates via `expo-updates` 0.28.x ships hotfixes without store review |
| **React Native** | **0.81** (bundled with SDK 54) | Native rendering | New Architecture default-on in SDK 54+; matches founder's first-time-RN-shipper risk profile |
| **expo-router** | **~5.0** | File-based navigation | Stack/tab navigation without boilerplate; native-tabs unstable submodule available SDK 54+ |
| **expo-camera** | bundled with SDK 54 | Photo capture for meal logging | Pre-installed; reference-object UX (coin/palm) renders as overlay |
| **expo-image-picker** | bundled with SDK 54 | Gallery fallback | **Critical:** SDK 54 defaults `allowsEditing: false` + `videoExportPreset: 'Passthrough'` — iOS now returns HEIC/AVIF. **Must run `expo-image-manipulator` to convert to JPEG before upload**; backend expects JPEG. Anti-pattern to skip this. |
| **expo-image-manipulator** | SDK 54-bundled | Resize + JPEG conversion pre-upload | Compress to ≤1280px longest edge + ~0.7 JPEG quality; reduces R2 storage cost ~5x and Gemini vision token cost ~3x. **Mandatory in upload pipeline.** |
| **expo-notifications** | SDK 54-bundled | FCM push for 8pm dinner reminder | Required for retention mechanic (3/7/14-day streak push). |
| **@react-native-firebase/app + /messaging + /auth** | 21.x (SDK 54-compatible) | Phone OTP + FCM | Native module path required for production phone auth + reliable FCM background delivery. Requires custom dev client (no Expo Go). |
| **TanStack Query** (React Query v5) | **5.x** | Server state (meal log, advice, totals) | Industry default 2026; handles offline cache, background refetch, optimistic updates for correction UI |
| **Zustand** | **5.x** | Client state (onboarding flow, draft photo, streak counter) | Lightweight; pairs with TanStack Query (one for server, one for client) — anti-pattern to use Redux for this scale |
| **Sentry React Native SDK** | latest (2026), via Sentry Wizard | Crash + error monitoring | Free tier 5K events/mo plenty for 20-100 alpha users; `ota_updates` context auto-enriched; first paid concern only post-PMF |
| **PostHog React Native** | latest (2026) | Product analytics + feature flags | 1M events/mo free (vastly more generous than Mixpanel); autocapture taps + screens; feature flag SDK lets founder dark-launch weight-loss V1.1 to subset of users |
- Manual builds V1, no CI/CD until month 4 (founder discipline)
- Two profiles: `development` (custom dev client for Firebase native auth + FCM testing on physical device) + `preview` (internal-test APK) + `production` (Play Store AAB)
- Android-only V1 — saves $99/yr Apple fee, halves submission surface
### Backend (FastAPI on Indian-friendly PaaS)
| Technology | Version | Purpose | Why |
|---|---|---|---|
| **Python** | **3.12** | Runtime | LTS-grade for FastAPI; async ecosystem mature; ships on all considered PaaS |
| **FastAPI** | **0.128.x** (current stable) | HTTP API + OpenAPI auto-docs | Async-native; `BackgroundTasks` covers post-response advice generation; OpenAPI spec drives RN client typing |
| **uvicorn** | latest 2026 | ASGI server | Standard FastAPI runner; gunicorn+uvicorn workers in prod |
| **Pydantic v2** | **2.x** | Request/response schemas | Native FastAPI integration; ~5x faster than v1; required for FastAPI 0.118+ |
| **SQLAlchemy** | **2.0** (async) | ORM | Convention: keep SQLAlchemy models separate from Pydantic schemas (anti-pattern to mix). Use `asyncpg` driver — sync drivers block event loop and kill concurrency at scale. |
| **asyncpg** | latest | Async Postgres driver | Required for FastAPI concurrency; sync `psycopg2` is an anti-pattern with async FastAPI |
| **Alembic** | latest | DB migrations | Standard for SQLAlchemy 2.0; auto-generate + manual review |
| **httpx** | latest | Outbound HTTP to AI providers | Async client; required for non-blocking calls into `ai_provider.py` |
| **Pillow** | latest | Server-side image validation | Verify dimensions, strip EXIF (DPDP — GPS in photo metadata is PII) before R2 upload |
| **firebase-admin** | latest Python SDK | Verify Firebase ID tokens server-side | Verifies the phone-OTP token from mobile; do **not** trust phone number from client payload |
### Hosting / PaaS
| Technology | Version | Purpose | Why |
|---|---|---|---|
| **Render** (V1 choice — decision D-01) | current | FastAPI deploy on free tier, **Singapore** region | **Zero-credit-card free tier** — the binding V1 constraint. Singapore is +50-100ms vs Mumbai, accepted for alpha. Free instances sleep after inactivity; warm via cron-ping before alpha sessions. Mumbai-compute migration is a **deferred Phase-4 trigger** (fires on latency complaints at scale), never the V1 plan. |
| ~~Fly.io / Railway~~ (rejected, D-01) | — | — | **Rejected:** both require a credit card on file in 2026, which fails the zero-CC bootstrap constraint. Fly.io Mumbai (bom1) sub-20ms latency stays attractive only as a Phase-4 migration target, not V1. |
| **Supabase Postgres** | Postgres 15/16 | DB hosted in **Mumbai region** | Free tier: 500 MB DB, 1 GB storage, 50K MAU. **Only managed Postgres with India region** between Neon (no India) and Fly Postgres (works but expensive at $38/mo Basic). Supabase pauses inactive projects after 1 week — set up cron-ping or upgrade to $25 Pro before alpha launch. |
| ~~Fly Postgres~~ (rejected, D-01) | Postgres 16 | DB co-located with API in `bom1` | **Rejected for V1:** presumed API on Fly.io, which D-01 eliminated (credit-card required). Co-location latency only relevant if a Phase-4 Mumbai-compute migration ever happens; Supabase Mumbai is the V1 DB regardless. |
### Object Storage
| Technology | Version | Purpose | Why |
|---|---|---|---|
| **Cloudflare R2** | current | Meal photo storage in India jurisdiction | **Jurisdictional bucket required** — set jurisdiction to `india` on bucket creation. Access endpoint: `https://<account_id>.in.r2.cloudflarestorage.com`. Guarantees DPDP-compliant residency (not just network edge). Zero egress fees (huge for image-heavy app). |
| **boto3** (Python) | latest | S3-compatible R2 client | R2 speaks S3 protocol; use boto3 with `endpoint_url` pointing to `.in.r2.cloudflarestorage.com`. **One client per jurisdiction** — multi-endpoint clients not supported. |
- Bucket lifecycle rule: delete after 90 days from soft-delete tombstone (DPDP 30-day hard-delete + 60-day buffer for backup integrity)
- Presigned URLs (5-min TTL) for mobile uploads — never proxy uploads through FastAPI (saves bandwidth + memory)
- **Anti-pattern:** Local Uploads are NOT supported on jurisdictional buckets (would temporarily route data outside India). Use standard S3-compatible upload only.
### Authentication
| Technology | Version | Purpose | Why |
|---|---|---|---|
| **Firebase Authentication** (phone OTP) | Firebase JS SDK ≥ 12.0.0 + @react-native-firebase/auth 21.x | Phone number sign-up + login | Free tier: 50K MAU. **No DLT registration required** (Firebase handles SMS through Google's carrier relationships) — the design doc's "DLT takes 3-7 days" pain point is sidestepped entirely. |
| **firebase-admin** (Python) | latest | Backend ID-token verification | `auth.verify_id_token(token)` on every authenticated endpoint; never trust client-submitted phone number |
- DLT Principal Entity registration: 3-7 days, paperwork-heavy
- Per-OTP cost: ₹0.15 (MSG91) × estimated 5 OTPs/user × 100 users = ~₹75 + DLT template fees
- Firebase: 50K MAU free, ~10K free SMS/month on Spark plan
- **Migrate to MSG91 + DLT only when:** Firebase SMS quota becomes binding (likely Phase 3 at 500+ MAU) OR India SMS deliverability degrades (rare)
### AI Provider Stack (the non-negotiable, free-first layer)
#### Vision (photo → dish + macros)
| Provider | Model | Free Tier (verified 2026) | Cost (paid) | Use |
|---|---|---|---|---|
| **Google AI Studio** (primary) | **Gemini 2.5 Flash** (NOT 2.0 — retires 2026-03-03) | 10 RPM, 250K TPM, **500 RPD** (some reports cite 1500 RPD for Flash; verify on signup) | ~₹0.08/call paid | Primary vision. Multimodal-native; rate limits apply uniformly across text+image. |
| **OpenRouter** (fallback 1) | `qwen/qwen2.5-vl-32b-instruct:free` or `:72b-instruct:free` | ~20 RPM, 50 RPD if <$10 credit purchased, 1000 RPD if ≥$10 credit | $0 input/output for free variants | First fallback on Google 429. Qwen 2.5 VL is the strongest open vision model for food per research. |
| **OpenAI** (paid fallback) | `gpt-4o-mini` (vision) | n/a | ~$0.15/1M input tokens | Last resort paid; only when Google + OpenRouter free both exceeded. |
- 20 alpha users × 2 meals/day = 40 vision calls/day = **well within Gemini 2.5 Flash 500 RPD**. Phase 1 = ₹0.
- 100 Phase-2 users × 2 meals/day = 200 calls/day. Still under Gemini 500 RPD. **Bursty hour matters more than daily total** — 10 RPM means 1 call per 6 seconds. Queue per-user requests, accept ~10s P95 latency during peak meals.
#### Text (advice + dish decomposition + daily summary)
| Provider | Model | Free Tier (verified 2026) | Cost (paid) | Use |
|---|---|---|---|---|
| **Groq** (primary) | `llama-3.3-70b-versatile` | 30 RPM, 6K TPM, **1,000 RPD** (binding constraint) | ~$0.59/M input | Primary text. 500+ tok/s — fastest inference available. Llama 3.3 70B competitive with GPT-4-class for advice quality. |
| **OpenRouter** (fallback) | `meta-llama/llama-3.3-70b-instruct:free` or `mistralai/mixtral-8x7b-instruct:free` | ~20 RPM, 50-1000 RPD by credit | $0 free variants | First fallback on Groq 429. |
| **Google AI Studio** (paid fallback) | Gemini 2.5 Flash text-only | covered above | ~₹0.10/call | If both free providers exceeded. |
- 20 users × 2 meal-advice + 1 daily-summary = 60 advice calls/day. **Within Groq 1000 RPD.**
- 100 users × 3 advice/day = 300 calls/day. Still within Groq 1000 RPD.
- **RPD breach point ≈ 330 daily-active users.** Plan to migrate text to paid Gemini Flash at Phase 2 end / Phase 3 entry.
#### Dev / prompt iteration
| Provider | Model | Cost | Use |
|---|---|---|---|
| **Ollama** | `llama3.1:8b` or `qwen2.5:7b` | ₹0 (founder's machine) | Prompt iteration without burning RPD. **NOT production-grade** — don't ship as user-facing. Use to draft prompts, then deploy to Gemini/Groq for validation. |
#### `ai_provider.py` design (V1)
# Provider routing rules (locked Week 0d):
# Vision:
#   1. Google AI Studio Gemini 2.5 Flash (free)
#   2. On 429 → OpenRouter Qwen 2.5 VL 32B free
#   3. On 429 again → Gemini 2.5 Flash paid
#   4. On 5xx → GPT-4o-mini paid (last resort)
#
# Text:
#   1. Groq Llama 3.3 70B (free)
#   2. On 429 → OpenRouter Llama 3.3 70B free
#   3. On 429 again → Gemini 2.5 Flash paid
#
# Cache: deduplicate identical (image_hash, user_goal) for 24h to save RPD.
- `VisionProvider.classify_meal(image_bytes) -> MealMacros`
- `TextProvider.generate_advice(log_context, goal, budget) -> str`
- Provider switch via env var `AI_PROVIDER_VISION_PRIMARY` — config flag, not code change
- Retry/backoff with `tenacity` (3 attempts, exponential backoff)
- Structured JSON output enforced via Pydantic v2 model_validate on every response (anti-pattern: trust raw LLM output)
- Gemini 2.5 Flash free: 10 RPM, 250K TPM, 500 RPD ([Google AI Developers rate limits](https://ai.google.dev/gemini-api/docs/rate-limits))
- Groq free: 30 RPM, 6K TPM, 1000 RPD ([Groq docs](https://console.groq.com/docs/rate-limits))
- OpenRouter `:free` variants: ~20 RPM, 50 RPD (<$10 credit) or 1000 RPD (≥$10 credit)
### Nutrition Data Layer
| Source | Format | Purpose | Implementation |
|---|---|---|---|
| **IFCT 2017** (Indian Food Composition Tables) | 528 raw foods, CSV/JSON | Macros ground truth for raw ingredients | Load into Postgres `nutrition_facts` table; query by ingredient name + alias. **⚠️ License-gated (D-31):** IFCT is ICMR-NIN copyright — "no part stored/reproduced electronically *for creating a product* without prior written permission of NIN." Commercial (₹299/mo) use needs a written-permission email to NIN (may be free; cannot be skipped). The IFCT food table is NOT shipped with INDB — request from ICMR-NIN. |
| **Dish decomposition layer** | INDB-seeded + LLM for gaps | Cooked dish → ingredient breakdown | Seed from **INDB** (1,014 recipes, one row per ingredient with food_code + amount/unit; grams need the `INDB.do` unit→g conversion — only ~46% rows are already grams). Covers ~43/50 whitelist; LLM-decompose only the ~4 gaps (pani_puri, pongal_ven, bisi_bele_bath, litti). **Seed, not drop-in (D-30).** |
| **Founder-curated portion table** | Spreadsheet → JSON | Typical Indian portion sizes per dish | Built during Gate 0a (Week 0). INDB serving sizes = standardized priors, NOT measured — **Gate-0a truth must be WEIGHED on a kitchen scale** (INDB ≠ image-linked truth). Add a rich/plain oil-variant axis (INDB = one fixed oil amount). One roti ≈ 30g flour ≈ 100 kcal. One katori dal ≈ 150g. |
### Push Notifications
| Technology | Version | Purpose | Why |
|---|---|---|---|
| **FCM** (Firebase Cloud Messaging) | HTTP v1 API (mandatory 2026) | Daily 8pm dinner-reminder push + streak milestones | Free, unlimited; integrates with Firebase Auth already chosen. **HTTP v1 API requires Service Account Key JSON** in EAS environment — legacy API is deprecated. |
| **Expo Push Service** | latest | Push token mgmt + send abstraction | Wraps FCM/APNs; simpler API for Phase 1; can switch to direct FCM later if needed |
| **APScheduler** (Python) | latest | Server-side cron for 8pm push (IST) | Schedules per-user notifications based on user's preferred dinner time + log gap |
### Payments (Phase 3 only)
| Technology | Version | Purpose | Why |
|---|---|---|---|
| **Razorpay** | Razorpay Python SDK + Razorpay Node SDK (verified Context7) | ₹299/mo subscription | India-default payment gateway. UPI Autopay supports recurring up to ₹15,000/mo (₹299 well within). Handles GST collection automatically. |
| **UPI Autopay** | (via Razorpay Subscriptions) | Recurring auto-debit | One-time UPI PIN auth; "₹299 will be auto-debited on the 5th" pattern is standard. 40+ banks supported. |
## Alternatives Considered
| Category | Recommended | Alternative | Why not |
|---|---|---|---|
| Mobile framework | Expo (managed) | Bare React Native | First-time RN shipper risk; Expo handles Gradle/Xcode config; EAS Build is essentially free for solo dev |
| Mobile framework | Expo | Flutter | Founder has not stated Dart experience; React mental model + JS ecosystem broader; design doc locks RN at Week 0d |
| Backend lang | FastAPI (Python) | Node/Express, Hono | AI ecosystem is Python-native; pydantic+SQLAlchemy mature; founder's prior Python familiarity assumed |
| Hosting | Render free tier (Singapore) | Fly.io Mumbai / Railway Singapore | Both require a credit card on file in 2026 — fails the zero-CC bootstrap constraint (D-01). Fly.io Mumbai sub-20ms latency stays a deferred Phase-4 migration target only. |
| Hosting | Render | Self-hosted VPS (Hetzner) | Operational overhead unjustified at this scale; revisit at Phase 3+ if margin pressure demands |
| DB | Supabase Postgres (Mumbai) | Neon | Neon has no India region; Supabase is the only managed Postgres in Mumbai in price band |
| DB | Supabase | RDS Mumbai | AWS operational overhead too high for solo founder |
| Object storage | Cloudflare R2 (india jurisdiction) | S3 Mumbai (ap-south-1) | R2: zero egress, true jurisdictional guarantee; S3 charges egress per GB which compounds fast |
| Vision primary | Gemini 2.5 Flash | Gemini 2.0 Flash | **2.0 retires March 2026 — do not start here** |
| Vision primary | Gemini 2.5 Flash | Claude Sonnet vision | No free tier; cost/call ~10x Gemini Flash |
| Text primary | Groq Llama 3.3 70B | Together AI / Fireworks | Groq's 500+ tok/s + free RPD beat both on cost/latency for this scale |
| Auth | Firebase phone OTP | MSG91 + DLT | DLT registration friction; Firebase free tier sufficient through Phase 2 |
| Push | FCM v1 + Expo Push | OneSignal | OneSignal adds vendor; FCM is the default for Android-only V1; founder already adopting Firebase for auth |
| Payments | Razorpay | Cashfree, PayU | Razorpay's UPI Autopay maturity + dev docs lead the India market |
| Analytics | PostHog | Mixpanel | PostHog 1M events/mo free vs Mixpanel's 100K; PostHog includes feature flags + session replay free |
| Error monitoring | Sentry | Bugsnag | Sentry free tier + native Expo integration via Sentry Wizard |
| State mgmt | TanStack Query + Zustand | Redux Toolkit | Overkill for V1 scope; TanStack handles server state better than RTK Query for cache-first patterns |
## Installation (Phase 0d / Week 0 — locked stack)
### Backend bootstrap
# Use uv (faster than pip; standard 2026)
### Mobile bootstrap
### EAS Build setup
# Place google-services.json in assets/, reference in app.json under expo.android.googleServicesFile
### Cloudflare R2 (India jurisdiction)
# In Cloudflare dashboard → R2 → Create bucket
#   Location hint: choose "India" jurisdiction
#   Bucket name: ai-coach-meals-prod
# Endpoint: https://<account_id>.in.r2.cloudflarestorage.com
# Create API token scoped to this bucket
## India-Specific Constraints — Checklist
- [x] **DPDP residency:** Cloudflare R2 `india` jurisdiction (not just Mumbai PoP) + Supabase Mumbai region
- [x] **DPDP user rights:** "Delete my data" hard-delete cron at 30 days (Postgres + R2)
- [x] **DPDP consent:** Explicit opt-in screens for photo upload, profile, analytics (PostHog respects user-id opt-out)
- [x] **DPDP age gate:** 18+ check on signup (Firebase custom claims or app-side gate)
- [x] **EXIF stripping:** GPS metadata in photo is PII — strip via Pillow before R2 upload
- [x] **SMS DLT compliance:** Sidestepped via Firebase Auth in V1; revisit at scale
- [x] **Razorpay GST:** SDK handles GST line-items; founder registers GSTIN before ₹20L annual receipts
- [x] **CDSCO/ASCI:** Disclaimer copy in app + marketing: "Not medical advice."
## Anti-Pattern Index (DO NOT)
| # | Anti-pattern | Why bad | What to do instead |
|---|---|---|---|
| 1 | Start with Gemini **2.0** Flash | Retires March 2026; wasted prompt engineering | Gemini 2.5 Flash from day 0 |
| 2 | R2 Mumbai-edge bucket (no jurisdiction set) | Doesn't satisfy DPDP residency requirement | Set bucket jurisdiction to `india` |
| 3 | Sync FastAPI handlers + sync DB driver | Blocks event loop; dies at 50+ concurrent users | `async def` everywhere + `asyncpg` |
| 4 | LLM-direct macros from photo | Hallucinated numbers; breaches ±35% gate | Photo → dish-ID + portion (LLM) → IFCT lookup (deterministic) |
| 5 | Skip JPEG conversion (SDK 54 HEIC default) | Backend can't process HEIC; ~30% upload failures | `expo-image-manipulator` to JPEG before upload |
| 6 | Trust client-submitted phone number | Spoofable | Always `firebase-admin.verify_id_token()` server-side |
| 7 | Local notifications only for retention | Android kills them inconsistently | FCM server-driven scheduling |
| 8 | USDA FoodData as nutrition source | Western portions/ingredients | IFCT 2017 + INDB seed + dish-decomposition layer. **NB (D-30/D-31):** IFCT/INDB are license-gated (NIN written permission for commercial use) and INDB is a SEED not a drop-in (grams need conversion; IFCT table requested separately; no weighed image-linked truth) — do not assume free/instant. |
| 9 | MSG91 + DLT for V1 | 3-7 day registration delay; founder is in Gates 0a-0d | Firebase Auth phone OTP; defer MSG91 to Phase 3 |
| 10 | Stripe for India payments | Higher card decline rate; weaker UPI integration | Razorpay UPI Autopay |
| 11 | Card e-mandates over UPI Autopay for ₹299 | Higher failure rate at low ticket | UPI Autopay (₹15K limit suffices) |
| 12 | Redux Toolkit for V1 client state | Overkill; ceremony tax | Zustand + TanStack Query |
| 13 | Mixpanel free for analytics | 100K events too low for autocapture | PostHog (1M events free) |
| 14 | Self-hosted Postgres on VPS | Backup/HA/patching is solo-founder time sink | Supabase Mumbai managed |
| 15 | AWS RDS Mumbai | IAM/VPC overhead unjustified at this scale | Supabase or Fly Postgres |
| 16 | Local upload to R2 jurisdictional bucket | Not supported; uploads fail | Standard S3 multipart upload only |
| 17 | One Pydantic model = SQLAlchemy + API schema | Drift between DB schema and API surface | Separate `models/` (SQLA) and `schemas/` (Pydantic) |
| 18 | Hardcode AI provider in service code | Defeats `ai_provider.py` abstraction | Env-var-driven primary + fallback chain |
| 19 | Skip image compression pre-upload | 5x R2 storage cost + 3x vision token cost | `expo-image-manipulator` to ≤1280px / 0.7 quality |
| 20 | Ship without Sentry / PostHog in alpha | Can't debug crashes or measure D7 retention | Both wired up by Week 4 |
## Sources
### Verified via Context7 / Official Docs (HIGH confidence)
- [Expo SDK 54 documentation](https://docs.expo.dev) — `/expo/expo` Context7
- [FastAPI 0.128 documentation](https://fastapi.tiangolo.com) — `/fastapi/fastapi` Context7
- [SQLAlchemy 2.0 documentation](https://docs.sqlalchemy.org/en/20/) — `/websites/sqlalchemy_en_20`
- [Firebase JS SDK auth API](https://firebase.google.com/docs/auth/web/phone-auth) — `/websites/firebase_google`
- [Cloudflare R2 jurisdictions](https://developers.cloudflare.com/r2/reference/data-location/) — `/websites/developers_cloudflare_r2` (India jurisdiction confirmed)
- [OpenRouter free model rate limits](https://openrouter.ai/docs/faq) — `/websites/openrouter_ai`
- [Ollama Python SDK](https://github.com/ollama/ollama-python) — `/ollama/ollama-python`
- [Groq Python SDK](https://github.com/groq/groq-python) — `/groq/groq-python`
- [Razorpay Python SDK](https://github.com/razorpay/razorpay-python) — `/razorpay/razorpay-python`
### Verified via WebSearch (MEDIUM confidence)
- [Gemini API rate limits 2026](https://ai.google.dev/gemini-api/docs/rate-limits) — Gemini 2.0 retirement March 2026, 2.5 Flash limits
- [Groq free tier 2026](https://console.groq.com/docs/rate-limits) — 30 RPM / 6K TPM / 1000 RPD
- [Fly.io Mumbai region pricing](https://fly.io/pricing/) — bom1 region, $1.94/mo shared CPU
- [Railway pricing 2026](https://railway.com/pricing) — Singapore region, $5/mo Hobby
- [Supabase pricing 2026](https://supabase.com/pricing) — Mumbai region available, 500MB free
- [Neon vs Supabase Mumbai 2026](https://agentdeals.dev/neon-vs-supabase) — Confirms Neon has no India region
- [Razorpay UPI Autopay guide](https://razorpay.com/blog/master-recurring-payments-upi-autopay-guide/) — ₹15K limit, ₹299 example
- [Firebase Auth pricing](https://firebase.google.com/pricing) — 50K MAU free, phone OTP included
- [Expo SDK 54 + Firebase phone auth](https://rnfirebase.io/auth/phone-auth) — dev client required
- [FCM v1 API mandatory 2026](https://docs.expo.dev/push-notifications/sending-notifications-custom/) — service account JSON required
- [Qwen 2.5 VL OpenRouter free](https://openrouter.ai/qwen/qwen2.5-vl-72b-instruct:free) — 32B and 72B free variants
### Confidence Summary
| Area | Confidence | Reason |
|---|---|---|
| Mobile (Expo SDK 54 + RN 0.81) | **HIGH** | Context7-verified, current as of Jan 2026 |
| Backend (FastAPI 0.128 + SQLA 2.0) | **HIGH** | Context7-verified, mature pattern |
| Hosting (Fly Mumbai vs Railway SG) | **HIGH** | Official pricing pages 2026 |
| Storage (R2 india jurisdiction) | **HIGH** | Cloudflare docs explicit |
| Database (Supabase Mumbai) | **HIGH** | Supabase region docs |
| Auth (Firebase phone OTP) | **HIGH** | Firebase docs + Expo integration guides |
| AI providers (Gemini/Groq/OpenRouter) | **HIGH** | Multiple 2026-dated sources align on limits |
| Payments (Razorpay UPI Autopay) | **HIGH** | Razorpay official 2026 docs |
| Nutrition (IFCT 2017 + INDB) | **MEDIUM** | INDB verified live (1,014 recipes, seed-only — grams need conversion); IFCT/INDB commercial use is license-gated, NIN written permission required (D-30/D-31) |
| Analytics (PostHog) | **HIGH** | PostHog docs + comparison sources |
## Roadmap Implications
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
