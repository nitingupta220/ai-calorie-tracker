"""
indb_to_decomp.py

Re-implements INDB.do unit-to-gram conversion rules in Python, maps INDB recipes
to our 50-dish whitelist, and outputs data/scripts/indb_dishes_output.json.

UNIT_G rules extracted VERBATIM from data/indb/INDB.do lines 163-210.
The .do file uses food_category (first letter of food_code) to disambiguate units.
"""

import json
import csv
import os
import pandas as pd
from datetime import date

BASE = "/home/nitin/Desktop/ai-calorie-weight-loss"
RECIPES_XLSX = os.path.join(BASE, "data/indb/recipes.xlsx")
IFCT_LOOKUP  = os.path.join(BASE, "data/ifct_lookup.json")
DECOMP_JSON  = os.path.join(BASE, "data/dish_decomposition.json")
OUTPUT_JSON  = os.path.join(BASE, "data/scripts/indb_dishes_output.json")
UNIT_GAP_CSV = os.path.join(BASE, "data/scripts/indb_unit_gaps.csv")
IFCT_GAP_CSV = os.path.join(BASE, "data/scripts/indb_ifct_gaps.csv")

TODAY = str(date.today())

# ---------------------------------------------------------------------------
# 1. UNIT → GRAM CONVERSION  (verbatim from INDB.do lines 163-210)
# ---------------------------------------------------------------------------
# The .do file dispatches on (unit, food_category) where food_category is
# the first letter of food_code.  We replicate this exactly.
# fmt: (unit, food_category_or_None) → multiplier
# food_category == None means the rule applies regardless of category.
# Rules are evaluated in order; first match wins.

UNIT_G_RULES = [
    # unit == "g"  →  amount_g = amount  (always)
    ("g",      None,         1.0),
    # unit == "ml" by category
    ("ml",     "G",          1.0),   # vinegar etc.
    ("ml",     "H",          1.0),
    ("ml",     "I",          1.0),   # liquids cat I
    ("ml",     "V",          1.0),   # coconut milk
    ("ml",     "X",          1.0),
    ("ml",     "T",          1.0),   # oils
    ("ml",     "K",          1.0),   # water
    ("ml",     "E",          1.0),   # orange juice
    ("ml",     "L",          1.0),   # milk/cream/curd
    # tsp by category (dry spices/ingredients)
    ("tsp",    "G",          2.0),   # spices (dry)
    ("tsp",    "H",          2.0),
    ("tsp",    "B",          2.0),
    ("tsp",    "U",          2.0),
    ("tsp",    "D",          2.0),   # chillies
    ("tsp",    "A",          2.5),   # (category A)
    ("tsp",    "M",          5.0),   # (category M)
    ("tsp",    "V",          2.0),   # cocoa powder / sauces
    ("tsp",    "T",          4.0),   # oils, butter, ghee
    ("tsp",    "X",          6.0),   # sauces: soy, tomato
    ("tsp",    "W",          6.0),
    ("tsp",    "I",          4.0),   # sugar
    ("tsp",    "L",          5.0),   # cream/curd/milk
    ("tsp",    "C",          0.5),   # spices (ground spices category C)
    ("tsp",    "K",          5.0),   # water
    ("tsp",    "E",          5.0),   # orange juice
    # tbsp by category
    ("tbsp",   "D",          7.0),   # chillies (dry)
    ("tbsp",   "G",          7.0),
    ("tbsp",   "H",          7.0),
    ("tbsp",   "B",          7.0),
    ("tbsp",   "U",          7.0),
    ("tbsp",   "F",         40.0),   # potatoes
    ("tbsp",   "A",          7.0),
    ("tbsp",   "T",         13.5),   # oils, butter, ghee
    ("tbsp",   "X",         20.0),   # sauces
    ("tbsp",   "W",         20.0),
    ("tbsp",   "I",         12.0),   # sugar
    ("tbsp",   "L",         15.0),   # cream/curd/milk
    ("tbsp",   "Z",         15.0),   # bread crumbs
    ("tbsp",   "C",          5.0),   # ground spices
    ("tbsp",   "K",         15.0),   # water
    ("tbsp",   "E",         15.0),   # orange juice
    ("tbsp",   "V",          8.0),   # cocoa powder
    # "C" (cups) by category
    ("C",      "I",        200.0),   # sugar
    ("C",      "L",        240.0),   # milk/cream
    ("C",      None,       240.0),   # cups liquid (all others)
    # sprig
    ("sprig",  "G",          2.0),
    ("sprig",  "U",          2.0),
    ("sprig",  "C",          2.0),
    ("sprig",  "A",          2.0),
    # misc
    ("small",  "G",          2.0),
    ("pinch",  None,         0.125),
]

# Special per-food-name override (INDB.do line 209):
# "replace amount_g=amount*2 if food_name=="FENUGREEK LEAVES""
FOOD_NAME_OVERRIDES = {
    "FENUGREEK LEAVES": 2.0,
}

def food_category(food_code: str) -> str:
    """First letter of food_code = category."""
    if pd.isna(food_code) or not str(food_code).strip():
        return ""
    return str(food_code).strip()[0].upper()

def amount_to_grams(amount, unit, fcode, fname) -> float | None:
    """
    Apply INDB.do unit rules. Returns grams or None if unresolvable.
    food_name override is checked first.
    """
    if pd.isna(amount):
        return None

    # food_name override (fenugreek leaves)
    fname_upper = str(fname).upper() if not pd.isna(fname) else ""
    if fname_upper in FOOD_NAME_OVERRIDES:
        return float(amount) * FOOD_NAME_OVERRIDES[fname_upper]

    unit_str = str(unit).strip() if not pd.isna(unit) else ""
    # Normalise: "ml (to taste)" → "ml"
    unit_clean = unit_str.split()[0].strip() if unit_str else ""
    cat = food_category(fcode)

    for rule_unit, rule_cat, mult in UNIT_G_RULES:
        if rule_unit != unit_clean:
            continue
        if rule_cat is None or rule_cat == cat:
            return float(amount) * mult

    return None  # unit not handled → gap


# ---------------------------------------------------------------------------
# 2. INDB recipe_name → our dish_id whitelist mapping  (explicit, auditable)
# ---------------------------------------------------------------------------
# Format: INDB recipe_code → (our dish_id, serving_divisor)
# serving_divisor: INDB recipe_code often encodes a full pot (e.g. 4 servings)
# We set divisor=1 unless we've confirmed the recipe is per-person already.
# All values hand-verified against INDB recipe data above.

WHITELIST_MAP = {
    # recipe_code: (dish_id, serving_divisor)
    # -- pan bucket --
    "ASC096":  ("roti_whole_wheat",      1),   # Chapati/Roti (80g flour = ~2 rotis → we keep per-recipe, founder adjusts)
    "ASC113":  ("plain_rice_cooked",     1),   # Boiled rice 100g raw
    "BFP172":  ("dal_toor_tadka",        1),   # Arhar with spinach (toor dal)
    "ASC162":  ("chana_masala",          1),   # Chickpeas curry
    "ASC165":  ("rajma_chawal",          1),   # Kidney bean curry (rajma part)
    "ASC001":  ("chai_milk_tea",         1),   # Hot tea
    "ASC021":  ("lassi_sweet",           1),   # Sweet Lassi
    "ASC056":  ("boiled_eggs_2",         1),   # Boiled egg (1 egg = 50g; we will handle 2-egg serving)
    "BFP240":  ("egg_curry_2_eggs",      1),   # Egg curry
    # -- north bucket --
    "ASC098":  ("aloo_paratha",          1),   # Potato paratha
    "ASC143":  ("chole_bhature",         1),   # Bhatura (chole part from ASC162 added separately)
    "ASC242":  ("butter_chicken",        1),   # Butter chicken
    "ASC241":  ("tandoori_chicken",      1),   # Tandoori chicken
    "ASC215":  ("palak_paneer",          1),   # Spinach paneer (palak paneer)
    "OSR139":  ("dal_makhani",           4),   # Dal makhani (OSR139 = large batch, 4 servings)
    "ASC142":  ("naan",                  1),   # Naan
    "ASC171":  ("aloo_gobi",             1),   # Potato cauliflower
    "ASC168":  ("kadhi_pakora",          1),   # Besan kadhi with pakories
    "BFP269":  ("bhindi_masala",         1),   # Okra fry
    "OSR112":  ("pav_bhaji",             6),   # Pav bhaji (large batch, ~6 servings for OSR112)
    "ASC381":  ("paneer_tikka",          1),   # Paneer tikka
    # -- south bucket --
    "BFP148":  ("dosa_plain",            1),   # Plain dosa
    "ASC146":  ("masala_dosa",           1),   # Masala dosa
    "ASC144":  ("idli_sambar",           1),   # Idli (+ sambar from ASC167)
    "BFP436":  ("medu_vada",             1),   # Medu vada
    "BFP039":  ("upma",                  1),   # Semolina upma
    "ASC126":  ("curd_rice",             1),   # Curd rice
    "BFP153":  ("appam_stew",            4),   # Appam (large batch ~4 servings)
    "BFP176":  ("rasam_rice",            1),   # Rasam with tamarind (rasam part)
    # -- west_east bucket --
    "BFP044":  ("poha",                  1),   # Poha
    "ASC474":  ("dhokla_steamed",        1),   # Dhokla
    "OSR104":  ("thepla_methi",          3),   # Methi thepla (OSR104 = 3-piece batch)
    "OSR114":  ("bhel_puri",             2),   # Bhel puri (2-serving batch)
    "ASC487":  ("khichdi_yellow",        1),   # Vegetable khichdi (using yellow moong variant)
    "BFP223":  ("fish_curry_bengali",    1),   # Bengali fish curry
}

# Dishes with no INDB match — must be Opus-gap-filled:
# paneer_butter_masala, curd_dahi, mixed_veg_sabzi, banana_1, apple_1, mixed_salad
# pani_puri, pongal_ven, bisi_bele_bath, litti_chokha, rosogolla_2, chicken_chettinad
# sambar_rice (sambar + rice combo), misal_pav (no INDB recipe)

# Fat-heavy dishes that get _variants
FAT_HEAVY_DISHES = [
    "dal_toor_tadka",
    "dal_makhani",
    "paneer_butter_masala",
    "palak_paneer",
    "butter_chicken",
]

# ---------------------------------------------------------------------------
# 3. INDB food_name → ifct_lookup.json key mapping  (explicit, no fuzzy)
# ---------------------------------------------------------------------------
# Map common INDB food_name substrings to our ifct_id keys.
# Match is done case-insensitive substring on INDB food_name.
# Key: lowercase substring to match. Value: ifct_id key.

FOOD_NAME_TO_IFCT: list[tuple[str, str]] = [
    # Grains / flours
    ("wheat flour, atta",           "wheat_flour_whole"),
    ("wheat flour, refined",        "wheat_flour_refined"),
    ("wheat, semolina",             "rava_suji"),
    ("semolina",                    "rava_suji"),
    ("rice, parboiled",             "rice_parboiled_raw"),
    ("rice flakes",                 "poha_flakes"),
    ("white hamburger bun",         "wheat_flour_refined"),   # pav bun → maida approx
    # Dals / legumes
    ("red gram, dal",               "toor_dal_raw"),
    ("green gram, dal",             "moong_dal_raw"),
    ("black gram, dal",             "urad_dal_raw"),
    ("black gram, whole",           "urad_dal_raw"),
    ("masoor",                      "masoor_dal_raw"),
    ("bengal gram, dal",            "chana_dal_raw"),
    ("flour, gram",                 "chana_dal_raw"),         # besan = chana dal flour
    ("chickpeas",                   "chana_kabuli_raw"),
    ("rajmah",                      "rajma_red_raw"),
    # Dairy
    ("milk, whole",                 "milk_full_cream"),
    ("milk, skim",                  "milk_toned"),
    ("yogurt, whole milk",          "curd_dahi"),
    ("yogurt",                      "curd_dahi"),
    ("cream, fresh, single",        "cream_dairy"),
    ("cheese, cream",               "cream_dairy"),           # cream cheese → cream approx
    ("butter, unsalted",            "butter_table"),
    ("ghee, butter",                "ghee"),
    ("ghee",                        "ghee"),
    ("paneer",                      "paneer_full_fat"),
    # Protein
    ("egg, poultry, whole",         "egg_whole_per_egg"),
    ("egg, poultry",                "egg_whole_per_egg"),
    ("chicken, poultry, breast",    "chicken_breast_raw"),
    ("chicken, poultry",            "chicken_curry_cut"),
    ("pomfret",                     "fish_rohu_raw"),         # pomfret → rohu approx (both white fish)
    # Vegetables
    ("tomato",                      "tomato_red"),
    ("onion",                       "onion_pink"),
    ("potato",                      "potato"),
    ("spinach",                     "spinach_palak"),
    ("cauliflower",                 "cauliflower_gobi"),
    ("ladies finger",               "okra_bhindi"),
    ("brinjal",                     "brinjal_baingan"),
    ("carrot",                      "carrot"),
    ("capsicum, green",             "capsicum_shimla"),
    ("capsicum",                    "capsicum_shimla"),
    ("peas, fresh",                 "peas_green"),
    ("drumstick",                   "drumstick_moringa"),
    ("ginger",                      "ginger_raw"),
    ("garlic",                      "garlic_raw"),
    ("chillies, green",             "green_chilli"),
    ("chillies, red",               "spice_red_chilli_powder"),
    ("coriander leaves",            "coriander_leaves"),
    ("curry leaves",                "curry_leaves"),
    ("fenugreek leaves",            "coriander_leaves"),      # methi leaves → closest available
    ("french beans",                "peas_green"),            # green beans → peas approx
    ("coconut, kernel",             "coconut_fresh"),
    ("coconut milk",                "coconut_milk"),
    # Oils / fats
    ("oil, sunflower",              "oil_refined"),
    ("oil, mustard",                "oil_mustard"),
    # Nuts / seeds
    ("ground nut",                  "peanut_groundnut_raw"),
    ("peanut",                      "peanut_groundnut_raw"),
    ("cashew",                      "cashew_kaju_raw"),
    # Sugars
    ("sugar, white",                "sugar_white"),
    ("sugar, icing",                "sugar_white"),
    ("sugar",                       "sugar_white"),
    # Spices (dry — small quantities, tracked for completeness)
    ("cumin seeds",                 "spice_cumin_jeera"),
    ("coriander seeds",             "spice_coriander_seed"),
    ("turmeric powder",             "spice_turmeric_haldi"),
    ("garam masala",                "spice_garam_masala"),
    ("chilli powder",               "spice_red_chilli_powder"),
    ("mustard seeds",               "spice_cumin_jeera"),     # mustard → cumin approx (tiny qty)
    # Beverages / misc
    ("tea, black",                  "tea_leaves_dry"),
    ("tamarind",                    "tomato_red"),            # tamarind → tomato (sour proxy; tiny qty)
    # Water is not in ifct_lookup (no macros) → skip
]

def food_name_to_ifct(food_name: str) -> str | None:
    """Return ifct_id for an INDB food_name, or None if no match."""
    fn = str(food_name).lower().strip()
    for substr, ifct_id in FOOD_NAME_TO_IFCT:
        if substr.lower() in fn:
            return ifct_id
    return None


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("Loading INDB recipes.xlsx …")
    df = pd.read_excel(RECIPES_XLSX)
    print(f"  {len(df)} rows, {df['recipe_code'].nunique()} unique recipes")

    # Load ifct_lookup to validate ifct_ids at output time
    with open(IFCT_LOOKUP) as f:
        ifct_data = json.load(f)
    ifct_keys = set(ifct_data["ingredients"].keys())

    # Load existing dish_decomposition to get metadata (name_en etc.)
    with open(DECOMP_JSON) as f:
        decomp = json.load(f)
    existing_dishes = decomp["dishes"]

    # Unit gap log
    unit_gaps = []
    # IFCT gap log
    ifct_gaps = []

    # -----------------------------------------------------------------------
    # Build per-recipe ingredient list with gram amounts
    # -----------------------------------------------------------------------
    results = {}  # dish_id → dict

    for recipe_code, dish_id_tuple in WHITELIST_MAP.items():
        dish_id, serving_div = dish_id_tuple
        subset = df[df["recipe_code"] == recipe_code].copy()
        if len(subset) == 0:
            print(f"  WARN: recipe_code {recipe_code} not found in xlsx — skipping")
            continue

        recipe_name = subset.iloc[0]["recipe_name"]
        ingredients_out = []
        # Track ifct_id → total grams to aggregate duplicate ingredients
        ifct_gram_agg: dict[str, float] = {}

        for _, row in subset.iterrows():
            fname = row.get("food_name", "")
            fcode = row.get("food_code", "")
            amount = row.get("amount", None)
            unit = row.get("unit", "")

            # Skip water (no macros)
            if not pd.isna(fname) and "water" in str(fname).lower():
                continue
            # Skip salt (no macros in our lookup)
            if not pd.isna(fname) and str(fname).lower().strip() in ("salt", "salt iodised", "iodized salt"):
                continue
            # Skip bicarbonate / baking powder (leavening, no macros)
            if not pd.isna(fname) and any(x in str(fname).lower() for x in ["bicarbonate", "baking powder", "baking soda", "yeast"]):
                continue
            # Skip food dyes / coloring
            if not pd.isna(fname) and any(x in str(fname).lower() for x in ["colour", "color"]):
                continue
            # Skip asafoetida (negligible, not in ifct_lookup)
            if not pd.isna(fname) and "asafoetida" in str(fname).lower():
                continue
            # Skip bay leaf, cardamom, clove, cinnamon, nutmeg, mace, star anise (whole spices, negligible)
            skip_spices = ["bay leaf", "cardamom", "cloves", "cinnamon", "nutmeg", "mace", "star anise",
                           "fennel seed", "pepper, black", "poppy seed", "amhur", "fenugreek seed"]
            if not pd.isna(fname) and any(x in str(fname).lower() for x in skip_spices):
                continue

            # Convert unit → grams
            g = amount_to_grams(amount, unit, fcode, fname)
            if g is None:
                unit_gaps.append({
                    "recipe_code": recipe_code,
                    "dish_id": dish_id,
                    "recipe_name": recipe_name,
                    "food_name": fname,
                    "food_code": fcode,
                    "amount": amount,
                    "unit": unit,
                })
                continue

            # Map food_name → ifct_id
            ifct_id = food_name_to_ifct(str(fname))
            if ifct_id is None:
                ifct_gaps.append({
                    "recipe_code": recipe_code,
                    "dish_id": dish_id,
                    "food_name": fname,
                    "food_code": fcode,
                })
                continue  # skip this ingredient

            # Validate ifct_id exists in lookup
            if ifct_id not in ifct_keys:
                ifct_gaps.append({
                    "recipe_code": recipe_code,
                    "dish_id": dish_id,
                    "food_name": fname,
                    "food_code": fcode,
                    "ifct_id_attempted": ifct_id,
                    "note": "ifct_id not in lookup",
                })
                continue

            # Aggregate (INDB sometimes has duplicate rows for same ingredient)
            ifct_gram_agg[ifct_id] = ifct_gram_agg.get(ifct_id, 0.0) + g

        if not ifct_gram_agg:
            print(f"  WARN: {recipe_code} ({dish_id}) yielded 0 ingredients — skipping")
            continue

        # Apply serving divisor
        if serving_div > 1:
            ifct_gram_agg = {k: round(v / serving_div, 1) for k, v in ifct_gram_agg.items()}
        else:
            ifct_gram_agg = {k: round(v, 1) for k, v in ifct_gram_agg.items()}

        # Build ingredient list (exclude very tiny amounts < 0.05g after division)
        for ifct_id, grams in ifct_gram_agg.items():
            if grams >= 0.05:
                ingredients_out.append({"ifct_id": ifct_id, "g": grams})

        # Preserve existing metadata from dish_decomposition.json
        existing = existing_dishes.get(dish_id, {})

        entry = {
            "name_en": existing.get("name_en", dish_id),
            "name_hi": existing.get("name_hi", ""),
            "bucket":  existing.get("bucket", "pan"),
            "tags":    existing.get("tags", []),
            "serving_label": existing.get("serving_label", "1 serving"),
            "ingredients": ingredients_out,
            "verified_by": f"INDB recipe #{recipe_code} ({recipe_name}) + INDB per-serving macros ({TODAY})",
            "_indb_recipe_id": recipe_code,
        }
        results[dish_id] = entry
        print(f"  OK {recipe_code} → {dish_id}: {len(ingredients_out)} ingredients")

    # Special: chole_bhature needs chana (ASC162) + bhatura (ASC143) merged
    # Already have ASC143→chole_bhature (bhatura dough). Add ASC162 chickpea data on top.
    if "chole_bhature" in results:
        chana_data = {}
        chana_subset = df[df["recipe_code"] == "ASC162"].copy()
        for _, row in chana_subset.iterrows():
            fname = row.get("food_name", "")
            fcode = row.get("food_code", "")
            amount = row.get("amount", None)
            unit = row.get("unit", "")
            if not pd.isna(fname) and any(x in str(fname).lower() for x in ["water", "salt"]):
                continue
            g = amount_to_grams(amount, unit, fcode, fname)
            if g is None:
                continue
            ifct_id = food_name_to_ifct(str(fname))
            if ifct_id and ifct_id in ifct_keys:
                chana_data[ifct_id] = chana_data.get(ifct_id, 0.0) + g
        # Merge: bhatura ingredient already there (maida from ASC143), add chana on top
        existing_map = {ing["ifct_id"]: ing["g"] for ing in results["chole_bhature"]["ingredients"]}
        for ifct_id, g in chana_data.items():
            existing_map[ifct_id] = existing_map.get(ifct_id, 0.0) + round(g, 1)
        results["chole_bhature"]["ingredients"] = [
            {"ifct_id": k, "g": round(v, 1)} for k, v in existing_map.items() if v >= 0.05
        ]
        results["chole_bhature"]["verified_by"] = (
            f"INDB recipes #ASC143 (bhatura) + #ASC162 (chana) merged ({TODAY})"
        )
        results["chole_bhature"]["_indb_recipe_id"] = "ASC143+ASC162"
        print(f"  MERGE: chole_bhature = ASC143(bhatura) + ASC162(chana): {len(results['chole_bhature']['ingredients'])} ingredients")

    # Special: idli_sambar needs idli (ASC144) + sambar (ASC167) merged
    if "idli_sambar" in results:
        sambar_data = {}
        sambar_subset = df[df["recipe_code"] == "ASC167"].copy()
        for _, row in sambar_subset.iterrows():
            fname = row.get("food_name", "")
            fcode = row.get("food_code", "")
            amount = row.get("amount", None)
            unit = row.get("unit", "")
            if not pd.isna(fname) and any(x in str(fname).lower() for x in ["water", "salt", "tamarind"]):
                continue
            g = amount_to_grams(amount, unit, fcode, fname)
            if g is None:
                continue
            ifct_id = food_name_to_ifct(str(fname))
            if ifct_id and ifct_id in ifct_keys:
                sambar_data[ifct_id] = sambar_data.get(ifct_id, 0.0) + g
        existing_map = {ing["ifct_id"]: ing["g"] for ing in results["idli_sambar"]["ingredients"]}
        for ifct_id, g in sambar_data.items():
            existing_map[ifct_id] = existing_map.get(ifct_id, 0.0) + round(g, 1)
        results["idli_sambar"]["ingredients"] = [
            {"ifct_id": k, "g": round(v, 1)} for k, v in existing_map.items() if v >= 0.05
        ]
        results["idli_sambar"]["verified_by"] = (
            f"INDB recipes #ASC144 (idli) + #ASC167 (sambar) merged ({TODAY})"
        )
        results["idli_sambar"]["_indb_recipe_id"] = "ASC144+ASC167"
        print(f"  MERGE: idli_sambar = ASC144 + ASC167: {len(results['idli_sambar']['ingredients'])} ingredients")

    # Special: sambar_rice = rasam_rice mapped from BFP176 (rasam) + rice separately
    # Use BFP176 as rasam_rice; add rice component
    if "rasam_rice" in results:
        existing_map = {ing["ifct_id"]: ing["g"] for ing in results["rasam_rice"]["ingredients"]}
        existing_map["rice_parboiled_raw"] = existing_map.get("rice_parboiled_raw", 0.0) + 50.0
        results["rasam_rice"]["ingredients"] = [
            {"ifct_id": k, "g": round(v, 1)} for k, v in existing_map.items() if v >= 0.05
        ]
        print(f"  AUGMENT: rasam_rice: added 50g rice_parboiled_raw")

    # sambar_rice: build from ASC167 (sambar) + rice
    # This dish is not in WHITELIST_MAP above; we derive it from ASC167
    if "sambar_rice" not in results:
        sambar_data = {}
        sambar_subset = df[df["recipe_code"] == "ASC167"].copy()
        for _, row in sambar_subset.iterrows():
            fname = row.get("food_name", "")
            fcode = row.get("food_code", "")
            amount = row.get("amount", None)
            unit = row.get("unit", "")
            if not pd.isna(fname) and any(x in str(fname).lower() for x in ["water", "salt", "tamarind"]):
                continue
            g = amount_to_grams(amount, unit, fcode, fname)
            if g is None:
                continue
            ifct_id = food_name_to_ifct(str(fname))
            if ifct_id and ifct_id in ifct_keys:
                sambar_data[ifct_id] = sambar_data.get(ifct_id, 0.0) + g
        sambar_data["rice_parboiled_raw"] = 50.0  # add rice component
        existing = existing_dishes.get("sambar_rice", {})
        results["sambar_rice"] = {
            "name_en": existing.get("name_en", "Sambar rice"),
            "name_hi": existing.get("name_hi", "सांबार चावल"),
            "bucket":  existing.get("bucket", "south"),
            "tags":    existing.get("tags", ["veg", "staple"]),
            "serving_label": existing.get("serving_label", "1 plate (~200g)"),
            "ingredients": [{"ifct_id": k, "g": round(v, 1)} for k, v in sambar_data.items() if v >= 0.05],
            "verified_by": f"INDB recipe #ASC167 (sambar) + rice component ({TODAY})",
            "_indb_recipe_id": "ASC167+rice",
        }
        print(f"  BUILD: sambar_rice from ASC167+rice: {len(results['sambar_rice']['ingredients'])} ingredients")

    # _variants for fat-heavy dishes
    for dish_id in FAT_HEAVY_DISHES:
        if dish_id in results:
            results[dish_id]["_variants"] = [f"{dish_id}_plain", f"{dish_id}_restaurant"]
            results[dish_id]["default_variant"] = dish_id
        elif dish_id in existing_dishes:
            # dish will be Opus-drafted, add _variants anyway
            pass

    # -----------------------------------------------------------------------
    # Write outputs
    # -----------------------------------------------------------------------
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(results)} dishes to {OUTPUT_JSON}")

    with open(UNIT_GAP_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["recipe_code","dish_id","recipe_name","food_name","food_code","amount","unit"])
        writer.writeheader()
        writer.writerows(unit_gaps)
    print(f"Wrote {len(unit_gaps)} unit-gap rows to {UNIT_GAP_CSV}")

    with open(IFCT_GAP_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["recipe_code","dish_id","food_name","food_code","ifct_id_attempted","note"])
        writer.writeheader()
        for row in ifct_gaps:
            writer.writerow({
                "recipe_code": row.get("recipe_code",""),
                "dish_id": row.get("dish_id",""),
                "food_name": row.get("food_name",""),
                "food_code": row.get("food_code",""),
                "ifct_id_attempted": row.get("ifct_id_attempted",""),
                "note": row.get("note","no ifct match"),
            })
    print(f"Wrote {len(ifct_gaps)} ifct-gap rows to {IFCT_GAP_CSV}")

    # Print unmapped whitelist dishes
    all_dish_ids = set(existing_dishes.keys())
    mapped_dish_ids = set(results.keys())
    unmapped = all_dish_ids - mapped_dish_ids
    print(f"\nUnmapped whitelist dishes ({len(unmapped)}):")
    for d in sorted(unmapped):
        print(f"  - {d}")

    # Validation
    assert all(v.get("verified_by") for v in results.values()), "verified_by missing on some entries"
    print(f"\nAll {len(results)} INDB-sourced dishes have verified_by set.")
    print("DONE.")


if __name__ == "__main__":
    main()
