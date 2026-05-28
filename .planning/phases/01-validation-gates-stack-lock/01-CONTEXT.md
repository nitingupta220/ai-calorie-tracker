# Phase 1: Validation Gates + Stack Lock - Context

**Gathered:** 2026-05-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 locks all four risk gates (Gate 0a vision benchmark, Gate 0b advice rubric, Gate 0c Trial User commitments, Gate 0d stack + Play account + hosting decision) BEFORE any production code begins. The output of this phase is the locked-in design state: a passing vision benchmark, a passing advice-rubric benchmark, ≥10 verbal-commit Trial Users with ≥3 verbatim ₹299 price-WTP quotes, and a committed stack + decisions ledger in `.planning/decisions/`. No production app code, no UI, no Play Store submission — only gates + decisions + a curated `dish_decomposition.json` + `veg_protein_prices` table seed.

</domain>

<decisions>
## Implementation Decisions

### Hosting (Compute + Database + Storage)

- **D-01:** **Compute = Render free tier (Singapore region)** for FastAPI backend during Phase 0-1 + Phase 6 alpha. No credit card required. Push-to-deploy from GitHub. Free web service sleeps after 15 min idle with ~60s wake.
  - **Reason:** Fly.io and Railway both require credit card in 2026 (Fly removed free tier; Railway requires CC since Aug 2023). Render is the only free-no-CC option that fits FastAPI well. Cross-border processing from Singapore is DPDP-compliant with consent + standard safeguards disclosed in privacy policy.
  - **Trade-off:** +50-100ms latency vs Mumbai-native compute. Acceptable for Phase 1 alpha (20 users); re-evaluate Mumbai hosting (Fly bom1 + CC) at Phase 4 alpha completion or Phase 5 public launch.

- **D-02:** **Database = Supabase Mumbai free tier** (500MB, 50K MAU, no CC required). Indian region satisfies DPDP residency requirement for PII (user profile, meal logs, consent ledger).
  - **Free-tier quirk:** Supabase auto-pauses after 1 week idle. Handled via GitHub Actions cron-ping every 6h (free, ~10 lines yaml). Disable cron when paid tier kicks in.

- **D-03:** **Cold-start mitigation during Phase 1 alpha = GitHub Actions cron every 10 minutes against Render `/healthz`** for the 14-day alpha window. Keeps Render warm during user-active periods. Disable after alpha to conserve Actions minutes.
  - **Layered with mobile-side caching** (recent meal results cached locally) — deferred to Phase 3 mobile build.
  - **Upgrade trigger:** Move to Render Starter $7/mo (CC required) ONLY if Gate 7 retention passes AND founder commits to ≥2 months of Phase 4+ work.

- **D-04:** **Photo storage = Cloudflare R2 with `jurisdiction=india`** (free 10GB, no CC required at signup). Endpoint `<acct>.in.r2.cloudflarestorage.com`. Bucket created with explicit jurisdiction parameter — Mumbai PoP alone does NOT satisfy DPDP residency.

- **D-05:** **Auth = Firebase Phone OTP** (free 50K MAU, no CC, no DLT registration required vs MSG91). Server verifies ID token via `firebase-admin`.

### Gate 0a — Vision Benchmark Labeling Protocol

- **D-06:** **Ground-truth labeler = Claude Opus 4.7 (existing subscription) + founder verification on all 30 photos.** NOT Gemini (avoids circular bias with Gemini 2.5 Flash under test). Opus emits dish-name + portion estimate; founder verifies every label manually. Zero incremental cost (existing Claude Code subscription).

- **D-07:** **Macros computed deterministically from `dish_decomposition.json` + IFCT 2017 lookup** — never from LLM math. Labeling LLM emits dish-name + portion only; macros are looked up from the decomposition table aggregated against IFCT raw ingredients.

- **D-08:** **Dish-decomposition table source = layered cascade:**
  1. **Try first:** National Institute of Nutrition (NIN) cooked-dish dataset (if accessible — verify during Gate 0a kick-off)
  2. **Scrape:** Tarla Dalal recipe nutrition pages, Unlock.fit dish pages, any other accessible Indian recipe DB
  3. **Hybrid finalize:** Claude Opus 4.7 drafts decomposition (e.g., paneer butter masala = paneer 80g + tomato 60g + butter 15g + cashew 5g + cream 10g); founder verifies grams against IFCT 2017 + Tarla Dalal + Unlock.fit + Munmun Ganeriwal / Ryan Fernando published recipes
  4. **Output:** committed at `data/dish_decomposition.json` (50 dishes) — also seeded into Postgres if `veg_protein_prices` Postgres pattern is reused
  - Estimated 5-7 hours founder time across Gate 0a kickoff.

- **D-09:** **Photo stratification = 10/10/10 (single-dish / mixed / thali).** Per-bucket pass bar (≥70% dish-name + ≥60% macros within ±35%) from AI-SPEC §5 — aggregate pass cannot mask thali-bucket failure.

- **D-10 (Reviewer Concern flag):** Using an LLM (Opus 4.7) to label ground-truth for an LLM-under-test (Gemini 2.5 Flash) risks circular bias even when families differ. Mitigations:
  - Different LLM family (Opus, not Gemini) ✓
  - Macros via deterministic IFCT lookup, not LLM math ✓
  - Founder manually verifies every single label (not spot-check) ✓
  - **Reserve ~₹1,500-3,000 RD audit budget as V1.5 trigger** — if Gate 0a passes Phase 1 but real-user accuracy in Phase 6 alpha (target ≥75% on real photos) collapses, founder books a 30-min consultation with a senior Indian sports nutritionist / RD to audit the labels + decomposition table.

### Gate 0c — Trial User Recruit + Commitment Bar

- **D-11:** **WhatsApp pitch tone = short, direct, founder-voice (3-4 sentences).** Honest framing, no deck-style pitch, no salesy hype. Example template (founder may iterate exact wording):
  > "Hey [name], building an AI app for Indian-veg-budget-aware calorie tracking + advice. Photo your meal, get macros + 1-line tip in your context. Looking for 20 early users for 2-week test. Free, no card needed. You in?"

- **D-12:** **Commitment bar = verbal 'yes, send me the link when ready' + WhatsApp confirm.** Unambiguous yes only — 'maybe' / 'send and I'll see' / 'sounds cool' do NOT count. Sets expectation: when alpha link arrives, user installs and logs meals for 2 weeks.

- **D-13:** **₹299 willingness-to-pay capture = open-ended price ladder** to avoid leading-the-witness compliance bias. Ask: *"If this app worked exactly like I described, what would you pay per month? ₹0, ₹100, ₹299, ₹499, more?"* Capture verbatim quote. Gate 0c bar = ≥3 quotes with a specific ₹ figure attached.

- **D-14:** **Recruit funnel = personal network first** — gym buddies, college fitness friends, Instagram DMs to people founder already follows / who follow founder. Hit 10 commitments here. Document the segmentation bias (Tier-1 city / similar income / similar gym scene) as a known caveat for alpha generalization. Reddit / cold-DM outreach deferred to Phase 6 alpha if 20-name list is short.

### Veg-Protein ₹/gram Reference Table

- **D-15:** **Source = hybrid of three quick-commerce platforms + RD published price sheets.** Pull average prices for top-50 veg-protein sources from Zepto + BigBasket + Blinkit across 4 metro cities (Delhi / Mumbai / Bangalore / Hyderabad). Cross-reference against published RD price sheets (Munmun Ganeriwal, Ryan Fernando, NFNA). RD sheets serve as anchor for staples; quick-commerce data provides freshness + multi-city perspective.

- **D-16:** **Refresh cadence = quarterly manual founder refresh + monthly automated anomaly alert.** Cron compares current scrape against last quarter — any item moving >15% pings founder for early refresh. Catches festival inflation, tomato/onion seasonal shocks.

- **D-17:** **Storage = Postgres table `veg_protein_prices`** (NOT JSON in repo, per founder preference). Schema TBD by planner — at minimum: `id, food_name, source_platform (zepto/bb/blinkit/rd), city, price_per_kg_inr, protein_per_100g, cost_per_g_protein_inr, scrape_date`. Allows per-region pricing in V1.5; SQL-aggregatable across sources for advice-engine consumption. Adds Alembic migration to Phase 2 backend spine.

- **D-18:** **Coverage = top 50 sources** for broader regional fit (vs top-25 minimum). Includes pan-Indian staples (paneer, dal varieties, soya chunks/granules, chana, rajma, peanut, eggs as veg+egg boundary), Western regional staples (oats, sprouts, almonds, walnuts, whey for non-veg-friendly users), and Indian regional staples (ragi, jowar, idli/dosa batter, sattu, makhana, mushroom, methi seeds, beet, spinach). Founder time ~6-7 hours during Gate 0a kickoff.

### Decisions Ledger Format

- **D-19:** Each major locked decision in this CONTEXT.md gets a corresponding 1-paragraph ADR-lite entry in `.planning/decisions/` (path created in Phase 2 Week 0). Format: `YYYY-MM-DD-decision-slug.md` with `status / context / decision / consequences` sections. Phase 2 planner will create the folder + seed it from these D-01..D-18 entries.

### Claude's Discretion

- Exact GitHub Actions yaml for cron-ping → planner discretion (standard pattern)
- Exact prompt template for Opus labeling → planner / ai-researcher discretion (already drafted in AI-SPEC §3 Appendix; just adapt for Opus instead of Gemini)
- Exact Zepto/BigBasket/Blinkit scrape implementation (scraping library, captcha handling, rate-limiting) → planner / executor discretion; scope-limited to one-off Gate 0a + quarterly refresh, not real-time
- Exact Postgres schema for `veg_protein_prices` → planner discretion within constraints in D-17

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `.planning/PROJECT.md` — locked V1 scope, persona, moat, premises
- `.planning/REQUIREMENTS.md` — GATE-01..04 detail + 67 v1 REQ-IDs mapped to phases
- `.planning/ROADMAP.md` — 5-phase coarse plan + Phase 1 goal + success criteria
- `.planning/research/SUMMARY.md` — 3-stack-corrections synthesis (Gemini 2.5 Flash, R2 india jurisdiction, Supabase Mumbai) + roadmap implications
- `.planning/research/STACK.md` — verified 2026 stack with Context7-verified versions
- `.planning/research/ARCHITECTURE.md` — `ai_provider.py` as load-bearing first-class component + presigned-PUT + two-step vision contracts
- `.planning/research/PITFALLS.md` — 27 catalogued pitfalls; WoZ QA promoted to Gate; DPDP pulled to Phase 2 Week 1; Play account Week 0d

### AI System Contract (Phase 1 + Phase 2 spine)
- `.planning/phases/01-validation-gates-stack-lock/01-AI-SPEC.md` — 937-line locked design contract: §5 eval dimensions D1-D12, §6 12 guardrails G1-G12, §7 production monitoring metrics M1-M10, Pydantic schemas, prompt structure, cost/latency budget
- `.planning/research/FEATURES.md` — 50-dish whitelist composition + V1 table-stakes additions (manual weight log + water tracker)

### Founder Vision Source
- `~/.gstack/projects/ai-calorie-weight-loss/nitin-unknown-design-20260527-181050.md` — adversarial-reviewed (3 iterations + founder-feedback iteration) design doc; full weekly milestones, Approach C rationale, persona discipline, Reviewer Concerns section

### Indian Nutrition + Pricing References (cited in Gate 0a/0b/veg-₹ work)
- IFCT 2017 (Indian Food Composition Tables, NIN/ICMR) — raw-ingredient nutrition baseline
- NIN cooked-dish dataset — verify accessibility during Gate 0a
- ISSN 2024 Position Stand on Protein — 1.6-2.2 g/kg muscle-gain target band
- Tarla Dalal recipe nutrition pages — dish decomposition cross-ref
- Unlock.fit dish pages — Indian-context portion conventions
- Munmun Ganeriwal published recipes / NFNA / Ryan Fernando — Indian sports-nutrition pricing + macro authority
- Zepto / BigBasket / Blinkit (multi-city avg) — veg-protein quick-commerce pricing source

### Regulatory (cited in compliance work)
- DPDP Act 2023 (MeitY) — Indian region storage requirement + consent ledger + 30-day hard-delete
- CDSCO Medical Devices Rules 2017 — banned-words discipline (treat / cure / diagnose / medicine / drug)
- ASCI Code 2023 — health/fitness advertising claim substantiation
- Razorpay UPI Autopay docs — Phase 3 paid tier prep (₹15K monthly mandate ceiling)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **None yet** — greenfield project, no code committed. Phase 1 produces no production code; all artifacts are markdown decisions + data files (JSON / SQL seeds).

### Established Patterns (from research + design doc)
- **`ai_provider.py` abstraction** as first-class folder (`server/app/providers/`) — locked in research/ARCHITECTURE.md; planner enforces lint rule banning provider SDK imports outside this folder.
- **Two-step vision pipeline** (LLM → dish ID → deterministic IFCT lookup → macros aggregate) — locked in AI-SPEC §1 + §3; macros must NEVER come from LLM math.
- **Inline advice rendering** (`<AdviceInline />` as child of `<MacrosCard />`) — locked in AI-SPEC §1 + design doc P1; advice in a separate tab = moat collapse.
- **Pydantic v2 structured outputs** — locked in AI-SPEC §4b; vision and advice both validate via Pydantic before render.
- **Append-only `correction_event` table** from day 1 — locked in REQUIREMENTS HISTORY-04 + ARCHITECTURE; corrections become V1.5 fine-tuning corpus.
- **Free-first multi-provider AI strategy** — locked in PROJECT.md Constraints + AI-SPEC §2; Phase 0-1 testing on free tiers (Google AI Studio + Groq + OpenRouter + Ollama), paid fallback wired but unused until rate-limited.

### Integration Points
- **GitHub Actions cron-ping** integrates with `/healthz` endpoint to be exposed by FastAPI in Phase 2 Week 1.
- **Postgres `veg_protein_prices` table** integrates with advice-engine prompt construction (Phase 2 Week 3) — SQL pre-fetch + JSON-encode in prompt context.
- **`dish_decomposition.json`** integrates with vision pipeline (Phase 2 Week 2) as deterministic lookup table.
- **Eval pytest scripts** (`evals/gate_0a_vision.py`, `evals/gate_0b_advice.py` per AI-SPEC §5) — produced in Phase 1 Gate 0a/0b execution; run via CI in Phase 2+ on `prompts/**`, `providers/**`, `services/advice_*` PR paths.

</code_context>

<specifics>
## Specific Ideas

- **Founder explicitly wants all design decisions locked before any code** (saved to project memory: `feedback_design_before_code.md`). Phase 1 is the right scope for this lock-in. Phase 2 plan should not start until Phase 1 gates have passed AND all D-01..D-18 decisions are committed to `.planning/decisions/`.

- **Founder explicitly wants both gstack + GSD toolchains active** (saved to project memory: `feedback_toolchain_gstack_gsd.md`). Phase 1 work uses gstack `/office-hours` design doc as canonical vision source + GSD `.planning/` structure for execution. Downstream planner should reference both.

- **Caveman mode active** for all founder communication — no preamble, no fluff in user-facing messages. Code, commits, security warnings stay normal English.

- **Existing Claude Code Opus 4.7 subscription** — leverage for Gate 0a labeling (zero incremental cost). Do NOT default to OpenAI/GPT for this.

- **Zero-CC constraint is hard** — every external service in Phase 0-1 must work without a credit card. Founder has no budget runway. Cost ceiling for entire Phase 0-1 = ~₹0-200 total (negligible discretionary).

- **WoZ QA Gate already promoted from task to gate** by research/PITFALLS — Phase 3 Week 6 must produce ≥35 founder-written advice examples + ≥70% AI-vs-WoZ match before Phase 4 alpha entry. Phase 1 sets the stage; founder confirms understanding now so Phase 2 + 3 planners respect this.

</specifics>

<deferred>
## Deferred Ideas

- **RD (registered dietitian) audit of Gate 0a labels** — deferred to V1.5 trigger condition (real-user vision accuracy in Phase 6 alpha collapsing below 75%). Reserve ~₹1,500-3,000 budget. Not blocking Phase 1.

- **Mumbai-native hosting (Fly.io bom1)** — deferred to Phase 4 / Phase 5 trigger (Gate 7 retention passes AND founder commits 2+ months). Requires credit card. Will not happen during Phase 0-1.

- **Render Starter $7/mo (no sleep, always-on)** — deferred to same Phase 4 trigger. Requires CC. Cron-ping keeps free tier warm during alpha.

- **Per-region pricing for veg-protein table** — deferred to V1.5. Postgres schema (D-17) supports it from day 1 (city column), but advice engine uses global average until V1.5.

- **Always-fresh daily scrape of Zepto/BB/Blinkit** — deferred to Phase 4+. Manual quarterly + automated anomaly alert is the Phase 1/2/3 cadence.

- **Reddit r/indianfitness DM outreach** — deferred to Phase 6 alpha expansion if personal network funnel produces <20 named contacts. Not Gate 0c work.

- **15-min RD onboarding call commitment-tier (Tier-3 strongest signal)** — rejected for Gate 0c; verbal-yes-plus-WhatsApp-confirm is the bar. RD-call expectation may return as Phase 4 alpha qualification for top-5 power users.

- **Voice note + text follow-up pitch variant** — kept available for top-5 highest-priority recruits during Gate 0c. Documented; not the default.

- **Founder-only ground-truth labeling (no LLM)** — explicitly rejected by founder in favor of Opus + founder verification. Documented.

- **JSON file instead of Postgres for `veg_protein_prices`** — explicitly rejected by founder in favor of Postgres-native pattern. Schema design added to Phase 2 Week 1-2 scope.

- **Top-25 veg-protein coverage instead of top-50** — explicitly rejected by founder in favor of broader regional fit. Top-50 adds ~3 hours founder time but covers regional staples (ragi, jowar, idli/dosa batter, makhana, sattu).

</deferred>

---

*Phase: 1-Validation Gates + Stack Lock*
*Context gathered: 2026-05-28*
