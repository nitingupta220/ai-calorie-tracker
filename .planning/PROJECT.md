# AI Personal Coach — Indian Youth (codename: ai-calorie-weight-loss)

## What This Is

An AI-powered nutrition + advice app for urban Indian youth (18-30) that uses food-photo logging as the demo hook and renders Indian-context advice inline on every meal result. Positioned as "trainer replacement at ₹299/mo instead of ₹3,000/mo." V1 ships as a React Native (Expo) Android app with FastAPI backend, free-first multi-provider AI (Google AI Studio + Groq + OpenRouter + Ollama), and serves both muscle-gain and weight-loss goals within a single youth persona.

## Core Value

A user can photograph their Indian meal and immediately get accurate macros + one specific, budget-aware, veg-protein-gap-closing next action grounded in their own recent log — so they trust the app more than their gym trainer.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Photo-to-macros: snap an Indian meal photo → receive dish name + calories + protein/carbs/fat within 5 seconds
- [ ] 50-dish pan-Indian whitelist recognition (North + South + West/East staples)
- [ ] Inline contextual advice on every meal result — 1-2 sentences, specific food + quantity + ₹ cost + reference to recent log
- [ ] Muscle-gain goal track (V1) — onboarding routes user to muscle-gain target macros + advice content
- [ ] User log: last 3 days of meals viewable; advice engine uses last 3 days as context (V1.5 extends to 14 days)
- [ ] Daily totals + macro target progress on home screen
- [ ] Edit / correction flow — tap dish name or macros to fix, corrections captured as training signal
- [ ] Reference-object photo guidance (coin/palm) for portion estimation
- [ ] Retention mechanic — daily 8pm push "log today's dinner to close your protein gap" + 3/7/14-day streak badges
- [ ] Phone OTP signup via Firebase Auth
- [ ] Privacy + DPDP plumbing — privacy policy, "Delete my data" button, Indian-region storage (Cloudflare R2 Mumbai), consent screens, 30-day hard-delete on account deletion
- [ ] CDSCO + ASCI-compliant disclaimer in app and marketing copy
- [ ] Multi-provider AI abstraction (`ai_provider.py`) — free-first routing (Google AI Studio Gemini 2.5 Flash → Groq Llama 3.3 → OpenRouter free → paid Gemini/GPT-4o-mini fallback)
- [ ] Internal alpha distribution via Play Internal Testing with 20 hand-recruited Trial Users
- [ ] Photo dataset growth toward 3,000+ labeled meals for V1.5 fine-tuning

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Weight-loss goal track in V1 — moved to V1.1 (~2 weeks post-alpha launch). Reason: persona discipline; ship one goal first, prove engine, then add second.
- Housewife / 30-45 female persona — V2 with separate brand if at all. Reason: opposite acquisition channel (WhatsApp/community vs Instagram), opposite voice; founder cannot fluently speak this segment.
- Pre-diabetic / medical-niche users — V2 only. Reason: CDSCO medical-device regulation risk; trainer-replacement framing must stay fitness-not-medical.
- Long-tail dishes (Punjabi street specialties, Tamil temple-style sides, Bengali sweets, niche regional cuisine) — V1.5 expansion after 50-dish whitelist proven. Reason: scope discipline; ship 50 well rather than 500 badly.
- Hindi / regional voice + text input — V2. Reason: V1 persona is English/Hinglish-comfortable; voice doubles scope.
- iOS app — V2. Reason: $99/yr fee, halves V1 surface, target persona skews Android in India.
- Social features (leaderboards, group challenges, sharing feeds) — V2. Reason: retention before community; streaks suffice in V1.
- Razorpay subscriptions / paid tier — Phase 3 only (~month 4). Reason: validate retention + advice quality first; pricing without retention is theater.
- Multi-photo combo meals — V1.5. Reason: single-photo flow is the install hook; combos add UX complexity.
- Workout programs / exercise tracking — V2. Reason: doc focuses on nutrition coaching; workout programming is separate product surface.
- Wizard-of-Oz manual founder advice as user-facing product mode — rejected. Used only as QA tool for 5 users × 7 days mid-build to seed prompt-tuning data.

## Context

**Founder profile:** Solo bootstrap founder, age band matches V1 persona (urban Indian youth), daily failing user of existing trackers (HealthifyMe / MyFitnessPal / Cult.fit). Has done customer interviews; collected verbatim complaints. Wants both gstack + GSD toolchains active throughout.

**Existing artifacts:** `/office-hours` design doc at `~/.gstack/projects/ai-calorie-weight-loss/nitin-unknown-design-20260527-181050.md` (4 iterations, 3 adversarial review passes, quality 7/10 ship-with-concerns). Single source of truth for problem framing, premises, moat, scope, gates.

**Customer evidence (verbatim from interviews):**
- "People don't know how much to eat and what to eat specifically in Indian diets."
- "Many people recommend diets according to Western context — costly, not common in India."
- "Wanted budget diets."
- "Gym trainers give schedules not good for their bodies — overdo treadmill, cardio, random exercises."
- "Young guys at gym: trainers over-exercise them or give unclear instructions; suggest diets heavy in calories that affect health."
- "Most India is vegetarian — they want veg sources of protein more and more."

**Trend signal:** "Calorie tracking is a new trend on Indian Instagram" — observed market movement.

**Market context:** Indian health-app installs +249% in 3 years; nutrition market projected ~₹30,000 cr by 2030 (~19% YoY). Cal AI (global) at ~$300M ARR in <12mo confirms category demand.

**Competitor landscape:** HealthifyMe (40M users, 12yr Indian food DB, generic Ria advice, service complaints), NutriScan (India-specific AI tracker, new), FitTrack AI (free photo logging, claims veg-protein focus), Cult.fit (₹2k+/mo, classes-focused), Cal AI (global, no Indian context), gym trainers (₹3-8k/mo, generic), Instagram dietitians (free, generic).

**Risk gates from design doc (mandatory before any V1 code):**
- Gate 0a: 30-dish pan-Indian benchmark recognition ≥70% dish-name + ≥60% macros within ±35%
- Gate 0b: 14 days founder own meals + advice quality ≥70% scoring 4/4 rubric (specific food + quantity + ₹ cost + log reference)
- Gate 0c: ≥10 verbal commitments from 20 named Trial Users
- Gate 0d: Stack lock (Expo + RN + FastAPI + Postgres + Firebase OTP + `ai_provider.py` abstraction)

## Constraints

- **Tech stack**: React Native + Expo + EAS Build (V1); FastAPI on Render free (Singapore) + Supabase Mumbai Postgres; Cloudflare R2 with `jurisdiction=india` for photo storage; Firebase phone OTP — Reason: Render is the only no-CC FastAPI host in 2026 (Fly removed free, Railway requires CC). Supabase Mumbai + R2 india jurisdiction satisfy DPDP residency for PII + photos. Singapore compute disclosed in privacy policy. Re-evaluate Mumbai compute (Fly bom1 or Render India) at Phase 4-5 trigger
- **AI models**: Multi-provider abstraction via `ai_provider.py`; Phase 0 testing = 100% free tiers (Google AI Studio Gemini 2.0 Flash + Groq Llama 3.3 70B); Phase 1 alpha = free-first then paid; Phase 2+ = paid Gemini Flash primary, OpenRouter fallback — Reason: bootstrap budget, vendor-risk mitigation
- **Budget**: ~₹0 in Phase 0, ~₹0-200 across Phase 1 alpha (4 weeks), ~₹1,700/mo ceiling at 100 free users — Reason: solo bootstrap founder, no external funding
- **Timeline**: 14-week target to public launch; 10-12 weeks if founder has shipped React Native before, 14-20 weeks if first-time RN shipper — Reason: founder native-app fluency unknown
- **Compliance**: DPDP Act 2023 + CDSCO/ASCI advertising disclaimers — Reason: Indian regulatory obligations; medical-device territory must be avoided
- **Persona discipline**: V1 brand voice + onboarding + first growth loop locked to urban Indian youth 18-30; engine serves both muscle-gain (V1) and weight-loss (V1.1) goals — Reason: solo founder bandwidth; multi-persona V1 dilutes both
- **Regional scope discipline**: 50-dish pan-Indian whitelist, not unrestricted — Reason: scope discipline; ship 50 well

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Approach C (full native app) over Approach D (WhatsApp-first hybrid) | Founder's call. Native install matches target youth expectation; WhatsApp positioning would undermine trainer-replacement brand claim | — Pending (validated at Gate 7 retention) |
| Photo-to-macros = demo hook; inline advice = moat (stacked, not separated) | Hook drives install; advice retains. Advice must render INLINE on macros card, not in separate tab. Buried advice = moat collapse | — Pending |
| V1 persona = urban Indian youth 18-30, muscle-gain goal first | Persona discipline. Solo founder cannot serve two opposite-channel personas at once | — Pending |
| 50-dish pan-Indian whitelist (not region-restricted) | Founder pushback on North-only restriction; reframed as scope discipline by dish count | ✓ Good (corrected mid-design) |
| Free-first multi-provider AI strategy (Google AI Studio + Groq + Ollama + OpenRouter primary) | Bootstrap budget; vendor risk mitigation; founder explicit ask | ✓ Good |
| Android-first, iOS V2 | Target persona ₹299-499 willingness skews Android in India; saves $99/yr Apple fee | — Pending |
| Adversarial spec review applied (3 iterations) on design doc | Better baseline; surfaced critical gaps (timeline, vendor risk, compliance, retention mechanic) | ✓ Good |
| Both gstack + GSD toolchains active throughout project | Founder explicit request; complementary not alternative | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-28 — corrected Gemini 2.5 Flash + Render hosting drift per /plan-eng-review D1 (was Gemini 2.0, Railway). Original: 2026-05-27 from /office-hours design doc iteration 4.*
