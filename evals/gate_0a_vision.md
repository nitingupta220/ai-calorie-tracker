# Gate 0a · Vision Benchmark Eval Harness Spec

Per AI-SPEC §5 + CONTEXT D-06..D-10.

This document specifies the eval harness. The actual Python script is built in Phase 2 Week 1; this spec exists so founder + downstream planner are aligned.

## What it tests

Whether **Gemini 2.5 Flash** can identify Indian meal dishes + portion accurately enough to ground the macros-via-IFCT-lookup pipeline (AI-SPEC §1 two-step contract).

## Inputs

1. `data/photos/<bucket>/*.jpg` — 30 founder-curated photos (10/10/10 single/mixed/thali per `data/photos/CURATION-CHECKLIST.md`)
2. `data/photos/<bucket>/labels_truth.csv` — founder-verified ground truth: `filename, dish_id, portion_g, notes`
3. `data/dish_decomposition.json` — 50-dish whitelist, ingredient breakdowns
4. `data/ifct_lookup.json` — raw-ingredient nutrition reference

## Outputs

1. `evals/gate_0a_results.md` — per-bucket scores + per-photo rows + pass/fail
2. `evals/gate_0a_run-YYYY-MM-DD.json` — machine-readable run record (Phoenix tracing attached)
3. `.planning/decisions/YYYY-MM-DD-gate-0a-{pass|fail}.md` — decision record

## Pipeline

```
photo (1280px JPEG)
  │
  ▼
Gemini 2.5 Flash via ai_provider.py
  │   prompt: "Identify the Indian dish(es) in this photo. Return JSON: {dishes: [{name: '<dish>', portion_g: <int>, confidence: <0-1>}]}"
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
truth_macros (same pipeline using labels_truth.csv dish_id + portion_g)
  │
  ▼
Per-photo scoring:
  - dish_correct: bool (predicted dish_id == truth dish_id) — or 1.0 if any predicted matches truth in multi-dish
  - portion_within_20pct: bool (|pred_portion - truth_portion| / truth_portion ≤ 0.20)
  - macros_within_35pct: bool (|pred_kcal - truth_kcal| / truth_kcal ≤ 0.35 for kcal AND protein)
  - confidence: float
```

## Per-bucket scoring

For each bucket (single, mixed, thali):
```
dish_accuracy        = sum(dish_correct) / 10
macros_within_35pct  = sum(macros_within_35pct) / 10
mean_confidence      = mean(confidence)
```

## Pass bar

Per bucket:
- `dish_accuracy ≥ 0.70`
- `macros_within_35pct ≥ 0.60`

**ALL three buckets** must pass independently. Aggregate cannot mask bucket failure.

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
- `arize-phoenix` (tracing per AI-SPEC §5 §7)

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
    """Run Gemini on one photo, score vs truth."""
    pred: MealVisionResult = await VisionProvider().classify_meal(path.read_bytes())
    # ... per-photo scoring per spec above
    return {...}

async def main():
    for bucket in ['single', 'mixed', 'thali']:
        truth = pd.read_csv(f'data/photos/{bucket}/labels_truth.csv')
        results = await asyncio.gather(*[
            score_photo(Path(f'data/photos/{bucket}/{r.filename}'), r)
            for r in truth.itertuples()
        ])
        # compute per-bucket scores, append to gate_0a_results.md

if __name__ == '__main__':
    asyncio.run(main())
```

## Founder-side runbook

1. Photos curated + `labels_truth.csv` written → see `data/photos/CURATION-CHECKLIST.md`
2. Acquire Gemini 2.5 Flash API key:
   - Visit https://aistudio.google.com → sign in with Google account → API keys → Create key (free tier, no CC required, 10 RPM / 250K TPM / 500 RPD)
   - Set env: `export GOOGLE_AI_STUDIO_API_KEY=<key>` (also `GEMINI_API_KEY` for SDK compatibility)
3. Phase 2 Week 1 implements `evals/gate_0a_vision.py` per skeleton above
4. Run: `python -m evals.gate_0a_vision` → outputs `evals/gate_0a_results.md` + JSON
5. Founder + Phase 2 planner review results → pass/fail decision → write `.planning/decisions/<date>-gate-0a-{pass|fail}.md`

## Failure modes

| Failure | Likely cause | Remediation |
|---------|--------------|-------------|
| Single bucket < 70% dish | Generic Gemini prompt; doesn't know Indian context | Add few-shot examples to prompt (5 dishes from each bucket); rerun |
| Mixed bucket < 70% dish | Gemini conflates multi-item plates | Switch to 2-step prompt (detect dishes → identify each); add bounding-box requirement |
| Thali bucket < 70% dish | Thali decomposition fails | Add explicit "thali handling" branch in prompt; render confidence-gate UX in product |
| Any bucket < 60% macros within ±35% (despite ≥70% dish) | Portion estimation is the bottleneck | Reference-object detection (₹ coin / palm) required; tighten dish_decomposition serving sizes |
| Off-whitelist > 5 of 30 photos | Whitelist too narrow | V1.5 expansion required; OR confidence-low UX path on by default |

## Cost estimate

30 photos × Gemini 2.5 Flash vision call ~₹0.08 paid (~₹2.40 if exhausting free tier). Within Phase 0-1 budget (~₹0-200) per PROJECT.md.

If using free tier: 30 photos = 6 minutes wall clock at 10 RPM cap. Trivial.

## Phase 0-1 schedule

| Day | Task | Owner |
|-----|------|-------|
| 1 | Acquire Gemini key | founder |
| 1-3 | Photo curation (10/10/10 stratified) | founder |
| 3 | Founder verifies Opus labels against truth | founder + Opus |
| 4 | Phase 2 Week 1 implements `gate_0a_vision.py` | Phase 2 planner |
| 5 | Eval run + scoring | automated + founder |
| 5 | Pass/fail decision documented in `.planning/decisions/` | founder |

Total wall clock: ~5 days. Founder time: ~5-7 hours (per CONTEXT D-08).

## Reviewer concerns (carried forward)

- **D-10 circular bias:** Opus 4.7 labels ground truth for Gemini 2.5 Flash. Different model families + deterministic IFCT macros + manual verification mitigate. RD audit budget (₹1,500-3,000) reserved as V1.5 trigger if Phase 6 alpha real-user accuracy drops below 75%.
- **Off-whitelist coverage cliff:** by design 3+ photos test this. Score interpretation requires looking at off-whitelist count + handling, not just bucket pass/fail.
- **Lighting variance:** founder must include 2 dim/fluorescent photos per bucket. If those fail disproportionately, image preprocessing (auto-brightness) becomes Phase 2 work.
