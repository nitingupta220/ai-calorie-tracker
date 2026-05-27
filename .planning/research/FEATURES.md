# Feature Research

**Domain:** AI-powered Indian-context nutrition coach mobile app (Android-first, youth 18-30)
**Researched:** 2026-05-27
**Confidence:** HIGH (verified across HealthifyMe, Cal AI, NutriScan, MyFitnessPal, Cult.fit official sources + customer interview verbatim already in design doc)

## Executive Take

The Indian fitness/nutrition app category in 2026 has hardened into a clear stack: photo-to-macros input is now table stakes (HealthifyMe Auto Snap, Cal AI, NutriScan all ship it); voice-multimodal input is the next emerging table stake (HealthifyMe Ria Voice launched on OpenAI Realtime API; NutriScan Monika voice assistant). What is NOT table stakes — and where incumbents fail — is **culturally-grounded, budget-aware, vegetarian-protein-gap-solving inline advice on every meal**. Cal AI has no Indian context. HealthifyMe Ria is generic and paywalled at ₹999/mo. NutriScan tracks Indian food well but does not productize trainer-replacement coaching. This is the unoccupied wedge the design doc targets.

Founder design doc has already done feature scoping (50-dish whitelist, muscle-gain V1, inline-advice moat, no social V1). This research **validates and stress-tests** that scope against the 2026 competitive landscape rather than redefining it.

## Feature Landscape

### Table Stakes (Users Expect These — Missing = Users Leave for HealthifyMe / Cal AI)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Photo-to-macros (single meal) | HealthifyMe Auto Snap, Cal AI, NutriScan all ship this; Cal AI hit $300M ARR on this hook | MEDIUM | Already V1 scope. Gemini 2.0 Flash + 50-dish whitelist. Gate 0a validates. |
| Daily calorie + macro target with progress bar | Every tracker since MyFitnessPal 2005 has this; users will not log without seeing "X / Y kcal today" | LOW | Already V1 scope (home screen totals). |
| Manual food entry fallback ("dish not supported") | 50-dish whitelist will fail on 30%+ of real meals; users abandon if there's no escape hatch | LOW | Already V1 scope (free-text macros entry on whitelist miss). |
| Edit / correct macros after AI guess | Photo accuracy is ±25-35%; users see wrong portion → must be able to fix or trust collapses | LOW-MEDIUM | Already V1 scope (Week 3 deliverable, doubles as training signal). |
| Onboarding goal capture (weight, height, goal, activity) | Cal AI's "personalized plan" framing is now standard; without it the app feels generic | LOW | Already V1 scope (Week 4). Keep to 6-8 questions — Cal AI does ~12 and still converts, but each extra Q costs ~5-8% completion. |
| Phone OTP / one-tap signup | Indian youth expect phone signup; email-only loses 40%+ in tier-2 cities | LOW | Already V1 scope (Firebase OTP). |
| Streak counter (daily logged-meal streak) | Every retention-focused tracker has this since Duolingo proved it; without it D7 retention craters | LOW | Already V1 scope (3/7/14-day badges, Week 7). |
| Last-N-days meal history view | Users need to see "what did I eat yesterday" — core trust feature | LOW | Already V1 scope (last 3 days V1, 14 days V1.5). |
| Push notification reminders (1-2/day) | All trackers send dinner-reminder; without it ~60% users forget to log within 3 days | LOW | Already V1 scope (8pm dinner push). |
| Privacy / "Delete my data" + Indian-region storage | DPDP Act 2023 legal requirement, not optional. Play Store review will check. | MEDIUM | Already V1 scope (Week 11). Cloudflare R2 Mumbai. |
| Health disclaimer ("not medical advice") | CDSCO / ASCI mandatory. Cannot ship without. | LOW | Already V1 scope. |
| Water intake tracking | MyFitnessPal, HealthifyMe, NutriScan all ship it; users notice absence | LOW | **GAP — not in V1.** Consider: add 1-tap water button on home screen. ~2 hours dev. |
| Weight log (manual entry) | Goal-progress is moot without weight tracking; users will ask "where do I enter my weight?" | LOW | **GAP — not explicit in V1.** Required for muscle-gain progress; add as MVP-essential. ~4 hours dev. |

### Differentiators (Competitive Advantage — Where We Win)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Inline contextual advice on every meal result** | The moat. Cal AI has no advice. HealthifyMe paywalls Ria at ₹999. We render 1-2 lines free on every macros card. | MEDIUM-HIGH | Already V1 scope (Week 3). Grounded in last 3-day log. Vegetarian-protein-gap default. **Implementation must keep this INLINE — burying in coach tab collapses moat (design doc note).** |
| **Vegetarian-protein-gap awareness** | ~70% of India is vegetarian; no app productizes "you're at 32g, target 90g, add 50g paneer for ₹18". HealthifyMe gives generic Ria advice; Cal AI is Western. | MEDIUM | Already V1 scope. Differentiator depends on advice prompt template citing veg protein sources ranked by ₹/gram. |
| **Budget-aware ₹ cost in advice** | Direct verbatim from interviews: "Wanted budget diets." No incumbent shows ₹ cost in food suggestions. | MEDIUM | Already V1 scope. Needs price reference table for top 30 veg-protein foods (paneer, dal, eggs, chana, soya chunks, peanuts, curd). One-time data work. |
| **50-dish pan-Indian recognition (North + South + West + East)** | Cal AI fails on Indian dishes; HealthifyMe has DB but photo recognition still misses regional staples. India-first from day 0. | MEDIUM | Already V1 scope. Gate 0a benchmark. |
| **Trainer-replacement positioning ("₹299/mo vs ₹3,000/mo trainer")** | Brand-level differentiator. Verbatim from interviews: "Gym trainers give schedules not good for their bodies." HealthifyMe / Cult.fit cannot claim this — their business models include human coaches. | LOW (positioning, not code) | Already locked in design doc. Marketing copy + onboarding flow must reinforce. |
| **Reference-object photo guidance (coin/palm)** | Improves portion estimation accuracy from ±35% toward ±25%. No competitor surfaces this UX nudge. | LOW | Already V1 scope (Week 5). 1-time onboarding tooltip + camera overlay hint. |
| **Free-tier inline advice** | HealthifyMe Smart (₹208/mo) + Coach (₹1,500+/mo) gate advice behind paywall. We give it free in V1-V2. Pricing only in Phase 3 once retention proven. | LOW (business model, not code) | Already locked. Differentiator only viable if free-tier AI costs stay ≤₹17/user/mo (modelled in unit economics). |
| **Founder-curated dish whitelist + correction-as-signal loop** | Every user correction becomes prompt-tuning data → dish recognition improves weekly. HealthifyMe's 12-year DB is static; we improve faster from day 1. | MEDIUM | Already V1 scope (correction flow Week 3). Data flywheel = post-PMF moat (per design doc P4). |

### Anti-Features (Commonly Requested, Deliberately NOT Building for V1)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Social feed / community / friend leaderboards | MyFitnessPal has 280M-member community; "social fitness" is trendy | Solo founder bandwidth; community = moderation surface = legal liability under IT Rules 2021; pre-PMF community is empty and embarrassing | V2 only. V1 retention via streaks suffices (per design doc). |
| Workout / exercise program tracking | Cult.fit, HealthifyMe both ship workouts; users may ask "where are workouts?" | Doubles scope; workout programming is separate product surface; founder is not a trainer | V2 separate product. V1 explicitly nutrition-only. Onboarding copy: "We coach your food, not your gym." |
| Hindi / regional language voice input | NutriScan, HealthifyMe Ria Voice both support Hindi; India = multilingual | V1 persona is English/Hinglish-comfortable urban youth; voice input doubles AI scope; speech-to-text in Hindi has its own accuracy problems | V2. Stick to English/Hinglish text in V1. |
| Multi-meal combo photo (full thali in one shot) | Real users eat thalis, not single dishes | Photo decomposition complexity 5x single dish; single-photo flow is the install hook; combos add UX confusion | V1.5. Single dish + "add another" button as workaround. |
| iOS app | Founder may want it; affluent users skew iPhone | $99/yr Apple fee; halves V1 surface; V1 persona (₹299-499 willingness) skews Android in India | V2. Android-only V1. |
| Wearable / smartwatch integration (Apple Watch, Fitbit, Mi Band) | Cronometer, MyFitnessPal sync from wearables | Adds 4-6 SDK integrations; Android wearable market in India is fragmented (Boat, Noise, Fire-Boltt, Mi all different APIs) | V2. V1 = manual weight + water entry only. |
| Meal photo gallery auto-detect (HealthifyMe Auto Snap clone) | HealthifyMe ships this; users may compare | Requires gallery permission (privacy red flag at signup); background processing battery drain; not novel anymore | V1.5 maybe. V1 = explicit camera capture only — better consent story for DPDP. |
| AI chat tab ("ask Ria-style coach") | HealthifyMe Ria, Cal AI all have chat | Pulls advice INTO a tab away from meals → moat collapse (design doc explicit warning); free-text chat = unbounded AI cost; users ask "is paneer good" 50x/day | V2. V1 advice is INLINE on macros card, period. No separate chat surface. |
| Pre-diabetic / PCOS / medical-condition mode | Large addressable market; HealthifyMe and NutriScan both offer PCOS plans | CDSCO medical-device regulation territory; one wrong macro recommendation → legal exposure; founder cannot fluently coach this segment | V2 with medical-advisor review. V1 = fitness positioning only. |
| Razorpay subscriptions / paid tier in V1 | Revenue! | Pricing without retention is theater (design doc); retention gate (5/20 D7) must pass first; payment integration is 2-week diversion mid-build | Phase 3, month 4+. V1-V2 = free for all alpha + first 100 public users. |
| Recipe library / meal planning UI | HealthifyMe ships 1000s of recipes | Content team work; not a moat; doesn't help with "log what I already ate" core loop | V2. V1 advice can suggest recipes as 1-line text ("try besan chilla tomorrow") without a recipe-detail screen. |
| Barcode scan for packaged foods | MyFitnessPal Premium feature; common ask | Indian packaged-food barcode coverage is poor outside metro brands; Open Food Facts has weak Indian data; building DB is a project of its own | V1.5 evaluate. V1 = manual entry for packaged foods. |
| Steps / activity counter | Every fitness app has it | Google Fit / Health Connect integration is 2-3 weeks; not central to nutrition-coaching value prop | V2. Onboarding asks "activity level: low/med/high" for TDEE calc; that's enough. |
| Calendar export / share weekly summary as image | Instagram-shareability could drive virality | Pre-PMF; founder has no bandwidth for share-asset design; first build users → measure → then add sharing | V1.5. |

## Feature Dependencies

```
Phone OTP signup
    └──requires──> Firebase Auth setup
                       └──requires──> Stack lock (Gate 0d)

Photo-to-macros
    └──requires──> ai_provider.py abstraction
                       └──requires──> Gate 0a (vision benchmark pass)
    └──requires──> 50-dish whitelist + IFCT decomposition table

Inline advice (THE MOAT)
    └──requires──> Photo-to-macros (need macros card to render advice ON)
    └──requires──> Last-3-day meal log (advice cites recent meals)
    └──requires──> Gate 0b (advice rubric pass)
    └──requires──> Veg-protein ₹/gram reference table

Streak counter
    └──requires──> Daily meal log persistence + date math
    └──requires──> Push notification permission (8pm reminder)

Correction flow
    └──requires──> Photo-to-macros (have something to correct)
    └──enhances──> Photo-to-macros accuracy over time (training signal)

DPDP "Delete my data"
    └──requires──> Cloudflare R2 Mumbai + Postgres user_id cascading delete
    └──BLOCKS──> Play Store listing (Week 13 launch)

Weight log (GAP IDENTIFIED)
    └──enhances──> Onboarding goal capture
    └──enhances──> Muscle-gain progress story

Water tracker (GAP IDENTIFIED)
    └──enhances──> Daily home screen completeness perception
```

### Dependency Notes

- **Inline advice requires photo-to-macros first:** Cannot render advice ON a macros card that does not exist. Week 2 (vision) must ship before Week 3 (advice) — already ordered correctly in milestone plan.
- **Streak requires push notification:** 8pm dinner reminder is the streak's return-trigger. Push permission must be requested in onboarding (Week 4), not Week 7 when streak ships.
- **DPDP plumbing blocks public launch:** Week 11 deliverable is non-negotiable before Week 13 Play Store flip. Cannot ship without privacy policy + delete button.
- **Correction flow + dataset growth are coupled:** Every correction feeds the V1.5 fine-tuning dataset (3,000+ labeled meals target). Build correction UI as JSON-logged training row, not just a UI fix.
- **Weight + water (new gaps):** Both block "user perceives app as complete tracker." Add to V1 — small dev cost, large perception cost.

## MVP Definition

### Launch With (V1 alpha — Week 12 / Internal Testing)

Minimum viable product per design doc + this research's gap additions:

- [x] Phone OTP signup (Firebase)
- [x] Onboarding: goal (muscle-gain only), height/weight/age, activity, veg-or-non-veg, budget bucket
- [x] Photo-to-macros (50-dish whitelist, Gemini 2.0 Flash)
- [x] Daily home screen: calorie + protein/carbs/fat progress vs target
- [x] **Inline advice on every macros card (THE MOAT)** — 1-2 sentences, specific food + quantity + ₹ cost + last-3-day log reference
- [x] Last 3 days meal history
- [x] Edit / correct macros (also captures training signal)
- [x] Reference-object photo guidance (coin/palm tooltip in camera)
- [x] Manual entry fallback for non-whitelist dishes
- [x] Streak counter (3/7/14-day badges)
- [x] Daily 8pm push notification (personalized: "Log dinner — protein at Xg / Yg")
- [x] DPDP plumbing (privacy policy, delete-my-data, Mumbai storage, consent screens)
- [x] CDSCO/ASCI disclaimer
- [x] **NEW (research gap): Manual weight log entry** — daily/weekly weight tracking, ~4 hours dev. Required for muscle-gain progress narrative.
- [x] **NEW (research gap): Water intake tracker** — 1-tap glass button on home screen, ~2 hours dev. Without it, app perceived as incomplete.

### Add After Validation (V1.1-V1.5 — weeks 14-26 post-alpha)

- [ ] Weight-loss goal track — trigger: muscle-gain flow proven, 5/20 D7 retention achieved
- [ ] Last 14 days meal history (vs V1's 3 days) — trigger: advice quality plateau on short context
- [ ] Multi-meal combo photo (thali in one shot) — trigger: ≥30% of meals are combos in user data
- [ ] Whitelist expansion 50 → 100 dishes — trigger: ≥20% of photos hit "dish not supported"
- [ ] Razorpay subscription (₹299/mo paid tier) — trigger: Phase 3 / month 4 / ≥10 verbal "I'd pay" quotes
- [ ] Barcode scan for packaged foods — trigger: ≥5/20 users request it unprompted
- [ ] Weekly summary card (shareable as Instagram story) — trigger: organic share signal observed

### Future Consideration (V2+)

- [ ] iOS app — defer until ≥5,000 Android installs and ≥50 paying users
- [ ] Social / community / leaderboards — defer until retention >40% D30 (community on top of churn is wasted work)
- [ ] Hindi / regional voice input — defer until founder has bandwidth + tier-2/3 city signal
- [ ] Workout / exercise tracking — defer to V2 separate product surface
- [ ] Pre-diabetic / PCOS / medical mode — defer, requires medical advisor + CDSCO clearance
- [ ] Housewife persona (30-45 female) — defer; opposite acquisition channel, V2 separate brand
- [ ] Wearable integrations (Apple Watch, Mi Band, Boat, Noise) — V2; manual entry is enough V1
- [ ] AI chat tab — defer indefinitely; inline-advice moat depends on advice NOT being a separate surface
- [ ] HealthifyMe Auto Snap-style gallery auto-detect — V1.5 evaluate; privacy story complicates V1

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Photo-to-macros (50-dish whitelist) | HIGH | MEDIUM | P1 |
| Inline contextual advice (the moat) | HIGH | MEDIUM-HIGH | P1 |
| Daily home dashboard (kcal + macros) | HIGH | LOW | P1 |
| Last 3-day history | HIGH | LOW | P1 |
| Edit / correct macros | HIGH | LOW-MEDIUM | P1 |
| Phone OTP signup | HIGH | LOW | P1 |
| Manual entry fallback | HIGH | LOW | P1 |
| Streak counter + push notification | HIGH | LOW | P1 |
| DPDP + privacy plumbing | HIGH (legal) | MEDIUM | P1 |
| Reference-object photo tooltip | MEDIUM | LOW | P1 |
| **Weight log (research-identified gap)** | HIGH | LOW | P1 |
| **Water tracker (research-identified gap)** | MEDIUM | LOW | P1 |
| Weight-loss goal track | HIGH | MEDIUM | P2 (V1.1) |
| 14-day history extension | MEDIUM | LOW | P2 (V1.5) |
| Multi-meal combo photo | MEDIUM | HIGH | P2 (V1.5) |
| Whitelist expansion 50→100 | MEDIUM | MEDIUM (data work) | P2 (V1.5) |
| Razorpay subscription | HIGH (revenue) | MEDIUM | P2 (Phase 3) |
| Barcode scan | LOW-MEDIUM | HIGH (DB coverage) | P3 |
| Social / community | LOW (pre-PMF) | HIGH | P3 (V2) |
| Workout tracking | LOW (off-mission) | HIGH | P3 (V2) |
| Hindi voice input | MEDIUM | HIGH | P3 (V2) |
| iOS app | MEDIUM | HIGH ($99/yr + native rewrite) | P3 (V2) |
| Wearable integrations | LOW | HIGH (fragmented APIs) | P3 (V2) |
| AI chat tab | NEGATIVE (collapses moat) | MEDIUM | NEVER (anti-feature) |

## Competitor Feature Analysis

| Feature | HealthifyMe (40M users) | Cal AI (global, MFP-acquired Mar 2026) | NutriScan (India-focused) | Cult.fit | Our Approach |
|---------|------------------------|----------------------------------------|---------------------------|----------|--------------|
| Photo-to-macros | Yes — Auto Snap (gallery auto-detect) | Yes — core feature, paywalled | Yes — Indian-trained, multimodal (photo/voice/text) | No (workout-focused) | Yes — explicit capture, 50-dish whitelist, free in V1 |
| Indian food recognition | Strong DB (12yr), photo OK on basics | Weak — global model, no Indian context | Strong — India-first claim | N/A | Strong — Gate 0a validates ≥70% dish + ≥60% macros within ±35% |
| Inline advice on meal | No — Ria is separate chat tab, paywalled at ₹999/mo | No — calorie display only, no coaching | Yes — chat with "AI nutritionist" but separate surface | Human coach only at premium tier | **Yes — inline on every macros card, free V1 (THE MOAT)** |
| Vegetarian-protein focus | Generic | None | Some PCOS-veg plans | None | **Default mode; ₹/gram veg-protein table** |
| Budget-aware (₹ cost in advice) | No | No (USD-pricing in places) | No | No | **Yes — every advice line includes ₹ cost when food suggested** |
| Onboarding question count | ~10-12 | ~12 (then paywall) | ~8 | ~6 then upsell | **Target 6-8 (goal, height, weight, age, activity, veg/non-veg, budget bucket, phone OTP)** |
| Streak / habit mechanic | Yes (login streak) | Yes (animated badges) | Yes | Yes (class-attendance) | Yes — 3/7/14-day meal-log badges |
| Voice input | Yes — Ria Voice (OpenAI Realtime API, 2026 launch) | No | Yes — Monika (Hindi + English) | No | **No in V1 — anti-feature for V1 scope; V2** |
| Barcode scan | Premium | Yes | Limited Indian coverage | No | **No in V1 — V1.5 evaluate** |
| Water tracker | Yes | No (focused) | Yes | No | **Yes — 1-tap (research gap addition)** |
| Weight log | Yes | Yes | Yes | Yes | **Yes — manual entry (research gap addition)** |
| Sleep tracking | Yes (synced) | No | No | Partial | No (V2; not core to nutrition coaching) |
| Workouts / exercise | Yes — major feature | No | No | **Yes — core product** | **No in V1 — explicit anti-feature** |
| Social / community | Limited | No | No | Yes (class community) | **No in V1 — explicit anti-feature** |
| Wearable sync | Yes (Apple Watch, Fitbit, Garmin) | Yes (Apple Health) | No | Limited | **No in V1 — V2** |
| Free tier strength | Weak (demo-only, advice paywalled) | Paywall after onboarding ($2.99/wk - $29.99/yr) | Freemium (limits unclear) | No free tier (₹1,999+/mo) | **Strong — full advice + tracking free in V1-V2; Razorpay only Phase 3** |
| Price (paid tier) | ₹208/mo Smart, ₹1,500+/mo Coach, ₹1,20,000/yr Elite | $29.99/yr (~₹2,500/yr) dynamic pricing | Unclear public | ₹1,999-3,999/mo | ₹299/mo target (Phase 3) — "trainer-replacement" positioning |

## Indian-Context Specifics (Quality Gate)

1. **Regional dish coverage:** 50-dish pan-Indian whitelist (15 pan-India + 12 North + 12 South + 11 West/East) covers ~80% of common daily eating across tier-1/2 cities. Long-tail (Bengali sweets, Tamil temple sides, Punjabi street specialties) = V1.5. This is the design doc's "scope discipline by dish count" — validated against NutriScan's claim of "thousands of regional dishes" (which is largely DB-padding, not real recognition coverage).

2. **Vegetarian-protein-gap focus:** Verbatim customer quote: *"Most India is vegetarian — they want veg sources of protein more and more."* No incumbent productizes this. HealthifyMe gives generic advice; Cal AI is Western (chicken/eggs-default). Our advice engine must rank veg-protein suggestions by ₹/gram (paneer ~₹4-6/g protein, eggs ~₹3/g, dal ~₹2/g, soya chunks ~₹1.5/g, peanuts ~₹2.5/g). Build this reference table during Week 3 (advice engine).

3. **₹/day budget awareness:** Verbatim: *"Many people recommend diets according to Western context — costly, not common in India. Wanted budget diets."* Onboarding must capture a budget bucket (e.g., ₹150/day food / ₹300/day / ₹500+/day). Every advice line should respect this — "add 50g paneer for ₹18" not "add a salmon fillet."

4. **Trainer-replacement framing:** Verbatim: *"Gym trainers give schedules not good for their bodies — overdo treadmill, cardio, random exercises... suggest diets heavy in calories that affect health."* Brand positioning: "₹299/mo AI vs ₹3,000/mo trainer." HealthifyMe / Cult.fit cannot replicate — their business model includes human coaches. Single most defensible positioning element.

5. **DPDP Act 2023 + CDSCO/ASCI:** Indian-region storage (Cloudflare R2 Mumbai) is legal requirement, not preference. "Delete my data" button is statutory. Health disclaimer ("not medical advice") is CDSCO-mandated. None of these are differentiators — they are legal gates that block Play Store listing if missing.

## Sources

**Competitors analyzed (HIGH confidence, primary sources):**
- [HealthifyMe — Features page](https://www.healthifyme.com/smart/features.html)
- [HealthifyMe — Pricing](https://plans.healthifyme.com/)
- [HealthifyMe Ria Voice launch on OpenAI Realtime API](https://www.cxodigitalpulse.com/healthify-launches-ria-voice-a-real-time-multimodal-ai-coach-powered-by-openais-realtime-api/)
- [Cal AI — App Store listing](https://apps.apple.com/us/app/cal-ai-food-tracking/id6504333972)
- [Cal AI pricing 2026](https://nutriscan.app/blog/posts/cal-ai-pricing-2026-monthly-yearly-premium-abc6e7b26f)
- [Cal AI UI breakdown](https://screensdesign.com/showcase/cal-ai-calorie-tracker)
- [NutriScan — Indian food tracker](https://nutriscan.app/apps/track-food-en)
- [NutriScan — Voice calorie counter](https://nutriscan.app/apps/voice-activated-calorie-counter)
- [MyFitnessPal — Google Play India listing](https://play.google.com/store/apps/details?id=com.myfitnesspal.android&hl=en_IN)
- [MyFitnessPal 2026 Winter Release](https://www.globenewswire.com/news-release/2026/02/24/3243668/0/en/MyFitnessPal-Debuts-Its-2026-Winter-Release.html)
- [Cult.fit — Fitness plans](https://www.cult.fit/fitness)
- [Cult.fit vs HealthifyMe comparison](https://www.fittrackai.in/blog/cultfit-vs-healthifyme-which-is-better-for-indians-in-2026)

**Retention / churn research (MEDIUM-HIGH confidence):**
- [Why 80% quit calorie tracking apps](https://www.kygo.app/post/why-80-of-people-quit-food-logging-apps-and-how-to-actually-stick-with-it)
- [Calorie tracking apps fail — alternatives](https://yomp.fit/blog/why-calorie-tracking-apps-dont-work-and-what-to-do-instead)
- [Streak gamification habit loops](https://medium.com/design-bootcamp/streaks-and-daily-rewards-as-habit-forming-systems-dab7f5a34539)
- [Fitness app retention strategies (CleverTap)](https://clevertap.com/blog/fitness-apps-retain-new-users/)

**Onboarding research (MEDIUM confidence):**
- [Fitness app onboarding best practices](https://uxcam.com/blog/10-apps-with-great-user-onboarding/)
- [Psychology of fitness app onboarding (Amalgama)](https://amalgama.co/the-psychology-behind-fitness-apps-onboarding/)

**AI coach interaction patterns (MEDIUM confidence):**
- [AI nutrition coaches 2026 trend report](https://macrotracking.ai/blogs/technology/ai-nutrition-coaches-2026)
- [Building an AI nutritionist app guide 2026](https://www.lowcode.agency/blog/build-ai-nutritionist-app)

**Internal sources (HIGH confidence):**
- `/home/nitin/Desktop/ai-calorie-weight-loss/.planning/PROJECT.md` — locked feature scope
- `/home/nitin/.gstack/projects/ai-calorie-weight-loss/nitin-unknown-design-20260527-181050.md` — design doc iteration 4 with customer verbatim quotes

---
*Feature research for: AI-powered Indian-context nutrition coach (urban youth 18-30, muscle-gain V1)*
*Researched: 2026-05-27*
