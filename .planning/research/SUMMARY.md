# Project Research Summary

**Project:** AI Personal Coach — Indian Youth (codename: ai-calorie-weight-loss)
**Domain:** AI-powered Indian-context nutrition coach (mobile Android-first, vision + advice LLM, solo bootstrap, DPDP-bound)
**Researched:** 2026-05-27
**Confidence:** HIGH

## Executive Summary

Mobile AI nutrition coach for urban Indian youth (18-30), Android-first, wedging into a category (HealthifyMe, Cal AI, NutriScan, Cult.fit) where photo-to-macros is now table stakes but **culturally-grounded, budget-aware, vegetarian-protein-gap-closing inline advice on every meal is the unoccupied moat**. Research confirms the design doc's wedge: no incumbent productizes ₹/gram veg-protein recommendations grounded in last-3-day user log, rendered free on every macros card. HealthifyMe paywalls Ria (₹999/mo). Cal AI has no Indian context. Trainer-replacement positioning (₹299/mo vs ₹3,000/mo) is structurally defensible — HealthifyMe/Cult.fit business models include human coaches and cannot replicate.

Build approach: Expo SDK 54 + RN 0.81 (managed workflow for first-time RN shipper risk) on FastAPI 0.128 + async SQLAlchemy 2.0 backend, with hard architectural commitment to a single `ai_provider.py` abstraction routing vision (Gemini 2.5 Flash → OpenRouter Qwen 2.5 VL → paid Gemini → GPT-4o-mini) and text (Groq Llama 3.3 70B → OpenRouter → paid Gemini) on 429-fallback. Photo upload via presigned PUT direct to Cloudflare R2 with `jurisdiction=india`. Vision pipeline is two-step: model identifies dish + portion, founder-curated decomposition maps to IFCT 2017 raw ingredients, deterministic lookup returns macros. Advice rendered inline on `<MacrosCard />` in a single API response — moving it to a "Coach tab" collapses the moat.

Dominant risks are not technical: accuracy collapse on multi-item thalis (Pitfall 1), generic-advice moat collapse if WoZ QA is skipped (Pitfalls 4 + 14), DPDP non-compliance from treating privacy as Week 11 task (Pitfall 9), first-time-RN-shipper timeline optimism (Pitfall 8). Mitigations: stratify Gate 0a benchmark (10 single / 10 mixed / 10 thali — per-bucket pass bar); **promote WoZ QA to Gate** (≥35 examples, AI-vs-WoZ ≥70% match before alpha); **pull DPDP plumbing into Week 1** (region pinning, consent ledger schema, hard-delete cron); **buy Play Developer account Week 0d** (3-7 day identity check).

**Three stack corrections vs design doc:**
1. **Gemini 2.5 Flash** as vision primary, not 2.0 (retires 2026-03-03).
2. **Cloudflare R2 `jurisdiction=india`** (endpoint `<acct>.in.r2.cloudflarestorage.com`), not Mumbai PoP.
3. **Hosting locked (D-01): Render free tier, Singapore region** for compute. Fly.io Mumbai (bom1, sub-20ms, $13-20/mo prod) and Railway Singapore (+50-100ms, better DX) were both rejected — each requires a credit card in 2026, failing the zero-CC bootstrap constraint. Render free has no CC requirement; the Mumbai-compute latency win is a deferred Phase-4 trigger only. **Supabase Mumbai remains the managed Postgres** (Neon excluded — no India region). Note: Render free instances sleep when idle, so server-side cron runs as GitHub Actions scheduled workflows, not in-process APScheduler (D-03).

**Two feature additions** research surfaced as table stakes: **manual weight log** (~4h dev — required for muscle-gain progress) and **water intake tracker** (~2h dev — every incumbent ships it). Both V1.

## Key Findings

### Recommended Stack

- **Expo SDK 54 + RN 0.81 + expo-router 5** — Android-first; EAS Build dev/preview/production; custom dev client for @react-native-firebase native modules.
- **expo-image-manipulator (mandatory)** — SDK 54 returns HEIC/AVIF on iOS-sourced images; convert to JPEG ≤1280px / q=0.7 (5x R2 savings, 3x vision token savings).
- **FastAPI 0.128 + Pydantic v2 + SQLAlchemy 2.0 async + asyncpg + Alembic** — async throughout; separate `models/` and `schemas/`.
- **Render free tier, Singapore region [V1, locked per D-01]** — no credit card required (Fly.io and Railway both rejected: CC required in 2026, fails zero-CC constraint). Mumbai-compute migration is a deferred Phase-4 trigger. Free instances sleep idle → cron via GitHub Actions, not in-process APScheduler (D-03).
- **Supabase Mumbai Postgres** — only managed Postgres with India region in price band; free tier 500MB / 50K MAU; auto-pauses after 1 week idle.
- **Cloudflare R2, jurisdiction=india** — presigned PUT direct from mobile; zero egress fees.
- **Firebase Phone Auth** — 50K MAU free, no DLT required; firebase-admin verifies ID tokens.
- **AI providers:** Gemini 2.5 Flash (vision) + Groq Llama 3.3 70B (text) + OpenRouter (fallback) + Ollama (dev-only). All routed through `ai_provider.py` — no SDK imports outside (lint-enforced).
- **FCM HTTP v1 + APScheduler** — server-driven 8pm IST push.
- **Razorpay UPI Autopay (Phase 3)** — ₹299/mo recurring; GSTIN before ₹20L threshold.
- **Sentry + PostHog (1M events free)** — wired Week 4, not post-PMF.

### Expected Features

**Must have (V1 table stakes):**
- Photo-to-macros (50-dish whitelist via Gemini 2.5 Flash).
- Daily home: kcal + protein/carbs/fat progress vs target.
- Inline 1-2 sentence advice on every macros card (the moat).
- Last 3 days meal history.
- Edit / correct macros (training corpus signal).
- Phone OTP signup (Firebase).
- Onboarding: goal / height-weight-age / activity / veg-non-veg / budget bucket (6-8 questions).
- Streak counter (3/7/14-day badges).
- Daily 8pm push with personalized macro-gap copy.
- Manual entry fallback for non-whitelist dishes.
- Reference-object photo guidance (coin/palm).
- DPDP plumbing (privacy policy, granular consents, delete-my-data, 30-day hard-delete, age-18+ gate, EXIF strip).
- CDSCO/ASCI disclaimer permanent + on every advice card.
- **NEW — Manual weight log** (~4h dev) — muscle-gain progress narrative.
- **NEW — Water intake tracker** (~2h dev) — 1-tap home button.

**Should have (V1 differentiators):**
- Vegetarian-protein-gap default with ₹/gram ranking.
- Budget-aware ₹ cost in every advice line.
- 50-dish pan-Indian recognition (15 pan-India + 12 North + 12 South + 11 W/E).
- Trainer-replacement positioning.
- Free-tier inline advice (HealthifyMe paywalls at ₹999).
- Correction-as-training-signal flywheel.

**Defer (V1.5 / V2):**
- Weight-loss goal → V1.1 (trigger: muscle-gain D7 ≥25% AND advice 4/4 ≥75%).
- 14-day history, multi-meal thali photo, whitelist 50→100 → V1.5.
- Razorpay subscriptions → Phase 3.
- iOS, social, Hindi voice, workouts, wearables, PCOS mode, AI chat tab — V2+ (AI chat tab is explicit **anti-feature**).

### Architecture Approach

Thin React Native client → FastAPI API → service layer → `ai_provider.py` → external AI + R2 + FCM + Postgres.

**Hard commitments:**
1. Presigned-PUT direct to R2 (backend never proxies bytes).
2. Two-step vision (LLM identifies dish + portion → decomposition → IFCT lookup; never single-step LLM macros).
3. Inline advice in single `MealResponse` (parallel async tasks, 6s hard timeout, macros-only fallback).
4. Append-only `correction_event` table from day 1.
5. All PII in Postgres, only `meals/{uuid}/{uuid}.jpg` in R2.

**Major components:**
1. Mobile Camera + Compression + Upload (`expo-camera` + `expo-image-manipulator` → presigned PUT to R2 india).
2. FastAPI API layer (auth / uploads / meals / advice / summary / push / compliance routers).
3. `ai_provider.py` — first-class folder; VisionProvider + TextProvider with free-first routing + 429 fallback + per-call cost log.
4. Vision pipeline service — orchestrates Gemini → decomposition → IFCT → persist + parallel advice task.
5. Dish decomposition + IFCT 2017 (`data/ifct_2017.sqlite` + 50-dish ground-truth shipped in repo).
6. Advice engine — prompt with goal + target + last-3-day log + day-so-far + budget + veg/non-veg + dish.
7. Daily summary + streak service + APScheduler push worker.
8. Compliance / DSR service — consent_log + soft-delete + 30-day hard-delete cron.
9. Postgres (Supabase Mumbai) — users / meal_photo / daily_summary / streak / push_event / consent_log / correction_event.
10. Cloudflare R2 india jurisdiction — presigned URLs only.

### Critical Pitfalls

1. **Vision accuracy collapse on thalis (Pitfall 1)** — 49-76% accuracy drop on 4+ item dishes. Prevention: stratified Gate 0a benchmark (10 single / 10 mixed / 10 thali, per-bucket pass); confidence-gate render (>3 items OR conf <0.6 → "tap each to confirm"); "snap each item separately" tooltip.

2. **Generic AI advice = moat collapse (Pitfall 4)** — easiest prompt produces most generic output. Prevention: server-side reject advice without log-number reference; 4/4 rubric is law; **WoZ QA upgraded to Gate** — ≥35 examples + AI-vs-WoZ ≥70% match before Week 9 alpha; per-dish hand-written templates as fallback.

3. **DPDP Act 2023 compliance gaps (Pitfall 9)** — ₹250 crore fine ceiling; Play Store rejects. Prevention: **DPDP plumbing pulled into Week 1** — R2 jurisdiction=india code-verified, Supabase region code-verified, consent_log schema Week 1, granular consents Week 4 (AI-training DEFAULT OFF), age-18+ hard gate, EXIF strip via Pillow. Week 11 = audit + privacy policy, not build.

4. **First-time RN shipper timeline (Pitfall 8)** — 40-60% underestimate per community retrospectives. Prevention: Hello-World ships Week 1 (not Week 14); EAS Build configured Week 1; pre-budget 5-10 days for known time sinks; **Play Developer account Week 0d** (3-7 day verification).

5. **Provider lock-in + rate-limit surprise (Pitfalls 6 + 7)** — Gemini 10 RPM caps at ~50 lunch-concurrent users. Prevention: lint rule forbidding provider SDK imports outside `providers/`; auto-fallback on 429 wired Week 1; pre-launch load test (20 concurrent uploads dinner-hour) before Week 9 alpha; per-call provider tag for cost attribution.

Additional flags: Pitfall 3 (IFCT raw-ingredient gap — decomposition layer Week 2); Pitfall 14 (WoZ as Gate); Pitfall 16 (Play submission Week 12 not 14); Pitfall 20 (ISSN 2024 protein 1.8 g/kg muscle-gain default).

## Implications for Roadmap

### Phase 0 — Gates (Week 0, no production code)
**Rationale:** Risk gates remain entry barrier; stack corrections + Play account + DPDP-schema-readiness land here.
**Delivers:** Gate 0a (stratified 30-photo benchmark), Gate 0b (14-day founder advice 4/4 ≥70%), Gate 0c (≥10 verbal price + commitment quotes), Gate 0d (stack lock + 3 corrections + **Play Developer account purchased** + compute hosting locked to **Render free Singapore** per D-01, zero-CC — Fly/Railway rejected).
**Avoids:** Pitfalls 1, 4, 16, 7, 8.

### Phase 1 — Backend Spine + Vision + DPDP Plumbing (Weeks 1-2)
**Rationale:** Vision must exist before advice; DPDP plumbing must land Week 1 or it's lipstick on Week 11.
**Delivers:** FastAPI + Supabase Mumbai + Firebase auth verify + R2 india presigned uploads + `ai_provider.py` v1 (Gemini 2.5 Flash + Groq, 429-fallback tested) + vision pipeline + dish decomposition + IFCT lookup + Hello-World mobile call. **DPDP:** R2 jurisdiction code-verified, Supabase region code-verified, consent_log + soft_delete_at columns, EXIF strip, age-18+ field.
**Uses:** FastAPI 0.128 / SQLAlchemy 2.0 async / boto3 / firebase-admin / google-genai / groq.
**Avoids:** Pitfalls 3, 6, 9, 18.

### Phase 2 — Advice Engine + Correction Capture (Week 3)
**Rationale:** Advice engine validates API shape before mobile; correction_event must ship before any user.
**Delivers:** Advice engine + prompt v0 + last-3-day context + 4/4 server-side validator + per-dish template fallback + `PATCH /meals/{id}` + append-only `correction_event` + prompt versioning (semver, version-controlled).
**Avoids:** Pitfalls 4, 5, 27.

### Phase 3 — Mobile Client (Weeks 4-6)
**Rationale:** Backend API stable by end of Week 3; granular DPDP consents + Android-13+ push permission in onboarding; reference-object enforced in camera.
**Delivers:**
- Week 4: Expo scaffold + auth + onboarding (goal / body / diet / **granular consents** / **push permission rationale**) + ISSN-2024 protein target (1.8 g/kg muscle-gain default).
- Week 5: Camera + compression + reference-object overlay + presigned upload + `<MacrosCard />` with `<AdviceInline>` child + **manual weight log + water tracker (research additions)**.
- Week 6: History + 1-tap correction sheet + **Wizard-of-Oz QA as Gate** — 5 users × 7 days, ≥35 examples, AI-vs-WoZ ≥70% match required.
**Avoids:** Pitfalls 2, 5, 14, 22.

### Phase 4 — Retention Loop (Week 7)
**Rationale:** Needs real meal data for personalization.
**Delivers:** FCM token registration + APScheduler 8pm IST per-user + personalized macro-gap copy + streak (3/7/14-day) + recovery framing.
**Avoids:** Pitfalls 5, 22.

### Phase 5 — Hardening + Alpha Prep (Week 8)
**Delivers:** Offline queue (24h TTL) + Sentry/PostHog full wiring + per-user cost telemetry dashboard + **pre-launch load test** (20 concurrent uploads dinner-hour, ≥95% success / <8s P95) + Play Internal Testing track + **fallback drill** (10% traffic through OpenRouter 24h).
**Avoids:** Pitfalls 6, 21, 25.

### Phase 6 — Closed Alpha (Weeks 9-10)
**Delivers:** 20 users live + daily dashboards (correction rate, push CTR, D1→D2 dropoff, vision accuracy, cost/user) + WhatsApp DM check-ins day 3 + 5.
**Avoids:** Pitfalls 5, 13, 12.

### Phase 7 — DPDP Capstone (Week 11)
**Rationale:** Plumbing exists from Week 1; this is the audit + public-facing policy.
**Delivers:** Privacy policy live + hard-delete cron audited end-to-end + Data Safety form pre-filled + CDSCO/ASCI disclaimer audit + banned-words marketing check.
**Avoids:** Pitfalls 9, 10, 11.

### Phase 8 — Gate 7 + Launch Prep (Weeks 12-14)
**Rationale:** Play Store Production submission Week 12 (not 14) for 7-14 day new-developer review.
**Delivers:** Gate 7 (5/20 D7 + price-WTP verbatim) + ASO copy + screenshots + **Production submission Week 12** + Razorpay account opening (test ₹1 by Week 14) + GSTIN registration + public launch Week 14.
**Avoids:** Pitfalls 16, 17, 15.

### Phase 9 — Phase 3 Paid (Month 4+)
**Rationale:** Razorpay only after retention proven (5/20 D7 + ≥10 verbal "I'd pay").
**Delivers:** Razorpay subscription + ₹299 paid tier + weight-loss V1.1 (trigger: D7 ≥25% + advice 4/4 ≥75%) + whitelist expansion if ≥20% photos unsupported.
**Avoids:** Pitfalls 11, 15, 12.

### Phase Ordering Rationale

- **Dependencies:** Vision → advice → mobile → retention → DPDP capstone. Correction-event before any user. Play account Week 0d (3-7 day check).
- **Architecture grouping:** Backend spine + ai_provider + vision + DPDP share infra (Phase 1-2). `<MacrosCard />` + `<AdviceInline />` co-located by design.
- **Pitfall-driven changes vs design doc:** WoZ promoted to Gate, Gate 0a stratified, load test pre-alpha, Play submission Week 12, GSTIN before Phase 3, DPDP plumbing pulled to Week 1.

### Research Flags

**Needs research-phase:**
- **Phase 0:** Gemini 2.5 Flash prompt engineering for Indian multimodal (`response_schema`, in-context examples for 50-dish whitelist) — sparse docs.
- **Phase 3 Week 5:** AR-overlay reference-object guidance on Android with expo-camera — sparse community docs.
- **Phase 4:** Personalized push copy templates hitting 4/4 rubric in <50 tokens — non-trivial prompt design.
- **Phase 8:** 2024-2025 Play Store health-app policy + Data Safety form — recent changes.
- **Phase 9:** Razorpay UPI Autopay subscription UX — bank-mandate quirks.

**Standard patterns (skip research):**
- Phase 1 (FastAPI + Postgres scaffold) — Context7-verified.
- Phase 2 (advice engine plumbing) — standard.
- Phase 5 (Sentry/PostHog wiring + offline queue) — Sentry Wizard automates.
- Phase 7 (DPDP audit) — mechanical checklists.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | Context7-verified core libs; 2026 official docs for Gemini retirement, R2 india jurisdiction, Fly.io Mumbai pricing, Supabase regions, Firebase pricing. Three corrections verified against primary sources. |
| Features | **HIGH** | Verified against HealthifyMe, Cal AI, NutriScan, MyFitnessPal, Cult.fit official 2026 + design-doc customer verbatim. Two table-stake additions (weight log + water) universal across incumbents. |
| Architecture | **HIGH** | Standard 2026 mobile-AI patterns + design-doc constraints + Context7-verified library patterns. Presigned-PUT + two-step vision + inline-advice-single-response all canonical. |
| Pitfalls | **HIGH** | Top critical drawn from DPDP Act 2023, CDSCO MD Rules 2017, ASCI Code 2023, ISSN 2024, U.Sydney 2024 multimodal-LLM food study, adversarial-reviewed design doc. Moderate pitfalls MEDIUM. |

**Overall confidence:** **HIGH**

### Gaps to Address

- **Gemini 2.5 Flash free-tier RPD verification:** STACK.md notes "500 RPD (some reports cite 1500)." → Founder verifies on Google AI Studio Week 0d; if 500 RPD, document paid-Gemini migration trigger at ~250 DAU.
- **Compute hosting:** ~~Trade-off documented but not picked.~~ **RESOLVED (D-01): Render free tier, Singapore region.** Fly.io Mumbai and Railway Singapore both rejected (each requires a credit card in 2026 — fails zero-CC constraint). Mumbai-compute migration deferred to Phase-4 trigger. Render free sleeps idle → cron via GitHub Actions (D-03), not in-process APScheduler.
- **D7 retention baseline for Indian-context AI nutrition:** Industry numbers don't perfectly map to wedge-positioned product. → Use design-doc 5/20 D7 Gate 7 bar; collect WhatsApp verbatim during alpha to ground-truth.
- **Vegetarian-protein ₹/gram price table:** Mentioned as Week 3 deliverable, no source given. → Founder builds during Gate 0a / Week 3 from local market prices; commits as `data/veg_protein_prices.json` with date stamp.
- **Supabase auto-pause behavior:** Free tier pauses after 1 week idle. → Cron-ping monitor OR upgrade to $25 Pro before Week 9 alpha.
- **Thali photo accuracy from Gemini 2.5 Flash:** Literature on prior models; 2.5 Flash on multi-item Indian dishes unpublished. → Gate 0a thali bucket directly tests; if fails, "snap each item separately" UX in V1, multi-item-single-photo to V1.5.

## Sources

### Primary (HIGH)
- Context7 verified: `/expo/expo` (SDK 54), `/fastapi/fastapi` (0.128), `/websites/sqlalchemy_en_20`, `/websites/firebase_google`, `/websites/developers_cloudflare_r2`, `/websites/openrouter_ai`, `/groq/groq-python`, `/razorpay/razorpay-python`, `/ollama/ollama-python`.
- Google AI Developers rate limits 2026 — Gemini 2.0 retirement 2026-03-03, 2.5 Flash 10 RPM / 250K TPM / 500 RPD.
- Groq docs 2026 — 30 RPM / 6K TPM / 1000 RPD.
- Fly.io pricing — bom1 Mumbai $1.94/mo shared CPU.
- Supabase pricing — Mumbai region, 500 MB / 50K MAU free.
- Cloudflare R2 jurisdictions — India bucket via `<acct>.in.r2.cloudflarestorage.com`.
- DPDP Act 2023 (MeitY primary text).
- CDSCO Medical Devices Rules 2017.
- ASCI Code 2023 + Influencer Guidelines 2021/2023.
- ISSN Position Stand on Protein 2017, updated 2024.
- IFCT 2017 (NIN/ICMR) — 528 raw foods.
- Razorpay UPI Autopay docs — ₹15K monthly limit.
- HealthifyMe / Cal AI / NutriScan / MyFitnessPal / Cult.fit official 2026 pages.

### Internal
- `.planning/PROJECT.md` — locked feature scope.
- `~/.gstack/projects/ai-calorie-weight-loss/nitin-unknown-design-20260527-181050.md` — adversarial-reviewed design doc iteration 4.
- `.planning/research/STACK.md`, `FEATURES.md`, `ARCHITECTURE.md`, `PITFALLS.md`.

---

## Roadmap Implications (TL;DR for orchestrator)

Suggested phases (coarse granularity per founder config — may collapse to 5-6):

1. **Phase 0 — Gates (Week 0)** — Risk gates + stack corrections + Play account + compute hosting locked to Render free Singapore (D-01).
2. **Phase 1 — Backend Spine + Vision + DPDP Plumbing (Weeks 1-2)** — `ai_provider.py` + vision pipeline + DPDP pulled forward.
3. **Phase 2 — Advice Engine + Correction Capture (Week 3)** — Moat engine + training-corpus capture.
4. **Phase 3 — Mobile Client (Weeks 4-6)** — Onboarding + camera + MacrosCard with inline advice + WoZ Gate.
5. **Phase 4 — Retention Loop (Week 7)** — Personalized 8pm push + streak.
6. **Phase 5 — Hardening + Alpha Prep (Week 8)** — Load test + cost telemetry + fallback drill.
7. **Phase 6 — Closed Alpha (Weeks 9-10)** — 20 users + daily monitoring.
8. **Phase 7 — DPDP Capstone (Week 11)** — Audit + public privacy policy.
9. **Phase 8 — Gate 7 + Launch Prep (Weeks 12-14)** — Production submission Week 12, public launch Week 14.
10. (Future) **Phase 9 — Paid Tier (Month 4+)** — Razorpay + V1.1 weight-loss.
