# Gate 0a · Photo Curation Brief

**Founder task.** Cannot delegate. ~2 hours over 3-5 days.

## Goal

Produce 30 real meal photos that test Gemini 2.5 Flash vision accuracy across the messy reality of Indian meals.

## Bucket targets (stratified, NOT mixed)

| Bucket | Count | What it tests |
|--------|------:|---------------|
| Single dish | 10 | "1 thing on the plate" — paneer butter masala in a katori, dosa solo, 2 boiled eggs. Tests dish-name accuracy. |
| Mixed (2-3 items) | 10 | "Dal + rice + sabzi" — multi-item plate but not a thali. Tests dish-separation + portion. |
| Thali | 10 | Full thali — 4-7 items, all visible. Tests confidence-gate UX and multi-dish decomposition. |

Per-bucket pass bar: **≥70% dish-name + ≥60% macros within ±35%** (AI-SPEC §5).
Aggregate pass cannot mask thali-bucket failure.

## Capture rules

- **Use the actual phone you ship with** (Android, ~₹15-30k price band — Redmi / Samsung A-series / Pixel a)
- **Vary lighting:** 3 daylight, 3 indoor warm, 2 mixed dim, 2 fluorescent canteen-style per bucket
- **Vary plate:** 5 steel thali, 3 ceramic plate, 2 banana leaf or paper plate per bucket (south + east bias OK)
- **Include reference object in 5 photos** (₹10 coin OR a palm next to plate) — tests reference-object portion accuracy
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

For each photo, founder fills in `data/photos/<bucket>/labels.csv`:

```csv
filename,dish_id,portion_g,notes
01-paneer-butter-masala-katori-daylight.jpg,paneer_butter_masala,150,1 katori standard
02-boiled-eggs-2-indoor-warm.jpg,boiled_eggs_2,100,2 medium eggs ~50g each
...
```

`dish_id` MUST match keys in `data/dish_decomposition.json` (or be `__off_whitelist__:<free-text>` for the 3+ off-whitelist photos).
`portion_g` = founder's best estimate vs the standard serving in `dish_decomposition.json`.
`notes` = anything ambiguous about the photo for the labeling pass.

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

## Pass bar (locked)

| Metric | Pan | North | South | West/East | Aggregate |
|--------|-----|-------|-------|-----------|----------|
| Dish-name ≥70% | ✓ | ✓ | ✓ | ✓ | n/a (per-bucket) |
| Macros within ±35% ≥60% | ✓ | ✓ | ✓ | ✓ | n/a (per-bucket) |

**Note:** The bucket dimension above is mis-stated — the actual buckets are single/mixed/thali (capture format), not regional cuisine. Pan/N/S/W-E are cuisine diversity within the 30 photos. Per-bucket pass bar applies to single/mixed/thali. Regional diversity is a quality check on the photo set, not a separate pass metric.

## Fail criteria

If any of single/mixed/thali bucket fails ≥70% dish or ≥60% macros, Gate 0a does NOT pass.
- Single failing → likely Gemini prompt issue or off-whitelist dishes — adjust prompt, expand whitelist, retry
- Mixed failing → dish-separation issue — may need 2-step prompt (identify dishes first, then per-dish portion)
- Thali failing → confidence-gate UX must front-load this (user prompted "thali detected — confirm 4 dishes?")

If 2+ buckets fail, escalate to founder + reviewer for design call: shrink scope to single-dish only V1, or invest in fine-tuning Gemini.

## Output

Gate 0a passes when:
- [ ] 30 photos shot, 10/10/10 stratified
- [ ] `labels_truth.csv` complete (founder-verified ground truth)
- [ ] Gemini run on all 30 photos → `labels_gemini.csv`
- [ ] Per-bucket scores computed in `evals/gate_0a_results.md`
- [ ] All three buckets pass ≥70% dish + ≥60% macros within ±35%
- [ ] Pass result documented in `.planning/decisions/2026-MM-DD-gate-0a-pass.md`

If any bucket fails, document failure cause + remediation plan in `.planning/decisions/2026-MM-DD-gate-0a-fail.md`.
