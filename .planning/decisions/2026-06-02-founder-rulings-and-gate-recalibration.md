# ADR-lite · 2026-06-02 Founder Rulings + Gate-0a Recalibration

Added 2026-06-02. Founder rulings from the pre-build audit + an external adversarial review of the photo→macros accuracy premise. These supersede conflicting earlier text and are mirrored in `CLAUDE.md`, the `.planning/` specs, the handoff set, and `bhog-v1-design-spec.html` (§ "Decisions Locked · 2026-06-02", cards F-01..F-16).

**Verification:** every load-bearing figure below was fact-checked against primary sources (Nutrition5k CVPR 2021, arXiv:2103.03375; GPT-4V food study, Nutrients 2025, PMC11858203; Martin et al. 2018, PMID 30401671; RevenueCat 2025–26; OpenAI HealthifyMe case study). **One reviewer claim FAILED verification and is omitted: "calorie-tracking retention 68%→21% by week 12 / AI apps churn 30% faster"** — unsourced; the only real 30% evidence points the other way (AI personalization *reduces* churn). See PITFALLS.md "Vision / Calorie-Accuracy Pitfalls" (V-01..V-06).

---

## D-20 · Gate-0a recalibration (HEADLINE)
- **Status:** LOCKED.
- **Context:** The original Gate-0a measured Gemini's macros against the founder's *eyeballed* portions run through an Opus-drafted (`verified_by:null`) decomposition table — agreement between two estimates, not accuracy, and circular on PORTIONS (D-10 only flagged labels). Verified: image-only calorie error floors ~26% (Nutrition5k); dish-ID is the easy ~20% (GPT-4V 93% ID but 11/16 nutrients significantly off); portion-from-2D is ill-posed; hidden oil/ghee invisible in pixels.
- **Decision:** (1) **Weighed ground truth** — founder weighs the 30 benchmark plates on a kitchen scale; truth macros derived from weighed grams. (2) **Split metrics** — dish-ID ≥80% (raised) scored *separately* from macro-within-±35% (≥70% single / ≥60% mixed); report median + P75/P90 tail. (3) **Thali reported-only / non-blocking** → "snap each item / tap to confirm" UX; pass bar re-introduced in V1.5. (4) **Reference object mandatory** in single+mixed; gate the reference-present arm, report no-reference separately.
- **Consequences:** +2–4h founder weighing + a ~₹600 kitchen scale. Gate now predicts field accuracy rather than self-agreement. Propagated to REQUIREMENTS GATE-01, ROADMAP P1 SC1, `evals/gate_0a_vision.md`, 01-AI-SPEC (D1/D2/CLI/M1), `data/photos/CURATION-CHECKLIST.md`, and the design-spec HTML.

## D-21 · INDB ingest for portion/decomposition priors
- **Status:** LOCKED.
- **Context:** No free Indian dataset carries weighed-gram macro truth (verified inventory: Indian Food Images / The-massive / IndianFoodNet-30 — recognition labels only). INDB (Indian Nutrient Databank, open-access, IFCT-derived) has ~1,014 Indian recipes WITH per-ingredient grams + per-serving macros.
- **Decision:** Ingest INDB alongside IFCT 2017 to seed `dish_decomposition.json` + verify rows before Gate 0a (TODOS-9).
- **Consequences:** ~3–5h ingest/mapping. Turns the decomposition table from Opus guesses into sourced grams. License IFCT-derived — verify before commercial use.

## D-22 · App name = Bhog (final)
- **Status:** LOCKED. Niwala (NAME.md) + Sahi/Tejo (NAME-V2.md) superseded.

## D-23 · RD audit = non-blocking V1.5 trigger
- **Status:** LOCKED. Founder-verification (now weighed, cross-checked vs INDB/IFCT) is V1 ground truth. RD audit fires only if alpha real-user accuracy <75%. CONTEXT/D-10 wins over AI-SPEC §5.

## D-24 · Observability = Postgres `ai_call_log` ledger
- **Status:** LOCKED. Render-compatible cost+eval spine. Phoenix local-dev only; hosted Phoenix → paid Phase 4. Supersedes the Fly-sidecar Phoenix plan (dead with D-01 Render). `ai_provider_pricing` table (MODEL-SPEC #14, migration 0010) powers the read-time cost-ledger join.

## D-25 · Enum source of truth = MODEL-SPEC DB enums
- **Status:** LOCKED. Advice Pydantic Literals aligned to DB (diet/budget/goal); `weight_loss` kept in the type, clamped behind a V1 muscle-gain-only flag.

## D-26 · DSR routes + auth defaults
- **Status:** LOCKED. `DELETE /me` (soft-delete) + `GET /me/export`; events logged as `consent_audit`; consent_type value `photo`. Delete/export accept any valid Firebase Bearer token (no fresh-OTP re-auth); a soft-deleted user can still export within the 30-day window.

## D-27 · Ops: Supabase free + DB DR + dev seed
- **Status:** LOCKED. Supabase free accepted; nightly `pg_dump` → R2 india DR cron closes the no-PITR total-loss risk for ₹0. Dev seed (`seed_dev`) + mocked-provider cassette (`MOCK_AI=1`) so the local analyze→advice loop runs with no live Gemini key / Firebase token.

## D-28 · Timeline = 10–12 weeks
- **Status:** LOCKED. Founder has ample React Native experience; the 14–20wk first-timer swing + RN-spike pivot trigger are dropped.

## D-29 · Positioning guardrail (from accuracy reality)
- **Status:** LOCKED. Market "macro estimate / range", never "exact calories". The moat is budget-aware veg-protein-gap advice grounded in the user's own log, NOT photo accuracy — capped ~75% even for HealthifyMe Snap (GPT-4V + fine-tuned ensemble + humans-in-loop). The bigger strategic pivot (US South-Asian diaspora / GLP-1 adherence companion, B2B2C) is logged as an OPEN question for a separate conversation — NOT decided here.

## D-30 · INDB = seed, not drop-in (verified live 2026-06-02)
- **Status:** LOCKED (research-verified; agents downloaded + parsed the live INDB repo). INDB provides genuine dish-decomposition STRUCTURE (`recipes.xlsx`: 10,271 ingredient rows × 1,014 recipes — food_code + amount + unit) + per-100g & per-serving macros, covering ~43/50 of the whitelist at recipe-prior level. BUT: (a) grams are NOT stored — only ~46% of rows are already grams, the rest need the shipped `INDB.do` unit→g conversion (~45 rules); (b) the IFCT food table (NIN_fct) is NOT in the repo — request from ICMR-NIN; (c) NO weighed / image-linked truth; (d) one fixed oil amount per dish (no rich/plain variants); (e) macros are calculated sums with no cooking-yield correction and no lab validation; (f) ~4 genuine whitelist gaps (pani_puri, pongal_ven, bisi_bele_bath, litti).
- **Decision:** Use INDB as the SEED for `dish_decomposition.json` (run the gram-conversion, map ~43 dishes), LLM-decompose only the ~4 gaps, add a rich/plain oil-variant axis, and manufacture weighed-plate truth separately for the 30 Gate-0a photos. INDB is NOT the ±35% accuracy oracle — weighed plates are. Refines the earlier "INDB ingest = drop-in ground truth" framing in D-21/F-16.
- **Consequences:** Pile-1 is SCOPED but not "done" — it becomes Phase-1 execution work (TODOS-9). Confidence MEDIUM on the 86% coverage (name-level, not ±35%-validated).

## D-31 · IFCT/INDB commercial license gate (LAUNCH BLOCKER)
- **Status:** LOCKED (adversarially verified, HIGH confidence). IFCT 2017 is ICMR-NIN copyright: "no part can be stored or reproduced in any electronic format **for creating a product** without the prior written permission of the National Institute of Nutrition." Personal-use only; no commercial carve-out. The INDB GitHub repo has NO license (all rights reserved); the paper's CC BY covers only the manuscript, not the data. INDB embeds IFCT values, so the restriction reaches it.
- **Decision:** Before any IFCT/INDB-derived macro ships in the paid (₹299/mo) tier, obtain WRITTEN PERMISSION — email ICMR-NIN (nin@ap.nic.in / ifct2017@gmail.com) for commercial/product use of IFCT 2017, and Anuvaad (awasthi@anuvaad.org.in) to confirm INDB data license + request an explicit repo LICENSE. Track as a LAUNCH GATE (TODOS-10). Until granted, gate IFCT/INDB macros behind the free tier / a feature flag.
- **Consequences:** Contradicts (now-corrected) CLAUDE.md assumption that IFCT is a free drop-in. Adds a legal/permission step to the launch path. The "paid app = a product" reading is reasoned interpretation of NIN's wording, not a court ruling — but a written-permission step is unavoidable on any reading (NIN may grant free, as use is "encouraged").
