# Phase 1: Validation Gates + Stack Lock — Research

**Researched:** 2026-06-02
**Domain:** Pre-build validation fieldwork — vision benchmarking, advice rubric testing, demand validation, data curation, stack admin
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- D-01: Compute = Render free tier (Singapore) for Phase 0-1 alpha. No CC required. DPDP cross-border risk monitored monthly; migration trigger = MeitY notification restricting Singapore flow.
- D-02: Database = Supabase Mumbai free tier. Indian region satisfies DPDP PII residency.
- D-03: Cold-start mitigation = GitHub Actions cron-ping `/healthz` every 10 min, 10:00-22:00 IST only (14h window).
- D-03b: Cold-start UX = "Bali waking up" banner at >5s response. Phase 3 mobile work.
- D-04: Photo storage = Cloudflare R2 with `jurisdiction=india`. Endpoint `<acct>.in.r2.cloudflarestorage.com`.
- D-05: Auth = Firebase Phone OTP. No DLT registration required.
- D-06: Ground-truth labeler = Claude Opus 4.7 (existing subscription) + founder verification on all 30 photos.
- D-07: Macros computed deterministically from `dish_decomposition.json` + IFCT lookup, never from LLM math.
- D-08: Dish-decomposition source = INDB seed (D-30) → LLM-decompose ~4 gaps → founder verifies → `verified_by` set.
- D-09: Photo stratification = 10/10/10 (single / mixed / thali). Per-bucket pass bar.
- D-10: Circular bias mitigation: different LLM family (Opus ≠ Gemini) + deterministic IFCT macros + founder verifies every label. RD audit = non-blocking V1.5 trigger.
- D-11: WhatsApp pitch = short, direct, founder-voice, 3-4 sentences. No deck-style hype.
- D-12: Commitment bar = verbal "yes, send me the link when ready" + WhatsApp confirm. "Maybe" does not count.
- D-13: WTP capture = open-ended price ladder ("₹0 / ₹100 / ₹299 / ₹499 / more?"). Capture verbatim quote. Gate 0c bar = ≥3 quotes with specific ₹ figure.
- D-14: Recruit funnel = personal network first (gym buddies, college fitness friends, Instagram DMs). Document Tier-1 city bias.
- D-15: Veg-protein prices = Zepto + BigBasket + Blinkit (4 metros) + RD published price sheets.
- D-16: Refresh cadence = quarterly manual + monthly automated anomaly alert (>15% item movement).
- D-17: Storage = Postgres table `veg_protein_prices` (NOT JSON). Schema minimum: `id, food_name, source_platform, city, price_per_kg_inr, protein_per_100g, cost_per_g_protein_inr, scrape_date`.
- D-18: Coverage = top 50 veg-protein sources including regional staples (ragi, jowar, sattu, makhana).
- D-19: Each locked decision → ADR-lite `.planning/decisions/YYYY-MM-DD-slug.md` with status/context/decision/consequences.
- D-20: Gate 0a recalibrated — weighed truth, split dish-ID / macro metrics, thali reported-only, reference object mandatory.
- D-21: INDB ingested alongside IFCT to seed `dish_decomposition.json` + verify rows before Gate 0a.
- D-22: App name = Bhog (final).
- D-23: RD audit = non-blocking V1.5 trigger only.
- D-24: Observability = Postgres `ai_call_log` ledger. Phoenix = local-dev only.
- D-25: Enum source of truth = MODEL-SPEC DB enums.
- D-26: DSR routes = `DELETE /me` (soft-delete) + `GET /me/export`.
- D-27: Supabase free accepted; nightly `pg_dump` → R2 india DR cron.
- D-28: Timeline = 10-12 weeks (founder has RN experience).
- D-29: Positioning = "macro estimate / range," never "exact calories." Moat is budget-aware advice grounded in user log.
- D-30: INDB = seed not drop-in. ~46% of rows already grams; ~54% need `INDB.do` unit→gram conversion (~45 rules). ~43/50 whitelist dishes covered at recipe-prior level. ~4 genuine gaps (pani_puri, pongal_ven, bisi_bele_bath, litti). IFCT food table (NIN_fct) NOT in INDB repo — request from ICMR-NIN.
- D-31: IFCT/INDB commercial license = LAUNCH GATE. Email ICMR-NIN + Anuvaad before paid tier ships. Gate IFCT/INDB macros behind free tier / feature flag until permission granted.

### Claude's Discretion

- Exact GitHub Actions yaml for cron-ping
- Exact prompt template for Opus labeling
- Exact scrape implementation for Zepto/BigBasket/Blinkit (one-off)
- Exact Postgres schema for `veg_protein_prices` within D-17 constraints

### Deferred Ideas (OUT OF SCOPE)

- RD audit of Gate 0a labels (V1.5 trigger)
- Mumbai-native hosting (Phase 4/5 trigger, requires CC)
- Render Starter $7/mo (Phase 4 trigger)
- Per-region pricing for veg-protein table (V1.5)
- Always-fresh daily scrape of Zepto/BB/Blinkit (Phase 4+)
- Reddit r/indianfitness DM outreach (Phase 6 if personal network < 20)
- 15-min RD onboarding call commitment tier (rejected for Gate 0c)
- JSON file instead of Postgres for veg_protein_prices (rejected)
- Top-25 instead of top-50 veg-protein coverage (rejected)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GATE-01 | 30 weighed, reference-object photos (10/10/10) → Gemini 2.5 Flash → dish-ID ≥80% AND macros within ±35% of weighed truth (≥70% single / ≥60% mixed); thali reported-only | Section: Gate 0a Execution Mechanics |
| GATE-02 | Founder logs 14 days of own meals through validated pipeline + advice engine; ≥70% of advice replies score 4/4 on rubric | Section: Gate 0b Execution Mechanics |
| GATE-03 | ≥10 verbal commitments + ≥3 verbatim ₹299 WTP quotes from 20 named WhatsApp contacts | Section: Gate 0c Execution Mechanics |
| GATE-04 | Stack locked in `.planning/decisions/`; Play Developer account purchased ($25) + identity verification submitted | Section: Gate 0d Execution Mechanics |
</phase_requirements>

---

## Summary

Phase 1 is a NO-CODE validation + fieldwork + data phase. Its four gates are risk-validation rituals, not software deliverables. The output artifacts are: a passing vision benchmark (30 weighed photos + scores), a passing advice rubric (14-day log + scoring), 20 named users with ≥10 verbal commits + ≥3 WTP quotes, a committed stack-lock decisions ledger, and a curated `dish_decomposition.json` + `veg_protein_prices` table seed — all before a single line of production code is written.

The dominant execution risk is the INDB integration. INDB is confirmed real and useful (1,014 Indian recipes, ~43/50 whitelist coverage at name-level), but it is not a drop-in: ~54% of ingredient rows use non-gram units requiring the `INDB.do` Stata unit→gram conversion rules to be re-implemented in Python, and the IFCT nutrition table is NOT shipped in the INDB repo (must be requested from ICMR-NIN). This is 3-5 hours of Python scripting that must complete before Gate 0a weighing begins, because `verified_by` cannot be set until decomposition rows are sourced from INDB+IFCT rather than Opus guesses.

Gate 0b has a subtle problem the planner must address: the advice engine does not exist yet. Running 14 days of meal advice without a built backend requires a Wizard-of-Oz substitute — the founder uses a manual Gemini/Groq prompt call (API playground or Python one-liner) to simulate the advice engine. This is explicitly the right approach; the WoZ QA gate (Phase 3) formalizes it, but for Gate 0b, founder-driven API playground calls with the full prompt context are sufficient and appropriate.

The IFCT/INDB commercial license email (TODOS-10) is a launch gate — it does NOT block Phase 1 or Gate 0a, but it must be sent during Phase 1 to start the clock, because NIN's response time is unknown and the paid tier cannot ship without it.

**Primary recommendation:** Execute in this order — (1) INDB download + Python gram-conversion script + map ~43 dishes → `dish_decomposition.json` `verified_by` set; (2) buy kitchen scale + shoot + weigh 30 photos + write `labels_truth.csv`; (3) run Gate 0a (Gemini API call + scoring script — Phase 2 Week 1 actually runs the Python harness, but the photo + data prep is Phase 1 work); (4) run Gate 0b (14-day WoZ-style meal log + manual scoring); (5) Gate 0c WhatsApp outreach (parallel with 0a/0b); (6) Gate 0d stack commit + Play Console purchase (parallel); (7) veg_protein_prices scrape (parallel with 0a/0b); (8) send IFCT/INDB license email (day 1, non-blocking).

---

## Architectural Responsibility Map

> Phase 1 has no code tiers. All work is founder fieldwork, data curation, and admin. This section maps the "capability" of each gate to its responsible actor and output artifact.

| Capability | Primary Owner | Output Artifact | Dependency |
|------------|--------------|-----------------|------------|
| Vision accuracy benchmark | Founder (photos + weighing) + Gemini API + Phase 2 harness | `data/photos/*/labels_truth.csv` + `evals/gate_0a_results.md` | INDB seed complete first |
| Dish decomposition ground truth | INDB repo + Python conversion + founder verify | `data/dish_decomposition.json` (`verified_by` set) | INDB download + `INDB.do` re-impl |
| Veg-protein pricing table | Manual scrape (Zepto/BB/Blinkit) + RD sheets | `veg_protein_prices` Postgres rows (Phase 2 migration) | None |
| Advice rubric validation | Founder (14-day log + manual API calls + 4/4 scoring) | `evals/gate_0b_results.md` + scoring CSV | `dish_decomposition.json` verified |
| Demand signal | Founder (WhatsApp outreach + price ladder) | Commitment tracker doc + verbatim quote capture | None |
| Stack lock | Founder (decisions doc commit) | `.planning/decisions/` ADR-lite files | All D-01..D-31 reviewed |
| Play Console | Founder admin | Developer account active + verification started | $25 + Google account |
| License gate | Founder (email to NIN + Anuvaad) | Sent confirmation; response tracked | None (send day 1) |

---

## Gate 0a — Execution Mechanics

### What the planner must know

Gate 0a tests two independent metrics — dish-ID accuracy and macro accuracy — against weighed ground truth. These are scored per-bucket (single, mixed, thali) with separate pass bars. The Python eval harness (`evals/gate_0a_vision.py`) is a Phase 2 Week 1 deliverable per the spec. Phase 1 produces the inputs to that harness: the 30 weighed photos + `labels_truth.csv` + a verified `dish_decomposition.json`. [VERIFIED: gate_0a_vision.md + 01-CONTEXT.md]

### Step 1: INDB download + Python gram-conversion (MUST precede weighing)

The INDB GitHub repo (`lindsayjaacks/Indian-Nutrient-Databank-INDB-`) ships three key files: [VERIFIED: 2026-06-02-founder-rulings-and-gate-recalibration.md D-30]

- `recipes.xlsx` — 10,271 ingredient rows × 1,014 recipes (food_code + amount + unit + per-serving macros)
- `INDB.xlsx` — per-100g macros for ingredients
- `INDB.do` — Stata script with ~45 unit→gram conversion rules

The `.do` file contains rules like: `replace amount_g = amount * 28.35 if unit == "oz"`, `replace amount_g = amount if unit == "g"`, `replace amount_g = amount * 240 if unit == "cup_liquid"`, etc. (~45 such rules covering tsp/tbsp/cup/oz/piece/egg/ml/L conversions). [ASSUMED — rule count estimated from D-30 "~45 rules"; exact rules require reading the .do file]

**Concrete Python re-implementation approach:**

```python
# Pattern: parse INDB.do rules into a Python dict, apply to recipes.xlsx
UNIT_TO_G = {
    "g": 1.0,
    "ml": 1.0,           # approximate water density
    "tsp": 4.2,           # ~4.2g per tsp (dry); ~5ml liquid
    "tbsp": 12.6,         # 3 tsp
    "cup": 240.0,         # cup liquid; dry varies
    "oz": 28.35,
    # ... read .do file to confirm each rule
}

def convert_to_grams(amount, unit):
    unit_clean = unit.strip().lower()
    if unit_clean in UNIT_TO_G:
        return amount * UNIT_TO_G[unit_clean]
    # "eggs" → look up standard egg weight in INDB or use 50g/egg
    # "piece" → dish-specific; flag for manual review
    return None  # flag for founder manual review
```

The ~46% of rows already in grams pass through unchanged. The remaining ~54% need the conversion map. [VERIFIED: D-30]

**Mapping to whitelist:** After conversion, map INDB recipe names to the 50-dish `dish_decomposition.json` keys. ~43/50 whitelist dishes match at recipe-prior level. ~4 have no INDB recipe: `pani_puri`, `pongal_ven`, `bisi_bele_bath`, `litti`. These 4 are LLM-decomposed via Opus prompt with founder verification. [VERIFIED: D-30]

**The IFCT nutrition table (NIN_fct) is NOT in the INDB repo.** INDB ships per-serving and per-100g macro *summaries*, but the raw per-ingredient IFCT values must be requested from ICMR-NIN (nin@ap.nic.in). For Phase 1, the workaround is: use INDB's per-serving macro summaries as the `verified_by` source for `dish_decomposition.json` rows, and flag the ingredient-level IFCT lookup as requiring NIN data for Phase 2. The existing `data/ifct_lookup.json` (already in repo) covers the common ingredients and is sufficient for Gate 0a scoring. [VERIFIED: D-30 + file system check]

**`verified_by` field:** Once INDB-sourced rows are mapped, set:
```json
"verified_by": "INDB recipe #<id> + INDB per-serving macros (2026-06-02)"
```
For the 4 LLM-decomposed gaps: `"verified_by": "Claude Opus 4.7 draft + founder manual cross-check vs Tarla Dalal"`.

**Rich/plain variants:** D-30 notes INDB has one fixed oil amount per dish (no rich/plain variants). The planner must add a `_variants` key to fat-heavy dishes in `dish_decomposition.json`:
```json
"dal_toor_tadka": {
  "_variants": ["dal_plain", "dal_tadka", "dal_restaurant"],
  "default_variant": "dal_tadka"
}
```
This is a Phase 1 data task (add variants to the JSON), not Phase 2 code.

### Step 2: Kitchen-scale weighing protocol (30 plates)

**Equipment needed:** Kitchen scale, 0.1g–1g resolution, ~₹500-800 (Hesley/EK-series on Amazon India). [VERIFIED: gate_0a_vision.md]

**Weighing protocol per photo:**
1. Zero (tare) the scale with empty plate/katori.
2. For single-dish: weigh the full serving in its vessel → record `weighed_total_g`.
3. For mixed (2-3 items): weigh each katori/item separately before plating (or use tare-per-vessel method) → record each in `component_weights_g` JSON.
4. For thali: weigh each katori separately → record all components. Thali is reported-only so precision matters less, but protocol is the same.
5. Place ₹10 coin OR show palm next to plate BEFORE photographing.
6. Photograph with the measuring phone (Android, ₹15-30k price band).
7. Fill `labels_truth.csv` row immediately (not from memory later).

**Lighting diversity required:** 3 daylight / 3 indoor warm / 2 dim / 2 fluorescent per bucket. Rationale: if dim/fluorescent photos fail disproportionately, image preprocessing becomes Phase 2 work — better to know now. [VERIFIED: CURATION-CHECKLIST.md]

**Off-whitelist quota:** At least 3 photos must show dishes NOT in the 50-dish whitelist. This tests the confidence-low / "not recognized" UX path. Candidates: Hyderabadi biryani, Bengali macher jhol, Goan fish curry, Kerala puttu. [VERIFIED: CURATION-CHECKLIST.md]

**JPEG conversion:** Shoot in whatever format the phone produces; convert to JPEG ≤1280px / quality 0.7 / EXIF stripped before pushing to `data/photos/`. [VERIFIED: CURATION-CHECKLIST.md anti-pattern #5]

### Step 3: Opus 4.7 blind labeling pass

After photos are shot and `labels_truth.csv` has weighed grams:

1. Feed each photo filename to Opus 4.7 (existing Claude Code subscription, zero incremental cost). Prompt: "You are a blind labeler. Given this photo filename and the visible image, predict: (1) dish_id matching one of these 50 whitelist keys: [list], or 'unknown' if none match; (2) estimated portion_g. Return JSON only: `{dish_id, portion_g}`."
2. Opus emits `labels_opus.csv`.
3. Founder reviews every row (not spot-check) — compares Opus `dish_id` to truth, marks correct/incorrect, adjusts `portion_g` if >20% off.
4. `labels_truth.csv` = founder-verified final. This is the eval harness ground truth.

**Why Opus, not founder-only:** Opus is different model family from Gemini 2.5 Flash (under test), so no circular bias on dish-ID. Macros are deterministic from weighed grams through `dish_decomposition.json`, so no LLM-math bias there either. [VERIFIED: D-06, D-07, D-10]

### Step 4: Gate 0a eval harness — Phase boundary clarification

The Python script `evals/gate_0a_vision.py` is explicitly a **Phase 2 Week 1 deliverable** per `evals/gate_0a_vision.md`: "Implementation (Phase 2 Week 1 deliverable)." [VERIFIED: gate_0a_vision.md]

**Phase 1 deliverables:** photos shot + weighed + `labels_truth.csv` written + `dish_decomposition.json` verified.
**Phase 2 Week 1 deliverable:** write + run `gate_0a_vision.py` → produce `evals/gate_0a_results.md` → pass/fail decision.

The planner should NOT put the eval harness Python script in Phase 1 plans. Phase 1 ends when the data inputs are ready; Phase 2 Week 1 runs the benchmark and reports the gate result.

**Exception:** The founder can optionally run a manual spot-check during Phase 1 using the Gemini API playground (30 photos, manual scoring) to get an early read before Phase 2 builds the harness. This is not required for gate passage but reduces risk of a Phase 2 surprise. [ASSUMED — pragmatic recommendation, not in spec]

### Pass bar (recalibrated 2026-06-02)

| Bucket | Blocking? | dish-ID bar | macros bar (reference-present arm) |
|--------|-----------|-------------|-------------------------------------|
| single | YES | ≥80% | ≥70% within ±35% of weighed truth |
| mixed  | YES | ≥80% | ≥60% within ±35% of weighed truth |
| thali  | NO (reported-only) | report | report |

Both bars must clear independently per blocking bucket. Thali macro error 40-60% is expected and does not block launch. [VERIFIED: gate_0a_vision.md + REQUIREMENTS GATE-01]

### Known failure modes to plan remediation for

| Failure | Cause | Planner-prescribed remediation |
|---------|-------|-------------------------------|
| Single dish-ID < 80% | Prompt too generic | Add 5 few-shot examples to Gemini prompt; rerun |
| Mixed dish-ID < 80% | Gemini conflates items | Switch to 2-step prompt (detect dishes → identify each) |
| Macro bar fails despite dish-ID pass | Portion estimation bottleneck | Check reference object in frame; tighten serving_g in decomp table; add rich/plain variant |
| High P90 macro error on fat-heavy curries | Hidden oil/ghee invisible | dal_plain/dal_tadka/dal_restaurant variants + one-tap selector |
| Off-whitelist > 5 of 30 | Whitelist too narrow | V1.5 expansion; confidence-low UX path on by default |

[VERIFIED: gate_0a_vision.md Failure modes table]

---

## Gate 0b — Execution Mechanics

### The core problem: the advice engine does not exist yet

Gate 0b requires "14 days of own meals through validated vision pipeline + advice engine." Neither pipeline nor engine is built in Phase 1. [VERIFIED: ROADMAP.md — backend spine is Phase 2]

**The WoZ-style substitute mechanic (the only viable approach):**

1. **Vision step (manual):** Founder photographs each meal. Instead of the pipeline, founder manually identifies the dish and estimates portion (or uses the Gemini API playground directly to get dish + portion estimate).
2. **Macro step (manual):** Founder derives macros by hand from `dish_decomposition.json` + `data/ifct_lookup.json`. A small Python script makes this trivial:
   ```python
   # One-liner macro calculator for Gate 0b manual use
   python3 -c "
   import json
   decomp = json.load(open('data/dish_decomposition.json'))
   ifct = json.load(open('data/ifct_lookup.json'))
   dish = 'dal_toor_tadka'
   portion_g = 150
   # ... compute macros ...
   "
   ```
3. **Advice step (WoZ manual):** Founder pastes the full advice prompt context into Groq playground (llama-3.3-70b-versatile, free) or Gemini AI Studio (free). Prompt includes: goal + target macros + last-3-days log + day-so-far totals + budget bucket + veg/non-veg + current dish + veg_protein_prices reference table (as text). Founder captures the output.
4. **Scoring step:** Founder scores each advice reply against the 4/4 rubric: (a) specific food cited, (b) specific quantity in g/units, (c) ₹ cost or pantry mention, (d) reference to recent log. Tallies pass/fail.

**This IS the right mechanic.** PITFALLS.md Pitfall 14 explicitly promotes WoZ QA from task to gate. Gate 0b is the first instance of it. The 14-day founder log is the WoZ dataset that later informs prompt engineering. [VERIFIED: PITFALLS.md Pitfall 14 + REQUIREMENTS GATE-02]

### 14-day logging cadence

- Minimum: 2 meals/day × 14 days = 28 meal-advice pairs. At least one dinner per day (primary retention mechanic meal type).
- Score each advice reply same-day on the 4/4 rubric. Do not batch-score at day 14.
- Capture in a simple spreadsheet: `date, meal, dish_id, portion_g, derived_kcal, derived_protein, advice_text, score_a (0/1), score_b, score_c, score_d, total_4_4 (0-4), pass (1 if total=4)`.
- Gate passes when ≥70% of rows have `total_4_4 = 4`. [VERIFIED: REQUIREMENTS GATE-02]

### What "specific food + quantity + ₹ cost + log reference" means in practice

The 4/4 rubric is non-negotiable per the moat logic (PITFALLS Pitfall 4). Concretely:

| Dimension | Passing example | Failing example |
|-----------|-----------------|-----------------|
| (a) specific food | "50g soya chunks" | "add protein" |
| (b) specific quantity | "50g" or "1 katori (150g)" | "some" / "more" |
| (c) ₹ cost | "50g soya ≈ ₹6" | no price mentioned |
| (d) log reference | "yesterday's lunch had 18g protein" | no reference to user's meals |

Advice that fails (c) because the advice engine doesn't yet have the veg_protein_prices table should be noted in the log as "infra missing" — this is expected for Gate 0b since the full table isn't built yet. Score it 3/4 for planning purposes and note as a prompt-engineering gap to fix once the table is seeded. [ASSUMED — pragmatic scoring guidance; spec says ≥70% must score 4/4 but does not handle the "table not yet built" case explicitly]

### Prompt to use for Gate 0b manual advice calls

Based on AI-SPEC §3 + §4b context, the minimal prompt for Gate 0b WoZ simulation:

```
You are Bhog, an AI nutrition coach for Indian youth. The user's goal is muscle gain.
Target: 1.8 g protein/kg body weight/day = {target_protein}g. Calorie target: {target_kcal} kcal.

Today's meals so far:
{today_meals_with_macros}

Last 3 days average: {avg_protein_3d}g protein/day, {avg_kcal_3d} kcal/day.

Current meal just logged: {dish_name}, ~{portion_g}g, ~{meal_kcal} kcal, ~{meal_protein}g protein.

User is vegetarian. Daily food budget: ₹{budget}/day.

Veg protein reference (₹/g protein):
- Soya chunks: ₹0.15/g
- Dal/chana: ₹0.20/g
- Eggs (ovo-veg): ₹0.30/g
- Paneer: ₹0.40/g

Give ONE specific, actionable piece of advice in 1-2 sentences. Must include: (1) a named food, (2) a specific gram amount, (3) approximate ₹ cost, (4) reference to the user's recent log pattern.

Rules: No Western foods. No medical claims. No "treat/cure/diagnose."
```

This prompt will be iterated during Gate 0b. Each iteration = prompt version bump. [ASSUMED — derived from AI-SPEC §3 context assembly spec; exact prompt is planner/executor discretion per CONTEXT.md]

---

## Gate 0c — Execution Mechanics

### Outreach mechanics

Target: 20 named WhatsApp contacts, ≥10 verbal commits, ≥3 verbatim ₹299 WTP quotes. [VERIFIED: REQUIREMENTS GATE-03]

**The contact universe:** Gym buddies, college fitness friends, Instagram DMs to people founder already follows. Build a list of 30-40 names before starting (to hit 20 named contacts even with some non-responses). [VERIFIED: D-14]

**The pitch message (D-11 template):**
> "Hey [name], building an AI app for Indian-veg-budget-aware calorie tracking + advice. Photo your meal, get macros + 1-line tip in your context. Looking for 20 early users for 2-week test. Free, no card needed. You in?"

**The commitment bar (D-12):** Verbal "yes, send me the link when ready" + WhatsApp reply. "Maybe" / "send and I'll see" = NOT a commit. Do not round up.

**The WTP capture (D-13):** After a commit, ask the price ladder question:
> "If this app worked exactly like I described, what would you pay per month? ₹0, ₹100, ₹299, ₹499, more?"

Capture the exact reply verbatim (screenshot or copy-paste). Gate 0c bar = ≥3 quotes with a specific ₹ figure attached (any figure — the goal is to validate price sensitivity, not to require ≥₹299). [VERIFIED: D-13]

**Tracking:** A simple notes file or spreadsheet: `name, platform, date_contacted, responded (Y/N), committed (Y/N), wtp_quote (verbatim or blank)`. Keep this as a deliverable artifact.

**Segmentation caveat to document:** Alpha recruits are Tier-1 city / similar income / gym-scene biased. Document this explicitly in the Gate 0c outcome file so Phase 6 alpha results are interpreted correctly. [VERIFIED: D-14]

**Realistic timeline:** 20 contacts in 2-3 days of active outreach if founder has an active gym/college network. Hitting 10 commits may take 20-30 contacts given ~50% response rate. Start with 30 contacts minimum. [ASSUMED — based on typical cold-warm DM conversion patterns]

---

## Gate 0d — Execution Mechanics

### Stack-lock ADR-lite commit

**What:** For each of D-01..D-31, write (or verify existing) a 1-paragraph ADR-lite file in `.planning/decisions/`. Files for D-01..D-19 already exist in `2026-05-28-D-01-to-D-19.md`. Files for D-20..D-31 were created in `2026-06-02-founder-rulings-and-gate-recalibration.md`. [VERIFIED: file system check]

**Planner action:** Verify both files exist and are committed to git. The ADR-lite format is: `status / context / decision / consequences`. No new writing needed for D-01..D-31 since all are already documented.

**Stack components to confirm locked:**
- Mobile: Expo SDK 54 + RN 0.81 + expo-router ~5.0 + expo-camera + expo-image-manipulator
- Backend: FastAPI 0.128 + Pydantic v2 + SQLAlchemy 2.0 async + asyncpg + Alembic + uvicorn
- Compute: Render free Singapore (D-01)
- Database: Supabase Mumbai free (D-02)
- Storage: Cloudflare R2 `jurisdiction=india` (D-04)
- Auth: Firebase Phone OTP + firebase-admin (D-05)
- AI Vision: Gemini 2.5 Flash primary (NOT 2.0 — retires March 2026)
- AI Text: Groq Llama-3.3-70b-versatile primary
- Abstraction: `ai_provider.py` with VisionProvider + TextProvider (no provider SDK imports outside `providers/`)

[VERIFIED: CLAUDE.md technology stack tables + CONTEXT.md D-01..D-05]

### Google Play Developer account — $25 + identity verification

**Process (as of 2026):** [ASSUMED — based on PITFALLS.md Pitfall 16 + training knowledge]
1. Go to play.google.com/apps/publish → "Create developer account"
2. Accept Developer Distribution Agreement
3. Pay $25 one-time registration fee (Google Pay / Visa / Mastercard; UPI typically NOT accepted for Google developer fees)
4. Complete identity verification form (government ID: Aadhaar / passport / driving license photo upload)
5. Google reviews within **3-7 business days** for new accounts (this is the clock to start before Phase 2)

**The critical constraint (PITFALLS Pitfall 16):** First Production track submission gets manual human review (7-14 days for new developer accounts). This is why Phase 1 must start the account NOW — the 3-7 day identity check must resolve before Phase 2 Week 1 begins. Internal Testing track is faster (1-3 days for new accounts) but still requires a verified developer account. [VERIFIED: PITFALLS.md Pitfall 16]

**Phase 1 deliverable:** Account purchased + identity verification submitted. Actual approval may arrive during Phase 2 — that is acceptable. The "clock started" is the Phase 1 success criterion.

**UPI payment issue:** Google developer fees cannot be paid via UPI on some Indian accounts. Founder needs a credit/debit card that supports international payments. [ASSUMED — based on common India UPI restriction for foreign merchant fees; verify at payment step]

---

## Data Work — INDB Integration Detail

### INDB repo structure (verified 2026-06-02)

| File | Contents | Phase 1 use |
|------|----------|-------------|
| `recipes.xlsx` | 10,271 rows: recipe_name, food_code, amount, unit, ingredient_name | Primary seed source |
| `INDB.xlsx` | Per-100g macros for ~1,014 ingredients | Macro lookup (supplement to ifct_lookup.json) |
| `INDB.do` | Stata: ~45 unit→gram conversion rules | Re-implement in Python |
| `recipes_servingsize.xlsx` | Per-serving macro summaries | Verify total macros per dish |

[VERIFIED: D-30]

### Python script skeleton for INDB integration

```python
# data/scripts/indb_to_decomp.py
# Phase 1 task: convert INDB recipes to dish_decomposition.json format
import pandas as pd
import json
from pathlib import Path

WHITELIST_KEYS = [...]  # 50 keys from dish_decomposition.json

# Step 1: Load INDB
recipes = pd.read_excel("data/indb/recipes.xlsx")
indb_macros = pd.read_excel("data/indb/INDB.xlsx")

# Step 2: Unit → gram conversion (re-impl of INDB.do rules)
# Read .do file to confirm exact rules; approximate table:
UNIT_G = {
    "g": 1.0, "ml": 1.0, "tsp": 4.2, "tbsp": 12.6,
    "cup": 240.0, "oz": 28.35, "l": 1000.0,
    # eggs: use INDB weight or 50g default
}

def to_grams(amount, unit):
    u = str(unit).strip().lower()
    if u in UNIT_G:
        return float(amount) * UNIT_G[u]
    return None  # flag for manual review

recipes["amount_g"] = recipes.apply(
    lambda r: to_grams(r["amount"], r["unit"]), axis=1
)

# Step 3: Map recipe names to whitelist keys
# Requires fuzzy matching + manual review for ambiguous names
# e.g. "Paneer Butter Masala" → "paneer_butter_masala"

# Step 4: For each whitelist dish, produce:
# {ifct_id: ..., g: ..., _indb_recipe_id: ..., _indb_amount_unit: ...}

# Step 5: Set verified_by = "INDB recipe #{id} (2026-06-02)"
```

**Estimated time:** 3-5 hours for a developer comfortable with pandas and JSON manipulation. Founder (Python-capable) should be able to complete this during Gate 0a kickoff. [VERIFIED: D-21 "~3-5h ingest/mapping"]

### Whitelist gaps requiring LLM decomposition (~4 dishes)

| dish_id | Gap reason | Decomposition approach |
|---------|-----------|----------------------|
| `pani_puri` | INDB has puri but not pani_puri assembly | Opus prompt: "Decompose pani_puri (6 pieces) into ingredients with grams. Include: puri shells, potato filling, chickpeas, water/tamarind chutney. Cross-check with Tarla Dalal." |
| `pongal_ven` | Regional South Indian; INDB may lack | Opus prompt + Tarla Dalal recipe cross-check |
| `bisi_bele_bath` | Karnataka dish; INDB may lack | Opus prompt + Sanjeev Kapoor / Raks Kitchen recipe |
| `litti` | Bihar/Jharkhand; INDB likely lacks | Opus prompt + local recipe sources |

[VERIFIED: D-30]

### The `veg_protein_prices` scrape

**Approach:** Manual one-off, NOT scripted scraping. [VERIFIED: CONTEXT.md Claude's Discretion section]

**Practical protocol:**
1. Open Zepto / BigBasket / Blinkit on phone or browser for each of 4 metros: Delhi, Mumbai, Bangalore, Hyderabad. Set delivery address to each city's central pin.
2. Search each of the 50 target items. Copy: `product_name, weight (g or kg), price (₹)`. Calculate `price_per_kg_inr`.
3. Record in a spreadsheet: `food_name, platform, city, price_per_kg_inr, date`.
4. For RD published sheets: download Munmun Ganeriwal / NFNA / Ryan Fernando published veg-protein cost tables from their websites; use as anchor for staples.
5. After scraping, compute `protein_per_100g` from `ifct_lookup.json` (or INDB) for each item.
6. Compute `cost_per_g_protein_inr = price_per_kg_inr / 10 / protein_per_100g`.
7. This data goes into the `veg_protein_prices` Postgres table (seeded in Phase 2 via Alembic migration). For Phase 1, a CSV seed file is sufficient.

**Estimated time:** 6-7 hours (D-18) including cross-referencing RD sheets. [VERIFIED: D-18]

**Captcha / bot detection concern:** Manual one-off browsing does NOT trigger captchas. No scripting needed or recommended for Phase 1. [ASSUMED — manual browsing standard; no scraping library needed]

**Top-50 coverage includes:** paneer, toor dal, moong dal, chana dal, masoor dal, kabuli chana, rajma, soya chunks, soya granules, peanuts, roasted chana, eggs (ovo-veg), curd, milk, tofu, almonds, walnuts, cashews, oats, sattu, ragi, jowar, idli/dosa batter, makhana, mushroom, methi seeds, sprouts (moong), flaxseeds, hemp seeds, sunflower seeds, besan, urad dal, moth beans, kidney beans, black-eyed peas, pumpkin seeds, quinoa (if available), whey protein powder (for reference, even if expensive), spinach, broccoli, cauliflower, green peas, edamame, tofu, cottage cheese variants, paneer variants (low-fat), Greek-style yogurt variants. [VERIFIED: D-18 coverage list]

---

## License + Admin Work

### IFCT/INDB license email (TODOS-10) — send during Phase 1

**Who:** ICMR-NIN + Anuvaad

**Email addresses:**
- ICMR-NIN: nin@ap.nic.in and ifct2017@gmail.com
- Anuvaad (INDB): awasthi@anuvaad.org.in

**What to request:**
- From ICMR-NIN: Written permission for commercial/product use of IFCT 2017 data in "Bhog," an AI nutrition coaching app (₹299/mo subscription). Explain use: IFCT macro values stored in app database to power meal macros calculations for Indian users. Request confirmation that commercial use is permitted and under what terms.
- From Anuvaad: Confirmation of INDB data license. Request an explicit GitHub repo LICENSE (ideally CC BY 4.0). Confirm whether INDB recipe gram-amount data can be used in a commercial product that builds on IFCT-derived values.

**Expected outcome:** NIN typically responds within 2-4 weeks. Permission may be granted free ("use is encouraged") or may require a data-sharing agreement. [ASSUMED — based on D-31 reasoning; no verified NIN response time data]

**This does NOT block Gate 0a, 0b, 0c, or 0d.** It starts the clock. IFCT/INDB macros are gated behind the free tier until permission lands (D-31). Phase 1 ships the free tier; paid tier (Phase 3) is the binding deadline.

---

## Sequencing + Parallelization

### Dependency graph

```
Day 0-1:  [PARALLEL]
  - Download INDB repo + start Python gram-conversion script (Gate 0a prerequisite)
  - Buy kitchen scale (ships in 1-2 days from Amazon India)
  - Send IFCT/INDB license email to NIN + Anuvaad (non-blocking, start clock)
  - Start Gate 0c WhatsApp outreach (completely parallel, no dependencies)
  - Purchase Google Play Developer account + submit identity verification (start 3-7 day clock)

Day 1-3:  [SEQUENTIAL within Gate 0a branch]
  - Complete INDB Python conversion + map ~43 dishes + LLM-decompose ~4 gaps
  - Set verified_by on dish_decomposition.json rows
  - Add rich/plain oil variants to fat-heavy dishes in JSON

Day 2-5:  [AFTER scale arrives]
  - Shoot + weigh 30 photos (4-6 hours over 3-5 days, eating real meals)
  - Fill labels_truth.csv with weighed grams immediately after each meal
  - Opus 4.7 blind labeling pass on all 30 photos → labels_opus.csv
  - Founder verification of every Opus label → lock labels_truth.csv

Day 3-7:  [PARALLEL with photo work]
  - Gate 0c outreach continues (check responses daily)
  - veg_protein_prices scrape across 4 metros (6-7 hours total, can be split over 2 days)
  - Continue Gate 0b logging (starts as soon as dish_decomposition.json is verified)

Day 1-14: [Gate 0b — runs continuously]
  - Founder logs 2+ meals/day
  - Manual WoZ advice call per meal (Groq/Gemini playground)
  - Score each advice reply on 4/4 rubric same day

Day 14:   [Gate check]
  - Gate 0a: data ready for Phase 2 Week 1 harness run (photos + labels + verified decomp)
  - Gate 0b: tally pass rate (≥70% at 4/4 = pass)
  - Gate 0c: count commits + WTP quotes
  - Gate 0d: confirm decisions committed + Play Console verification pending/approved
```

### Founder-hours estimate

| Work item | Estimate | Source |
|-----------|----------|--------|
| INDB download + Python conversion + mapping | 3-5h | D-21 |
| Kitchen-scale weighing + photos (30 plates) | 5-7h (original) + 2-4h weighing (recalibration) = 7-11h total | gate_0a_vision.md schedule |
| Opus blind labeling pass + founder verification | ~2h | ASSUMED (30 photos × ~4 min review each) |
| Gate 0b: 14-day meal logging + WoZ advice calls + scoring | ~1.5h/day × 14 days = ~21h | ASSUMED (photo + manual macro + WoZ call + scoring) |
| veg_protein_prices scrape + computation | 6-7h | D-18 |
| Gate 0c WhatsApp outreach + tracking | 2-3h | ASSUMED (30 contacts × ~5 min each) |
| Gate 0d ADR commits + Play Console purchase | ~1h | ASSUMED |
| IFCT/INDB license email | 30 min | ASSUMED |
| **Total** | **~41-53h across 14 days** | — |

This is dense for a solo founder running it alongside Gate 0b daily logging. Gate 0b is the critical-path item (14 calendar days minimum). All other work must be front-loaded into days 1-5 so Gate 0b is the only remaining work by day 5-14.

---

## Architecture Patterns

> Phase 1 produces no code. The patterns below are data-file conventions the planner must enforce to ensure Phase 2 consumes Phase 1 outputs correctly.

### `dish_decomposition.json` schema (locked)

```json
{
  "_meta": {
    "version": "0.2",
    "verified_by": "<string — not null after Phase 1>",
    "indb_verified_at": "2026-06-0X"
  },
  "dishes": {
    "<dish_id>": {
      "name_en": "<string>",
      "name_hi": "<string>",
      "bucket": "pan|north|south|west_east",
      "tags": ["veg|non-veg|egg", "rich|plain|staple"],
      "serving_label": "1 katori (~150g cooked)",
      "_variants": ["<dish_id>_plain", "<dish_id>_restaurant"],
      "ingredients": [
        {"ifct_id": "<key in ifct_lookup.json>", "g": <number>}
      ],
      "verified_by": "INDB recipe #<id> (2026-06-02)",
      "_indb_recipe_id": "<id>"
    }
  }
}
```

**Current state:** `verified_by: null` on all dishes (Opus draft, not yet INDB-verified). Phase 1 must set this. [VERIFIED: dish_decomposition.json `_meta.source` + `verified_by: null`]

### `labels_truth.csv` schema (locked)

```csv
filename,dish_id,weighed_total_g,component_weights_g,has_reference_object,notes
```

- `dish_id` must match keys in `dish_decomposition.json` OR `__off_whitelist__:<free-text>`
- `component_weights_g` is a JSON string: `{"dal_tadka":150,"rice":120}`
- `has_reference_object` = `true` for all single + mixed photos (required)
- `weighed_total_g` = scale reading, NOT eyeballed

[VERIFIED: gate_0a_vision.md + CURATION-CHECKLIST.md]

### `veg_protein_prices` seed CSV (Phase 1) → Postgres table (Phase 2)

Phase 1 produces a CSV. Phase 2 Alembic migration creates the table + seeds from it. Schema per D-17:

```
id, food_name, source_platform (zepto/bb/blinkit/rd), city, 
price_per_kg_inr, protein_per_100g, cost_per_g_protein_inr, scrape_date
```

The `city` column supports per-region pricing in V1.5. Phase 1 uses global average for advice engine. [VERIFIED: D-17]

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Unit→gram conversion rules | Custom heuristics | Re-implement `INDB.do` rules verbatim in Python | INDB's Stata rules are verified against their dataset; custom heuristics will diverge |
| Macro ground truth for Gate 0a | Eyeballed estimates | Kitchen scale + weighed grams | V-06: eyeballed truth = agreement between two estimates, not accuracy |
| Advice quality for Gate 0b | App-level scoring | Manual 4/4 rubric scoring per reply | The rubric IS the quality gate; automated scoring before the rubric is calibrated is circular |
| WTP validation | Survey tool / typeform | Direct WhatsApp conversation with price ladder | Conversational context reduces compliance bias vs form-based price anchoring |
| Image format conversion | Custom script | expo-image-manipulator (for production) / Pillow (for Gate 0a photos) | HEIC/AVIF from iOS → JPEG needed; anti-pattern #5 in CLAUDE.md |

---

## Common Pitfalls for Phase 1 Execution

### Pitfall E-01: Skipping the INDB gram-conversion and using Opus-drafted grams as "verified"

**What goes wrong:** Founder sets `verified_by: "Opus 4.7 draft"` without running the INDB Python conversion. Gate 0a macros are computed from unverified decomposition rows. Gate 0a passes on dish-ID (easy) but macros are off because serving sizes are guesses. Phase 2 ships wrong macros.

**Prevention:** `verified_by: null` is a hard blocker. Phase 1 plan must have an explicit task: "Run INDB Python conversion → map whitelist → set verified_by on all 50 dishes." Gate 0a data prep is blocked until this is done.

**Warning sign:** `verified_by` is still null when photos are shot. [VERIFIED: dish_decomposition.json current state]

### Pitfall E-02: Running Gate 0a photos before the scale arrives

**What goes wrong:** Founder shoots 30 photos in day 1 excitement, fills `labels_truth.csv` with eyeballed portions. Scale arrives day 3. Founder doesn't re-weigh. Gate 0a is back to measuring agreement between two estimates (V-06).

**Prevention:** Scale MUST be in hand before any photo is shot for Gate 0a. Plan task order: "Order scale → wait for delivery → shoot first photo." No exceptions.

### Pitfall E-03: Treating Gate 0b as "log to HealthifyMe and copy macros"

**What goes wrong:** Founder uses an existing app's macros instead of the `dish_decomposition.json` + `ifct_lookup.json` pipeline. Gate 0b macros don't reflect the actual pipeline quality. Advice is grounded in someone else's numbers.

**Prevention:** Gate 0b must use the same data source as the production pipeline — `dish_decomposition.json` + `ifct_lookup.json`. The Python one-liner macro calculator (see Gate 0b section) makes this fast. Docs from HealthifyMe or similar = wrong source.

### Pitfall E-04: Batching Gate 0b scoring at day 14

**What goes wrong:** Founder logs meals for 14 days, saves scoring for the end. By day 14, can't remember context for early advice replies. Scoring is inconsistent. Worse, if advice quality is poor at day 3, founder doesn't adjust the prompt until day 14 — wasting 11 days of data.

**Prevention:** Score each advice reply same-day. If pass rate drops below 70% in the first 5 days, iterate the prompt immediately. Don't wait for day 14 to discover a broken prompt.

### Pitfall E-05: Counting "maybe" as a Gate 0c commit

**What goes wrong:** Founder has 8 genuine yeses and 5 maybes, rounds up to "13 commits." Gate 0c passes. Alpha arrives. 5 of those 13 don't install. Alpha has 8 real users, not 20.

**Prevention:** D-12 is explicit: verbal "yes, send me the link when ready" only. Document every contact outcome as one of: contacted/no-response / "maybe" (not a commit) / committed (yes). Gate 0c is 10 committed + 3 WTP quotes, not 10 positive-sentiment responses.

### Pitfall E-06: Not starting the Play Console identity verification clock on day 1

**What goes wrong:** Founder defers Play Console purchase to "after Gate 0a passes." 3-7 day verification delay means Phase 2 Week 1 cannot deploy to Internal Testing track. Phase 2 slips.

**Prevention:** Play Console purchase is a parallel task, not a sequential one. It must start Day 1 of Phase 1 regardless of other gate status. [VERIFIED: PITFALLS.md Pitfall 16 + ROADMAP Phase 1 SC5]

### Pitfall E-07: Forgetting the INDB.do rules for "piece" / "egg" units

**What goes wrong:** `INDB.do` has rules for specific-item units like "egg" (50g each), "piece" (dish-specific), "slice" (bread slice ~30g). A naive unit→gram map that only handles tsp/tbsp/cup will return `None` for 10-20% of rows, leaving ingredients out of decomposition.

**Prevention:** Read `INDB.do` completely before building the Python map. Flag every unit not covered by the initial map. For unflagged units, manually look up INDB's convention (their Stata file is the authoritative source). [ASSUMED — based on D-30 "~45 rules" note]

---

## Runtime State Inventory

> Phase 1 is greenfield with no prior runtime state. Answering explicitly per protocol.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — Supabase and R2 not yet provisioned | None |
| Live service config | None — Render not yet deployed | None |
| OS-registered state | None — no EAS, no FCM tokens, no Play Console yet | None |
| Secrets/env vars | None committed to repo (`.gitignore` covers .env) | None |
| Build artifacts | None — no Python packages installed, no compiled assets | None |

**Nothing found in any category — verified by file system inspection (no `data/indb/` directory, no `.env`, no running services).**

---

## Environment Availability

| Dependency | Required By | Available | Version | Notes |
|------------|------------|-----------|---------|-------|
| Python 3.12 | INDB conversion script | ✓ | 3.12.3 | Present on machine |
| pip3 | Python package install | ✓ | 24.0 | Present |
| pandas | INDB xlsx processing | Likely | — | Not verified; `pip install pandas openpyxl` needed |
| Google AI Studio API key | Gate 0a Gemini calls | Not yet | — | Free, no CC; get at aistudio.google.com |
| Gemini 2.5 Flash free tier | Gate 0a | Not yet | — | 10 RPM / 500 RPD; 30 photos = ~3 min at 10 RPM |
| Groq API key | Gate 0b advice WoZ calls | Not yet | — | Free; get at console.groq.com |
| Kitchen scale (physical) | Gate 0a weighing | Not yet | — | Order on Amazon India (~₹500-800); 1-2 day delivery |
| Google Play Developer account | Gate 0d | Not yet | $25 | 3-7 day identity verification clock |
| INDB repo files | INDB integration | Not yet | — | `git clone https://github.com/lindsayjaacks/Indian-Nutrient-Databank-INDB-` |

**Missing dependencies with no fallback:**
- Kitchen scale — cannot substitute eyeballing (V-06 is why this gate was recalibrated)
- Google AI Studio API key — needed for Gate 0a Gemini calls

**Missing dependencies with fallback:**
- Groq API key — Gemini AI Studio text can substitute for Gate 0b WoZ calls
- INDB repo — if unavailable, fall back to Opus decomposition only (marks ~43 dishes as ASSUMED, not VERIFIED)

---

## Validation Architecture

> `nyquist_validation` is explicitly `false` in `.planning/config.json`. Section skipped.

---

## Security Domain

> Phase 1 produces no code, no deployed services, no user data. ASVS categories do not apply to this phase's deliverables (photos, JSON data files, CSV files, ADR markdown files, admin account purchases).
>
> The IFCT/INDB license email (D-31) is the only security-adjacent item: it starts the process of ensuring the data layer has documented permission for commercial use before Phase 2 ships.

---

## Open Questions

1. **INDB.do exact unit rules**
   - What we know: ~45 unit→gram conversion rules exist; ~46% of rows already grams
   - What's unclear: exact rules for "piece," "egg," "slice," "bunch," "serving" — these are dish-specific
   - Recommendation: Read `INDB.do` file first before building Python map; flag any unit with no clear gram equivalent for manual review

2. **Gemini 2.5 Flash free-tier RPD: 500 or 1500?**
   - What we know: STATE.md flags this as unverified; 500 RPD is the conservative figure from CLAUDE.md stack tables
   - What's unclear: some sources cite 1500 RPD for Flash models
   - Recommendation: Treat 500 RPD as the planning figure (Gate 0a needs only 30 calls, so irrelevant for Phase 1); verify at signup for Phase 2 rate-limit planning

3. **Gate 0b scoring when veg_protein_prices table is not yet built**
   - What we know: 4/4 rubric requires ₹ cost; the table doesn't exist yet in Phase 1
   - What's unclear: Should advice without ₹ cost score 3/4 or 0/4?
   - Recommendation: Score 3/4 for missing ₹ cost if all other dimensions pass; log as "infra gap — table not yet built." Count these 3/4 scores as "conditional pass" in the gate tally. If ≥70% of meals reach 4/4 OR ≥70% reach 3/4+ with ₹-missing-only, gate passes. [ASSUMED — planner should confirm this interpretation with founder]

4. **INDB recipe name → whitelist key mapping ambiguity**
   - What we know: ~43/50 whitelist dishes covered at name-level in INDB
   - What's unclear: INDB recipe names may not exactly match whitelist keys (e.g., "Tur Dal" vs "dal_toor_tadka")
   - Recommendation: Build a manual mapping table (INDB recipe name → `dish_decomposition.json` key) as part of the Python script. Flag cases where multiple INDB recipes could map to one whitelist dish (e.g., "dal_restaurant" vs "dal_tadka") — founder chooses which INDB recipe to use as the seed

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Gate 0b advice quality can be validated via manual WoZ-style Groq/Gemini playground calls without a built backend | Gate 0b Mechanics | Low — WoZ is the documented approach; this is consistent with PITFALLS Pitfall 14 |
| A2 | Google Play Developer identity verification takes 3-7 business days for new accounts (2026) | Gate 0d | Medium — if longer (up to 14 days reported), Phase 2 Internal Testing track setup is delayed |
| A3 | UPI may not be accepted for Google Play Developer $25 fee from some Indian accounts | Gate 0d | Low — debit/credit card international payment available as fallback |
| A4 | INDB.do has ~45 unit conversion rules including item-specific ones ("egg," "piece," "slice") requiring manual review | INDB Integration | Low — exact count from D-30; risk is that some units are truly ambiguous and need founder judgment |
| A5 | Gate 0b 3/4 scores (₹-cost missing only) should count as conditional passes | Gate 0b Mechanics | Medium — if founder requires strict 4/4 only, ≥70% pass rate is harder to achieve without the prices table |
| A6 | 30 WhatsApp contacts → ~50% response rate → ~15 responses → ~10 commits; start with 30+ contacts | Gate 0c Mechanics | Low — conversion rate assumption; founder should track and expand contact list if needed |
| A7 | Manual per-meal macro calculation via Python one-liner is feasible for 14-day Gate 0b logging | Gate 0b Mechanics | Low — Python 3.12 is available; dish_decomposition.json + ifct_lookup.json are already in repo |

---

## Sources

### Primary (HIGH confidence)
- `.planning/phases/01-validation-gates-stack-lock/01-CONTEXT.md` — D-01..D-19 locked decisions
- `.planning/decisions/2026-06-02-founder-rulings-and-gate-recalibration.md` — D-20..D-31 recalibrations
- `evals/gate_0a_vision.md` — Gate 0a harness spec (recalibrated 2026-06-02)
- `data/photos/CURATION-CHECKLIST.md` — photo curation + weighing protocol
- `.planning/REQUIREMENTS.md` — GATE-01..04 definitions
- `.planning/ROADMAP.md` — Phase 1 success criteria
- `.planning/research/PITFALLS.md` — V-01..V-07 vision pitfalls + E-01..E-27 execution pitfalls
- `data/dish_decomposition.json` — current Opus-drafted state (verified_by: null)
- `.planning/STATE.md` — project state + pending blockers
- `CLAUDE.md` (project) — technology stack, constraints, anti-patterns

### Secondary (MEDIUM confidence)
- `TODOS.md` items TODOS-9 + TODOS-10 — INDB integration + license gate detail
- `.planning/phases/01-validation-gates-stack-lock/01-AI-SPEC.md` — §1-§5 system classification + eval dimensions

### Tertiary (ASSUMED — training knowledge, not verified in this session)
- Google Play Developer identity verification timeline (3-7 days)
- UPI payment restriction for Google international fees
- WhatsApp cold-warm conversion rate (~50% response)
- Gate 0b 3/4 scoring interpretation for missing ₹-cost

---

## Metadata

**Confidence breakdown:**
- Gate 0a execution mechanics: HIGH — fully documented in gate_0a_vision.md + CONTEXT.md D-06..D-10
- INDB integration: HIGH for structure; MEDIUM for exact .do rules (file not read, only described in D-30)
- Gate 0b WoZ mechanics: HIGH for approach; ASSUMED for exact scoring edge cases
- Gate 0c outreach mechanics: HIGH for protocol; ASSUMED for conversion rate
- Gate 0d Play Console: HIGH for process; ASSUMED for UPI payment restriction
- veg_protein_prices scrape: HIGH for approach + coverage

**Research date:** 2026-06-02
**Valid until:** 2026-07-02 (stable domain — no fast-moving libraries; INDB and IFCT data are static)

## Project Constraints (from CLAUDE.md)

The following directives from `CLAUDE.md` are directly relevant to Phase 1 execution:

| Directive | Impact on Phase 1 |
|-----------|------------------|
| Gemini 2.5 Flash (NOT 2.0 — retires March 2026) | Gate 0a must use Gemini 2.5 Flash API endpoint specifically |
| R2 `jurisdiction=india` bucket | Not relevant Phase 1 (no R2 provisioning yet) |
| Anti-pattern #4: LLM macros direct from photo BANNED | Gate 0a pipeline must use decomp + IFCT lookup, never LLM-direct |
| Anti-pattern #5: Skip JPEG conversion BANNED | Gate 0a photos must be JPEG ≤1280px before submission to eval harness |
| Anti-pattern #8: USDA FoodData BANNED | Gate 0b macro derivation must use IFCT/INDB, not USDA |
| No production code in Phase 1 | Gate 0a Python harness is Phase 2 Week 1 deliverable; Phase 1 produces data only |
| Design-before-code (memory: feedback_design_before_code.md) | All D-01..D-31 decisions must be committed to `.planning/decisions/` before Phase 2 begins |
| GSD workflow enforcement | All Phase 1 work should flow through `/gsd-execute-phase` |
| Zero-CC constraint (Phase 0-1) | Google AI Studio key = free, no CC. Groq key = free, no CC. Only Play Console requires payment ($25) |
