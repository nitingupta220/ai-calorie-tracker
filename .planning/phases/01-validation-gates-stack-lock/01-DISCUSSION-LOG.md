# Phase 1: Validation Gates + Stack Lock - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-28
**Phase:** 1-Validation Gates + Stack Lock
**Areas discussed:** Hosting (free-no-CC), Gate 0a labeling protocol, Gate 0c recruit + commitment bar, Veg-protein ₹/gram source

---

## Hosting — Free-no-CC stack

### Q1/4 — Initial recommendation rejected by user constraint (free, no credit card)

| Option | Description | Selected |
|---|---|---|
| Fly.io Mumbai (bom1) | Sub-20ms India latency, DPDP-aligned, ~$1.94-20/mo | |
| Railway Singapore | +50-100ms latency, best DX, Hobby $5/mo | |
| Defer — spike both Day 1 | Build dummy FastAPI on both, decide after deploying | |

**User's choice:** Free, no credit card — check all options. Triggered re-research.

### Q1/4 (revised after free-no-CC research)

| Option | Description | Selected |
|---|---|---|
| Render free (Singapore) | FastAPI-native, push-from-GitHub, ~60s cold start, no CC | ✓ |
| Hugging Face Spaces | Free 2 CPU / 16GB RAM Docker, US-only, sleeps 48hr | |
| PythonAnywhere | Free 1 web app, always-on but slow, no CC | |
| Koyeb — verify CC status before locking | Free tier exists; CC requirement unclear in 2026 | |

**User's choice:** Render free (Singapore).
**Notes:** Fly.io and Railway both eliminated — both require credit card in 2026 (Fly removed free tier; Railway requires CC since Aug 2023). Cross-border processing from Singapore is DPDP-compliant with consent + standard safeguards.

### Q2/4 — Supabase Mumbai auto-pause handling

| Option | Description | Selected |
|---|---|---|
| GitHub Actions cron ping | Free Actions cron hits /healthz every 6hr, ~10 lines yaml | ✓ |
| Render free-tier cron worker | Self-contained on same platform | |
| Manual wake — ignore auto-pause | Adds 30s to first query; fine for solo testing | |
| Switch DB — Neon free tier | Rejected: no India region, DPDP concern | |

**User's choice:** GitHub Actions cron ping.

### Q3/4 — Cold-start trade-off on Render (60s after 15min idle)

| Option | Description | Selected |
|---|---|---|
| Accept cold start; cron-ping keeps warm during alpha | Cron every 10min during alpha window, disable after | ✓ |
| Upgrade Render to $7/mo Starter at alpha | Always-on, CC required | |
| Cache last-meal result on mobile aggressively | Layered with cron-ping; defer to Phase 3 | |

**User's choice:** Accept + cron-ping during alpha.

### Q4/4 — More or next?

**User's choice:** Next area — Gate 0a labeling.

---

## Gate 0a — Vision Benchmark Labeling Protocol

### Q1/4 — Ground-truth labeler

| Option | Description | Selected |
|---|---|---|
| Founder + RD 30-min audit on sample | Founder + ₹1500-3000 RD consultation on 5-photo sample | |
| Founder alone (IFCT + research) | Zero cost; risk on ISSN protein-math + Indian portion conventions | |
| LLM-judge with founder sanity-check | Claude/GPT-4o labels; founder verifies; circular-bias risk | ✓ |
| Outsource via Topcoder/Fiverr nutrition labeler | ₹500-1500 per labeler; quality varies | |

**User's choice:** LLM-judge with founder sanity-check.
**Notes:** Risk flagged as Reviewer Concern in CONTEXT D-10. Mitigations baked in: different LLM family (Opus, not Gemini); macros from deterministic IFCT lookup (not LLM math); founder verifies every label manually; RD audit reserved as V1.5 trigger if real-user accuracy collapses.

### Q2/4 — Judge LLM family

| Option | Description | Selected |
|---|---|---|
| Claude Opus / Sonnet 4 | Strongest non-Gemini; free via existing subscription | |
| GPT-4o / GPT-4.5 (OpenAI) | Strong vision; different lineage; ~₹15 for 30 photos | |
| Multi-judge ensemble — Claude + GPT-4o | Highest robustness; ~₹15-30 + adjudication time | |
| Open-source: Qwen 2.5 VL via Groq/Together | Discouraged — second circularity (fallback in production) | |

**User's choice:** Claude Opus 4.7 (existing subscription).
**Notes:** Free via existing Claude Code subscription — zero incremental cost.

### Q3/4 — Dish decomposition table source

| Option | Description | Selected |
|---|---|---|
| Founder-built, Opus-assisted, IFCT-verified | One-time Gate 0a work; ~3-5 hours | |
| Scrape Tarla Dalal / Unlock.fit nutrition pages | Online sources; ~1-2 hr; consistency risk | |
| NIN cooked-dish dataset (if accessible) | Authoritative; coverage uncertain | |
| Hybrid: Opus draft → IFCT verify → RD published-recipe cross-ref | Best quality; ~5-7 hours | |

**User's choice:** Layered cascade — try NIN first, scrape Tarla Dalal + Unlock.fit + more, then hybrid (option 4).
**Notes:** Maximize source coverage, then synthesize. Locked at CONTEXT D-08.

### Q4/4 — Photo stratification

| Option | Description | Selected |
|---|---|---|
| Keep 10/10/10 (single/mixed/thali) | Per-bucket pass bar from AI-SPEC §5 | ✓ |
| 15/10/5 (weights toward easier) | Higher aggregate pass; masks thali weakness | |
| 5/10/15 (weights toward hardest) | Higher bar; better real-world signal | |
| Add 10 edge-case bucket (40 total) | Scope creep; defer to V1.5 | |

**User's choice:** Keep 10/10/10.

---

## Gate 0c — Trial User Recruit Pitch + Commitment Bar

### Q1/4 — WhatsApp pitch wording

| Option | Description | Selected |
|---|---|---|
| Short, direct, founder-voice | 3-4 sentences; honest; low-friction | ✓ |
| Long, pitch-y, dressed-up | Deck-style; risks salesy; lower WhatsApp response | |
| Voice note + 1-line text follow-up | Higher engagement; harder to scale | |
| Founder writes 3 variants, A/B with first 6 | Test pitches; adds 1-2 days | |

**User's choice:** Short, direct, founder-voice.

### Q2/4 — Commitment bar

| Option | Description | Selected |
|---|---|---|
| Verbal 'yes, send link when ready' + WhatsApp confirm | Minimum real-signal bar | ✓ |
| Scheduled install date in writing | Stronger; harder to get 10; locks Phase 2 timeline | |
| Calendar invite + 15-min onboarding call agreed | Strongest; ≤5 commitments likely | |
| Sliding scale (5 strong + 5 medium + 10 weak) | Three-tier system; self-deception risk | |

**User's choice:** Verbal 'yes' + WhatsApp confirm.

### Q3/4 — ₹299 WTP capture

| Option | Description | Selected |
|---|---|---|
| Open-ended price ladder | Avoid leading; capture verbatim | ✓ |
| Direct ask: 'Would you pay ₹299/mo?' | Leading; compliance bias | |
| Behavioral proxy: 'What are you paying today?' | Indirect; doesn't produce verbatim ₹299 quote | |
| Combine open-ended ladder + behavioral proxy | Best signal; 5 min/call | |

**User's choice:** Open-ended price ladder.

### Q4/4 — Recruit funnel source

| Option | Description | Selected |
|---|---|---|
| Personal network first — gym buddies, Insta DMs | Highest reply rate; clique bias | ✓ |
| Personal + Reddit r/indianfitness DM outreach | Cold outreach; ≤10% response | |
| Personal + local gym poster / WhatsApp group seeding | Random clickers dilute 'named' bar | |
| Tiered: personal first → Insta DM creator-commenters if <10 | Two-stage funnel | |

**User's choice:** Personal network first.
**Notes:** Bias toward Tier-1 city / similar income documented as known caveat for alpha generalization.

---

## Veg-Protein ₹/gram Reference Table

### Q1/4 — Source

| Option | Description | Selected |
|---|---|---|
| Hybrid: Zepto/BigBasket + founder local-market check | E-commerce + kirana cross-check | |
| Founder local-market manual only | Single-city bias | |
| Zepto/BigBasket scrape only | Urban-convenience pricing skews high | |
| Published RD price sheet (Munmun / Ryan Fernando / NFNA) | Authoritative; ages fast | |

**User's choice:** Zepto + BigBasket + Blinkit scrape + published RD price sheets (combined).

### Q2/4 — Refresh cadence

| Option | Description | Selected |
|---|---|---|
| Manual quarterly + automated monthly anomaly alert | Catches sudden price shocks | ✓ |
| Manual monthly refresh | ~30 min/mo founder time | |
| Daily automated scrape | Scope creep; maintenance overhead | |
| One-time at Gate 0a, never refresh | Drift over time; advice becomes wrong | |

**User's choice:** Quarterly + monthly anomaly alert.

### Q3/4 — Storage format

| Option | Description | Selected |
|---|---|---|
| JSON file in repo: `data/veg_protein_prices.json` | Version-controlled; diff-able | |
| Postgres table `veg_protein_prices` | DB row per item; per-region pricing later | ✓ |
| Both — JSON + sync to Postgres on deploy | Belt-and-suspenders | |
| CSV file in repo | Easier to edit by hand | |

**User's choice:** Postgres table.
**Notes:** Adds Alembic migration to Phase 2 backend spine. Schema per CONTEXT D-17.

### Q4/4 — Coverage scope

| Option | Description | Selected |
|---|---|---|
| Top 25 sources (90% of Indian-veg protein intake) | Manageable; 3-4 hours | |
| Top 50 sources (broader regional coverage) | Adds ragi/jowar/idli/dosa/sattu; 6-7 hours | ✓ |
| Top 10 only (gym-bro persona focus) | Too narrow | |
| Lazy build: start 15, expand to 25 by Phase 3 | Iteration-friendly; scope-drift risk | |

**User's choice:** Top 50 sources.

---

## Claude's Discretion

- Exact GitHub Actions cron yaml for /healthz keep-warm + Supabase keep-warm
- Exact Opus 4.7 labeling prompt template (adapt from AI-SPEC §3 Appendix)
- Exact scrape implementation for Zepto / BigBasket / Blinkit (library, captcha handling, rate-limiting) — scope-limited to one-off Gate 0a + quarterly refresh
- Exact Postgres schema for `veg_protein_prices` (within CONTEXT D-17 constraint)
- `.planning/decisions/` folder structure + ADR-lite template — created by Phase 2 planner

## Deferred Ideas

- RD audit of Gate 0a labels — V1.5 trigger condition
- Mumbai-native hosting (Fly.io bom1) — Phase 4/5 with CC
- Render Starter $7/mo — Phase 4/5 with CC
- Per-region pricing in advice engine — V1.5
- Always-fresh daily scrape — Phase 4+
- Reddit r/indianfitness DM outreach — Phase 6 alpha expansion
- 15-min RD-call commitment tier — Phase 4 alpha power-user qualification
- Voice note + text pitch variant — available for top-5 priority recruits
- Founder-only labeling — explicitly rejected (Opus + founder verification chosen)
- JSON file storage for veg-protein prices — explicitly rejected (Postgres chosen)
- Top-25 veg-protein coverage — explicitly rejected (Top-50 chosen)
