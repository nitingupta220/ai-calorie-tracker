# MODEL-SPEC — Canonical Data Model (Bhog backend, Phase 2 spine)

> Dev handoff. This is the **single source of truth for the Postgres schema**. Build the SQLAlchemy 2.0 (async) models + Alembic migrations from this doc. Do not invent columns. Anything marked `OPEN — needs founder` is the only thing you may not resolve yourself.
>
> **Authority chain (higher wins on conflict):** `CLAUDE.md` > `01-CONTEXT.md` (D-01..D-19) > `.planning/decisions/*` (D-CEO-01..03) > `01-AI-SPEC.md` > `REQUIREMENTS.md` > `research/ARCHITECTURE.md` (banner-superseded items honored).
>
> **Sibling specs (do not duplicate — cross-link):**
> - API routes / request-response shapes → `API-SPEC.md`
> - AI provider chain / Pydantic LLM I/O schemas → `01-AI-SPEC.md` §3, §4b
> - DPDP delete/export/consent flows (behavior) → `COMPLIANCE-SPEC.md`
> - Design tokens / enums shown in UI → `DESIGN.md`
>
> **Stack (locked):** Postgres 15/16 on Supabase Mumbai (D-02) · SQLAlchemy 2.0 async + `asyncpg` · Alembic · Pydantic v2 (separate `schemas/` from `models/`, anti-pattern #17). All timestamps `TIMESTAMPTZ`, stored UTC. App is IST-facing; do date bucketing in IST and store the bucket explicitly where it matters (see `daily_summary.summary_date`, `streak_event.event_date`).

---

## 0. Conventions (apply to every table)

- **PK:** `id BIGSERIAL PRIMARY KEY` for high-volume / append-only tables; `users.id` is `UUID` (matches R2 key path `meals/{user_id}/...`, ARCHITECTURE Pattern 2 + AP#5). FK columns therefore typed to match their target (`UUID` to users, `BIGINT` to serial parents).
- **Timestamps:** `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` on every table. `updated_at` only on mutable tables (NOT on append-only ones — see §7).
- **Soft-delete:** only `users.soft_delete_at TIMESTAMPTZ NULL`. No other table carries a soft-delete flag; child rows are reached by FK cascade at hard-delete time (§6).
- **Enums:** implemented as Postgres native `ENUM` types (named, listed per table). Widen-now discipline: where DPDP/audit correctness breaks if an enum is widened after rows exist, the **full V1+V1.1+known-V1.5 value set is declared now** (flagged inline). Adding a value to a native enum later is a migration; that is fine for non-audit enums but forbidden for `consent_type` (see §3.2 rationale).
- **No LLM-derived numbers stored as truth without provenance.** Macros on `meal_photo` are the deterministic IFCT aggregate (D-07); the vision LLM output that produced the dish-id is captured for audit, never the macro math.
- **Append-only tables never UPDATE/DELETE** except via the DPDP hard-delete cascade. Enforced by convention + a DB trigger (§7).

---

## 1. Table Inventory (Phase-2 baseline vs deferred)

| # | Table | Append-only? | Phase | REQ / D source | Notes |
|---|-------|:---:|:---:|---|---|
| 1 | `users` | no | **P2 baseline** | INFRA-06, AUTH-01..05, ONBOARD-01/02 | profile + goal + budget + diet + soft-delete |
| 2 | `meal_photo` | no (mutable: status, corrected macros) | **P2 baseline** | INFRA-06, TRACK-04..09, HISTORY-03 | core meal row; presign→analyze lifecycle |
| 3 | `consent_log` | **YES** | **P2 baseline** | INFRA-06, COMP-03/09, ONBOARD-03 | DPDP §6 verifiable consent ledger; wide enum NOW |
| 4 | `correction_event` | **YES** | **P2 baseline** | INFRA-06, HISTORY-04, ARCH AP#7/Pattern5 | V1.5 fine-tuning corpus; wide schema NOW |
| 5 | `daily_summary` | no (recomputed) | **P2 baseline** | INFRA-06, HISTORY-01, RETAIN-02 | per-user-per-IST-day totals + gap |
| 6 | `ai_call_log` | **YES** | **P2 baseline** | INFRA-04, AI-SPEC §4b/§7, COMP cost gate | per-provider-call telemetry; cost gate ledger |
| 7 | `provider_quota` | no (per-day counter) | **P2 baseline** | AI-SPEC §4 State Mgmt | RPD counter per provider per day |
| 8 | `vision_cache` | no (TTL evict) | **P2 baseline** | AI-SPEC §4 idempotency / §4b caching | `(image_sha256, goal_hash)` → MealResponse 24h |
| 9 | `veg_protein_prices` | no (versioned by scrape_date) | **P2 baseline** | D-15..D-18, D-CEO-03, ADVICE-05 | schema is `data/veg_protein_prices_schema.sql` verbatim |
| 10 | `consent_audit` | **YES** | **P2 baseline** | COMP-04 (365-day deletion audit) | survives hard-delete; PII-stripped hash only |
| 11 | `push_event` | **YES** | **P3** (deferred) | INFRA-06 (table named), RETAIN-01/02/04 | FCM token + per-push send/open log |
| 12 | `streak_event` | **YES** | **P3** (deferred) | D-CEO-02, RETAIN-03 | own-rank cohort pill; nightly cron writes |
| 13 | `whatsapp_session` | no (24h TTL evict) | **P2 baseline** (stub) / **P4** (wire) | D-CEO-01 | E.164-keyed pre-install session; link not rewrite |

**Phase-2 baseline = create in the Alembic baseline + early P2 migrations** (tables 1-10, 13). Tables 11-12 are **deferred to Phase 3** per REQUIREMENTS traceability (RETAIN-* and D-CEO-02 are Phase 3). `whatsapp_session` table+stub lands in Phase 2 per D-CEO-01 ("Phase 2 (table + stub)"), wiring in Phase 4.

> **INFRA-06 reconciliation:** REQUIREMENTS INFRA-06 lists 7 tables `{users, meal_photo, daily_summary, streak, push_event, consent_log, correction_event}`. This spec **renames `streak` → `streak_event`** (D-CEO-02 locked the append-only event-log shape; the bare `streak` counter is derived, not stored) and **defers `push_event` + `streak_event` to Phase 3** to match the RETAIN-*/D-CEO-02 phase mapping. The Phase-2 Alembic baseline therefore creates `{users, meal_photo, consent_log, correction_event, daily_summary}` + the AI tables + `veg_protein_prices` + `consent_audit` + `whatsapp_session` stub. This is a deliberate, traced deviation, not a contradiction.

---

## 2. ER Overview (ASCII)

```
                                  ┌──────────────────────────────┐
                                  │            users             │  (UUID PK)
                                  │  firebase_uid, phone_e164,    │
                                  │  goal, diet_preference,       │
                                  │  budget_bucket, city,         │
                                  │  weight_kg, height_cm, dob,   │
                                  │  ai_training_opt_in,          │
                                  │  soft_delete_at               │
                                  └──────────────┬───────────────┘
                                                 │ 1
        ┌──────────────┬───────────────┬─────────┼──────────────┬──────────────┬───────────────┐
        │ N            │ N             │ N        │ N            │ N            │ N             │ N
┌───────▼──────┐ ┌─────▼────────┐ ┌────▼───────┐ ┌▼───────────┐ ┌▼──────────┐ ┌▼────────────┐ ┌▼────────────┐
│  meal_photo  │ │ consent_log  │ │daily_summary│ │correction_ │ │push_event │ │streak_event │ │ ai_call_log │
│ (BIGSERIAL)  │ │ (BIGSERIAL,  │ │ (BIGSERIAL) │ │   event    │ │(BIGSERIAL,│ │(BIGSERIAL,  │ │ (BIGSERIAL, │
│ status,      │ │  APPEND-ONLY)│ │ uniq(user,  │ │(BIGSERIAL, │ │ P3,       │ │ P3,         │ │ APPEND-ONLY,│
│ macros,      │ │              │ │  date)      │ │ APPEND-ONLY)│ │ APPEND-ON)│ │ APPEND-ONLY)│ │ user_id     │
│ confidence,  │ └──────────────┘ └─────────────┘ └─────┬──────┘ └───────────┘ └─────────────┘ │ NULLABLE)   │
│ is_off_      │                                        │ N                                    └─────────────┘
│ whitelist    │◄───────────────────────────────────────┘ (meal_photo_id FK)
└──────┬───────┘
       │ (R2 key: meals/{user_id}/{photo_uuid}.jpg — bytes in R2, NOT in DB; AP#5)
       │
   referenced by ai_call_log.meal_photo_id (NULLABLE — advice/push calls have no photo)

  STANDALONE (no users FK or weak link only):
  ┌────────────────────┐  ┌────────────────┐  ┌───────────────┐  ┌─────────────────┐  ┌──────────────────┐
  │ veg_protein_prices │  │ provider_quota │  │ vision_cache  │  │ whatsapp_session│  │  consent_audit   │
  │ food_id→ifct keys  │  │ (provider,date)│  │ image_sha256  │  │ phone_e164 PK   │  │ user_id_hash     │
  │ (reference data)   │  │  PK            │  │  +goal_hash PK│  │ linked_user_id? │  │ (survives delete)│
  └────────────────────┘  └────────────────┘  └───────────────┘  └────────┬────────┘  └──────────────────┘
                                                                          │ nullable FK → users.id
                                                                          │ (Phase-4 link, NOT rewrite)
```

Cardinality: every PII-bearing child of `users` is `N:1` and cascades on hard-delete (§6). `ai_call_log.user_id`, `whatsapp_session.linked_user_id` are **nullable** (system/pre-install calls). `veg_protein_prices`, `provider_quota`, `vision_cache`, `consent_audit` carry **no live FK to users** (reference/telemetry/post-delete-audit data).

---

## 3. Table Definitions (locked)

### 3.1 `users` — profile / goal / budget / diet  (mutable)

REQ: AUTH-01..05, ONBOARD-01/02, INFRA-06. City is the single source of truth shared by budget optimizer (D-CEO-03) + streak cohort (D-CEO-02).

| Column | Type | Null | Default | Notes |
|---|---|:---:|---|---|
| `id` | `UUID` | no | `gen_random_uuid()` | PK. Used in R2 key path. |
| `firebase_uid` | `TEXT` | no | — | from verified Firebase ID token (D-05). **UNIQUE.** |
| `phone_e164` | `TEXT` | no | — | normalized E.164 `+91…` (server-side, never trust client — AI-SPEC FM#3, D-05). **UNIQUE.** PII. |
| `goal` | `ENUM goal_t` | no | `'muscle_gain'` | `goal_t = {muscle_gain, weight_loss}`. **Declare both now** (weight_loss is V1.1, ONBOARD-01 V1=muscle_gain only; PostHog dark-launch per CLAUDE.md). |
| `diet_preference` | `ENUM diet_t` | no | — | `diet_t = {veg, egg, non_veg, vegan, lacto_veg_no_egg, lactose_intolerant}`. **Declare full set now** — advice guardrails G8 + eval D7 branch on every value (eggs-to-lacto-veg, dairy-to-vegan/lactose). Maps to `veg_protein_prices.diet_compatible` codes VG/EG/NV/VN. |
| `height_cm` | `NUMERIC(5,1)` | no | — | ONBOARD-01. |
| `weight_kg` | `NUMERIC(5,1)` | no | — | onboarding seed weight; ongoing weights in `OPEN` weight_log (§3.14). |
| `date_of_birth` | `DATE` | no | — | PII. 18+ age gate (AUTH-04) computed at signup; **never** sent to LLM (AI-SPEC FM#3 / G11). |
| `is_adult` | `BOOLEAN` | no | — | **stored age-gate verdict** computed from `date_of_birth` at signup (AUTH-04). The `current_user` dependency (API-SPEC §1 step 5) reads this flag per-request to reject non-adult tokens — it does NOT recompute from DOB each call. Reconciliation: API-SPEC enforces a *stored* verdict; this column is that store. (Added 2026-05-29 cross-spec reconciliation G5.) |
| `activity_level` | `ENUM activity_t` | no | — | `activity_t = {sedentary, light, moderate, active, very_active}` (Mifflin-St-Jeor multiplier, ONBOARD-02). |
| `budget_bucket` | `ENUM budget_t` | no | — | `budget_t = {b100_150, b150_250, b250_plus}` (ONBOARD-01 ₹100-150 / ₹150-250 / ₹250+). Drives advice D6 + optimizer. |
| `city` | `TEXT` | yes | NULL | **single source of truth** for budget-optimizer pricing (D-CEO-03) AND streak cohort_city (D-CEO-02). NULL ⇒ user is OUT of streak cohort (§3.12). Lowercase city slug (`mumbai`, `delhi`…). |
| `target_kcal` | `INTEGER` | yes | NULL | computed ONBOARD-02; cached for advice prompt (avoids recompute). |
| `target_protein_g` | `INTEGER` | yes | NULL | ISSN 1.8 g/kg default (ONBOARD-02). |
| `ai_training_opt_in` | `BOOLEAN` | no | `FALSE` | **default OFF** (COMP-09, ONBOARD-03, DPDP explicit opt-in). |
| `fcm_token` | `TEXT` | yes | NULL | latest device token (RETAIN-01). Per-send history in `push_event` (P3). |
| `push_opt_out` | `BOOLEAN` | no | `FALSE` | RETAIN-05. |
| `leaderboard_opt_in` | `BOOLEAN` | no | `FALSE` | **default OFF** (D-CEO-02 DPDP minimization). |
| `soft_delete_at` | `TIMESTAMPTZ` | yes | NULL | AUTH-05; set on delete request; 30-day hard-delete cron reads this (COMP-04, §6). |
| `created_at` | `TIMESTAMPTZ` | no | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | no | `now()` | auto-update trigger. |

Indexes: `UNIQUE(firebase_uid)`, `UNIQUE(phone_e164)`, `INDEX(soft_delete_at) WHERE soft_delete_at IS NOT NULL` (cron scan), `INDEX(city)`.

### 3.2 `consent_log` — DPDP verifiable consent ledger  (**APPEND-ONLY**)

REQ: COMP-03/09, ONBOARD-03, D-CEO-01 (whatsapp_preinstall). **Rationale for wide enum NOW:** DPDP §6 verifiable consent requires the ledger to be complete and immutable. If `consent_type` is widened by a later migration *after rows exist*, you cannot prove the absence of a consent that did not yet exist as an enum value — the audit story breaks. Therefore the **entire known consent surface (V1 + V1.1 + D-CEO) is declared on day 1.**

| Column | Type | Null | Notes |
|---|---|:---:|---|
| `id` | `BIGSERIAL` | no | PK. |
| `user_id` | `UUID` | yes | FK→`users.id` ON DELETE CASCADE. NULLABLE: pre-install WhatsApp consent has no user yet (D-CEO-01) — `user_id_hash` carries the link. |
| `user_id_hash` | `TEXT` | no | SHA-256 of `user_id` (or of `phone_e164` for pre-install). **Survives hard-delete** so a deletion-time copy can prove consent history existed (mirrors `consent_audit`). |
| `consent_type` | `ENUM consent_type_t` | no | **WIDE, declared now (8 values):** `{photo, profile, analytics, ai_training, whatsapp_preinstall, leaderboard, age_18plus, disclaimer_ack}`. `ai_training` default action at signup is implicit-revoke (opt-in OFF). `disclaimer_ack` added 2026-05-29 (reconciliation G1 — ONBOARD-05 CDSCO disclaimer acknowledgement). **`consent_log` holds CONSENTS/acknowledgements ONLY** — NOT profile values (budget/diet/goal live on `users` under the single `profile` consent) and NOT DSR events (`delete_requested`/`export_generated`/`hard_deleted` live in `consent_audit.event_type`). `action` is `{grant, revoke}` only — there is no `event` action. |
| `action` | `ENUM consent_action_t` | no | `{grant, revoke}`. |
| `policy_version` | `TEXT` | no | privacy-policy semver shown at consent time (COMP-02). |
| `purpose_text_hash` | `TEXT` | no | SHA-256 of the exact purpose string the user saw — proves *what* they consented to. |
| `app_version` | `TEXT` | no | client build that captured consent. |
| `source_screen` | `TEXT` | no | e.g. `onboarding_consent`, `settings_ai_training`, `whatsapp_footer`. |
| `created_at` | `TIMESTAMPTZ` | no | `now()`. **No `updated_at`** (append-only). |

Index: `INDEX(user_id, consent_type, created_at DESC)`, `INDEX(user_id_hash)`.
**Current consent state** = latest row per `(user_id, consent_type)` by `created_at`. Never UPDATE a prior row; always INSERT a new `grant`/`revoke`.

### 3.3 `correction_event` — V1.5 fine-tuning corpus  (**APPEND-ONLY**)

REQ: HISTORY-04, ARCH Pattern 5 + Anti-Pattern 7. **Rationale for wide schema NOW:** corrections generated from Phase 6 are the V1.5 fine-tuning corpus; if a column needed for replay (the provider/model/prompt-version that produced the wrong answer) is added later, all prior rows are lossy and un-replayable. Capture the full provenance from row 1.

| Column | Type | Null | Notes |
|---|---|:---:|---|
| `id` | `BIGSERIAL` | no | PK. |
| `user_id` | `UUID` | no | FK→`users.id` ON DELETE CASCADE. |
| `meal_photo_id` | `BIGINT` | no | FK→`meal_photo.id` ON DELETE CASCADE. |
| `correction_kind` | `ENUM correction_kind_t` | no | `{dish_name, portion_g, macro_value, advice_rating, off_whitelist_relabel}`. Wide now — covers HISTORY-03 dish/macro edits + advice ≤3-star (AI-SPEC F2) + off-whitelist relabel (TRACK-07). |
| `field_name` | `TEXT` | no | which field changed, e.g. `dishes[0].name`, `macros.protein_g`, `portion_g`, `advice.rating`. |
| `before_value` | `JSONB` | no | value before edit (the model's output). |
| `after_value` | `JSONB` | no | value after edit (the user-corrected ground truth). |
| `source` | `ENUM correction_source_t` | no | `{user_edit, founder_woz, rd_audit, eval_replay}`. Wide now — distinguishes real-user corrections from WoZ/RD-audit labels in the corpus. |
| `ai_provider_id` | `TEXT` | yes | provider name that produced `before_value` (e.g. `gemini_2_5_flash_free`). NULL if before-value was already a template/fallback. |
| `ai_model_version` | `TEXT` | yes | model id (e.g. `gemini-2.5-flash`). |
| `prompt_template_version` | `TEXT` | yes | `prompts/*` VERSION at generation time (e.g. `vision_v1`). |
| `created_at` | `TIMESTAMPTZ` | no | `now()`. **No `updated_at`.** |

Index: `INDEX(user_id, created_at DESC)`, `INDEX(meal_photo_id)`, `INDEX(correction_kind)`.

### 3.4 `meal_photo` — core meal row  (mutable: lifecycle + corrected values)

REQ: TRACK-04..09, HISTORY-01/02/03, INFRA-06. Lifecycle: row inserted at presign (`status=pending`), flipped in analyze (`status=done|failed`). Off-whitelist + confidence feed the correction corpus from day 1.

| Column | Type | Null | Default | Notes |
|---|---|:---:|---|---|
| `id` | `BIGSERIAL` | no | — | PK. |
| `user_id` | `UUID` | no | — | FK→`users.id` ON DELETE CASCADE. |
| `r2_key` | `TEXT` | no | — | `meals/{user_id}/{uuid}.jpg`. Bytes in R2 india-jurisdiction (D-04, AP#5). **UNIQUE.** |
| `r2_jurisdiction` | `TEXT` | no | `'india'` | provenance: bucket jurisdiction at upload (D-04, COMP-01 boot check). Locked literal `india`. |
| `r2_region` | `TEXT` | no | `'mumbai'` | network-PoP provenance (distinct from jurisdiction; CLAUDE.md exec summary). |
| `status` | `ENUM meal_status_t` | no | `'pending'` | **`{pending, analyzing, done, failed}`** — `pending` at presign, set `analyzing` at the start of `/meals/{key}/analyze`, flipped to `done`/`failed` at the end. `failed` = vision unavailable across all providers (AI-SPEC G1 → 502). `analyzing` added 2026-05-29 (reconciliation G4 — API-SPEC §5.2 sets it; also lets the orphan janitor distinguish never-analyzed `pending` from crashed-mid-analyze `analyzing`). Non-DPDP enum, safe to widen. |
| `captured_at` | `TIMESTAMPTZ` | yes | NULL | client capture time (IST-derived day bucket for daily_summary). |
| `meal_slot` | `ENUM meal_slot_t` | yes | NULL | `{breakfast, lunch, dinner, snack}` — for last-3-day log table (AI-SPEC §4 context). |
| `dishes` | `JSONB` | yes | NULL | validated `VisionResult.dishes` (AI-SPEC §4b): `[{name, portion_g, confidence}]`. Mutable on correction. |
| `kcal` | `NUMERIC(7,1)` | yes | NULL | **deterministic IFCT aggregate** (D-07), NOT LLM math. NULL until `status=done`. |
| `protein_g` | `NUMERIC(6,1)` | yes | NULL | " |
| `carbs_g` | `NUMERIC(6,1)` | yes | NULL | " |
| `fat_g` | `NUMERIC(6,1)` | yes | NULL | " |
| `fiber_g` | `NUMERIC(6,1)` | yes | NULL | optional (ifct_lookup tracks `fib`). |
| `confidence` | `REAL` | yes | NULL | `min()` per-item confidence from VisionResult; feeds G2 gate (<0.6 ⇒ user-confirm) + correction corpus. |
| `is_off_whitelist` | `BOOLEAN` | no | `FALSE` | TRUE when vision returned `unknown` / dish outside 50-whitelist (TRACK-07). Feeds correction corpus + V1.5 whitelist-expansion trigger (D-08). |
| `reference_object` | `ENUM ref_obj_t` | yes | NULL | `{coin, palm, spoon, none}` (TRACK-02, AI-SPEC VisionResult). |
| `advice_text` | `TEXT` | yes | NULL | rendered inline advice (ADVICE-01). |
| `advice_rubric_passed` | `BOOLEAN` | yes | NULL | server-side 4/4 result (ADVICE-03, AI-SPEC M2 source-of-truth column). |
| `advice_prompt_version` | `TEXT` | yes | NULL | ADVICE-04 traceability. |
| `advice_is_fallback` | `BOOLEAN` | no | `FALSE` | TRUE if `Advice.fallback_for()` template used (AI-SPEC G4/G5). |
| `corrected` | `BOOLEAN` | no | `FALSE` | TRUE once any `correction_event` references this row (HISTORY-03). |
| `created_at` | `TIMESTAMPTZ` | no | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | no | `now()` | auto-update trigger. |

Indexes: `UNIQUE(r2_key)`, `INDEX(user_id, created_at DESC)` (last-3-day log query, AI-SPEC §4 `WHERE user_id=? AND created_at > now()-3d LIMIT 9`), `INDEX(user_id, captured_at)` (daily_summary), `INDEX(status) WHERE status='pending'` (orphan-janitor cron, ARCH Pattern 2 con).

### 3.5 `daily_summary` — per-user-per-IST-day totals  (mutable: recomputed)

REQ: HISTORY-01, RETAIN-02. Recomputed on each meal write/correction for the affected IST day (ARCH correction flow).

| Column | Type | Null | Notes |
|---|---|:---:|---|
| `id` | `BIGSERIAL` | no | PK. |
| `user_id` | `UUID` | no | FK→`users.id` ON DELETE CASCADE. |
| `summary_date` | `DATE` | no | **IST calendar day** (resets midnight IST — HISTORY-06 water reset semantics). |
| `total_kcal` | `NUMERIC(7,1)` | no | DEFAULT 0. |
| `total_protein_g` | `NUMERIC(6,1)` | no | DEFAULT 0. |
| `total_carbs_g` | `NUMERIC(6,1)` | no | DEFAULT 0. |
| `total_fat_g` | `NUMERIC(6,1)` | no | DEFAULT 0. |
| `protein_gap_g` | `NUMERIC(6,1)` | yes | `target_protein_g - total_protein_g` snapshot (RETAIN-02 push copy). |
| `water_ml` | `INTEGER` | no | DEFAULT 0 (HISTORY-06; 250ml-per-tap running total). |
| `meals_logged` | `INTEGER` | no | DEFAULT 0 (streak qualification input). |
| `created_at` | `TIMESTAMPTZ` | no | `now()`. |
| `updated_at` | `TIMESTAMPTZ` | no | `now()` (recompute touches this). |

Index: **`UNIQUE(user_id, summary_date)`** (idempotent recompute / upsert key).

### 3.6 `ai_call_log` — per-provider-call telemetry  (**APPEND-ONLY**)

REQ: INFRA-04, AI-SPEC §4b telemetry hook + §7 (cost gate source of truth). Restated here for completeness with the audit-required addition.

| Column | Type | Null | Notes |
|---|---|:---:|---|
| `id` | `BIGSERIAL` | no | PK. |
| `ts` | `TIMESTAMPTZ` | no | `now()`. (AI-SPEC uses `ts`, not `created_at`, for this table — keep that name.) |
| `user_id` | `UUID` | yes | **NULLABLE** FK→`users.id` ON DELETE SET NULL — system calls (daily-summary copy, eval replays, WhatsApp pre-install) have no user. SET NULL not CASCADE: cost ledger must survive user deletion for aggregate accounting. |
| `meal_photo_id` | `BIGINT` | yes | NULLABLE FK→`meal_photo.id` ON DELETE SET NULL — advice/push calls may have no photo. |
| `provider` | `TEXT` | no | e.g. `gemini_2_5_flash_free`, `groq_llama_3_3_70b`, `openrouter_qwen_vl`. |
| `model` | `TEXT` | yes | e.g. `gemini-2.5-flash`. |
| `stage` | `ENUM ai_stage_t` | no | `{vision, advice, daily_summary, decomposition_llm}` — decomposition is normally SQL (no LLM) but the enum value exists for the off-whitelist LLM-decomposition fallback path. |
| `prompt_version` | `TEXT` | no | from `prompts/*` VERSION. |
| `latency_ms` | `INTEGER` | no | per call. |
| `input_tokens` | `INTEGER` | yes | from usage metadata. |
| `output_tokens` | `INTEGER` | yes | " |
| `status` | `ENUM ai_call_status_t` | no | **`{ok, rate_limited, server_error, validation_error, timeout, aggregate_timeout, fallback_template}`** — `timeout` = single-provider call timeout; `aggregate_timeout` = the `asyncio.wait_for` whole-pipeline cap (AI-PROVIDER-SPEC AP-07); `fallback_template` = advice fell back to a template line. Reconciliation G3 (2026-05-29): renamed `fallback_used` → `fallback_template` to match the literal AI-PROVIDER-SPEC actually writes; the boolean `fallback_fired` column below remains the generic fallback flag. |
| `fallback_fired` | `BOOLEAN` | no | DEFAULT FALSE (AI-SPEC M4 / F8). |
| `rubric_passed` | `BOOLEAN` | yes | advice-stage only (AI-SPEC M2). NULL for vision. |

Index: `INDEX(ts DESC)`, `INDEX(provider, ts DESC)` (daily cost rollup), `INDEX(stage, ts DESC)`. **No UPDATE/DELETE** except hard-delete SET-NULL.

### 3.7 `provider_quota` — RPD counter  (mutable: per-day counter)

REQ: AI-SPEC §4 "Provider rate-limit state". One row per provider per UTC day.

| Column | Type | Null | Notes |
|---|---|:---:|---|
| `provider` | `TEXT` | no | part of PK. |
| `quota_date` | `DATE` | no | part of PK. **UTC day** (matches Gemini/Groq RPD reset which is UTC-based). |
| `rpd_consumed` | `INTEGER` | no | DEFAULT 0; incremented on success. |
| `rpd_limit` | `INTEGER` | yes | known free-tier ceiling cached (Gemini 500, Groq 1000) for fast pre-check. |
| `updated_at` | `TIMESTAMPTZ` | no | `now()`. |

PK: **`(provider, quota_date)` composite.** No `id`. Redis deferred to Phase 3 if contention (AI-SPEC §4).

### 3.8 `vision_cache` — exact-match dedup  (mutable: TTL evict)

REQ: AI-SPEC §4 idempotency + §4b caching. 24h TTL.

| Column | Type | Null | Notes |
|---|---|:---:|---|
| `image_sha256` | `TEXT` | no | part of PK. SHA-256 of the JPEG bytes. |
| `goal_hash` | `TEXT` | no | part of PK. hash of `(goal, diet_preference)` so cache is goal-scoped (AI-SPEC `user_goal_hash`). |
| `meal_response_json` | `JSONB` | no | cached `MealResponse` (macros + dishes + advice). |
| `created_at` | `TIMESTAMPTZ` | no | `now()`. |
| `expires_at` | `TIMESTAMPTZ` | no | `now() + interval '24 hours'`. Evict cron / lazy check. |

PK: **`(image_sha256, goal_hash)` composite.** Index: `INDEX(expires_at)` (evict scan). Contains no direct PII (hashes + de-identified macros); not FK'd to users.

### 3.9 `veg_protein_prices` — ₹/g-protein reference  (mutable: versioned by scrape_date)

REQ: D-15..D-18, D-CEO-03, ADVICE-05. **Schema is `data/veg_protein_prices_schema.sql` verbatim — do not redefine here.** Build the Alembic migration directly from that file (table + 3 indexes + materialized view `v_vpp_latest_per_food_city` + `updated_at` trigger). Key facts the dev must honor:

- **`food_id` is the join key to `ifct_lookup.json` ingredient keys AND to `dish_decomposition.json` `ifct_id`** (e.g. `paneer_full_fat`, `toor_dal_raw`, `soya_chunks_dry`). One shared vocabulary across all three artifacts. When seeding, every `food_id` MUST exist in `data/ifct_lookup.json.ingredients`.
- `diet_compatible TEXT[]` uses codes `{VG, EG, NV, VN}` (veg / egg / non-veg / vegan) — these map to `users.diet_preference` for the optimizer filter (D-CEO-03) and advice G8 cross-check.
- Reference data, not user data: **no FK to users, NOT in the DPDP hard-delete cascade.**
- Materialized view refreshed nightly (after scrape) per the SQL comment; budget-optimizer screen 005 reads the view, not the base table.

### 3.10 `consent_audit` — post-deletion proof  (**APPEND-ONLY**, survives hard-delete)

REQ: COMP-04 ("audit log of deletions retained 365 days"), ARCH deletion flow (`audit_event{type:"hard_deleted", user_id_hash}`).

| Column | Type | Null | Notes |
|---|---|:---:|---|
| `id` | `BIGSERIAL` | no | PK. |
| `user_id_hash` | `TEXT` | no | SHA-256 of the deleted `users.id`. **NO FK** (the user row is gone). |
| `event_type` | `ENUM audit_event_t` | no | `{delete_requested, hard_deleted, export_generated}` (COMP-04/05). |
| `policy_version` | `TEXT` | yes | policy in force at the event. |
| `r2_objects_deleted` | `INTEGER` | yes | count purged from R2 (audit completeness). |
| `created_at` | `TIMESTAMPTZ` | no | `now()`. Retain 365 days (separate retention cron, longer than 30-day hard-delete). |

Index: `INDEX(user_id_hash)`, `INDEX(created_at)`. This table is **deliberately outside** the user-cascade — it is the deletion receipt.

### 3.11 `push_event` — FCM send/open log  (**APPEND-ONLY**, Phase 3)

REQ: RETAIN-01/02/04, INFRA-06. Token-of-record lives on `users.fcm_token`; this table is the per-send event log.

| Column | Type | Null | Notes |
|---|---|:---:|---|
| `id` | `BIGSERIAL` | no | PK. |
| `user_id` | `UUID` | no | FK→`users.id` ON DELETE CASCADE. |
| `fcm_token` | `TEXT` | no | token used for this send (snapshot — tokens rotate). |
| `push_kind` | `ENUM push_kind_t` | no | `{dinner_reminder_8pm, streak_milestone, protein_gap}` (RETAIN-02/03). |
| `copy_text` | `TEXT` | no | personalized body sent (RETAIN-02). |
| `gap_snapshot_json` | `JSONB` | yes | macro-gap at send time (ARCH push flow). |
| `sent_at` | `TIMESTAMPTZ` | yes | NULL until FCM accepts. |
| `delivered` | `BOOLEAN` | no | DEFAULT FALSE (RETAIN-04). |
| `opened_at` | `TIMESTAMPTZ` | yes | tap→deeplink (RETAIN-04 open-rate). |
| `created_at` | `TIMESTAMPTZ` | no | `now()`. **No `updated_at`** (append-only; `delivered`/`opened_at` are late-arriving event facts written once — acceptable single-write updates, not mutations of prior semantics; if strict-append needed, model opens as separate rows. **Locked: single-write update of `delivered`/`opened_at` permitted, all else append-only.**) |

Index: `INDEX(user_id, created_at DESC)`.

### 3.12 `streak_event` — own-rank cohort pill  (**APPEND-ONLY**, Phase 3)

REQ: D-CEO-02, RETAIN-03. Nightly cron at 22:00 UTC (03:30 IST) writes one row per qualifying user (D-CEO-02). `cohort_city` couples to `users.city` (single source of truth, shared w/ optimizer). Unknown-city users are OUT of cohort (no row written).

| Column | Type | Null | Notes |
|---|---|:---:|---|
| `id` | `BIGSERIAL` | no | PK. |
| `user_id` | `UUID` | no | FK→`users.id` ON DELETE CASCADE. |
| `event_date` | `DATE` | no | IST day the streak was evaluated. |
| `streak_len` | `INTEGER` | no | consecutive-day count (3/7/14 badges, RETAIN-03). |
| `cohort_city` | `TEXT` | no | snapshot of `users.city` at compute time (D-CEO-02). Row only written if `users.city IS NOT NULL` AND `leaderboard_opt_in=TRUE`. |
| `cohort_month_bucket` | `TEXT` | no | `YYYY-MM` cohort key (D-CEO-02 city-month-cohort percentile). |
| `cohort_rank` | `INTEGER` | yes | own-rank ("47th in Mumbai") — NULL if cohort < 5 opt-ins (pill hides, D-CEO-02). |
| `cohort_size` | `INTEGER` | yes | denominator for the pill. |
| `created_at` | `TIMESTAMPTZ` | no | `now()`. **No `updated_at`.** |

Index: `UNIQUE(user_id, event_date)` (one eval per day), `INDEX(cohort_city, cohort_month_bucket, streak_len DESC)` (percentile compute).

### 3.13 `whatsapp_session` — pre-install WhatsApp session  (mutable: 24h TTL; Phase-2 stub, Phase-4 wire)

REQ: D-CEO-01. **Normalized E.164 phone is the PK** (not a surrogate). `linked_user_id` is a **nullable FK** so the Phase-4 install merge is a *link*, not a row rewrite. 24h TTL (DPDP §5 legitimate-use). STOP-cascade clears the session.

| Column | Type | Null | Notes |
|---|---|:---:|---|
| `phone_e164` | `TEXT` | no | **PK.** normalized server-side (D-CEO-01). PII. |
| `linked_user_id` | `UUID` | yes | nullable FK→`users.id` ON DELETE CASCADE. Set at Phase-4 install-merge (link, not rewrite). |
| `wa_consent_granted` | `BOOLEAN` | no | DEFAULT FALSE; inline consent-footer acceptance (D-CEO-01 lawful basis). Mirrored to `consent_log` as `whatsapp_preinstall`. |
| `last_message_at` | `TIMESTAMPTZ` | no | drives 24h TTL eviction. |
| `expires_at` | `TIMESTAMPTZ` | no | `last_message_at + interval '24 hours'`. |
| `stopped` | `BOOLEAN` | no | DEFAULT FALSE; TRUE on STOP keyword → STOP-cascade purges session + halts sends (D-CEO-01). |
| `created_at` | `TIMESTAMPTZ` | no | `now()`. |
| `updated_at` | `TIMESTAMPTZ` | no | `now()`. |

Index: `INDEX(expires_at)` (TTL evict), `INDEX(linked_user_id)`.
**Phase-2 deliverable = table + a no-op stub route registration** (D-CEO-01 "table + stub"). No message handling until Phase 4 (post Meta Business Verification).

### 3.14 `weight_log` — OPEN

REQ: HISTORY-05 (manual weight log, Phase 3). Not yet schema-locked in any source. Minimal proposed shape: `{id BIGSERIAL, user_id UUID FK CASCADE, weight_kg NUMERIC(5,1), logged_on DATE, created_at}` with `UNIQUE(user_id, logged_on)` (daily granularity per HISTORY-05). **OPEN — needs founder** to confirm whether weight history is its own table (proposed) vs appended to `daily_summary`. Phase 3, not Phase 2 — does not block the baseline migration. Defaulting to standalone `weight_log` table unless founder objects.

---

## 4. Enum Catalog (Postgres native ENUM types — create before tables)

| Enum type | Values | Widen-now? | Used by |
|---|---|:---:|---|
| `goal_t` | `muscle_gain, weight_loss` | yes (V1.1) | `users.goal` |
| `diet_t` | `veg, egg, non_veg, vegan, lacto_veg_no_egg, lactose_intolerant` | yes (guardrails branch on all) | `users.diet_preference` |
| `activity_t` | `sedentary, light, moderate, active, very_active` | — | `users.activity_level` |
| `budget_t` | `b100_150, b150_250, b250_plus` | — | `users.budget_bucket` |
| `consent_type_t` | `photo, profile, analytics, ai_training, whatsapp_preinstall, leaderboard, age_18plus, disclaimer_ack` | **yes — DPDP-critical, never widen later** | `consent_log.consent_type` (8 values; `disclaimer_ack` added per G1 reconciliation — consents/acks ONLY, not profile values, not DSR events) |
| `consent_action_t` | `grant, revoke` | — | `consent_log.action` |
| `correction_kind_t` | `dish_name, portion_g, macro_value, advice_rating, off_whitelist_relabel` | yes (corpus) | `correction_event.correction_kind` |
| `correction_source_t` | `user_edit, founder_woz, rd_audit, eval_replay` | yes (corpus) | `correction_event.source` |
| `meal_status_t` | `pending, analyzing, done, failed` | — (`analyzing` added per G4) | `meal_photo.status` |
| `meal_slot_t` | `breakfast, lunch, dinner, snack` | — | `meal_photo.meal_slot` |
| `ref_obj_t` | `coin, palm, spoon, none` | — | `meal_photo.reference_object` |
| `ai_stage_t` | `vision, advice, daily_summary, decomposition_llm` | — | `ai_call_log.stage` |
| `ai_call_status_t` | `ok, rate_limited, server_error, validation_error, timeout, aggregate_timeout, fallback_template` | — (`fallback_used`→`fallback_template` per G3) | `ai_call_log.status` |
| `audit_event_t` | `delete_requested, hard_deleted, export_generated` | — | `consent_audit.event_type` |
| `push_kind_t` | `dinner_reminder_8pm, streak_milestone, protein_gap` | — | `push_event.push_kind` (P3) |

Note: `veg_protein_prices` uses **CHECK constraints** (not native enums) for `source_platform`/`category` per its committed SQL — keep as-is, do not convert.

---

## 5. Alembic Migration Order (locked)

Topological by FK dependency. One logical migration per group; group 1 is the baseline (`alembic revision --autogenerate` then hand-verify — autogenerate alone is anti-pattern, review every op).

1. **`0001_enums_and_users`** — create ALL enum types (§4) first, then `users`. (Enums must precede any table referencing them.)
2. **`0002_meal_consent`** — `meal_photo`, `consent_log` (both FK→users).
3. **`0003_summary_correction_ai`** — `daily_summary`, `correction_event` (FK→users + meal_photo, so after 0002), `ai_call_log` (FK→users + meal_photo).
4. **`0004_ai_infra`** — `provider_quota`, `vision_cache` (no user FK; order-independent but grouped).
5. **`0005_veg_protein_prices`** — table + indexes + materialized view + trigger (verbatim from `data/veg_protein_prices_schema.sql`). No user FK.
6. **`0006_consent_audit`** — `consent_audit` (no FK; survives delete).
7. **`0007_whatsapp_session_stub`** — `whatsapp_session` (FK→users nullable). Phase-2 stub.
8. **`0008_push_streak`** — `push_event`, `streak_event` (FK→users + meal_photo). **Phase 3** — do not run in the P2 baseline.
9. **`0009_weight_log`** — **Phase 3, OPEN** (pending founder confirm §3.14).

Append-only-trigger migration (§7) runs **after** the tables it guards exist; fold into each table's creating migration or a single `0003b_append_only_triggers` after group 3 (and re-applied for `push_event`/`streak_event` in 0008).

---

## 6. DPDP Hard-Delete FK Cascade Order (COMP-04, AUTH-05)

Trigger: `users.soft_delete_at + 30 days < now()` (GitHub Actions cron, NOT APScheduler — D-03 banner). The cron must: (a) derive R2 keys from `meal_photo.r2_key` and purge R2 objects under `meals/{user_id}/` **first** (storage before DB, so a DB row always points to deletable bytes), then (b) delete the `users` row and let FK `ON DELETE` rules cascade.

**Cascade behavior per FK (declared on the FK, executed by deleting `users`):**

```
DELETE users (id = X)
  └─ ON DELETE CASCADE → meal_photo            (then its children below)
        └─ ON DELETE CASCADE → correction_event (meal_photo_id)
        └─ ON DELETE SET NULL → ai_call_log     (meal_photo_id)
  └─ ON DELETE SET NULL → consent_log           (user_id → NULL; row SURVIVES PII-stripped — user_id_hash, written at INSERT, is the retained consent proof. G1/G7 reconciliation: NOT cascade-deleted, else §3.2's "user_id_hash survives" was a lie.)
  └─ ON DELETE CASCADE → daily_summary
  └─ ON DELETE CASCADE → correction_event       (user_id path — same rows as via meal_photo; CASCADE is idempotent)
  └─ ON DELETE CASCADE → push_event             (P3)
  └─ ON DELETE CASCADE → streak_event           (P3)
  └─ ON DELETE SET NULL → ai_call_log           (user_id — cost ledger survives, de-identified)
  └─ ON DELETE CASCADE → whatsapp_session        (linked_user_id)

SURVIVES (no FK / SET NULL — by design):
  • consent_log         — user_id SET NULL; row retained PII-stripped (user_id_hash) as DPDP §6 verifiable-consent proof; the full grant/revoke history survives de-identified (G7 reconciliation)
  • consent_audit       — deletion receipt, user_id_hash only, retain 365d (COMP-04); event_type ∈ {delete_requested, hard_deleted, export_generated}
  • ai_call_log         — user_id/meal_photo_id SET NULL; cost aggregates intact
  • vision_cache        — hashes only, no PII; TTL-evicts in 24h anyway
  • veg_protein_prices  — reference data
  • provider_quota      — system counters
```

> **Purge execution (reconciled with COMPLIANCE-SPEC §4.3, 2026-05-29):** the GitHub-Actions-triggered purge service does **explicit ordered deletes** — (1) harvest R2 keys + purge R2 objects under `meals/{user_id}/` FIRST, (2) delete CASCADE-children, (3) `consent_log` user_id → NULL (retain proof), (4) `ai_call_log` user_id/meal_photo_id → NULL, (5) INSERT `consent_audit{event_type:hard_deleted}`, (6) delete `users` last. FK `ON DELETE` clauses above are declared as defense-in-depth so a bare `DELETE users` still does the right thing; the service's explicit ordering guarantees R2-harvest-before-row-loss + consent-proof retention. (Earlier COMPLIANCE text proposing `ON DELETE RESTRICT` + an `audit_event` table is superseded by this: clauses are CASCADE/SET NULL as listed, the audit table is `consent_audit`.)

**Pre-delete copy step:** before deleting, the compliance service INSERTs a `consent_audit{event_type:hard_deleted, user_id_hash, r2_objects_deleted}` row so the receipt exists after cascade. Detailed behavior/runbook → `COMPLIANCE-SPEC.md` (this doc owns the *schema + cascade topology* only).

---

## 7. Append-Only Enforcement (convention + DB trigger)

Append-only tables: **`consent_log`, `correction_event`, `ai_call_log`, `consent_audit`, `push_event`*, `streak_event`** (* `push_event` permits single-write update of `delivered`/`opened_at` only, §3.11).

**Convention (primary):** application code NEVER issues `UPDATE`/`DELETE` against these tables. SQLAlchemy models for them expose no update methods; repository layer offers `insert()` only. Reviewers reject any `update()`/`delete()` on these models (add to PR checklist + a `ruff`/grep CI rule analogous to AI-SPEC G11).

**DB trigger (defense-in-depth):** a `BEFORE UPDATE OR DELETE` trigger that `RAISE EXCEPTION` — with two carve-outs:
1. the DPDP hard-delete cascade (cascade DELETE must be allowed) → trigger checks `current_setting('app.allow_purge', true) = 'on'`; the cron sets this session GUC before cascading.
2. `push_event.delivered`/`opened_at` single-write (allow UPDATE only when those are the sole changed columns).

```sql
-- pattern (apply per append-only table; tune column carve-outs)
CREATE OR REPLACE FUNCTION trg_append_only_guard()
RETURNS TRIGGER AS $$
BEGIN
  IF current_setting('app.allow_purge', true) = 'on' THEN
    RETURN OLD;  -- DPDP cascade purge path
  END IF;
  RAISE EXCEPTION 'append-only table %, % blocked', TG_TABLE_NAME, TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER guard_consent_log
  BEFORE UPDATE OR DELETE ON consent_log
  FOR EACH ROW EXECUTE FUNCTION trg_append_only_guard();
-- repeat for correction_event, ai_call_log, consent_audit, streak_event
```

`provider_quota`, `vision_cache`, `daily_summary`, `users`, `meal_photo`, `veg_protein_prices`, `whatsapp_session` are **mutable** — no guard trigger; they keep `updated_at` auto-touch triggers instead.

---

## 8. Cross-Source Reconciliation Summary

- **`streak` (INFRA-06) = `streak_event` (D-CEO-02):** renamed to the locked append-only event shape; bare counter is derived. Deferred to P3.
- **`push_event`:** named in INFRA-06 (P2 list) but RETAIN-* are Phase 3 → **deferred to P3** here. Documented deviation (§1).
- **`ai_call_log`/`provider_quota`/`vision_cache`:** authored from AI-SPEC §4/§4b/§7 verbatim; `ai_call_status_t` gains `aggregate_timeout` per audit.
- **`food_id` vocabulary unified:** `veg_protein_prices.food_id` = `ifct_lookup.json` ingredient key = `dish_decomposition.json` `ifct_id`. Single namespace; seed-time validation required.
- **`diet_preference` (users) ↔ `diet_compatible` (prices):** `diet_t` enum maps to `{VG,EG,NV,VN}` codes for optimizer + G8.
- **R2 provenance** (`r2_jurisdiction='india'`, `r2_region='mumbai'`) on `meal_photo` operationalizes COMP-01 boot check + AP#2/#5.
- **Cost gate** (AI-SPEC M3, ≤₹15/user/mo) reads `ai_call_log` (price computed at read-time from a pricing table — that pricing table is config, not a DB table here).
