# TODOS

Deferred work captured for Phase 2 planner + downstream agents. Created 2026-05-28 by `/plan-eng-review`.

Each entry: **what** / **why** / **pros** / **cons** / **context** / **blocked by**.

---

## 1. `ai_provider.py` retry + fallback contract spec

**What.** Define explicit retry-budget and aggregate-timeout contract for the multi-provider fallback chain (Gemini free → OpenRouter free → Gemini paid → GPT-4o-mini paid).

**Why.** AI-SPEC §3-§4 ships a skeleton but `tenacity` retry config + per-provider timeout + aggregate user-facing timeout are unspecified. Worst-case user could see 4×10s = 40s wait during free-tier RPM exhaustion.

**Pros.** Bounded user wait. Predictable failure mode. Testable.

**Cons.** Adds Phase 2 Week 1 scope (~3-5h).

**Context.** REQ INFRA-* + AI-SPEC §3. Pattern: each provider attempt = max 8s (vision) or 3s (text). Aggregate cap = 15s. On exhaust → user-facing "AI busy, retry" + retry button. Tenacity decorators in `server/app/providers/ai_provider.py`. Unit tests cover all 4 hop transitions + aggregate cap.

**Blocked by.** None. Phase 2 Week 1 work.

---

## 2. `consent_ledger` schema spec

**What.** Design Postgres schema for DPDP consent tracking — consent grants, withdrawals, purpose-binding, timestamp, IP, app version, user-readable consent text hash.

**Why.** CONTEXT D-02 + REQ COMP-* mention consent ledger but no fields, no migration. DPDP Act 2023 §6 requires verifiable consent record + revocation log + purpose limitation. Phase 2 planner needs this spec before Phase 2 Week 1 begins.

**Pros.** Audit-ready from day 1. Legal posture defensible. Enables granular consent UX in onboarding (V004 sketch already has DPDP consent block).

**Cons.** Adds ~4h Phase 2 Week 1 schema work + ~2h Alembic migration setup.

**Context.** Suggested fields: `id, user_id (FK), grant_type (enum: photo / analytics / marketing), granted_at, withdrawn_at NULLABLE, purpose_text_hash (SHA256 of consent copy at grant time), app_version, ip_country (NOT full IP — DPDP minimization)`. Append-only invariant. Cascade on user delete.

**Blocked by.** Phase 1 completion. Phase 2 Week 1 deliverable per CONTEXT canonical_refs.

---

## 3. `correction_event` schema spec

**What.** Design Postgres schema for append-only meal corrections (dish-name fix, macro override, ingredient adjust).

**Why.** CONTEXT code_context calls it "append-only `correction_event` table from day 1" — locked invariant. But no fields, no FK contract. V1.5 fine-tuning corpus depends on this; lossy schema = no training value.

**Pros.** Captures training corpus from V1 day 1. Enables V1.5 fine-tuning trigger. Auditable correction history.

**Cons.** Adds Phase 2 Week 2 schema work (~2-3h).

**Context.** Suggested fields: `id, user_id (FK), meal_id (FK), event_type (enum: dish_rename / macro_override / ingredient_add / ingredient_remove), original_value (JSONB), corrected_value (JSONB), created_at, ai_provider_id, ai_model_version, prompt_template_version`. INSERT only — no UPDATE, no DELETE except cascade on user delete (which writes a tombstone row first for DPDP grievance log).

**Blocked by.** Phase 1 completion. Phase 2 Week 2 deliverable.

---

## 4. Presigned-PUT R2 upload contract

**What.** Spec the Firebase ID token → server → R2 presigned PUT URL exchange protocol.

**Why.** research/ARCHITECTURE.md mentions presigned PUT but AI-SPEC §3 doesn't specify token validation step + URL TTL + content-type lock + EXIF-strip placement. Attack surface: token replay, oversized upload, malicious content-type.

**Pros.** Prevents bandwidth proxy through FastAPI (huge cost saving). Locks security contract before code. Mobile team builds against fixed API.

**Cons.** Adds Phase 2 Week 1 spec work (~2h).

**Context.** Suggested contract: client sends `Authorization: Bearer <firebase_id_token>` to `POST /uploads/photo`. Server validates token via `firebase-admin`, allocates `photo_id`, returns presigned R2 PUT URL with TTL=5min + content-type=image/jpeg locked + max-size header. Client uploads directly to R2. Server-side worker triggers on R2 event → Pillow EXIF strip (D-04 says do this server-side AFTER upload; spec must confirm).

**Blocked by.** Phase 1 completion. Phase 2 Week 1.

---

## 5. EAS Build distribution pipeline spec

**What.** Define `eas.json` profiles (development / preview / production) + signing-key custody + Sentry source-map upload step + Google Play credential plumbing.

**Why.** REQ ALPHA-* covers Play Internal Testing target but no build pipeline. Distribution is part of complete (Step 0 distribution check). Deferred = silent drop risk.

**Pros.** Foundation for first preview APK in Phase 3 + first production AAB in Phase 4. Sentry source-maps wire crash dedupe before alpha.

**Cons.** ~3-4h Phase 3 setup (one-time).

**Context.** Profiles: development (custom dev client for Firebase native auth + FCM physical-device testing), preview (internal-test APK), production (Play Store AAB). Signing keys live in 1Password vault + EAS-managed; founder retains escrow copy. Sentry-cli installed; `expo-updates`-triggered source-map upload on every build. Google Play service-account JSON in EAS secrets, scoped to Internal Testing track first.

**Blocked by.** Play Developer account purchase (Gate 0d).

---

## 6. Off-whitelist Indian dish UX path

**What.** Spec the user-facing flow when Gemini classifies a meal as off-whitelist (not in the 50-dish `dish_decomposition.json`).

**Why.** Coverage cliff: regional dishes (Bisi Bele Bath, Litti Chokha, Dhokla variants, Tamil temple sides, Bengali sweets) will hit this path. CONTEXT G-12 partially mentions but user-facing copy undefined. Silent failure = trust loss.

**Pros.** Honest UX + correction-event capture turns off-whitelist hits into V1.5 expansion fuel.

**Cons.** Adds Phase 2 Week 3 (advice prompt) + Phase 3 mobile UX scope.

**Context.** Suggested flow: Gemini returns low-confidence (<0.6) or "unknown dish" → MacrosCard renders with `confidence: low` pill + Bali message "Bhai, ye dish nayi hai mere liye. Macros approximate hain — tap to fix." Correction submitted → enters V1.5 expansion queue. Coverage badge ("50 dishes" / "supported list") in app help.

**Blocked by.** Phase 2 advice prompt design.

---

## 7. WoZ QA Gate founder-bandwidth conflict

**What.** Re-evaluate WoZ QA Gate timing (currently Phase 3 Week 6) to avoid single-founder serial-execution risk.

**Why.** Phase 3 Week 6 stacks ≥35 founder-written advice samples + mobile build + Trial User recruit. Single founder = serial bottleneck.

**Pros.** De-risks Phase 3-4 transition. Buys schedule headroom.

**Cons.** Either bring WoZ forward (Phase 2 Week 3 alongside advice prompt design) or lower the sample bar (35 → 20).

**Context.** Options: (a) Phase 2 Week 3 WoZ sampling alongside prompt design = parallel work + prompt iteration loop (b) Lower bar to 20 + qualitative review = faster but weaker statistical signal (c) Keep current and accept schedule slip risk. Research/PITFALLS already promoted WoZ from task to gate; founder confirmed.

**Blocked by.** Phase 2 advice prompt design (option a) or none (option b).

---

## 8. Gemini lunch-rush queue depth

**What.** Spec per-user request queueing + observability for Gemini 10 RPM bottleneck during 12pm-2pm IST lunch peak.

**Why.** Phase 6 alpha = 20 users × ~3 meals/day. Lunch concentration = potential 15+ requests in 60s. Gemini free = 10 RPM. Fallback chain hits OpenRouter (20 RPM also bounded). Queue depth + visibility needed.

**Pros.** Predictable behavior under burst load. Observable via Phoenix tracing already specified in AI-SPEC §5.

**Cons.** Adds Phase 2 Week 2 scope (~2-3h). Queue implementation in FastAPI requires async task pattern (`asyncio.Queue` or external like `arq` if Redis available — likely overkill for Phase 2).

**Context.** Suggested: simple `asyncio.Semaphore(10)` gate around Gemini calls + per-user request token bucket + Phoenix span attribute `gemini.queued_ms`. Bali UX: "5 users ahead of you bhai, ek minute." Phoenix dashboard panel for queue depth + 429 rate.

**Blocked by.** Phase 1 completion. Phase 2 Week 2.

---

## 9. INDB integration — seed dish_decomposition.json (verified 2026-06-02, D-30)

**What.** Use INDB (Indian Nutrient Databank — GitHub `lindsayjaacks/Indian-Nutrient-Databank-INDB-`) as the SEED for `data/dish_decomposition.json`: (1) download `recipes.xlsx` + `INDB.xlsx` + `recipes_servingsize.xlsx` + `INDB.do`; (2) run / re-implement `INDB.do`'s ~45 unit→gram rules in Python to produce per-ingredient grams (~54% of rows are non-gram); (3) map the ~43 matchable whitelist dishes into `dish_decomposition.json` (ingredient, grams, food_code, per-serving macros); (4) LLM-decompose ONLY the ~4 gaps (pani_puri, pongal_ven, bisi_bele_bath, litti); (5) request the IFCT food table (NIN_fct) from ICMR-NIN to recompute/extend; (6) set `verified_by` (not null).

**Why.** Verified live: INDB is the best Indian seed (1,014 recipes × ingredient rows) but a SEED not a drop-in (grams need conversion, IFCT table not shipped, no weighed truth, one fixed oil amount). Turns `dish_decomposition.json` from Opus guesses into sourced data for ~86% of the whitelist (D-30).

**Cons.** ~1-2 days (gram-conversion + mapping + gap dishes + rich/plain oil-variant axis). The 86% coverage is name-level, NOT yet ±35%-validated.

**Blocked by.** Nothing for the seed work; BUT shipping IFCT/INDB macros in the paid tier is blocked by TODOS-10 (license).

---

## 10. IFCT/INDB commercial license — LAUNCH GATE (D-31)

**What.** Obtain written permission for commercial use of IFCT 2017 + confirm INDB data license. Email ICMR-NIN (nin@ap.nic.in / ifct2017@gmail.com) for IFCT product/commercial use; email Anuvaad (awasthi@anuvaad.org.in / aswathy@anuvaad.org.in) to confirm INDB license + request an explicit repo LICENSE (ideally CC BY 4.0).

**Why.** IFCT 2017 (ICMR-NIN copyright) forbids electronic reproduction "for creating a product" without prior written permission; INDB repo has no license; the paper's CC BY covers only the manuscript. A ₹299/mo app storing IFCT/INDB-derived macros needs this permission — unavoidable on any reading (may be granted free). Adversarially verified, HIGH confidence (D-31).

**Cons.** External dependency on NIN/Anuvaad response time. Until granted, gate IFCT/INDB macros behind the free tier / a feature flag.

**Blocked by.** Nothing — send the emails now; track as a launch gate (before Phase 5 public/paid launch).

---

---

## CEO Review Deferred Items (2026-05-28)

Added by `/plan-ceo-review` (SELECTIVE EXPANSION mode). Cherry-picks declined for V1; held for V1.1 or V1.5.

### CEO-1. Bali voice fallback (Hinglish dictation input)

**What.** Tap-to-speak alternative to photo for meal logging. Sarvam AI Saaras STT + clarifying-question loop + same dish→IFCT pipeline.

**Why.** Removes hard photo-only friction. Dark restaurant / hands-dirty / quick-log moments. Estimated +20-30% logging coverage.

**Pros.** Brand-authenticity (Hinglish coach voice). Expands input modality. Hinglish input is a wedge no global competitor has.

**Cons.** Sarvam free tier limits unclear 2026. Hinglish accuracy variable. Adds ambiguity to advice grounding.

**Context.** From `/plan-ceo-review` 2026-05-28 cherry-pick C2. Bundle with CEO-4 (TTS) when picked up — share STT/TTS auth + endpoint patterns.

**Effort.** human ~5-7 days / CC ~3-4h.
**Priority.** P2.
**Blocked by.** None. V1.1 candidate.

### CEO-2. Daily Bali video card (Synthesia / D-ID)

**What.** 06:00 IST daily Bali avatar video personalized to user's log gap: *"Bhai, kal protein 60g/88g tha, aaj dal lunch mein add kar."* Server-side render + R2 cache + push notif.

**Why.** "They actually thought of me" delight moment. Shareable on WhatsApp. Could be a viral retention loop.

**Pros.** Massive delight signal. Shareable. Differentiator vs Cal AI.

**Cons.** Synthesia/D-ID free tier ~10-15 videos/mo per acct = exhausts at 5 users/day. Video gen 30-60s latency. Brand voice drift risk.

**Context.** From `/plan-ceo-review` 2026-05-28 cherry-pick C5. Revisit V1.5 unless cheaper Indian alternative emerges (watch Sarvam, Murf, ElevenLabs Hindi).

**Effort.** human ~4-6 days / CC ~3h.
**Priority.** P3.
**Blocked by.** Free Indian video-gen vendor below ₹0/mo at 100-user scale.

### CEO-3. Auto-photo gallery scan (forgotten-meal catch)

**What.** On-device classifier scans last 24h gallery photos, prompts *"Yeh dinner tha?"* to catch missed logs.

**Why.** ~40% of fitness-app users forget to log. Catches retention dropoff before it shows in streak.

**Pros.** Higher logging completeness. Compounds with streak mechanic.

**Cons.** Privacy-heavy permission ask (full gallery). Reservoir-depleting at install. On-device classifier model size + battery.

**Context.** From `/plan-ceo-review` 2026-05-28 cherry-pick C6. Defer to V1.5 — first ship trust, then ask for gallery.

**Effort.** human ~5 days / CC ~3h.
**Priority.** P3.
**Blocked by.** V1 trust established (Gate 7 retention pass) before asking for gallery.

### CEO-4. Hinglish TTS on advice card

**What.** Tap-to-listen on Bali's advice. Sarvam TTS + Hinglish voice + audio player.

**Why.** Accessibility (low-literacy users) + drive-time usability + delight.

**Pros.** Cheap (~1-2d). Compounds with C2 voice fallback if both picked up.

**Cons.** Audio file size on India mobile data. Voice quality variable.

**Context.** From `/plan-ceo-review` 2026-05-28 cherry-pick C7. Bundle with CEO-1 voice work.

**Effort.** human ~1-2 days / CC ~1h.
**Priority.** P3.
**Blocked by.** Bundle with CEO-1.

---

## Design Review Deferred Items (2026-05-28)

Added by `/plan-design-review` on screen 005 (budget optimizer).

### DESIGN-1. Grocery list export (BigBasket / Zepto / Blinkit)

**What.** Bottom CTA on Budget Optimizer screen — currently stub disabled with "V1.5" pill — wires to BigBasket / Zepto / Blinkit deep-link or partner API to pre-fill a cart with the top-3 selected protein sources.

**Why.** Closes the loop from optimizer recommendation → actual purchase. Removes friction between "Bhog said buy X" and "I bought X."

**Pros.** Conversion-meaningful. Demonstrably reduces friction. Tweet-worthy demo.

**Cons.** Each platform's deep-link / partner API has its own setup (BigBasket partner program, Zepto unclear, Blinkit unclear). Could be just scheme links (no partnership) initially. Affiliate revenue possible if partnerships land.

**Context.** From `/plan-design-review` 2026-05-28 screen 005 Q7. Spec already has disabled stub button — V1.5 promotes to active.

**Effort.** human ~5-7 days / CC ~2-3h. Per-platform setup varies.
**Priority.** P3.
**Blocked by.** Validate platform-side feasibility (scheme link vs API vs partnership).

### DESIGN-2. Per-city pricing UX

**What.** City selector on Budget Optimizer; uses existing `veg_protein_prices.city` column (D-17) to render city-specific avg instead of global avg.

**Why.** Tomato-onion seasonal shocks vary by city. Mumbai prices ≠ Bangalore prices for paneer. Better data fidelity.

**Pros.** Sharper recommendations. Trust signal ("Bhog knows my city").

**Cons.** Adds onboarding step OR Profile screen + city detection. Adds DPDP scope (geo data). Cohort-keying impact on streak ladder.

**Context.** From `/plan-design-review` 2026-05-28 screen 005. Schema D-17 already supports it; UX is V1.5 layer.

**Effort.** human ~2-3 days / CC ~1-2h.
**Priority.** P3.
**Blocked by.** None.

### DESIGN-3. Carbs / fat / micronutrient optimizers (scope expansion)

**What.** Replicate Budget Optimizer pattern for carbs, fat, fiber, or specific micronutrients (iron, B12 for vegan diets).

**Why.** Some user goals (cut, vegan-deficiency repair) need optimization on non-protein macros.

**Pros.** Wider scope appeal. Repeats moat for new dimensions.

**Cons.** Requires extending `veg_protein_prices` schema to `food_prices` general table. V1 scope-discipline = protein only.

**Context.** From `/plan-design-review` 2026-05-28 screen 005 Q4 locked to protein-only V1. V1.5 expansion.

**Effort.** human ~7-10 days / CC ~3-4h (mostly data work, not UI).
**Priority.** P3.
**Blocked by.** Pricing data expansion beyond `veg_protein_prices` table.

---

## Tracking

Each item gets a `## 1.` style header. When promoting to active work: move to `.planning/phases/0X-*/0X-PLAN.md` as a task with the same identifier (e.g., "from TODOS-3 correction_event schema") so traceability survives.

When complete: strike through, move to `## Completed` section at bottom with completion date + commit SHA.
