# Gate 0a · Vision Benchmark Eval Harness Spec

Per AI-SPEC §5 + CONTEXT D-06..D-10.

> **RECALIBRATED 2026-06-02 (founder ruling, see `.planning/decisions/` + PITFALLS V-01..V-06).** The external-review audit found the original bar measured *agreement between two estimates* (Gemini's macros vs the founder's **eyeballed** portions through an unverified table), not accuracy. Four changes are now baked in below: (1) **weighed ground truth** — plates are weighed on a kitchen scale, not eyeballed; (2) **dish-ID and macro accuracy scored separately**, dish-ID raised to ≥0.80 (recognition is the easy ~20%); (3) **thali bucket is reported-only / non-blocking** (re-introduced as a pass bucket in V1.5); (4) **reference object mandatory** in single + mixed photos, scored as the gated arm. The decomposition table is seeded/verified against **INDB (Indian Nutrient Databank) + IFCT 2017** before the run.

This document specifies the eval harness. The actual Python script is built in Phase 2 Week 1; this spec exists so founder + downstream planner are aligned.

## What it tests

Whether **Gemini 2.5 Flash** can identify Indian meal dishes + portion accurately enough to ground the macros-via-IFCT-lookup pipeline (AI-SPEC §1 two-step contract). Recognition and portion→macro accuracy are tested as **independent** metrics — naming the dish right says little about whether the calories are right (PITFALLS V-01; GPT-4V got 93% dish-ID but 11/16 nutrients significantly wrong).

## Inputs

1. `data/photos/<bucket>/*.jpg` — 30 founder-curated photos (10/10/10 single/mixed/thali per `data/photos/CURATION-CHECKLIST.md`). Single + mixed photos **must contain a reference object** (₹ coin / palm / standard plate) in frame.
2. `data/photos/<bucket>/labels_truth.csv` — founder-verified **WEIGHED** ground truth: `filename, dish_id, weighed_total_g, component_weights_g (json), has_reference_object (bool), notes`. Grams come from a **kitchen scale** (0.1–1 g resolution), not eyeball estimation. For mixed/thali, each component/katori is weighed separately.
3. `data/dish_decomposition.json` — 50-dish whitelist, ingredient breakdowns. **Seeded + verified against INDB recipe gram-amounts + IFCT 2017 before the run** (`verified_by` must be set, not null).
4. `data/ifct_lookup.json` — raw-ingredient nutrition reference.
5. `data/indb/` — Indian Nutrient Databank recipe gram-amounts + per-serving macros (ingested alongside IFCT to seed portion priors; see TODOS / data layer).

## Outputs

1. `evals/gate_0a_results.md` — per-bucket scores (dish-ID + macro, separate) + median/P75/P90 macro error + per-photo rows + pass/fail
2. `evals/gate_0a_run-YYYY-MM-DD.json` — machine-readable run record (persisted to the Postgres `ai_call_log` ledger; local-dev Phoenix trace optional)
3. `.planning/decisions/YYYY-MM-DD-gate-0a-{pass|fail}.md` — decision record

## Pipeline

```
photo (1280px JPEG, reference object in frame for single+mixed)
  │
  ▼
Gemini 2.5 Flash via ai_provider.py
  │   prompt: "Identify the Indian dish(es) in this photo. Use the reference object
  │            (coin/palm/plate) to estimate portion. Return JSON:
  │            {dishes: [{name: '<dish>', portion_g: <int>, confidence: <0-1>}]}"
  │   structured output enforced via Pydantic v2 schema (AI-SPEC §4b)
  ▼
Pydantic-validated response → MealVisionResult
  │
  ▼
For each dish:
  dish_id = match against dish_decomposition.json (fuzzy match → strict id)
  if no match → flag as off-whitelist
  ingredients = dish_decomposition[dish_id].ingredients × (portion_g / standard_g)
  macros = sum(ifct_lookup[ing.ifct_id].{kcal,p,c,f} × ing.g / 100) for each ingredient
  │
  ▼
predicted_macros
  vs
truth_macros (WEIGHED grams from labels_truth.csv through the verified decomposition table)
  │
  ▼
Per-photo scoring (dish-ID and macro tracked SEPARATELY):
  - dish_correct: bool (predicted dish_id == truth dish_id) — or 1.0 if any predicted matches truth in multi-dish
  - portion_within_20pct: bool (|pred_portion - weighed_portion| / weighed_portion ≤ 0.20)
  - macros_within_35pct: bool (|pred_kcal - truth_kcal| / truth_kcal ≤ 0.35 for kcal AND protein)
  - macro_abs_pct_error: float (for median + P75/P90 tail reporting)
  - has_reference_object: bool (split scoring into reference-present vs no-reference arms)
  - confidence: float
```

## Per-bucket scoring

For each bucket (single, mixed, thali), report dish-ID and macro accuracy **separately**, plus the tail:
```
dish_accuracy           = sum(dish_correct) / n
macros_within_35pct     = sum(macros_within_35pct) / n          # binding bar
portion_within_20pct    = sum(portion_within_20pct) / n         # diagnostic sub-metric
macro_err_median        = median(macro_abs_pct_error)           # tail visibility
macro_err_p75 / p90     = percentile(macro_abs_pct_error, 75/90)
mean_confidence         = mean(confidence)
# all of the above also computed for the reference-object-PRESENT subset
```
Never let a strong `dish_accuracy` average up a weak `macros_within_35pct` — they are independent gates.

## Pass bar (recalibrated 2026-06-02)

Truth is **weighed**, and dish-ID / macro are **separate** per-bucket gates:

| Bucket | Blocking? | dish_accuracy | macros_within_35pct (reference-present arm) |
|---|---|---|---|
| **single** | YES (launch-blocking) | ≥ 0.80 | ≥ 0.70 |
| **mixed** | YES (launch-blocking) | ≥ 0.80 | ≥ 0.60 |
| **thali** | NO — **reported-only diagnostic** | report | report (pass bar deferred to V1.5) |

- A blocking bucket passes only if **BOTH** dish-ID and macro bars clear (on the reference-present arm).
- **Thali does NOT block launch.** It ships as a confidence-gated "snap each item separately / tap to confirm" UX (PITFALLS V-05); a thali pass bar is re-introduced in V1.5 once multi-item handling is built.
- The no-reference arm is **reported separately**. If reference-present clears but no-reference doesn't, that becomes a hard product rule: reference object required for the first N logs / for any auto-macro render.
- Always report `macro_err_median` + P75/P90 per bucket so the heavy-tadka / hidden-oil tail (PITFALLS V-02, V-03) is visible, not hidden behind a within-tolerance pass rate.

## Off-whitelist handling

For each photo where Gemini returns a dish_id NOT in `dish_decomposition.json`:
- Score `dish_correct = 0.5` (partial credit — Gemini got SOMETHING, but our table doesn't cover it)
- Score `macros_within_35pct = 0` (can't compute deterministic macros for unknown dish)
- Flag for V1.5 whitelist expansion: log to `evals/gate_0a_off_whitelist.csv`

This is the **coverage cliff** per `/plan-eng-review` Finding #10 + TODOS-6. Acceptable as long as ≥3 off-whitelist photos in test set (per CURATION-CHECKLIST.md diversity rule) keep aggregate scores honest.

## Implementation (Phase 2 Week 1 deliverable)

Script: `evals/gate_0a_vision.py`

Dependencies (per AI-SPEC §5 install block):
- `google-genai` (Gemini SDK)
- `pydantic ≥ 2.x`
- `pandas` (CSV io + table outputs)
- `pillow` (image resize verify, EXIF strip)
- `arize-phoenix` — **local-dev trace inspection only**; production cost/eval spine is the Postgres `ai_call_log` ledger (AI-SPEC §5/§7, D-01 Render-compatible). Not a prod dependency.

Skeleton:
```python
# evals/gate_0a_vision.py
import asyncio
import json
import pandas as pd
from pathlib import Path
from pydantic import BaseModel
from server.app.providers.ai_provider import VisionProvider  # ai_provider.py
from server.app.schemas.vision import MealVisionResult       # Pydantic schema

DECOMP = json.loads(Path('data/dish_decomposition.json').read_text())
IFCT = json.loads(Path('data/ifct_lookup.json').read_text())

def derive_macros(dish_id: str, portion_g: int) -> dict:
    """Deterministic macros from decomp + IFCT. NEVER LLM math."""
    dish = DECOMP['dishes'][dish_id]
    standard_g = parse_serving_g(dish['serving_label'])  # extract grams from label
    scale = portion_g / standard_g
    totals = {'kcal': 0, 'p': 0, 'c': 0, 'f': 0}
    for ing in dish['ingredients']:
        if ing.get('_unit') == 'eggs':
            for k in totals: totals[k] += IFCT['ingredients'][ing['ifct_id']][k] * ing['g'] * scale
        else:
            for k in totals: totals[k] += IFCT['ingredients'][ing['ifct_id']][k] * ing['g'] * scale / 100
    return totals

async def score_photo(path: Path, truth_row: pd.Series) -> dict:
    """Run Gemini on one photo, score dish-ID and macro accuracy separately vs WEIGHED truth."""
    pred: MealVisionResult = await VisionProvider().classify_meal(path.read_bytes())
    # ... per-photo scoring per spec above; truth macros use weighed grams
    return {...}

async def main():
    for bucket in ['single', 'mixed', 'thali']:
        truth = pd.read_csv(f'data/photos/{bucket}/labels_truth.csv')
        results = await asyncio.gather(*[
            score_photo(Path(f'data/photos/{bucket}/{r.filename}'), r)
            for r in truth.itertuples()
        ])
        # compute per-bucket dish-ID + macro scores + median/P75/P90 + reference-arm split
        # single + mixed are blocking; thali is reported-only
```

## Founder-side runbook

1. Photos curated **with reference object in single+mixed**, plates **weighed on a kitchen scale**, `labels_truth.csv` written with weighed grams → see `data/photos/CURATION-CHECKLIST.md`
2. Acquire Gemini 2.5 Flash API key:
   - Visit https://aistudio.google.com → sign in with Google account → API keys → Create key (free tier, no CC required, 10 RPM / 250K TPM / 500 RPD)
   - Set env: `export GOOGLE_AI_STUDIO_API_KEY=<key>` (also `GEMINI_API_KEY` for SDK compatibility)
3. Verify `dish_decomposition.json` rows against **INDB recipe grams + IFCT** before the run (`verified_by` set, not null)
4. Phase 2 Week 1 implements `evals/gate_0a_vision.py` per skeleton above
5. Run: `python -m evals.gate_0a_vision` → outputs `evals/gate_0a_results.md` + JSON
6. Founder + Phase 2 planner review results (single + mixed pass/fail; thali diagnostic) → write `.planning/decisions/<date>-gate-0a-{pass|fail}.md`

## Failure modes

| Failure | Likely cause | Remediation |
|---------|--------------|-------------|
| Single bucket < 0.80 dish | Generic Gemini prompt; doesn't know Indian context | Add few-shot examples to prompt (5 dishes from each bucket); rerun |
| Mixed bucket < 0.80 dish | Gemini conflates multi-item plates | Switch to 2-step prompt (detect dishes → identify each); add bounding-box requirement |
| Single/mixed < macro bar despite dish-ID ≥0.80 | Portion estimation is the bottleneck (PITFALLS V-02) | Reference object already mandatory — check it's in frame + detected; tighten dish_decomposition serving sizes; add per-dish rich/plain variant for hidden fat (V-03) |
| High P90 macro error on fat-heavy curries | Hidden oil/ghee invisible (PITFALLS V-03) | dal_plain / dal_tadka / dal_restaurant variants + one-tap user selector; report these rows separately |
| Reference-present arm passes, no-reference arm fails | Portion ill-posed without scale prior | Hard product rule: reference object required for first N logs / auto-macro render |
| Thali macro error 40–60% | Multi-item compounding (V-05) | Expected — thali is reported-only; ship "snap each item" UX; no launch block |
| Off-whitelist > 5 of 30 photos | Whitelist too narrow | V1.5 expansion required; OR confidence-low UX path on by default |

## Cost estimate

30 photos × Gemini 2.5 Flash vision call ~₹0.08 paid (~₹2.40 if exhausting free tier). Within Phase 0-1 budget (~₹0-200) per PROJECT.md.

If using free tier: 30 photos = 6 minutes wall clock at 10 RPM cap. Trivial.

## Phase 0-1 schedule

| Day | Task | Owner |
|-----|------|-------|
| 1 | Acquire Gemini key | founder |
| 1-3 | Photo curation (10/10/10 stratified) **+ weigh each plate on kitchen scale + reference object in single/mixed** | founder |
| 3 | Ingest INDB; verify `dish_decomposition.json` rows vs INDB+IFCT (`verified_by` set) | founder + Opus |
| 4 | Phase 2 Week 1 implements `gate_0a_vision.py` | Phase 2 planner |
| 5 | Eval run + scoring (dish-ID + macro separate; thali diagnostic) | automated + founder |
| 5 | Pass/fail decision documented in `.planning/decisions/` | founder |

Total wall clock: ~5 days. Founder time: ~7–11 hours (≈5–7h curation/verify per CONTEXT D-08 + ~2–4h weighing per the 2026-06-02 recalibration). One ~₹500–800 kitchen scale (0.1–1 g).

## Reviewer concerns (carried forward)

- **D-10 circular bias (labels):** Opus 4.7 labels dish names for Gemini 2.5 Flash. Different model families + deterministic IFCT macros + manual verification mitigate. RD audit (₹1,500-3,000) reserved as a **non-blocking V1.5 trigger** if alpha real-user accuracy drops below 75% (per CONTEXT/D-10 — does NOT gate Gate 0a).
- **Circular bias (PORTIONS) — addressed by recalibration:** the original gate compared Gemini's portions against the founder's *eyeballed* portions through an unverified table (PITFALLS V-06). Now mitigated by **weighed** ground truth + decomposition rows verified against INDB+IFCT. Until weighing is done, a pass is not evidence of field accuracy.
- **Accuracy ceiling:** image-only calorie error floors at ~26% (Nutrition5k, CVPR 2021); ±35% is generous on the mean but the tail exceeds it — hence median + P75/P90 reporting and the reference-object requirement.
- **Off-whitelist coverage cliff:** by design 3+ photos test this. Score interpretation requires looking at off-whitelist count + handling, not just bucket pass/fail.
- **Lighting variance:** founder must include 2 dim/fluorescent photos per bucket. If those fail disproportionately, image preprocessing (auto-brightness) becomes Phase 2 work.
