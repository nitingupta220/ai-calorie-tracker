# Domain Pitfalls

**Domain:** AI-powered nutrition coach / calorie tracker (Indian-context, mobile, solo-bootstrap)
**Researched:** 2026-05-27
**Overall confidence:** HIGH (most pitfalls drawn from the project's adversarial-reviewed design doc + 2024-2025 literature on food-vision accuracy + Indian regulatory primary sources)

> **SUPERSEDED NOTE (2026-06-02):** Vision model is locked to **Gemini 2.5 Flash** (free tier 10 RPM / 250K TPM / 500 RPD), not the retired Gemini 2.0 Flash. Any "Gemini 2.0 Flash" or "15 RPM / 1500 RPD" figure below is a stale 2026-05-27 research note — read it as Gemini 2.5 Flash per the locked stack.

Pitfalls are organized by severity: Critical (causes rewrite, ship-blocker, legal exposure), Moderate (degrades retention or unit economics), Minor (recoverable in-flight). Each carries a phase pointer so the roadmap can route mitigation.

Source map for confidence calls:
- HIGH = primary docs (DPDP Act 2023, CDSCO MD Rules 2017, ASCI code), peer-reviewed nutrition-vision papers, vendor pricing pages
- MEDIUM = community post-mortems (Indiehackers, r/reactnative, RN release notes), competitor public reviews
- LOW = single-source or training-data-only inference

---

## Critical Pitfalls

### Pitfall 1: Vision Accuracy Collapse on Mixed Indian Dishes (Thali Problem)

**What goes wrong:** A user photographs a thali with 5-7 small items (sabzi, dal, rice, roti, raita, pickle, sweet). The vision model returns 1-2 items correctly, mislabels 2, and silently drops the rest. Macros card shows ~40% of true calories. User catches the error within 2-3 meals, loses trust, churns by day 4.

**Why it happens:**
- LLM vision models trained primarily on Western single-plate-single-dish imagery; Indian thali = multi-object segmentation problem the model wasn't optimized for.
- University of Sydney 2024 study on multimodal LLMs (GPT-4V, Gemini Pro Vision) on mixed Asian dishes reported 49-76% error on individual-item identification when 4+ items co-occur in one photo.
- Gemini 2.0 Flash improves over earlier multimodal SOTA but still degrades sharply past 3 co-occurring items.
- Founder's Gate 0a benchmark uses 30 photos but does not specifically stratify by thali-vs-single-dish — passing the gate on mostly-single-dish photos hides the thali failure.

**Consequences:** Trust collapse at the wedge feature. Once a user catches a wrong macros result on a meal they know the contents of, they cannot un-see it. D7 retention will not survive 2+ wrong reads in the first week.

**Prevention:**
- **Gate 0a stratification:** Make 30-photo benchmark include explicit buckets — 10 single-dish, 10 two-three-item plates, 10 full thalis (4+ items). Pass bar applies per-bucket, not aggregate. Failing the thali bucket = ship "single-photo, single-dish" UX with multi-item flow deferred to V1.5 (matches doc's "Multi-photo combo meals — V1.5" boundary, but does not currently extend to multi-item-single-photo).
- **Photo composition guidance in UI:** "Snap each item separately" tooltip on first photo. Reduce thali to N single-item photos rather than asking the model to do segmentation it cannot do.
- **Confidence-gated rendering:** If model returns >3 items OR overall confidence <0.6, do NOT render a macros number — show "Multiple items detected — tap each to confirm" with editable list. Don't let a low-confidence read masquerade as a high-confidence one.
- **Real-user benchmark before public launch:** Gate 7 alpha (week 12) should include a metric: % of photos where ALL items in the photo were named correctly (not just % of dishes named). If <60%, do not flip to public.

**Detection (warning signs):**
- Spike in tap-to-correct rate (target <15% of meals, alarm at >30%).
- "Wrong dish" verbatim in support / WhatsApp DMs.
- Per-meal calorie distribution showing implausibly low values (thalis logged as 200kcal).

**Phase:** Gate 0a (week 0), Week 2 vision pipeline, Week 5 reference-object UI, Gate 7 alpha (week 12) — block public launch on this.

**Confidence:** HIGH (literature + adversarial doc review explicitly raised this)

---

### Pitfall 2: Portion Estimation Without Reference Object (Depth Ambiguity)

**What goes wrong:** Same dish (paneer butter masala), two photos at different camera angles or distances → macros differ by 60-80%. User loses confidence after seeing inconsistent reads of the same meal.

**Why it happens:**
- A single 2D photo cannot resolve scale without a known-size reference. Models guess plate size from training-data priors → systematic ±30-50% error on portion (literature consensus: Lu et al. 2020, Mezgec & Korousic Seljak 2017).
- "Standard plate" assumption breaks on thali plates (larger), small Indian katori bowls (250ml vs Western soup bowl 400ml), banana-leaf serving (no plate boundary at all).
- LLMs do not natively report portion confidence — they emit a number; the user has no way to know it's a guess.

**Consequences:** Combined with Pitfall 1, this is the dominant source of "this app's macros are wrong" reviews on every existing tracker. HealthifyMe / Cal AI both ship with this limitation; users tolerate it more when the product TELLS them so.

**Prevention:**
- **Reference-object prompt required at meal photo (Week 5):** Hand / palm / coin in frame. Doc already calls this out — must be enforced in UI, not optional. First 3 onboarding photos = require reference object before save. After 3, allow skip but show "less accurate" badge.
- **Show estimate as range, not point:** Macros card shows "~520 kcal (range 380-650)" or honest "±30%" badge. Doc mentions "in-app disclaimer ±25-35%" — this must be ON the macros card, not buried in About.
- **Lock typical portion priors per dish:** For the 50-dish whitelist, founder-curated "typical Indian portion" g/ml values (1 roti = 40g, 1 katori dal = 150ml, 1 katori sabzi = 100g). Use these as floors/ceilings on model output. If model says 1 roti = 200g, override to typical with confidence flag.
- **Edit/correction flow as first-class UX (Week 3, 6):** Tap-to-fix should be one tap, not three. Treat corrections as training signal AND as the user's primary tool for accuracy, not a fallback.

**Detection (warning signs):**
- Founder's own meals during Gate 0b: same dish logged twice in same week with >40% variance.
- User correction rate on portion (not dish name) >25%.
- Verbatim "the amount is wrong" complaints exceeding "the dish is wrong."

**Phase:** Gate 0a (capture reference-object in benchmark photos), Week 2 (server-side portion floors/ceilings), Week 5 (reference-object UI), continuous (correction-flow polish).

**Confidence:** HIGH

---

### Pitfall 3: IFCT 2017 Raw-Ingredient Gap — Skipping Dish Decomposition

**What goes wrong:** IFCT 2017 has ~528 raw foods (raw paneer, raw tomato, raw onion). It does NOT have cooked dishes. Naive pipeline = "vision says paneer butter masala → lookup paneer butter masala in IFCT → not found → return paneer macros for 100g paneer." Result: missing the 30g butter + 15g cashew + cream + oil = real dish is 450kcal/100g, app reports 265kcal/100g. Off by 40-70% on every fat-heavy curry.

**Why it happens:**
- Most teams shipping Indian trackers reach for IFCT, see "official ICMR database," assume it solves the food-DB problem. It doesn't — it solves the *ingredient* problem.
- Cooked-dish databases for Indian food are fragmented (HealthifyMe has theirs proprietary, NIN has small recipe sets, no comprehensive open one).
- Dish decomposition (LLM-prompted: dish → ingredient list with grams → IFCT lookup → sum) is mentioned in design doc Week 2 but is the kind of step that gets skipped under deadline pressure.

**Consequences:** Macros are systematically wrong on every cooked dish that isn't a single ingredient (i.e. ~80% of Indian meals). Hidden because numbers look plausible — only catches when a user cross-references with another app or a dietitian.

**Prevention:**
- **Dish decomposition is non-negotiable Week 2 deliverable.** Pipeline: vision → dish name → LLM prompt "decompose into IFCT ingredients with typical Indian recipe grams" → sum IFCT macros → return. Cache decompositions per dish (50-dish whitelist → 50 cached decompositions, regenerate only on prompt change).
- **Founder-curated ground-truth decomposition table** for the 50-dish whitelist, built during Gate 0a. Each dish = {ingredients, typical_grams, source_recipe_url, founder_validated}. Treat as data, not LLM-generated-at-runtime.
- **Compare to NIN reference recipes** where available — National Institute of Nutrition has cooked-dish nutrient data for ~100 Indian dishes. Use as ground-truth for the whitelist overlap.
- **Per-dish macros sanity check:** For each whitelist dish, define plausible kcal/100g range (paneer butter masala 280-450, plain dal 80-120). If pipeline returns outside range, flag low confidence.

**Detection (warning signs):**
- During Gate 0b (founder's 14 days): founder's daily calorie total persistently <70% of expected (e.g. founder eats ~2400kcal but app shows 1600).
- Macros within ±35% bar (Gate 0a pass) achieved on dish-name match but failing on macros for cooked dishes specifically.
- Comparison test: log same dish in HealthifyMe AND in this app, expect within ±20% of each other. Larger delta = decomposition is broken.

**Phase:** Gate 0a (founder builds ground-truth table while benchmarking), Week 2 (decomposition layer ships with vision pipeline), Week 6+ (whitelist expands, decompositions added).

**Confidence:** HIGH (IFCT scope is documented, decomposition gap is the standard problem in Indian nutrition apps)

---

### Pitfall 4: Generic AI Advice Not Grounded in User's Log

**What goes wrong:** Advice engine prompt is "Give nutrition advice for a vegetarian user with muscle-gain goal." Output: "Eat more protein. Try paneer, lentils, eggs." Same advice for every user, every meal. Indistinguishable from HealthifyMe Ria. Moat collapses on day 1.

**Why it happens:**
- Easiest prompt to write produces the most generic output. LLMs default to safe-advice mode without rich context.
- Skipping the "feed last-3-days log + macros gap + budget + goal + dish just logged" context assembly because it's plumbing work, not glamorous AI work.
- "Inline on every macros card" requirement (P1) means the prompt fires per-meal, ~60 times/month per user — context-assembly cost feels heavy, gets cut.

**Consequences:** This is THE moat. If advice is generic, the product is "Cal AI with worse vision and Indian dishes." No reason to retain. No reason to pay ₹299.

**Prevention:**
- **Context-assembly checklist in every advice call:**
  - Goal (muscle-gain V1)
  - Today's macros so far + remaining-to-target
  - Last-3-days protein/calorie pattern
  - Veg/non-veg preference
  - Budget tier (₹/day food spend from onboarding)
  - The dish just logged
  - One reference from last-3-days log ("Yesterday's dal was 12g protein — today's is 18g, on track")
- **4/4 rubric is law, not aspiration.** Doc's rubric: specific food + specific quantity + ₹ cost + reference to recent log. Every advice output must hit 4/4. Anything <3/4 in QA gets the prompt rewritten.
- **Wizard-of-Oz QA loop is mandatory, not optional.** Week 6 design says "5 users x 7 days, founder writes manual advice interleaved with AI advice." This is the data source for prompt tuning. Skip = ship generic. The doc rejected WoZ as user-facing but kept it as QA — that QA mode MUST run.
- **Reject advice that doesn't reference user log.** Server-side check: if advice text doesn't contain a specific number from user's log (their protein count, their meal name from past 3 days), regenerate or fall back to a hand-written default for that meal type.
- **Per-dish advice templates as fallback safety net.** For each of 50 whitelist dishes, founder writes 2-3 candidate advice snippets. When LLM fails 4/4 check, fall back to template + small personalization (insert user's protein gap number).

**Detection (warning signs):**
- Founder's Gate 0b: <70% advice scoring 4/4. Doc treats this as a gate — honor it.
- Alpha users' verbatim feedback "this is the same advice as last meal" or "this is what HealthifyMe says."
- Low correction rate on advice (users ignore it = bad sign, not good — means it's wallpaper).

**Phase:** Gate 0b (validate advice quality before any RN code), Week 3 (advice engine v0 with full context assembly), Week 6 (WoZ QA loop), continuous (prompt tuning from QA data).

**Confidence:** HIGH (design doc identifies this as the moat; reviewer concerns flagged it)

---

### Pitfall 5: Retention Failure — Photo-Logging Effort Without Trigger

**What goes wrong:** User installs from Instagram post, logs 2 meals on day 1 (novelty), 1 meal on day 2, 0 on day 3. By day 4 the app is buried 3 screens deep on their home screen. Day 7 retention <10%, well below the 25% gate. Public launch blocked.

**Why it happens:**
- Photo-logging is effortful (open app, frame photo, wait 5s, verify). Habit doesn't form in 3 days.
- No external trigger pulls the user back. Lost to attention competitors (Instagram, WhatsApp, YouTube).
- Cal AI / MyFitnessPal both have this same dropoff; the apps that retain (Noom, Strava) ship hard around triggers + identity.
- "Streaks" alone are not enough — the user has to want to come back BEFORE the streak forms.

**Consequences:** Gate 7 fail = no public launch. Or worse, public launch with sub-15% D7 = burning the install funnel.

**Prevention:**
- **Daily 8pm push notification with PERSONALIZED hook** (Week 7 deliverable). Doc has this — "Log today's dinner to close your protein gap (you're at 48g, target 90g)." Variable: user's actual protein gap, not a static "log your meal" copy.
- **Streak counter visible on home screen + recovery framing.** "Best streak: 5 days" after a break — not "streak lost." Loss aversion + identity ("I'm someone who tracks").
- **Day 0 hook quality is the priority.** First meal logged → advice that's specifically useful → user shares screenshot. That's the loop. Without day-0 wow, no retention mechanic recovers.
- **Friction reduction sprint at Week 8.** Time-to-first-photo from open <10s. Macros card render <5s. Edit flow <2 taps. Measure these.
- **Morning AND evening push** (doc: 9am + 8pm, max 2/day). Different copy. Morning = "Log breakfast"; evening = "Close your protein gap."
- **Backup retention probes if pushes fail:** WhatsApp DM to alpha users at days 3 and 5 ("how's it going?"). High-touch, not scalable, but Phase 1 only and reveals where the funnel breaks.

**Detection (warning signs):**
- Day-1-to-day-2 dropoff >50% in alpha cohort.
- Push notification CTR <8% (industry baseline 10-15% for personalized).
- DAU/MAU <20% in alpha (target ≥30%).
- "I forgot about it" verbatim in interviews.

**Phase:** Week 7 (retention mechanic ships), Week 9-10 (alpha launch, monitor daily), Week 12 (Gate 7 evaluation), Week 13 (replan if fail).

**Confidence:** HIGH (universal across consumer health apps; doc dedicates a section)

---

### Pitfall 6: Free-Tier Rate Limit Surprise (Google AI Studio 15 RPM)

**What goes wrong:** Alpha launches Friday evening. 20 users open the app in the same hour, photograph dinners. Google AI Studio Gemini 2.0 Flash hits 15 requests-per-minute. Half the meals fail with 429. Users see "Try again" errors on their first impression. Half churn before day 2.

**Why it happens:**
- 15 RPM is comfortable for solo founder testing (Gate 0a: 30 photos over a week = 0.003 RPM avg). It is NOT comfortable for any clustered usage of 20 users.
- 1500 RPD (requests-per-day) sounds plenty (75/user/day) but doesn't help if all 20 fire in a 10-minute dinner window.
- "Free tier first, paid fallback" is documented in design doc but the fallback PATH must actually be wired — `ai_provider.py` abstraction must route on 429, not just on config flag.

**Consequences:** First impression = broken app. Recovery cost from a botched alpha launch is high (those 20 users were hand-recruited and will not give a second chance).

**Prevention:**
- **Auto-fallback on 429 hardcoded in `ai_provider.py`** from Week 1, not "we'll add it later." Sequence: Google AI Studio → OpenRouter free Gemini → Groq vision (Llama 3.2 vision) → paid Gemini Flash. Tested before alpha.
- **Local rate-limit budget tracker.** Before firing a call, check rolling-60-second count. If approaching 15 RPM, queue or pre-fall-back rather than 429-then-fall-back. Saves 200-500ms of latency on every fall-back path.
- **Pre-launch load test.** Simulate 20 concurrent photo uploads at dinner time, on actual API tier. Pass = >95% success, <8s P95 latency. Run before Week 9 alpha invites go out.
- **Cost ceiling alarm.** If fallback path hits paid tier, daily cost alarm at ₹50/day prevents runaway spend (doc has ₹0-200/month total Phase 1 budget; alarm at ₹50/day catches a misconfigured loop).
- **Provider SDK version pin.** Track Gemini SDK version; rate-limit semantics have changed between versions, breaking handlers silently.

**Detection (warning signs):**
- 429 rate in logs >2% of calls during alpha.
- Latency P95 >10s (sign of retry loops).
- User-visible "Try again" errors in WhatsApp DM feedback.

**Phase:** Week 1 (backend scaffold includes ai_provider with 429 fallback), Week 2 (pipeline tested under load), Week 8 (pre-launch load test), Week 9-12 (alpha monitoring).

**Confidence:** HIGH (current Google AI Studio free-tier limits documented; vendor SDK behavior verified via Context7 / official docs is recommended before code)

---

### Pitfall 7: Vendor Lock-In via Single-Provider Build

**What goes wrong:** Build ships using `google.generativeai` SDK directly throughout codebase. Month 5, Google changes Gemini Flash pricing OR introduces stricter rate limits OR adds policy that flags health-related prompts as restricted. Migrating to OpenRouter / Anthropic / OpenAI takes 2-3 weeks because vision and text calls are scattered across 12 files.

**Why it happens:**
- Provider SDKs are the easiest path. Founder under time pressure picks "just use the SDK" over "wrap behind interface."
- "We'll wrap it when we need to" — but the moment you need to is also the moment of crisis, when wrapping cost is highest.
- Doc explicitly addresses this with `ai_provider.py` abstraction — pitfall is failing to honor the abstraction discipline.

**Consequences:** Provider change becomes a 2-3 week project blocking other work. Worst case: pricing change wipes out unit economics overnight (doc shows ~₹17/user/mo at Gemini paid; ~₹28/user/mo on GPT-4o-mini fallback — 65% margin compression).

**Prevention:**
- **`ai_provider.py` is a contract, not a suggestion.** Every vision call goes through `VisionProvider.classify(image_bytes, prompt) → {items, macros, confidence}`. Every text call through `TextProvider.advise(context, prompt) → str`. No google.generativeai imports outside this module. Lint rule (ruff custom or grep in CI).
- **Two providers wired before launch.** Don't ship with only Google. Wire at minimum: Google AI Studio + OpenRouter (gives ~50 model fallbacks). Test the fallback path actually works monthly.
- **Per-call provider tag in logs** (not just for debugging — for cost attribution). When pricing changes, you can run "what would this month have cost on provider X?" analysis from logs alone.
- **Quarterly fallback drill.** First week of every quarter, route 10% of traffic through fallback provider for 24h. Reveals broken fallback before crisis.

**Detection (warning signs):**
- Codebase grep for `google.generativeai` returns hits outside `ai_provider.py` → broken abstraction.
- Provider config change requires code change → broken abstraction.
- Cost per call drift >20% month-over-month with no usage change → vendor pricing moved, react fast.

**Phase:** Week 0d (stack lock includes abstraction), Week 1-2 (wire 2 providers), Week 8 (fallback drill before alpha), continuous.

**Confidence:** HIGH

---

### Pitfall 8: First-Time React Native Shipper — Timeline Optimism

**What goes wrong:** Founder estimates 8-week native app build (Approach C). Actual: Week 4 stuck on Expo EAS Build credentials for Android signing. Week 6 stuck on push notification permissions on Android 13+. Week 9 still hasn't shipped first internal build. 14-week plan slips to 20+ weeks. Founder demoralized; alpha window misses Instagram-calorie-trend moment.

**Why it happens:**
- React Native + Expo is "easier than vanilla native" but still has ~30-40 platform-specific gotchas (camera permissions, push token registration, AAB signing, EAS credentials, Reanimated installation, native module bridging).
- First-time RN shippers underestimate by 40-60% (community-reported: r/reactnative timeline retrospectives, Indiehackers post-mortems).
- Doc acknowledges this: "10-12 weeks if shipped RN before, 14-20 weeks if first time." Acknowledging is not preventing.

**Consequences:** Timeline slip + founder cash runway + motivation. Worst: scope creep as founder adds "while I'm waiting on this" features.

**Prevention:**
- **Hello-World ship in Week 1, not Week 14.** Week 1 deliverable should include "Expo app builds, installs on founder's Android, sends one API call to FastAPI backend, displays response." Not just "scaffold." Ships to internal track.
- **EAS Build set up Week 1, not Week 8.** Most common timeline killer is hitting EAS credentials / Android signing for the first time at alpha-prep week. Set it up early when there's slack.
- **Time-boxed RN sprints.** If a single RN task takes >2 days, escalate: is there a webview fallback? A native-module workaround? Cut the feature?
- **Pre-budget the known time sinks:**
  - EAS Build first run: 0.5-1 day
  - Push notifications setup (Expo + FCM): 1-2 days
  - Camera permissions across Android versions: 0.5-1 day
  - Image upload optimization (1MB target after compression): 1-2 days
  - Background sync queue: 2-3 days
  - Play Internal Testing setup: 0.5-1 day
  Total = 5-10 days that the plan must absorb.
- **Approach D revisit trigger** (already in doc): if weeks 0-4 slip past 6 calendar weeks, reconsider WhatsApp-first hybrid. Honor this trigger.
- **Use Expo modules over custom native code wherever possible.** expo-camera, expo-notifications, expo-image-manipulator. Avoid ejecting from Expo managed workflow in V1.

**Detection (warning signs):**
- Week 1 deliverable not met by end of week 2 = slipping.
- Any RN task estimated at <1 day actually takes >2 days = recalibrate all estimates +50%.
- Hours-per-day on RN tooling vs. on product code: >40% on tooling = problem.

**Phase:** Week 0d (stack lock with explicit RN time-sink budgeting), Week 1 (hello-world ship + EAS setup), Week 4 (slip evaluation), Week 6 (Approach D revisit trigger).

**Confidence:** HIGH

---

### Pitfall 9: DPDP Act 2023 Compliance Gaps

**What goes wrong:** App goes live without (a) Indian-region storage proof, (b) explicit photo-upload consent, (c) one-tap "Delete my data" with 30-day hard delete, (d) opt-in (not opt-out) for "use my data to train AI." First user complaint → Data Protection Board investigation → fines up to ₹250 crore for significant breach (DPDP Act § 33).

**Why it happens:**
- DPDP Act 2023 was notified but Rules came in waves through 2024-2025; many India app builders still operate as if pre-DPDP.
- "Privacy policy" gets treated as a Week 11 task (doc has it there), but the technical plumbing it depends on (region pinning, delete pipeline, consent recording) must exist EARLIER or it's lipstick.
- AI-training opt-in is the most-missed clause — many apps default to "we may use your data to improve our AI" which under DPDP is invalid consent (not free, specific, informed, unconditional).

**Consequences:** Legal exposure scales with user count. At alpha (20 users) the risk is theoretical; at 1000 users a single complainant can trigger a Board notice. Worse than fines: app suspension on Play Store if reported.

**Prevention:**
- **DPDP-by-design from Week 1, not Week 11:**
  - Photo storage: Cloudflare R2 Mumbai or AWS Mumbai region only. Verify per-bucket region setting in code, not just assumed. (Doc has this.)
  - Postgres data: Railway region = Singapore by default. India region or move to alternative (Render India region, or self-hosted on Hetzner with India CDN). **VERIFY this — Railway's India presence is not standard and may need migration before public.**
  - DB backups: encrypted, retained ≤30 days, region-pinned.
- **Consent screens at signup (Week 4):** Three separate consents, each granular: (1) photo upload + storage, (2) macros + profile data for personalization, (3) anonymized data for AI improvement (DEFAULT OFF). Each timestamped + stored.
- **"Delete my data" button (Week 11 latest, but design Week 4):** UI in settings. Soft-delete immediately (user can no longer access). Cron hard-delete at 30 days: photos from R2, rows from Postgres, derived data, cache. Confirmation email/SMS at hard-delete.
- **Age gate 18+ at signup.** DPDP §9 children's data has stricter consent (verifiable parental consent). 18+ gate avoids this entirely in V1. Doc has this — enforce in code, not just policy.
- **Privacy policy linked from app store listing AND from in-app settings.** Specific to data types collected. Not a template.
- **Data Principal request workflow** (DPDP §11-13): even at 20 users, document a process to handle access/correction requests. WhatsApp inbox suffices in alpha; formal endpoint by public launch.

**Detection (warning signs):**
- Code grep for region/bucket config: any non-India region = critical bug.
- Manual audit of signup flow at Week 4: are consents granular and recorded?
- Test the delete flow end-to-end at Week 11. If you can still find a user's photo after 30 days, the cron is broken.

**Phase:** Week 1 (region pinning in backend scaffold), Week 4 (consent screens in onboarding), Week 11 (privacy policy + delete button + cron + audit), Week 13 (final compliance check before public).

**Confidence:** HIGH (DPDP Act 2023 primary source, MEITY rules drafts)

---

### Pitfall 10: CDSCO Medical-Device Territory via Marketing Copy

**What goes wrong:** App store listing or Instagram launch copy uses "diagnose your diet," "cure your weight problem," "treat your protein deficiency." Under Medical Devices Rules 2017 (CDSCO), any product claiming to diagnose, treat, prevent, monitor, or cure a disease can be classified as a software-as-medical-device (SaMD). Registration burden = months, not weeks. Worst: regulatory letter forcing app takedown.

**Why it happens:**
- "Treat" / "cure" / "diagnose" / "deficiency" are marketing-friendly words that creep into copy unconsciously. "Trainer replacement" framing flirts with this line.
- Indian regulators have moved aggressively on AI-health claims since 2024 (multiple notices to apps claiming "diabetes management").
- Doc has correctly identified this — "Trainer-replacement framing must stay fitness-not-medical." Pitfall is enforcement.

**Consequences:** Forced rebranding mid-funnel. App pulled from Play Store if reported. ASCI separately can issue takedown notice for marketing copy.

**Prevention:**
- **Banned-words list in all customer-facing copy:**
  - diagnose, treat, cure, prevent, manage (in medical sense), monitor (medical sense)
  - diabetes, hypertension, deficiency (medical use), syndrome, disorder
  - "doctor," "physician," "clinical" (unless disclaimer-bound)
- **Allowed framing:**
  - "Track your nutrition," "build muscle," "manage weight," "log meals," "fitness coach," "AI nutrition guidance"
  - Always paired with "Not medical advice. Consult a registered dietitian or physician for medical conditions or restricted diets." (Doc has this disclaimer text.)
- **In-app disclaimer on first launch + footer of every advice card.** Permanent, not buried.
- **Marketing copy review checklist** before every Instagram post, blog, app store update. 5-minute pass for banned words.
- **No before/after weight-loss-medical claims.** Before/after for muscle gain is OK; "lost 15kg in 2 months" without context is ASCI risk.
- **No pre-diabetic / medical-niche users V1** (doc Out of Scope) — honor this even if a user asks for the feature.

**Detection (warning signs):**
- Founder writing copy: pause and grep for banned words.
- ASCI / CDSCO appears in Google Alerts for the app — investigate immediately.
- User testimonials submitted: any mention of medical recovery (diabetes reversal, BP improvement) → do NOT use in marketing.

**Phase:** Week 13-14 (public prep, marketing copy review), Week 4 (in-app disclaimer in onboarding), continuous (every customer-facing surface).

**Confidence:** HIGH (CDSCO Medical Devices Rules 2017 primary source)

---

### Pitfall 11: ASCI Advertising Code Violations

**What goes wrong:** Instagram launch post: "Replace your gym trainer for ₹299. Lose 10kg in 30 days. Guaranteed." ASCI receives a complaint (anyone can file), issues a CCC ruling, post must be taken down, public listing on ASCI website (reputational hit), repeat offense → escalation to ad regulator + ministry.

**Why it happens:**
- ASCI's health-and-personal-care code requires evidence for efficacy claims. "Trainer replacement" is comparative — needs substantiation.
- "10kg in 30 days" is a quantified efficacy claim — needs clinical-grade backing (none available for an AI app).
- Influencer marketing copy is the highest-risk surface (Phase 3 plan in doc).

**Consequences:** Takedown + reputational hit + chilling effect on subsequent campaigns. Repeat = bigger trouble.

**Prevention:**
- **No quantified efficacy claims.** "Lose X kg in Y days," "build 5kg muscle in 2 months" = banned. Even with disclaimers.
- **Comparative claims need disclosure.** "Trainer replacement at ₹299/mo instead of ₹3000/mo" → fine as positioning. "Better than your trainer" → needs substantiation. Wording matters.
- **Influencer disclosures.** Any paid partnership tagged #ad or #sponsored per ASCI guidelines for influencer advertising (2021 updated 2023).
- **Testimonial rules:** real users only, results explicitly "not typical" disclaimer, no medical claims.
- **ASCI's pre-screen advisory service** available (low cost) for first major campaign. Worth using once for the public launch hero creative.
- **Maintain claim-substantiation file.** For every claim made in marketing, store the source. "₹299 vs ₹3000 trainer" = anchored to gym-trainer interview quotes from doc Customer Conversations.

**Detection (warning signs):**
- Marketing draft uses absolute numbers (kg, %, days) → review.
- Influencer post copy not pre-reviewed by founder → require review.
- ASCI mention in Google Alerts.

**Phase:** Week 13-14 (Play Store listing copy + first Instagram post), continuous (every marketing surface), Phase 3+ (influencer scaling).

**Confidence:** HIGH (ASCI code primary source)

---

### Pitfall 12: Two-Persona V1 Dilution

**What goes wrong:** Despite doc discipline (urban Indian youth 18-30, muscle-gain first), pressure mid-build to "also support women/housewives" or "also support weight-loss day 1" creeps in. Onboarding adds a second goal flow. Advice prompts gain a gender + goal switch. Push copy fragments. Result: brand voice fragments. Marketing channel split (Instagram gym-bros + WhatsApp homemakers). Solo founder spread across two GTMs. Neither reaches PMF.

**Why it happens:**
- "Just one more goal/persona" instinct flagged in doc closing observations. It returns at every scope decision.
- Customer interviews surface valid pain in adjacent personas; saying "not now" feels like leaving money on the table.
- Engine technically supports both — temptation to expose what the engine can do.

**Consequences:** V1 ships diluted. No persona's WhatsApp/Instagram thread is fully tuned. D7 retention misses on both. Failure mode looks like "the product is fine but no one is recommending it" — diffuse blame.

**Prevention:**
- **V1 persona lock is a hard contract.** Doc out-of-scope items (housewife persona V2, weight-loss V1.1) are commitments, not preferences.
- **Persona anchor:** One named persona from the 5 user interviews (doc Assignment item 6). Every product decision answers "would this help [Name]?" If unclear, the decision waits.
- **One brand voice:** casual, gym-coded, English/Hinglish. Every microcopy passes the voice test. No "wellness journey" softening for adjacent personas.
- **One channel:** Instagram organic V1. WhatsApp invites for alpha (high-touch). No Reddit ads / Facebook groups / influencer outreach until D7 ≥25%.
- **V1.1 trigger:** weight-loss goal added only AFTER muscle-gain D7 ≥25% AND advice 4/4 ≥75% on real users. Not a calendar trigger.
- **Scope-creep review at every milestone.** Doc has "After each phase transition" workflow — use it to actively re-scope OUT, not just IN.

**Detection (warning signs):**
- New onboarding question added that isn't part of original flow → why? Does V1 need it?
- Advice prompts gaining conditional logic for "if user_type == X" → wedge dilution.
- Marketing copy drafted that wouldn't fit on a gym-bro Instagram → off-persona.

**Phase:** Continuous from Week 0. Most acute at Week 11-12 (alpha feedback rolls in) and Week 14+ (post-launch).

**Confidence:** HIGH (doc-internal — adversarial reviewer flagged this explicitly)

---

## Moderate Pitfalls

### Pitfall 13: Solo Founder Bandwidth Collapse on UI Around Unvalidated AI

**What goes wrong:** Founder spends weeks 4-8 (4 calendar weeks) building React Native UI screens (onboarding, home, history, settings) on top of an AI engine that's only been tested by the founder. Alpha launches week 9; AI advice quality is 50% 4/4 (not 70%); UI looks great but feeds bad data to users. Refactoring AI engine requires reworking UI surfaces too.

**Why it happens:**
- UI work is visible and satisfying — feels like progress.
- AI prompt-tuning is invisible and frustrating — feels like stagnation.
- Solo founders gravitate to visible work under stress.
- Doc Gate 0b mandates 14 days of own meals + 70% 4/4 BEFORE Week 1. Pitfall is reaching Gate 0a-0b "pass enough" and moving on before AI is genuinely solid.

**Consequences:** Wasted UI work + delayed AI iteration + alpha disappointment.

**Prevention:**
- **AI advice 4/4 rate is the build's leading indicator.** Track weekly. If <70% sustained, freeze UI work and return to prompt tuning.
- **WoZ QA loop Week 6 must produce ≥20 advice-prompt-tuning examples** before considering AI complete.
- **One UI screen per week pace** — not three. Polish budget reserved for Week 8.
- **Decouple AI from UI via stable backend API.** AI engine can ship a new version without UI redeploy. Reduces fear of "but the UI is built against the old prompt."

**Phase:** Week 3+ continuous, Week 6 (WoZ QA loop), Week 8 (polish, not new screens).

**Confidence:** MEDIUM (founder-typology specific)

---

### Pitfall 14: Wizard-of-Oz QA Loop Skipped

**What goes wrong:** Week 6 plan includes founder writing manual advice for 5 users x 7 days, interleaved with AI advice, for QA + prompt tuning. Under time pressure, founder skips it. AI ships in alpha with prompts tuned only on founder's own meals (low-diversity, biased to founder's eating pattern). Alpha advice quality drops because real users eat differently than founder.

**Why it happens:**
- Manual writing for 5 users x 7 days = 35 advice instances minimum. ~30-60 min/day of founder work. Feels like a tax during build crunch.
- Doc says "Used only as QA tool for 5 users × 7 days mid-build to seed prompt-tuning data" — explicit but skippable.

**Consequences:** AI advice never learns from out-of-founder-distribution users until public alpha. Founder is debugging AI quality on actual paying-attention alpha users.

**Prevention:**
- **WoZ QA is a Gate, not a task.** Mark Week 6 as "AI advice ready for alpha when 5x7 = 35 WoZ examples completed AND AI-vs-WoZ side-by-side scoring shows AI matches WoZ at ≥70%."
- **5 users x 7 days is the minimum.** If they don't all respond, recruit more. The 35-example budget matters.
- **Capture both AI and WoZ outputs** in the same DB table. Tag each. Use diffs as the prompt-tuning corpus.
- **Schedule it explicitly** — block founder calendar Week 6 for 1hr/day for QA loop.

**Phase:** Week 6.

**Confidence:** MEDIUM

---

### Pitfall 15: Razorpay GST + GSTIN Cliff at ₹20L Annual Receipts

**What goes wrong:** App grows past 600 paying users at ₹299/mo = ₹21.5L/year. Founder hasn't registered for GSTIN (mandatory above ₹20L for service businesses in most states, ₹10L in special-category states). Razorpay continues collecting payments but no GST is charged or remitted. Discovered during income tax filing → penalty + back-GST + interest.

**Why it happens:**
- ₹20L feels far away in early days. Founder defers GSTIN registration.
- Razorpay handles payment processing but does NOT auto-register founder for GST.
- Once threshold is hit mid-month, all that month's invoices retroactively need GST.

**Consequences:** Penalty + interest on unremitted GST. Razorpay account flagged. Potential service interruption.

**Prevention:**
- **Register GSTIN BEFORE Phase 3 paid launch.** Doc has this — "Founder registers for GSTIN before annual receipts exceed ₹20L." Pre-register, even at zero receipts. Free to register, ₹0/month if no transactions.
- **Set Razorpay invoice template with GSTIN once registered.** 18% GST on subscriptions.
- **Quarterly GSTR-3B filing** discipline. Set calendar reminder.
- **Track MRR vs ₹20L/year threshold** monthly. Alarm at ₹1.5L MRR (= ₹18L/year, 90% of threshold).
- **Composition scheme NOT applicable** to app subscriptions (interstate / digital service) — file under regular regime.
- **State of registration matters:** founder's home state. Verify.

**Phase:** Week 13-14 (Razorpay setup), Phase 3 (paid launch, GSTIN must be live).

**Confidence:** HIGH (GST Act primary source)

---

### Pitfall 16: Play Store Review Delay Underbudgeted

**What goes wrong:** Week 13-14 public launch plan assumes Play Store review is quick. First submission goes to "Under Review" → 7-14 days (initial submissions are slower than updates). Policy issue surfaces (medical claims in description, missing privacy URL). 3-day fix cycle. Launch slips 2 weeks.

**Why it happens:**
- Internal Testing track ≠ Production track. First submission to Production is reviewed manually for new developers.
- Play Store policies tightened 2024-2025 around health apps, AI-generated content, and data safety form.
- Data Safety form is detailed (declare all data types collected, where stored, third parties). Common rejection cause when mismatched with actual code.

**Consequences:** Launch slippage at the worst possible moment (Week 14 momentum lost).

**Prevention:**
- **Internal Testing track set up Week 8 (per doc).** Production track submission STARTED Week 12, not Week 14. Buffer 2 weeks for review.
- **Pre-fill Data Safety form to match code reality.** Photo data, profile data, fitness data, all declared. Third parties: Google AI Studio, Groq, Cloudflare, Firebase. Match each declared type to actual collection in code.
- **Listing copy CDSCO/ASCI-compliant before submission** (Pitfalls 10, 11).
- **Privacy Policy URL live before submission** (Pitfall 9).
- **Screenshots + icon meet Play Store specs** (1024x500 feature graphic, 512x512 icon, etc.) — minor but rejected on mismatch.
- **Internal Testing track approval first** (faster, but still 1-3 days for new dev account).
- **$25 Play Developer account purchase + identity verification** (~3-7 days for new accounts under 2023 verification rules) BEFORE Week 8 — currently doc doesn't pin a week.

**Phase:** Week 0d (Developer account purchase + verification — earlier than doc states), Week 8 (Internal Testing track), Week 12 (Production track submission with full listing), Week 14 (launch flip).

**Confidence:** HIGH

---

### Pitfall 17: Razorpay Onboarding Delays (KYB + Settlement Account)

**What goes wrong:** Phase 3 paid launch planned. Razorpay account creation needs business KYC (PAN, GST, bank account, address proof, signed agreements). Solo founder running as proprietorship vs. registered entity affects flow. 5-15 business days for full activation. First paid users hit "payment failed."

**Why it happens:**
- "Sign up at Razorpay" sounds fast — it's not for first-time business accounts.
- Razorpay holds initial settlements (T+2 or T+3 default) — first ₹50k of payments may sit in escrow until KYB clears.

**Prevention:**
- **Razorpay account opened Week 13-14** (per doc) is fine IF it's just opening. **Full activation tested with ₹1 test transaction by Week 14**.
- **Founder business entity decided BEFORE Razorpay onboarding:** proprietorship (faster, simpler) vs. private limited (slower, more complex, future-proof for fundraising). V1: proprietorship is sufficient.
- **Bank account separation:** dedicated current account for business (not founder's personal savings account) — Razorpay requires it.
- **Settlement schedule configured:** default T+3 → request T+1 once volume justifies (post Phase 3).

**Phase:** Week 13-14 (Razorpay account creation), Phase 3 (full activation + first test transaction before paid users).

**Confidence:** HIGH

---

### Pitfall 18: Image Storage Cost Spiral on Cloudflare R2

**What goes wrong:** Photos uploaded uncompressed (4-8 MB per phone photo). At 100 users x 2 photos/day x 30 days = 6,000 photos/month = 30-50 GB/month. Cloudflare R2 storage is cheap (~$0.015/GB/month) BUT egress on photo retrieval (history views) adds up. Storage budget blown 3x.

**Why it happens:**
- React Native Expo default image upload doesn't compress aggressively.
- Photos retained indefinitely (doc: "retained while account active").
- Photos re-fetched on every history view if not cached client-side.

**Prevention:**
- **Client-side compression before upload** (Week 5 deliverable, per doc Week 5 camera screen). Target: 800x800 px max, JPEG quality 70-80, <500 KB per photo.
- **Server-side thumbnail generation** on upload: 200x200 thumbnail for history list, full-size only on detail tap.
- **Client-side image cache** (expo-file-system) keyed on photo ID. Re-fetch only on cache miss.
- **R2 region: Mumbai** for both compliance AND latency (egress within India is faster).
- **Storage cost dashboard from Week 1.** Alarm at ₹500/month threshold (well below doc's ₹1700 ceiling).
- **Retention policy:** photos older than 14 days move to lower-tier storage or get auto-thumbnail-only (keep macros, drop full-res). V1.5 optimization, plan for it.

**Phase:** Week 5 (compression in camera screen), Week 7 (history view with cache), continuous (cost monitoring).

**Confidence:** MEDIUM

---

### Pitfall 19: Firebase Phone OTP Cost / Rate-Limit Surprise

**What goes wrong:** Firebase Phone Auth free tier = 10K verifications/month free, then ~$0.05-0.06 per verification. Alpha + early public = under free tier. But abuse (someone hitting verify endpoint) or marketing burst can exceed quickly. Also, in India, telecom DLT (Distributed Ledger Technology) registration for SMS sender IDs adds friction — Firebase handles this for its own infrastructure but not all flows.

**Why it happens:**
- Doc picks Firebase OTP over MSG91 specifically for speed (DLT registration takes 3-7 days for MSG91). Trade-off is cost-at-scale + occasional Indian carrier-specific delivery issues.
- Bots hitting OTP endpoint = expensive fast.

**Prevention:**
- **reCAPTCHA Enterprise on OTP endpoint** (Firebase has this built in — enable it).
- **Rate limit OTP requests per phone number** (1 per minute, 3 per hour, 10 per day). Server-side.
- **Cost alarm at 8K verifications/month** (80% of free tier).
- **Backup SMS provider planned, not built.** If Firebase OTP fails in scale, MSG91 with DLT pre-registered. Don't build the migration; document the trigger.
- **Indian carrier delivery monitoring:** Reliance Jio, Airtel, Vi sometimes delay OTP SMS. Display "didn't get it? Try after 30s" with fallback to voice OTP.

**Phase:** Week 1 (Firebase setup with reCAPTCHA), Week 4 (onboarding flow with rate limit), continuous.

**Confidence:** MEDIUM

---

### Pitfall 20: Misaligned Macro Targets per Goal/Persona

**What goes wrong:** Onboarding asks weight, height, goal. Algorithm sets macro targets using a Mifflin-St Jeor formula or similar. For muscle-gain at user's stats, target = 1.6g protein/kg, ~+300 kcal surplus. Algorithm uses outdated formula or wrong activity multiplier. Real protein target should be 1.8-2.2g/kg for active muscle-gain user. Advice prompts user toward sub-optimal target. User asks dietitian, finds mismatch, churns + bad-mouths.

**Why it happens:**
- "Use the standard formula" sounds simple. Standard formulas vary in muscle-gain context (some recommend 1.4-1.6, current sports-nutrition consensus 1.6-2.2 for resistance-trained, more for cutting + resistance).
- Vegetarian-protein-gap framing (doc moat) requires the target to actually be a STRETCH for veg users (so the gap is real and addressable). If target is too low, no gap, no advice value.

**Prevention:**
- **Use evidence-based protein targets:** ISSN position stand (2017, updated 2024) for protein. For muscle-gain: 1.6-2.2 g/kg/day. Mid-range: 1.8 g/kg as V1 default.
- **Calorie targets via Mifflin-St Jeor + activity factor + 250-500 kcal surplus** for muscle gain. Conservative end (250) for V1 to avoid over-recommending.
- **Founder validates own targets against personal dietitian / known sports-nutrition source** during Gate 0b.
- **Disclosed methodology in app:** "Your protein target uses 1.8 g/kg based on body weight and goal (ISSN 2024)." Users curious about sources can read.
- **No exotic formulas** (Katch-McArdle requires body-fat %, which V1 doesn't collect). Stick to mainstream.
- **Edit targets in settings:** advanced users override defaults. Captures real-world target distribution as data.

**Phase:** Week 4 (onboarding builds targets), Gate 0b (founder validates own).

**Confidence:** MEDIUM-HIGH (sports nutrition literature consensus)

---

## Minor Pitfalls

### Pitfall 21: Offline Queue Edge Cases

**What goes wrong:** User logs meal offline (subway, no signal). App queues photo upload. User logs 5 more meals offline. Queue grows. User force-quits app. Queue lost. User logs back in, no meals appear.

**Prevention:** Persisted queue (AsyncStorage or expo-sqlite). 24-hour TTL (doc has this). Sync on app foreground. Show offline-pending badge on home screen. Don't allow >5 queued items (back-pressure).

**Phase:** Week 8 (polish + alpha prep).

**Confidence:** MEDIUM

---

### Pitfall 22: Push Notification Permissions on Android 13+

**What goes wrong:** Android 13+ requires runtime POST_NOTIFICATIONS permission. User denies. App is silent. Retention mechanic dies for those users with no way for them to discover it.

**Prevention:** Permission prompt with strong rationale screen FIRST (Week 4 onboarding — "We'll remind you at 8pm to log dinner so you hit your protein target"). If denied, soft re-prompt at Day 3 if user has used the app 2+ times.

**Phase:** Week 4 (onboarding), Week 7 (retention mechanic).

**Confidence:** HIGH

---

### Pitfall 23: Founder Verbatim Quotes Insufficient for Demand Bar

**What goes wrong:** Doc Open Question #1 — "No verbatim 'I would pay ₹299/mo' quote yet." Founder skips this because alpha is exciting. At Phase 3 launch, no validated price quote = pricing is theater.

**Prevention:** Week 1 user interviews (doc Assignment item 5) include the explicit price-WTP question. Capture verbatim. If 0/5 say yes, re-examine price BEFORE building 12 weeks of app on it. Add to Week 12 alpha exit interview as required field.

**Phase:** Week 1, Week 12.

**Confidence:** MEDIUM

---

### Pitfall 24: Edit/Correction Flow Treated as Afterthought

**What goes wrong:** Correction flow built in Week 6 as "tap to fix." Implementation is 3-tap deep, requires re-entering macros manually. Users don't correct → bad data accumulates → AI doesn't get the corrections training signal.

**Prevention:** Correction flow = one-tap to fix dish name (autocomplete from 50-whitelist), one-tap to fix portion (1.0x / 0.5x / 1.5x / 2.0x), tap-and-edit for custom. Corrections logged with original prediction → corpus for prompt tuning. Showcased in onboarding ("Got it wrong? Tap to fix in one second.")

**Phase:** Week 3 (initial), Week 6 (UI polish).

**Confidence:** MEDIUM

---

### Pitfall 25: Cost-Per-User Tracking Drift

**What goes wrong:** Doc has cost models (~₹17/user/mo Phase 2). Reality: no per-user cost telemetry built. At Phase 2 there's no way to know if you're at ₹17 or ₹40 until the invoice arrives.

**Prevention:** Every AI call tagged with user_id + provider + tokens + estimated cost. Daily aggregation table. Per-user dashboard. Alarm at user-level (>₹50/user/mo individual = investigate that user's usage).

**Phase:** Week 1 (logging), Week 8 (dashboard), continuous.

**Confidence:** MEDIUM

---

### Pitfall 26: AI Hallucinates Dishes Outside Whitelist

**What goes wrong:** User photos a dish that isn't in the 50-whitelist. Model returns a confident but wrong name from the whitelist. User sees "biryani" labeled for what they ate as "tehri." Confidence is high. App doesn't fall back to manual.

**Prevention:** Vision prompt explicitly enumerates the whitelist + instructs "return UNKNOWN if not in this list." Server-side validation: returned name must match whitelist exactly. If not in list, render "Dish not yet supported — log manually" (per doc). Confidence threshold tuning during Gate 0a.

**Phase:** Week 2 (vision pipeline), Gate 0a (whitelist enforcement testing).

**Confidence:** MEDIUM

---

### Pitfall 27: Prompt Drift Without Versioning

**What goes wrong:** Founder iterates on advice prompts during Weeks 3-6, doesn't version. Week 8 prompt produces different outputs than Week 4. Hard to A/B compare. WoZ QA examples no longer match prompt that's live.

**Prevention:** Prompt strings in version-controlled file with semver. Every prompt change = version bump + changelog. AI call logs include prompt_version. A/B testable.

**Phase:** Week 3 onward.

**Confidence:** MEDIUM

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall(s) | Mitigation |
|-------------|-------------------|------------|
| Gate 0a (vision benchmark) | Pitfall 1 (thali), Pitfall 2 (portion), Pitfall 3 (decomposition) | Stratify 30 photos by complexity; build ground-truth decomp table for 50 dishes; include reference object |
| Gate 0b (advice validation) | Pitfall 4 (generic advice), Pitfall 13 (founder bandwidth) | 4/4 rubric enforced; founder's own meals first, 14 days |
| Gate 0c (user commitments) | Pitfall 23 (price WTP unvalidated) | Add explicit ₹299/mo question to commitment script |
| Gate 0d (stack lock) | Pitfall 7 (vendor lock-in), Pitfall 8 (RN timeline), Pitfall 16 (Play account delay) | ai_provider.py contract; hello-world Week 1; Play Developer account purchase Week 0 |
| Week 1 backend scaffold | Pitfall 6 (rate limits), Pitfall 9 (region pinning), Pitfall 19 (Firebase OTP) | 429 fallback wired; R2 Mumbai verified; reCAPTCHA + rate-limit OTP endpoint |
| Week 2 vision pipeline | Pitfall 1, 2, 3, 26 (decomp, thali, portion, whitelist) | Decomposition layer; confidence-gated rendering; whitelist enforcement; reference-object expected |
| Week 3 advice engine | Pitfall 4 (generic), Pitfall 27 (prompt versioning) | Full context assembly; 4/4 gate; prompt strings in version control |
| Week 4 onboarding | Pitfall 9 (consent), Pitfall 12 (persona dilution), Pitfall 20 (macro targets), Pitfall 22 (push perms) | Granular consents; one persona only; ISSN-based protein target; permission rationale screen |
| Week 5 camera + reference object | Pitfall 2 (portion), Pitfall 18 (image cost) | Reference-object UI; client-side compression |
| Week 6 manual advice QA | Pitfall 14 (WoZ skipped) | Calendar block; 35-example minimum |
| Week 7 retention mechanic | Pitfall 5 (retention) | Personalized push; streak with recovery framing |
| Week 8 polish + alpha prep | Pitfall 6 (load test), Pitfall 21 (offline queue), Pitfall 25 (cost telemetry) | Load test on real API tier; persisted queue; per-user cost dashboard |
| Week 9-10 alpha | Pitfall 1, 4, 5 (vision, advice, retention) — live monitoring | Daily dashboards; WhatsApp DM check-ins on day 3 and 5 |
| Week 11 DPDP + privacy | Pitfall 9 (DPDP), Pitfall 10 (CDSCO) | Audit checklist; in-app disclaimer; delete cron tested |
| Week 12 alpha gate | Pitfall 5 (retention), Pitfall 23 (price quote) | Honor 5/20 retention gate; capture price-WTP verbatim |
| Week 13-14 public prep | Pitfall 10 (CDSCO), Pitfall 11 (ASCI), Pitfall 16 (Play review), Pitfall 17 (Razorpay) | Marketing copy banned-words scan; Play submission Week 12 not 14; Razorpay tested with ₹1 |
| Phase 3 paid launch | Pitfall 11 (ASCI influencer), Pitfall 15 (GSTIN), Pitfall 17 (Razorpay settlement), Pitfall 7 (vendor cost) | GSTIN pre-registered; influencer disclosure; quarterly fallback drill |

---

## Vision / Calorie-Accuracy Pitfalls (added 2026-06-02 · external-review-verified)

> Folded in after an external adversarial review of the photo→macros premise. Every figure below was fact-checked against primary sources (Nutrition5k CVPR 2021; GPT-4V food study, Nutrients 2025; Martin et al. 2018; RevenueCat 2025–26; OpenAI's HealthifyMe case study). Confidence tags reflect that check. **One reviewer claim FAILED verification and is deliberately omitted: "calorie-tracking retention 68%→21% by week 12 / AI apps churn 30% faster" — unsourced; the only real 30% evidence points the other way (AI personalization *reduces* churn ~30%).** The qualitative "diet apps decay hard over ~12 weeks" thesis is supported (JMIR MyFitnessPal review); the specific numbers are not.

### V-01 · Recognition accuracy ≠ calorie accuracy (dish-ID is the easy ~20%) [HIGH]

**What goes wrong:** The project can conflate "can it name the dish" with "can it tell me the calories." Different problems, order-of-magnitude difference in difficulty. Off-the-shelf transfer-learning models hit ~87–93% top-1 on Indian dish *recognition* (verified: MobileNetV3 87.64% / 92.39% / 93.5%, up to 95.3% augmented); GPT-4 Vision hit 93% precision *identifying* foods from 114 meal photos (Nutrients 2025, PMC11858203). But the **same** GPT-4V study found nutrient *values* unreliable: 11 of 16 nutrients differed significantly (p<0.05), 12 off by >10%. Naming "paneer butter masala" tells you nothing about whether it's 280 or 450 kcal.

**Why it matters here:** The promise ("accurate macros") and the wedge ("trust the app more than your trainer") live entirely on the hard side of this gap. Anti-pattern #4 (photo → dish-ID + portion → deterministic IFCT lookup, never LLM-direct macros) is *correct precisely because of* this gap. But the Gate-0a metric must score the two halves **separately** or it passes on the easy half and ships the hard half broken.

**Prevention:** Score dish-ID and macro-accuracy as independent gate metrics. Hold dish-ID to a HIGH bar (80%+, it's easy); treat macro-within-tolerance as the separately-binding pass criterion. Never let a strong dish-ID number average up a weak macro number. **Caveat:** the 87–93% figures are closed-set top-1 on small clean datasets (13–30 classes); they degrade on a 50-dish open-world whitelist with thalis and real phone photos. Lab ceiling, not field accuracy.

### V-02 · Portion-from-2D is mathematically ill-posed — the calorie-error floor [HIGH]

**What goes wrong:** Estimating real-world volume/mass from a single flat photo is an under-determined inverse problem (monocular scale ambiguity) — geometry, not model quality. Portion error propagates linearly into the calorie number. **Verified figure (Nutrition5k, Thames et al., CVPR 2021, arXiv:2103.03375, Table 3):** single-RGB-image direct calorie model = **26.1% mean calorie error (70.6 kcal MAE)**; adding depth/volume drops it to **16.5% (41.3 kcal MAE)**. The only demonstrated way to roughly halve the error is a depth channel this app does not have. (Caveat: the depth rows use the 3.5k RGB-D subset, not the full 5k. A portion-*independent* per-gram model reaches 9.5% — but that is not absolute-calorie prediction and not what we ship.)

**Why it matters here:** Nutrition5k is the *best case* — clean overhead Western single-component plates. Indian phone photos at arbitrary angles are strictly harder. ±35% tolerance is generous vs the 26% *mean*, but the *tail* (heavy-tadka curries, deep bowls) blows past 35%. Learned priors help the mean, not the tail.

**Prevention:** (1) **Reference object mandatory** in the accuracy-critical gate — coin/palm/plate gives the missing scale prior (Sketch 001's reticle is the right instinct; enforce it). (2) Per-dish portion floors/ceilings clamp absurd outputs. (3) Show macros as a **range**, not a point. (4) Treat the correction UI as the *primary* accuracy tool, not a fallback.

### V-03 · Hidden oil / ghee / cream is invisible in pixels [HIGH]

**What goes wrong:** Absorbed/emulsified fat carries large calorie load with little visual signature. **1 tbsp oil ≈ 120 kcal (100% fat) — verified exact.** "Dal" spans ~100–400 kcal by tadka (plain ~97–107 kcal/100g; light tadka ~137–147; restaurant ghee/cream ~220–270/katori). The model cannot see how much ghee went into the tempering. This is a *second, independent* error source stacked on portion ambiguity — the core reason image-only error stays high even when dish-ID and portion are both right. The deterministic IFCT pipeline only fixes this if the decomposition table's fat grams match the actual dish — which a fixed table cannot know.

**Prevention:** (1) Bound the claim: market "macro estimate / range," never "exact calories" — the moat is veg-protein-gap advice, not exact kcal. (2) Per-dish "rich vs plain" variants in the decomposition table (dal_plain / dal_tadka / dal_restaurant) with a one-tap user selector. (3) Honest ±tolerance badge. (4) Report fat-heavy curries separately in the gate; expect them to be worst.

### V-04 · Human accuracy ceiling: even people get ~5/20 photos within 20% [HIGH]

**What goes wrong / calibration:** Photo calorie estimation is hard for humans too. Crowdsourcing study (Martin et al., Interactive J Med Research 2018, PMID 30401671): 2,028 respondents, 20 photos, averaged only **5/20 (25%) within ±20%** of truth. Two implications, both true: (1) *Defensive* — a model near the ~26% Nutrition5k mean is roughly at the human-from-photo baseline; "not perfect" is the defensible target, and the reviewer's implicit "humans do better" premise is false. (2) *Cautionary* — the user's own ground-truth intuition is also poor, so corrections are a **noisy** training signal, and the founder's eyeballed portion labels (current Gate-0a "truth") are drawn from this same poor distribution.

**Prevention:** Use the 5/20 frame in copy ("estimate, not gospel"). Do NOT treat user corrections as gold labels — weight/dedupe/validate against weighed data before prompt-tuning. Recognize founder eyeball portions are subject to this ceiling (→ the ground-truth circular-bias risk, V-06).

### V-05 · Indian cuisine stacks every failure mode at once (thali = worst case) [HIGH]

**What goes wrong:** The failure modes are independent and a thali triggers all of them: (a) multi-object segmentation (4–7 small items — hardest recognition case), × (b) per-item portion ambiguity in katoris with no scale, × (c) per-item hidden-fat variance, × (d) regional/home-vs-restaurant variance, × (e) off-whitelist gaps. Errors compound *multiplicatively*: a thali naming 4/6 items, each within 26% on portion, each within a tadka band, can still land total macros 40–60% off. Single-dish ≈ Nutrition5k regime; thalis are outside any published accuracy result we can cite.

**Prevention:** (1) Single-dish = V1 happy path; thali = confidence-gated "tap each item to confirm" / "snap items separately," not auto-macro. (2) In the gate, relax/defer the thali bucket and report it separately. (3) Never let a thali failure hide inside an aggregate.

### V-06 · Ground-truth bottleneck: free Indian datasets give labels, not weighed grams [HIGH]

**What goes wrong:** Validating the portion→macro half needs *weighed-gram + per-dish macro* truth. **Every free Indian food dataset provides recognition labels only** (dish-name ↔ image), not grams. Verified inventory: Indian Food Images Dataset (Kaggle, ~4,000 img / 80 classes), The-massive-Indian-Food-Dataset (~4,770 / 15), IndianFoodNet-30 (~5,500 / 30, bounding boxes only) — all labels, zero grams. The datasets that *do* carry weighed-gram truth — **Nutrition5k** (CC BY 4.0, ~5k plates, scale-rig grams + macros + depth) and **SimpleFood45** — are Western. They calibrate *methodology* / a generic portion→mass regressor, not Indian macros. On the Indian composition side: **IFCT 2017** (528 raw foods, per-100g) and especially **INDB — Indian Nutrient Databank** (open-access; ~1,095 items + ~1,014 Indian *recipes* with per-ingredient gram amounts + per-serving macros, IFCT-derived) are the reference tables.

**Why it matters here:** This is the structural reason the current Gate-0a "truth" is weak — `labels_truth.csv` derives truth macros by running the founder's *eyeballed* `portion_g` through `dish_decomposition.json` (Opus-drafted, `verified_by: null`) + `ifct_lookup.json`. So "ground truth" is an assumption-on-an-assumption, scored against Gemini's assumptions → **agreement, not accuracy.**

**Prevention:** (1) **Weigh the 30 benchmark plates** on a kitchen scale → real gram truth (at least the single-dish bucket). (2) **Ingest INDB alongside IFCT** to seed the decomposition table + portion priors far better than guessing — strong recommendation. (3) Use Nutrition5k/SimpleFood45 to calibrate the ±35% methodology, not as Indian truth. (4) Verify licenses before commercial use (Nutrition5k = CC BY 4.0; Kaggle/Roboflow sets per-page; INDB depends on IFCT-derived sources).

### V-07 · Ground-truth is license-gated (IFCT/INDB), not free [HIGH]

**What goes wrong:** The plan assumed IFCT 2017 is a free drop-in macro layer. Adversarially verified (2026-06-02, by parsing the live sources): IFCT 2017 is ICMR-NIN copyright — *"no part can be stored or reproduced in any electronic format for creating a product without the prior written permission of the National Institute of Nutrition."* Personal-use only. INDB (the IFCT-derived recipe DB) ships with **NO license** on its GitHub repo (all rights reserved); the paper's CC BY covers only the manuscript, not the data. Since INDB embeds IFCT values, the restriction follows downstream.

**Why it matters here:** A commercial ₹299/mo app storing IFCT/INDB-derived macros to power the product is squarely "stored… for creating a product" — so a **written-permission step from ICMR-NIN is unavoidable** before the paid tier ships. It may be granted free (use is "encouraged"), but it cannot be skipped. A launch gate, not a nice-to-have — and it breaks the original "IFCT is a free drop-in" assumption (D-31 / TODOS-10).

**Prevention:** Email ICMR-NIN + Anuvaad early; gate IFCT/INDB macros behind the free tier / a feature flag until permission lands; for de-risking, lean LLM-decomposition + portion on permissive sources (USDA FDC public-domain, UK CoFID OGL) where they cover the ingredient — acknowledging India-specific IFCT values remain the gap needing sign-off. Also note INDB is a **seed, not a drop-in** (grams need the `INDB.do` unit→g conversion; the IFCT food table is not shipped; no weighed/image-linked truth; one fixed oil amount per dish) — D-30.

## Sources

- Design doc primary: `/home/nitin/.gstack/projects/ai-calorie-weight-loss/nitin-unknown-design-20260527-181050.md` (HIGH — adversarial-reviewed, iteration 4)
- PROJECT.md current state: `/home/nitin/Desktop/ai-calorie-weight-loss/.planning/PROJECT.md` (HIGH)
- DPDP Act 2023 (Ministry of Electronics and IT, India) — primary text (HIGH)
- CDSCO Medical Devices Rules 2017 + amendments (HIGH)
- ASCI Code for Self-Regulation in Advertising 2023 + Influencer Guidelines 2021/2023 (HIGH)
- GST Act, threshold notifications (HIGH)
- Vision-LLM food accuracy literature: University of Sydney 2024 multimodal LLM food study; Lu et al. 2020 portion estimation; Mezgec & Korousic Seljak 2017 NutriNet (HIGH-MEDIUM)
- ISSN Position Stand on Protein 2017, updated 2024 (HIGH)
- IFCT 2017 (NIN) scope documentation (HIGH)
- Google AI Studio / Gemini current free-tier limits (verify via Context7 / official docs before code) (MEDIUM-HIGH, time-sensitive)
- Cloudflare R2 pricing + Mumbai region (HIGH)
- Firebase Phone Auth pricing + Android 13+ notification permission docs (HIGH)
- Razorpay onboarding documentation (HIGH)
- Play Store review timelines + Data Safety form requirements (HIGH, 2024-2025)
- React Native + Expo community timeline retrospectives (r/reactnative, Indiehackers) (MEDIUM — community-reported, varies)
- Nutrition-app retention benchmarks (industry consensus: Cal AI public metrics, MyFitnessPal D7) (MEDIUM)
- Nutrition5k portion/calorie ground truth + image-only vs depth error: Thames et al., CVPR 2021, arXiv:2103.03375 (HIGH — primary, exact Table 3 figures)
- GPT-4 Vision food ID vs nutrient-value accuracy: Nutrients 2025, MDPI 17(4):607 / PMC11858203 (HIGH)
- Human photo-calorie estimation ceiling (5/20 within ±20%): Martin et al., Interactive J Med Research 2018, PMID 30401671 (HIGH)
- INDB — Indian Nutrient Databank (recipe gram amounts + per-serving macros, IFCT-derived): anuvaad.org.in; GitHub lindsayjaacks/Indian-Nutrient-Databank-INDB- (HIGH — open-access; **ingest alongside IFCT for portion/decomposition priors**)
- Indian food recognition accuracy (MobileNetV3 ~88–95% closed-set): transfer-learning literature (MEDIUM — small closed-set datasets, not field accuracy)
- CaLoRAify (VLM + RAG + LoRA reference architecture): arXiv:2412.09936, Dec 2024 (MEDIUM — single recent paper; NLG metrics not calorie MAE)
- HealthifyMe "Snap" architecture (GPT-4 Turbo Vision + fine-tuned ensemble + humans-in-loop, ~75% acc): OpenAI case study (openai.com/index/healthify), TechCrunch 2023-09-21 (HIGH)
- India app monetization (RPI ~$0.06 vs US $0.39; IN/SEA download-to-paid ~1.4%): RevenueCat State of Subscription Apps 2025 (2026 ed. ~$0.11 vs $0.55, same ~5× gap) (HIGH)
- HealthifyMe FY24 financials + Novo Nordisk GLP-1 / US pivot (Dec 2025): YourStory, Business Standard, Tracxn (MEDIUM-HIGH; coaches ~1,500–2,000+, not 600+)
