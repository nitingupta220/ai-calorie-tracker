# Requirements: AI Personal Coach — Indian Youth

**Defined:** 2026-05-27
**Core Value:** A user can photograph their Indian meal and immediately get accurate macros + one specific, budget-aware, veg-protein-gap-closing next action grounded in their own recent log — so they trust the app more than their gym trainer.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Pre-Build Validation Gates (Week 0)

- [ ] **GATE-01**: Founder captures 30-photo benchmark stratified across 10 single-dish / 10 mixed / 10 thali; Gemini 2.5 Flash recognition ≥70% dish-name match, ≥60% macros within ±35% of IFCT-derived ground truth (per-bucket pass bar)
- [ ] **GATE-02**: Founder logs 14 days of own meals through validated vision pipeline + advice engine; ≥70% of advice replies score 4/4 on rubric (specific food + specific quantity + ₹ cost or pantry mention + reference to recent log)
- [ ] **GATE-03**: Founder identifies 20 named Trial Users with WhatsApp contact; ≥10 verbal commitments; ≥3 verbatim price-WTP quotes ("I'd pay ₹299/mo for...")
- [ ] **GATE-04**: Tech stack locked (Expo + RN + FastAPI + Supabase Mumbai + R2 india-jurisdiction + Firebase OTP + ai_provider.py abstraction); compute hosting locked to Render free Singapore per D-01 (Fly.io/Railway rejected — credit-card required); Play Developer account purchased ($25) + identity verification submitted

### Infrastructure & AI Provider Abstraction (INFRA)

- [ ] **INFRA-01**: `ai_provider.py` abstraction implemented with VisionProvider + TextProvider classes; all LLM access funnels through this module (lint rule enforces no direct provider SDK imports outside `providers/`)
- [ ] **INFRA-02**: Vision provider chain wired with 429-fallback: Gemini 2.5 Flash (free → paid) → OpenRouter Qwen 2.5 VL (free) → GPT-4o-mini (paid)
- [ ] **INFRA-03**: Text provider chain wired with 429-fallback: Groq Llama 3.3 70B (free) → OpenRouter (free) → Gemini 2.5 Flash (paid)
- [ ] **INFRA-04**: Per-call provider tag + cost log persisted per request for attribution
- [ ] **INFRA-05**: FastAPI 0.128 + Pydantic v2 + SQLAlchemy 2.0 async + asyncpg + Alembic backend skeleton with `/healthz` and structured logging
- [ ] **INFRA-06**: Supabase Mumbai Postgres connected; Alembic baseline migration with `users`, `meal_photo`, `daily_summary`, `streak`, `push_event`, `consent_log`, `correction_event` tables
- [ ] **INFRA-07**: Cloudflare R2 bucket created with `jurisdiction=india` endpoint (`<acct>.in.r2.cloudflarestorage.com`); presigned PUT URL endpoint working from mobile client
- [ ] **INFRA-08**: Hosting deployed (Render free tier, Singapore — per D-01); `/healthz` reachable from EAS dev client

### Authentication (AUTH)

- [ ] **AUTH-01**: User signs up via Firebase phone OTP (Indian +91 numbers); server verifies ID token via firebase-admin
- [ ] **AUTH-02**: User session persists across app restarts (Firebase refresh token)
- [ ] **AUTH-03**: User signs out from settings; session cleared
- [ ] **AUTH-04**: Hard age gate (18+) at signup; under-18 rejected with explanation
- [ ] **AUTH-05**: Account deletion via in-app "Delete my data" button — soft-delete user record + flag photos + logs for 30-day hard-delete cron

### Onboarding (ONBOARD)

- [ ] **ONBOARD-01**: Onboarding asks: goal (muscle gain — V1 only), height, weight, age, activity level, veg/non-veg, daily food budget bucket (₹100-150 / ₹150-250 / ₹250+)
- [ ] **ONBOARD-02**: Target macros computed using ISSN 2024 protein guideline (1.8 g/kg for muscle-gain) + standard calorie maintenance formula; surfaced to user after onboarding
- [ ] **ONBOARD-03**: Granular DPDP consent screen — photo upload, profile data, analytics each with separate toggle; AI-training opt-in defaults to OFF
- [ ] **ONBOARD-04**: Push notification permission rationale screen before OS prompt (Android 13+); deferral handled gracefully
- [ ] **ONBOARD-05**: CDSCO/ASCI disclaimer ("Not medical advice...") shown once during onboarding; saved as acknowledged

### Photo Tracking (TRACK)

- [ ] **TRACK-01**: User opens camera in-app via `expo-camera`; captures meal photo
- [ ] **TRACK-02**: Reference-object overlay guide (coin / palm in frame) shown during capture; tooltip + visual cue
- [ ] **TRACK-03**: Photo compressed via `expo-image-manipulator` to JPEG ≤1280px, quality 0.7, EXIF stripped (location/device removed); HEIC/AVIF converted
- [ ] **TRACK-04**: Photo uploaded via presigned PUT directly to R2 india jurisdiction; backend never proxies bytes
- [ ] **TRACK-05**: Backend vision pipeline: photo URL → Gemini 2.5 Flash → dish name + portion estimate + per-item confidence; two-step (vision → dish decomposition → IFCT lookup → macros aggregate)
- [ ] **TRACK-06**: 50-dish pan-Indian whitelist recognized: 15 pan-India (roti, rice, dal, sabzi, paneer, chicken, egg, fish, curd, milk, chai, paratha, chana/rajma, bread, fruits) + 12 North (butter chicken, biryani, naan, kofta, poha, upma, pav bhaji, samosa, chole, palak paneer, dahi vada, kulcha) + 12 South (idli, dosa, sambar, rasam, vada, uttapam, curd rice, lemon rice, pongal, appam, veg stew) + 11 West/East (misal pav, vada pav, dhokla, thepla, machher jhol, litti chokha, dhansak, khichdi, bhindi, omelette, french toast)
- [ ] **TRACK-07**: Out-of-whitelist dishes return "Not recognized — log manually" with free-text macros entry fallback
- [ ] **TRACK-08**: Photo-to-macros result returned to client within 8s P95 (single API call); 6s hard timeout on advice task with macros-only fallback
- [ ] **TRACK-09**: Vision confidence gate: if >3 items detected OR any item confidence <0.6, render "Tap each item to confirm" UX before final macros lock
- [ ] **TRACK-10**: IFCT 2017 nutrition data shipped in-repo as `data/ifct_2017.sqlite`; 50-dish ground-truth decomposition table at `data/dish_decomposition.json`

### Inline Advice Engine (ADVICE)

- [ ] **ADVICE-01**: Every meal-photo result includes 1-2 sentence advice rendered inline on `<MacrosCard />` as `<AdviceInline />` child component (never a separate tab)
- [ ] **ADVICE-02**: Advice prompt includes: user goal + target macros + last-3-days meal log + day-so-far totals + budget bucket + veg/non-veg + current dish + ₹/gram veg-protein reference table
- [ ] **ADVICE-03**: Advice scored server-side against 4/4 rubric: (a) specific food cited, (b) specific quantity in g/units, (c) ₹ cost or pantry mention, (d) reference to user's recent log; rejected advice retried once before falling back to per-dish hand-written template
- [ ] **ADVICE-04**: Prompt versioned (semver, committed to repo at `prompts/advice_v0.json`); version recorded with each generated advice for A/B traceability
- [ ] **ADVICE-05**: Vegetarian-protein-gap ₹/gram reference table built from founder-curated Indian market prices (paneer, dal, eggs, soya, chana, peanut, etc.); committed as `data/veg_protein_prices.json` with date stamp
- [ ] **ADVICE-06**: CDSCO/ASCI disclaimer permanently rendered as footer text on every advice card

### Meal History & Correction (HISTORY)

- [ ] **HISTORY-01**: Home screen shows day's totals (kcal + protein/carbs/fat) with progress vs target
- [ ] **HISTORY-02**: Last 3 days meal log viewable via "History" tab; each meal shows photo thumbnail + dish + macros + advice
- [ ] **HISTORY-03**: User taps dish name on macros card → edit sheet opens; user corrects dish name or per-macro values; saved via `PATCH /meals/{id}`
- [ ] **HISTORY-04**: Every correction persisted in append-only `correction_event` table from day 1 (used for V1.5 fine-tuning corpus); never overwritten
- [ ] **HISTORY-05**: Manual weight log — user enters weight (kg) on dedicated screen; weight history viewable; minimum daily granularity
- [ ] **HISTORY-06**: Water intake tracker — 1-tap home-screen button to log 250ml; day's running total shown; resets at midnight IST

### Retention Loop (RETAIN)

- [ ] **RETAIN-01**: FCM device token registered at signup; stored per-user in `push_event` table
- [ ] **RETAIN-02**: APScheduler in-process worker schedules daily 8pm IST push per user with personalized copy ("You're at 42g protein, target 88g. Log dinner to close the gap.")
- [ ] **RETAIN-03**: Streak counter on home — 3-day / 7-day / 14-day badges; visual reset framing on break ("Best streak: 5 days")
- [ ] **RETAIN-04**: Push delivery success + open-rate logged for analytics
- [ ] **RETAIN-05**: User can mute / configure push notifications in settings; opt-in/out respected

### Compliance & Privacy (COMP)

- [ ] **COMP-01**: DPDP Act 2023 region pinning verified by automated check at boot: R2 jurisdiction=india + Supabase region=Mumbai; deploy fails if mismatch
- [ ] **COMP-02**: Privacy Policy live at app-bundled URL before any Play Store submission
- [ ] **COMP-03**: Consent ledger (`consent_log`) records every consent grant/revoke event with timestamp + consent type + user_id
- [ ] **COMP-04**: 30-day hard-delete cron: soft-deleted accounts + their photos + logs purged from R2 + Postgres within 30 days; audit log of deletions retained 365 days
- [ ] **COMP-05**: User-facing "Export my data" button (DPDP Right to Access) — generates JSON export of profile + meal logs + corrections, emailed to user
- [ ] **COMP-06**: ASCI-compliant marketing copy — no claims to "treat / cure / diagnose"; trainer-replacement framing reviewed for fitness-not-medical
- [ ] **COMP-07**: Play Store Data Safety form pre-filled accurately reflecting data collection + retention
- [ ] **COMP-08**: CDSCO banned-words lint check on marketing copy + in-app strings (treat/cure/diagnose/medicine/drug)
- [ ] **COMP-09**: AI training on user data requires explicit opt-in (default OFF); opt-in toggle in settings; revoke purges user data from any training corpus

### Wizard-of-Oz QA Gate (WOZ — promoted from task to gate)

- [ ] **WOZ-01**: Founder personally writes 5-7 advice replies per day for 5 Trial Users for 7 days = ≥35 hand-written advice examples captured as ground truth
- [ ] **WOZ-02**: AI-generated advice for same user-meals compared side-by-side; AI matches WoZ quality ≥70% on 4/4 rubric before automated advice goes live in alpha (Phase 6 entry gate)
- [ ] **WOZ-03**: Hand-written examples folded back into advice prompt as in-context learning examples (top-performing rubric matches)

### Internal Alpha Distribution (ALPHA)

- [ ] **ALPHA-01**: Play Internal Testing track configured; 20 hand-recruited Trial Users invited via Google account email
- [ ] **ALPHA-02**: Pre-launch load test passed: 20 concurrent uploads at dinner-hour, ≥95% success, P95 <8s
- [ ] **ALPHA-03**: Fallback drill completed: 10% traffic routed through OpenRouter for 24h, no quality regression observed
- [ ] **ALPHA-04**: Sentry + PostHog wired; per-user cost telemetry dashboard live before alpha invites sent
- [ ] **ALPHA-05**: Alpha retention gate (Gate 7): ≥5/20 users log meal photo on 7 consecutive days within 14-day alpha window; below 5, public launch deferred

### Public Launch (LAUNCH)

- [ ] **LAUNCH-01**: Google Play Store Production track submission Week 12 (not 14) to buffer 7-14 day first-developer review
- [ ] **LAUNCH-02**: ASO listing live (icon, screenshots, description, keywords); ASCI-compliant marketing copy in listing
- [ ] **LAUNCH-03**: Public launch on Production track Week 14+ only after Gate 7 + ASCI/CDSCO review passes
- [ ] **LAUNCH-04**: Post-launch monitoring — vision accuracy on real-user photos sustained ≥75%, advice 4/4-rubric rate ≥75% on samples, AI cost per active user ≤₹15/mo

### CEO Scope Expansions (CEO — locked /plan-ceo-review 2026-05-28)

- [ ] **REQ-CEO-01**: WhatsApp share-photo install hook via Meta WhatsApp Cloud API direct (1K free conversations/mo, no CC — Aadhaar/PAN/GSTIN verification) — new `POST /whatsapp/webhook` route reusing `ai_provider.py` + advice engine; response footer = install CTA; `whatsapp_session` table with 24h TTL (DPDP §5 legitimate-use, pre-install lawful basis via inline consent footer); Indian BSP fallback (Interakt / AiSensy) pre-onboarded before public launch (D-CEO-01)
- [ ] **REQ-CEO-02**: Own-rank social streak pill ("47th in Mumbai · 7-day streak") — `streak_event` table + nightly cron at 22:00 UTC (03:30 IST) computes city-month-cohort percentiles; opt-in via Settings (default OFF for DPDP minimization); pill hides if cohort < 5 opt-ins; server-computed (mobile renders rank, never computes); top-N cohort leaderboard deferred to V1.1 (D-CEO-02)
- [ ] **REQ-CEO-03**: ₹/protein budget optimizer screen in Tools tab — lookup-only V1: SQL aggregation over `veg_protein_prices` table, filter veg/non-veg/vegan + ₹ budget typed input, top-3 results highlighted with "BEST VALUE" pill; no new ML or data; V1.5 deferred: spend aggregation + grocery-list export to BigBasket/Zepto/Blinkit (D-CEO-03)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Weight-Loss Goal (V1.1)

- **V1.1-01**: Weight-loss goal track in onboarding (calorie deficit + protein-preservation advice)
- **V1.1-02**: Trigger: muscle-gain V1 D7 retention ≥25% AND advice 4/4 rate ≥75% before V1.1 ships

### Paid Tier (Phase 3, Month 4+)

- **PAID-01**: Razorpay UPI Autopay subscription at ₹299/mo
- **PAID-02**: GSTIN registration completed before annual receipts cross ₹20L threshold
- **PAID-03**: Paywall placement — free tier limited to N photos/day; subscription unlocks unlimited
- **PAID-04**: Trial-end conversion flow with 7-day grace
- **PAID-05**: Razorpay 2.36% effective fee modelled into pricing

### V1.5 Expansion

- **V15-01**: Whitelist expansion from 50 to 100 dishes
- **V15-02**: 14-day photo-history window (V1 = 3-day)
- **V15-03**: Multi-meal thali single-photo support
- **V15-04**: South Indian + Bengali + Gujarati + Maharashtrian regional cuisine deep coverage

### V2 (later)

- **V2-01**: Apple App Store iOS support
- **V2-02**: Hindi + regional language voice + text input
- **V2-03**: Workout programs / exercise tracking
- **V2-04**: Social features (groups, leaderboards, sharing)
- **V2-05**: Housewife / 30-45 female persona with separate brand
- **V2-06**: Pre-diabetic / medical-niche mode (CDSCO compliance work required)
- **V2-07**: Self-hosted Qwen 2.5 VL vision (cost lever at >1k DAU)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| AI chat tab / coach mode | Burying advice in a tab collapses the inline-advice moat (P1) |
| Email/password signup | Phone OTP is canonical for India; email sign-in adds surface for no value |
| Web app | Mobile-first; web later if at all |
| Barcode scanning | Indian packaged food coverage poor; photo-first covers more of daily eating |
| Restaurant menu database | Adds complexity; users mostly track ghar-ka-khana |
| Multi-photo combo meals in V1 | Single-photo flow is install hook; combos add UX complexity → V1.5 |
| Wearable integration (Fitbit, Apple Watch, Mi Band) | V2+; bootstrap solo doesn't have bandwidth for device pairing flows |
| Real-time chat with human dietician | Defeats AI-coach positioning + cannibalizes ₹299/mo price point |
| Social feed / groups / leaderboards | Retention before community; streaks suffice for V1 |
| AI training on user photos without opt-in | DPDP risk; default OFF, explicit opt-in required |
| Auto-detect from gallery (HealthifyMe Auto Snap clone) | DPDP consent surface complicates V1; revisit V1.5 |
| iOS in V1 | $99/yr fee + halves V1 surface; target persona Android in India |
| English-only out-of-context advice (Western diet recommendations) | Violates wedge; advice must be Indian-veg-budget-aware always |
| Generic "eat more protein" advice | Moat collapse trigger; advice must reference user log specifically (4/4 rubric) |
| Wizard-of-Oz advice as user-facing product mode | Used only as QA gate, not as product mode |

## Traceability

Which phases cover which requirements. Updated during roadmap creation. Mapped against 5-phase coarse vertical-MVP roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| GATE-01 | Phase 1 | Pending |
| GATE-02 | Phase 1 | Pending |
| GATE-03 | Phase 1 | Pending |
| GATE-04 | Phase 1 | Pending |
| INFRA-01 | Phase 2 | Pending |
| INFRA-02 | Phase 2 | Pending |
| INFRA-03 | Phase 2 | Pending |
| INFRA-04 | Phase 2 | Pending |
| INFRA-05 | Phase 2 | Pending |
| INFRA-06 | Phase 2 | Pending |
| INFRA-07 | Phase 2 | Pending |
| INFRA-08 | Phase 2 | Pending |
| AUTH-01 | Phase 2 | Pending |
| AUTH-02 | Phase 2 | Pending |
| AUTH-03 | Phase 3 | Pending |
| AUTH-04 | Phase 2 | Pending |
| AUTH-05 | Phase 2 | Pending |
| ONBOARD-01 | Phase 3 | Pending |
| ONBOARD-02 | Phase 3 | Pending |
| ONBOARD-03 | Phase 3 | Pending |
| ONBOARD-04 | Phase 3 | Pending |
| ONBOARD-05 | Phase 3 | Pending |
| TRACK-01 | Phase 3 | Pending |
| TRACK-02 | Phase 3 | Pending |
| TRACK-03 | Phase 3 | Pending |
| TRACK-04 | Phase 2 | Pending |
| TRACK-05 | Phase 2 | Pending |
| TRACK-06 | Phase 2 | Pending |
| TRACK-07 | Phase 2 | Pending |
| TRACK-08 | Phase 2 | Pending |
| TRACK-09 | Phase 2 | Pending |
| TRACK-10 | Phase 2 | Pending |
| ADVICE-01 | Phase 2 | Pending |
| ADVICE-02 | Phase 2 | Pending |
| ADVICE-03 | Phase 2 | Pending |
| ADVICE-04 | Phase 2 | Pending |
| ADVICE-05 | Phase 2 | Pending |
| ADVICE-06 | Phase 2 | Pending |
| HISTORY-01 | Phase 3 | Pending |
| HISTORY-02 | Phase 3 | Pending |
| HISTORY-03 | Phase 2 | Pending |
| HISTORY-04 | Phase 2 | Pending |
| HISTORY-05 | Phase 3 | Pending |
| HISTORY-06 | Phase 3 | Pending |
| RETAIN-01 | Phase 3 | Pending |
| RETAIN-02 | Phase 3 | Pending |
| RETAIN-03 | Phase 3 | Pending |
| RETAIN-04 | Phase 3 | Pending |
| RETAIN-05 | Phase 3 | Pending |
| COMP-01 | Phase 2 | Pending |
| COMP-02 | Phase 3 | Pending |
| COMP-03 | Phase 2 | Pending |
| COMP-04 | Phase 2 | Pending |
| COMP-05 | Phase 2 | Pending |
| COMP-06 | Phase 3 | Pending |
| COMP-07 | Phase 4 | Pending |
| COMP-08 | Phase 2 | Pending |
| COMP-09 | Phase 2 | Pending |
| WOZ-01 | Phase 3 | Pending |
| WOZ-02 | Phase 3 | Pending |
| WOZ-03 | Phase 3 | Pending |
| ALPHA-01 | Phase 4 | Pending |
| ALPHA-02 | Phase 4 | Pending |
| ALPHA-03 | Phase 4 | Pending |
| ALPHA-04 | Phase 4 | Pending |
| ALPHA-05 | Phase 4 | Pending |
| LAUNCH-01 | Phase 4 | Pending |
| LAUNCH-02 | Phase 4 | Pending |
| LAUNCH-03 | Phase 5 | Pending |
| LAUNCH-04 | Phase 5 | Pending |
| REQ-CEO-01 | Phase 2 (table+stub) | Pending |
| REQ-CEO-01 | Phase 4 (wire) | Pending |
| REQ-CEO-02 | Phase 2 (cron) | Pending |
| REQ-CEO-02 | Phase 3 (mobile) | Pending |
| REQ-CEO-03 | Phase 3 | Pending |
| V1.1-02 (trigger) | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 70 total (4 gates + 8 infra + 5 auth + 5 onboard + 10 track + 6 advice + 6 history + 5 retain + 9 comp + 3 woz + 5 alpha + 4 launch + 3 CEO + 1 V1.1 trigger / V1.1-02 trigger evaluated in Phase 5; V1.1-01 deferred-but-tracked)
- Mapped to phases: 70 / 70 (REQ-CEO-01 spans Phase 2 table+stub + Phase 4 wire; REQ-CEO-02 spans Phase 2 cron + Phase 3 mobile)
- Unmapped: 0

**Per-phase counts:**
- Phase 1 (Validation Gates + Stack Lock): 4 (GATE-01..04)
- Phase 2 (Photo → Macros End-to-End): 33 (INFRA-01..08 + AUTH-01,02,04,05 + TRACK-04..10 + ADVICE-01..06 + HISTORY-03,04 + COMP-01,03,04,05,08,09 + REQ-CEO-01 table+stub + REQ-CEO-02 cron)
- Phase 3 (Mobile App + Inline Advice + Retention): 24 (AUTH-03 + ONBOARD-01..05 + TRACK-01,02,03 + HISTORY-01,02,05,06 + RETAIN-01..05 + WOZ-01..03 + COMP-02,06 + REQ-CEO-02 mobile + REQ-CEO-03)
- Phase 4 (Alpha Hardening + Launch Submission): 9 (ALPHA-01..05 + COMP-07 + LAUNCH-01,02 + REQ-CEO-01 wire)
- Phase 5 (Public Launch + Paid Tier + V1.1): 3 (LAUNCH-03,04 + V1.1-02 trigger)

**Sum check:** 4 + 33 + 24 + 9 + 3 = 73 (= 70 v1 + REQ-CEO-01 counted in both Phase 2 and Phase 4 + REQ-CEO-02 counted in both Phase 2 and Phase 3 + V1.1-02 trigger evaluated as a Phase-5 gate)

---
*Requirements defined: 2026-05-27 (YOLO mode + auto-synthesis from PROJECT.md + research/SUMMARY.md + design doc iteration 4)*
*Last updated: 2026-05-27 — traceability mapped to 5-phase coarse vertical-MVP roadmap*
