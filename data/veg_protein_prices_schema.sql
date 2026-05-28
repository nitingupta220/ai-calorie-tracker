-- veg_protein_prices schema (per CONTEXT D-15..D-18)
-- Phase 1: this SQL defines the table; seed data populated via founder-led scrape of Zepto/BigBasket/Blinkit
-- Phase 2: Alembic migration adds this to Postgres
-- Phase 5 (V1.5): add city-based per-region pricing UX (already supported via city column)
--
-- COVERAGE TARGET: top 50 veg-protein sources per D-18.
-- REFRESH CADENCE: quarterly manual founder refresh + monthly anomaly alert per D-16.

CREATE TABLE IF NOT EXISTS veg_protein_prices (
    id                      BIGSERIAL PRIMARY KEY,

    -- Food identity
    food_id                 TEXT NOT NULL,                  -- matches ifct_lookup.json ingredient key (e.g., "paneer_full_fat")
    food_name_en            TEXT NOT NULL,                  -- "Paneer (full fat)"
    food_name_hi            TEXT,                           -- "पनीर"
    category                TEXT NOT NULL,                  -- "dairy" | "legume" | "soya" | "nut" | "egg" | "millet" | "vegan" | "other"
    diet_compatible         TEXT[] NOT NULL,                -- ["VG","EG","NV","VN"] subset

    -- Price + sourcing
    source_platform         TEXT NOT NULL,                  -- "zepto" | "bigbasket" | "blinkit" | "rd_sheet"
    city                    TEXT NOT NULL,                  -- "delhi" | "mumbai" | "bangalore" | "hyderabad"
    price_per_kg_inr        NUMERIC(8,2) NOT NULL,          -- ₹ per kg at retail
    pack_size_g             INTEGER,                        -- typical pack at this price (NULL if loose/per-kg)

    -- Nutrition derived (denormalized for fast advice-engine lookup)
    protein_per_100g_g      NUMERIC(5,2) NOT NULL,          -- protein grams per 100g edible
    cost_per_g_protein_inr  NUMERIC(6,3) NOT NULL,          -- the moat metric: ₹/g protein

    -- Audit
    scrape_date             DATE NOT NULL,                  -- when row was captured
    scrape_method           TEXT,                           -- "manual" | "playwright" | "api"
    notes                   TEXT,                           -- free-form (festival inflation, promo, etc)

    -- Timestamps
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT chk_source_platform CHECK (source_platform IN ('zepto','bigbasket','blinkit','rd_sheet')),
    CONSTRAINT chk_category CHECK (category IN ('dairy','legume','soya','nut','egg','millet','vegan','other')),
    CONSTRAINT chk_protein_positive CHECK (protein_per_100g_g > 0),
    CONSTRAINT chk_price_positive CHECK (price_per_kg_inr > 0),
    CONSTRAINT chk_cost_per_g_protein_positive CHECK (cost_per_g_protein_inr > 0)
);

-- Composite for budget-optimizer query: latest price per food per city per diet
CREATE INDEX idx_vpp_food_city ON veg_protein_prices (food_id, city, scrape_date DESC);

-- Diet filter (used by /api/budget-optimize endpoint)
CREATE INDEX idx_vpp_diet_compatible ON veg_protein_prices USING GIN (diet_compatible);

-- Anomaly detection (monthly cron per D-16): compare current scrape vs 3-month-old
CREATE INDEX idx_vpp_scrape_date ON veg_protein_prices (scrape_date DESC);

-- Most-recent-price-per-food materialized view (refresh nightly or after scrape)
-- Used by budget optimizer screen 005 to avoid join overhead.
CREATE MATERIALIZED VIEW IF NOT EXISTS v_vpp_latest_per_food_city AS
SELECT DISTINCT ON (food_id, city)
    id,
    food_id,
    food_name_en,
    food_name_hi,
    category,
    diet_compatible,
    source_platform,
    city,
    price_per_kg_inr,
    pack_size_g,
    protein_per_100g_g,
    cost_per_g_protein_inr,
    scrape_date
FROM veg_protein_prices
ORDER BY food_id, city, scrape_date DESC;

CREATE UNIQUE INDEX idx_v_vpp_latest_food_city ON v_vpp_latest_per_food_city (food_id, city);

-- Auto-update updated_at trigger
CREATE OR REPLACE FUNCTION trg_vpp_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER vpp_updated_at_trg
BEFORE UPDATE ON veg_protein_prices
FOR EACH ROW EXECUTE FUNCTION trg_vpp_updated_at();

-- ─────────────────────────────────────────────────────────────────────────────
-- Sample INSERT shape (founder fills in real data during Gate 0a scrape phase)
-- ─────────────────────────────────────────────────────────────────────────────
--
-- INSERT INTO veg_protein_prices (
--   food_id, food_name_en, food_name_hi, category, diet_compatible,
--   source_platform, city, price_per_kg_inr, pack_size_g,
--   protein_per_100g_g, cost_per_g_protein_inr,
--   scrape_date, scrape_method, notes
-- ) VALUES
-- ('paneer_full_fat', 'Paneer (full fat)', 'पनीर', 'dairy', ARRAY['VG','EG','NV'],
--  'zepto', 'mumbai', 360.00, 200,
--  18.30, 1.967,
--  '2026-05-28', 'manual', 'Amul brand fresh paneer 200g pack');
--
-- ─────────────────────────────────────────────────────────────────────────────
-- Target seed: top 50 foods × 4 cities × 4 sources = up to 800 rows
-- Realistic Gate 0a seed: top 20 foods × 4 cities × 2 best-source = ~160 rows
-- ─────────────────────────────────────────────────────────────────────────────
