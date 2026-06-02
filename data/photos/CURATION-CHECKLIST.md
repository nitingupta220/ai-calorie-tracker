# Gate 0a · Photo Curation Brief

**Founder task.** Cannot delegate. ~4–6 hours over 3-5 days (photo curation + **weighing each plate on a kitchen scale**).

> **RECALIBRATED 2026-06-02:** Ground truth is now **weighed** (kitchen scale), not eyeballed. A **reference object** (₹ coin / palm) is **mandatory** in every single-dish + mixed photo. The gate scores **dish-ID (≥80%) and macro-accuracy separately**, and the **thali bucket is reported-only / non-blocking** (re-introduced in V1.5). See `evals/gate_0a_vision.md` + PITFALLS V-01..V-06.

## Goal

Produce 30 real meal photos that test Gemini 2.5 Flash vision accuracy across the messy reality of Indian meals.

## Bucket targets (stratified, NOT mixed)

| Bucket | Count | What it tests |
|--------|------:|---------------|
| Single dish | 10 | "1 thing on the plate" — paneer butter masala in a katori, dosa solo, 2 boiled eggs. Tests dish-name accuracy. |
| Mixed (2-3 items) | 10 | "Dal + rice + sabzi" — multi-item plate but not a thali. Tests dish-separation + portion. |
| Thali | 10 | Full thali — 4-7 items, all visible. Tests confidence-gate UX and multi-dish decomposition. |

Per-bucket pass bar (weighed truth, recalibrated 2026-06-02): **dish-ID ≥80%** AND **macros within ±35%** (≥70% single / ≥60% mixed). **Thali = reported-only / non-blocking** (V1.5 re-intro). Report median + P75/P90 macro tail. (AI-SPEC §5.)

## Capture rules

- **Use the actual phone you ship with** (Android, ~₹15-30k price band — Redmi / Samsung A-series / Pixel a)
- **Vary lighting:** 3 daylight, 3 indoor warm, 2 mixed dim, 2 fluorescent canteen-style per bucket
- **Vary plate:** 5 steel thali, 3 ceramic plate, 2 banana leaf or paper plate per bucket (south + east bias OK)
- **Reference object MANDATORY in every single-dish + mixed photo** (₹10 coin OR palm next to plate) — the scale prior for portion estimation (the gate scores the reference-present arm; the no-reference arm is reported separately). Thali: include where natural.
- **DO NOT stage perfect photos.** Bhog is for messy real life. Half-eaten OK. Spilled ghee OK. Hand visible at corner OK.
- **DO NOT use studio shots, food blogs, or Instagram-pretty photos.** Real users won't shoot like that.

## Diversity hard requirements

- **At least 6 cuisines:** North (paneer/dal/roti), South (dosa/idli/sambar), West (poha/dhokla/thepla), East (litti/fish), Pan (chai/curd/banana), Maharashtrian street (misal/vada-pav)
- **At least 2 non-veg photos** (chicken curry, eggs, or fish) — even though V1 persona is veg-default, non-veg coverage matters for Eggetarian/NV diet users
- **At least 3 photos with off-whitelist dishes** (not in the 50-dish list) — tests Gemini's "unknown dish" handling + confidence-low UX path

## Off-whitelist suggestions

If you eat any of these during Week 0, photograph them — they're outside the locked 50 and test the coverage cliff:
- Hyderabadi biryani · Goan fish curry · Bengali macher jhol · Kerala puttu · Kashmiri rajma · Sindhi kadhi · Chettinad pepper chicken

## Storage

Save to `data/photos/`:

```
data/photos/
  ├── single/
  │   ├── 01-paneer-butter-masala-katori-daylight.jpg
  │   ├── 02-boiled-eggs-2-indoor-warm.jpg
  │   └── ...
  ├── mixed/
  │   ├── 01-dal-rice-sabzi-thali-corner-coin.jpg
  │   └── ...
  └── thali/
      ├── 01-south-thali-banana-leaf-daylight.jpg
      └── ...
```

Filename convention: `NN-<dish-or-bucket-shorthand>-<lighting>-<note>.jpg`.

Use `expo-image-manipulator` settings for the final test set:
- Resize: longest edge ≤1280px
- Format: JPEG quality 0.7
- Strip EXIF (Pillow server-side, but document GPS removal for QA)

Founder may shoot raw HEIC; CONVERT to JPEG via `expo-image-manipulator` before pushing to `data/photos/`. Backend will reject HEIC per CLAUDE.md anti-pattern #5.

## Ground-truth labels

For each photo, founder fills in `data/photos/<bucket>/labels_truth.csv` with **WEIGHED** grams:

```csv
filename,dish_id,weighed_total_g,component_weights_g,has_reference_object,notes
01-paneer-butter-masala-katori-daylight.jpg,paneer_butter_masala,158,"{""paneer_butter_masala"":158}",true,weighed on kitchen scale
01-dal-rice-sabzi-coin.jpg,dal_tadka;rice;aloo_sabzi,,"{""dal_tadka"":150,""rice"":120,""aloo_sabzi"":90}",true,each katori weighed separately
...
```

`dish_id` MUST match keys in `data/dish_decomposition.json` (or `__off_whitelist__:<free-text>` for the 3+ off-whitelist photos).
`weighed_total_g` / `component_weights_g` = **measured on a kitchen scale (0.1–1 g)**, NOT eyeballed. For mixed/thali, weigh each katori/item separately. This is the change that converts the gate from "agreement between two guesses" into "accuracy vs measured truth" (PITFALLS V-06).
`has_reference_object` = `true` for all single + mixed (mandatory).
`notes` = anything ambiguous for the labeling pass.

**Before labeling:** verify `data/dish_decomposition.json` rows against **INDB (Indian Nutrient Databank) recipe grams + IFCT 2017**, and set `verified_by` (no longer `null`).

## Labeling pass

**Step 1.** Opus 4.7 (me) labels each photo from `<filename>` → predicts `{dish_id, portion_g}` blind (no ground truth). I emit a `labels_opus.csv`.

**Step 2.** Founder reviews `labels_opus.csv` against truth. For every row:
- If Opus matched truth → mark `correct=Y`
- If Opus dish_id wrong → mark `correct=N` + add `correction` column with the right dish_id
- If Opus portion off by >20% → mark `portion_correct=N` + add corrected value

**Step 3.** Lock ground truth: `labels_truth.csv` = founder-verified rows used by eval harness.

## Gemini test pass

**Step 4.** Once OpenAI/Gemini key available (see `evals/gate_0a_vision.md`), run all 30 photos through Gemini 2.5 Flash via the vision-pipeline skeleton in AI-SPEC §3-§4. Gemini emits `{dish_name, portion_g, confidence}`.

**Step 5.** Score Gemini output vs `labels_truth.csv`:
- Per-bucket dish-name accuracy = correct dish_id matches / 10 per bucket
- Per-bucket macros accuracy = % of photos where derived macros (via IFCT lookup) fall within ±35% of truth-derived macros
- Aggregate must NOT mask any bucket failing the bar

## Pass bar (recalibrated 2026-06-02)

Two **independent** per-bucket metrics, scored against **weighed** truth on the **reference-present** arm:

| Bucket | Blocking? | dish-ID | macros within ±35% |
|--------|-----------|---------|--------------------|
| single | **YES** | ≥80% | ≥70% |
| mixed  | **YES** | ≥80% | ≥60% |
| thali  | NO — reported-only | report | report (pass bar → V1.5) |

- A blocking bucket passes only if **BOTH** bars clear. Never let dish-ID average up macros (PITFALLS V-01).
- **Thali does NOT block launch** — ships as a "snap each item / tap to confirm" UX; pass bar deferred to V1.5 (PITFALLS V-05).
- Always report `macro_err` **median + P75/P90** per bucket so the hidden-oil / portion tail is visible (PITFALLS V-02, V-03), not hidden behind a within-tolerance pass rate.
- The **no-reference arm is reported separately**; if it fails while reference-present passes → reference object becomes a hard product rule for the first N logs / any auto-macro render.
- Regional diversity (Pan / N / S / W-E) is a quality check on the photo set, not a separate pass metric.

## Fail criteria

If **single OR mixed** fails its dish-ID or macro bar, Gate 0a does NOT pass.
- Single failing → Gemini prompt / off-whitelist / portion — add few-shot, confirm reference object is detected, tighten decomposition serving sizes.
- Mixed failing → dish-separation — 2-step prompt (identify dishes → per-dish portion).
- Thali → **reported-only**; 40–60% macro error is expected (multi-item compounding, PITFALLS V-05) — ship the confidence-gate UX, no launch block.

If **single AND mixed both fail**, escalate to founder + reviewer: shrink scope to single-dish-only V1, or invest in better portion priors (INDB) / fine-tuning.

## Output

Gate 0a passes when:
- [ ] 30 photos shot, 10/10/10 stratified, **reference object in all single + mixed**
- [ ] **Each plate WEIGHED on a kitchen scale**; `labels_truth.csv` complete with weighed grams
- [ ] `dish_decomposition.json` rows verified vs **INDB + IFCT** (`verified_by` set, not null)
- [ ] Gemini run on all 30 photos → `labels_gemini.csv`
- [ ] Per-bucket **dish-ID + macro** scores + **median / P75 / P90** in `evals/gate_0a_results.md`
- [ ] **single + mixed pass** (dish-ID ≥80%; macros ≥70% single / ≥60% mixed); **thali reported**
- [ ] Pass result documented in `.planning/decisions/2026-MM-DD-gate-0a-pass.md`

If single/mixed fails, document cause + remediation plan in `.planning/decisions/2026-MM-DD-gate-0a-fail.md`.
