# Roadmap: AI Personal Coach — Indian Youth

## Overview

Vertical-MVP delivery of an Android nutrition coach for urban Indian youth (18-30). Each phase ships an end-to-end, user-visible slice — never a horizontal layer. Phase 1 locks risk gates + stack + DPDP plumbing readiness before any production code. Phase 2 delivers the photo → macros + inline advice spine on the server. Phase 3 puts that spine in a user's hand via the Expo app, gated by Wizard-of-Oz QA. Phase 4 hardens for a closed alpha and proves Gate 7 retention. Phase 5 ships to public Production and unlocks the V1.1 weight-loss track + paid tier. Coarse granularity per `config.json` — 5 broader phases, each a complete vertical slice.

All v1 code is deferred until Phase 1 gates pass; design-doc artifacts (`.planning/decisions/`, prompt schemas, decomposition tables) must be written first within each phase before implementation begins.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4, 5): Planned milestone work
- Decimal phases (e.g., 2.1): Reserved for urgent insertions

- [ ] **Phase 1: Validation Gates + Stack Lock** - Risk gates 0a-0d pass, stack corrections locked, Play account purchased, hosting picked — no production code until all four gates green
- [ ] **Phase 2: Photo → Macros End-to-End (Backend Spine)** - Server-side vertical slice: photo upload → vision → dish decomposition → IFCT macros → inline advice → correction capture, with DPDP plumbing pulled forward to Week 1
- [ ] **Phase 3: Mobile App + Inline Advice + Retention** - Expo Android app delivers the full user-facing slice: onboarding, camera, MacrosCard with inline advice, manual weight, water tracker, daily 8pm push, streaks; gated by WoZ QA
- [ ] **Phase 4: Alpha Hardening + Launch Submission** - Pre-alpha load test, Sentry/PostHog, cost telemetry, 20-user closed alpha, DPDP capstone audit, Gate 7 retention validation, Play Production submission Week 12
- [ ] **Phase 5: Public Launch + Paid Tier + V1.1** - Public Production launch, post-launch monitoring, Razorpay UPI Autopay + GSTIN, V1.1 weight-loss goal track (trigger-gated on D7 ≥25% + advice 4/4 ≥75%)

## Phase Details

### Phase 1: Validation Gates + Stack Lock
**Goal**: Prove the four mandatory risk gates pass and lock all stack + compliance + distribution decisions before a single line of production code is written.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: GATE-01, GATE-02, GATE-03, GATE-04
**Success Criteria** (what must be TRUE):
  1. Founder has run 30 **weighed**, reference-object meal photos (10 single / 10 mixed / 10 thali) through Gemini 2.5 Flash and demonstrated dish-ID ≥80% AND macros within ±35% of weighed truth (≥70% single / ≥60% mixed); thali is reported-only/non-blocking (V1.5) (Gate 0a, recalibrated 2026-06-02)
  2. Founder has logged 14 days of own meals through the validated pipeline + advice engine; ≥70% of replies score 4/4 on the rubric (specific food + quantity + ₹ cost + log reference) (Gate 0b)
  3. Founder has ≥10 verbal commitments + ≥3 verbatim price-WTP quotes from 20 named Trial Users on WhatsApp (Gate 0c)
  4. Stack is locked in `.planning/decisions/` — Expo + RN + FastAPI + Supabase Mumbai + R2 `jurisdiction=india` + Firebase OTP + `ai_provider.py` abstraction + Gemini 2.5 Flash (not 2.0) + compute hosting = Render free Singapore per D-01 (Gate 0d)
  5. Google Play Developer account purchased ($25), identity verification submitted, 3-7 day clock started before Phase 2 begins
**Plans:** 7 plans

Plans:
- [ ] 01-01-PLAN.md — INDB integration + dish_decomposition.json (Gate 0a prerequisite, Wave 1)
- [ ] 01-02-PLAN.md — IFCT/INDB license emails (Gate 0d / launch gate, Wave 1)
- [ ] 01-03-PLAN.md — veg_protein_prices seed CSV collection (Gate 0b enabler, Wave 1)
- [ ] 01-04-PLAN.md — Gate 0a photos: 30 weighed photos + Opus labeling (Wave 2, depends 01-01)
- [ ] 01-05-PLAN.md — Gate 0b: 14-day WoZ meal log + advice rubric scoring (Wave 1)
- [ ] 01-06-PLAN.md — Gate 0c: WhatsApp outreach + WTP quotes (Wave 1)
- [ ] 01-07-PLAN.md — Gate 0d: stack lock summary + Play Console (Wave 2, depends all)

### Phase 2: Photo → Macros End-to-End (Backend Spine)
**Goal**: Stand up the full server-side vertical slice — a user photo posted to the API returns dish name, macros, inline advice, and persists a correction-ready record — with DPDP plumbing baked in from day one.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06, INFRA-07, INFRA-08, AUTH-01, AUTH-02, AUTH-04, AUTH-05, TRACK-04, TRACK-05, TRACK-06, TRACK-07, TRACK-08, TRACK-09, TRACK-10, ADVICE-01, ADVICE-02, ADVICE-03, ADVICE-04, ADVICE-05, ADVICE-06, HISTORY-03, HISTORY-04, COMP-01, COMP-03, COMP-04, COMP-05, COMP-08, COMP-09, REQ-CEO-01 (table+stub), REQ-CEO-02 (cron)
**Success Criteria** (what must be TRUE):
  1. A meal photo uploaded by presigned PUT to Cloudflare R2 india jurisdiction is processed end-to-end by the FastAPI backend and returns dish name + macros + 1-2 sentence inline advice within an 8s P95 budget through a single API response (no separate advice fetch)
  2. The vision pipeline correctly identifies all 50 whitelist dishes via Gemini 2.5 Flash, decomposes them into IFCT 2017 ingredients using the founder-curated `data/dish_decomposition.json`, and aggregates macros — out-of-whitelist dishes return "Not recognized — log manually"
  3. The advice engine renders inline only when output passes the 4/4 server-side rubric validator (specific food + quantity + ₹ cost + recent-log reference); rejected advice retries once before falling back to per-dish hand-written templates; every call routes through `ai_provider.py` (lint rule enforces no provider SDK imports outside `providers/`) with 429-fallback verified on Gemini → OpenRouter → paid
  4. DPDP plumbing is verifiable on a boot check: R2 `jurisdiction=india` confirmed, Supabase region=Mumbai confirmed, `consent_log` + `correction_event` + `soft_delete_at` columns live, EXIF strip applied, age-18+ field on user record, 30-day hard-delete cron green
  5. Firebase phone-OTP signup + token verification works end-to-end via `firebase-admin`; a session token can be issued, persisted, and a "Delete my data" call soft-deletes the user with audit trail
**Plans**: TBD

### Phase 3: Mobile App + Inline Advice + Retention
**Goal**: Put the validated backend spine in a user's hands — a usable Expo Android app delivering onboarding, camera capture, MacrosCard with inline advice, history, corrections, manual weight, water tracker, daily push, and streaks — gated by Wizard-of-Oz QA before any automated advice goes live to Trial Users.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: AUTH-03, ONBOARD-01, ONBOARD-02, ONBOARD-03, ONBOARD-04, ONBOARD-05, TRACK-01, TRACK-02, TRACK-03, HISTORY-01, HISTORY-02, HISTORY-05, HISTORY-06, RETAIN-01, RETAIN-02, RETAIN-03, RETAIN-04, RETAIN-05, WOZ-01, WOZ-02, WOZ-03, COMP-02, COMP-06, REQ-CEO-02 (mobile), REQ-CEO-03
**Success Criteria** (what must be TRUE):
  1. A new user installs the Expo Android app, completes phone-OTP signup, walks through onboarding (goal / body / activity / veg-non-veg / budget / granular DPDP consents with AI-training default OFF / push permission rationale / CDSCO-ASCI disclaimer), and lands on a home screen showing day's kcal + protein/carbs/fat progress vs ISSN-2024 1.8 g/kg muscle-gain target
  2. The user opens the in-app camera with a reference-object overlay guide, captures a meal, sees the photo compressed (≤1280px JPEG / q=0.7 / EXIF stripped / HEIC-AVIF converted) and uploaded by presigned PUT, and within 8s P95 receives a `<MacrosCard />` with `<AdviceInline />` child + CDSCO disclaimer footer rendered together
  3. The user can view the last 3 days of meals as photo thumbnails, tap a dish name or macros value to open the edit sheet, save corrections via `PATCH /meals/{id}` (persisted append-only in `correction_event`), log manual weight on a dedicated screen, and 1-tap log 250ml water from the home screen
  4. Daily 8pm IST personalized push fires via FCM + APScheduler ("You're at 42g protein, target 88g. Log dinner to close the gap."), open-rate is logged, the user can mute in settings, and 3/7/14-day streak badges render with recovery framing on break
  5. Wizard-of-Oz QA Gate has passed: ≥35 founder-written advice examples captured across 5 Trial Users × 7 days; side-by-side AI-vs-WoZ comparison shows ≥70% match on the 4/4 rubric; top-performing examples folded into the prompt as in-context learning — Phase 4 entry is BLOCKED until this is met
**Plans**: TBD
**UI hint**: yes

### Phase 4: Alpha Hardening + Launch Submission
**Goal**: Harden the app for production load, run a 20-user closed alpha, complete the DPDP public-facing capstone, validate Gate 7 retention, and submit to Play Production Week 12 (not 14) to buffer the 7-14 day first-developer review.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: ALPHA-01, ALPHA-02, ALPHA-03, ALPHA-04, ALPHA-05, COMP-07, LAUNCH-01, LAUNCH-02, REQ-CEO-01 (wire)
**Success Criteria** (what must be TRUE):
  1. Pre-alpha load test passes — 20 concurrent uploads at simulated dinner-hour with ≥95% success rate and P95 <8s; fallback drill completes with 10% traffic routed through OpenRouter for 24h with no quality regression observed
  2. Sentry + PostHog wired across mobile and backend; per-user cost telemetry dashboard live and shows AI cost per active user ≤₹15/mo before any alpha invite is sent
  3. 20 hand-recruited Trial Users invited via Play Internal Testing track and active in the 14-day alpha window; daily dashboards track correction rate, push CTR, D1→D2 drop-off, vision accuracy, and cost/user; WhatsApp DM check-ins captured on day 3 and day 5
  4. DPDP capstone shipped: Privacy Policy live at app-bundled URL, hard-delete cron audited end-to-end on a real soft-deleted account, Data Safety form pre-filled accurately, CDSCO/ASCI banned-words lint passes on marketing copy + in-app strings
  5. Gate 7 retention validated — ≥5/20 users log a meal photo on 7 consecutive days within the 14-day alpha window; ASO listing (icon, screenshots, ASCI-compliant description, keywords) live; Production track submission filed Week 12
**Plans**: TBD

### Phase 5: Public Launch + Paid Tier + V1.1
**Goal**: Flip the app to Production for the open public, sustain accuracy + cost + advice-quality bars on real users, open the paid tier on Razorpay UPI Autopay once retention is proven, and unlock V1.1 weight-loss when its triggers are met.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: LAUNCH-03, LAUNCH-04, V1.1-02 (trigger), PAID-01 through PAID-05 deferred-but-tracked, V1.1-01 deferred-but-tracked
**Success Criteria** (what must be TRUE):
  1. Public launch on Play Production track completes Week 14+ after Gate 7 + ASCI/CDSCO review pass; install funnel is live and ASO listing is reachable
  2. Post-launch monitoring sustains vision accuracy ≥75% on real-user photos, advice 4/4-rubric rate ≥75% on sampled replies, and AI cost per active user ≤₹15/mo over the first 30 days
  3. Razorpay account opened with a test ₹1 transaction, GSTIN registration complete before annual receipts cross ₹20L threshold, paid tier (₹299/mo UPI Autopay) ships behind a feature flag with 7-day trial-end grace flow
  4. V1.1 weight-loss goal track ships only after both triggers are met: muscle-gain V1 D7 retention ≥25% AND advice 4/4-rubric rate ≥75% sustained for 14 days; otherwise V1.1 is deferred without scope creep
  5. Decision log captures launch outcomes in PROJECT.md — Approach C validated or invalidated by retention, persona discipline confirmed, V1.5 expansion triggers (whitelist 50→100, 14-day history, multi-meal thali) re-evaluated against real-user evidence
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Validation Gates + Stack Lock | 0/TBD | Not started | - |
| 2. Photo → Macros End-to-End | 0/TBD | Not started | - |
| 3. Mobile App + Inline Advice + Retention | 0/TBD | Not started | - |
| 4. Alpha Hardening + Launch Submission | 0/TBD | Not started | - |
| 5. Public Launch + Paid Tier + V1.1 | 0/TBD | Not started | - |

---

*Roadmap created: 2026-05-27 (coarse granularity, vertical MVP mode, derived from REQUIREMENTS.md + research/SUMMARY.md + adversarial design doc)*
