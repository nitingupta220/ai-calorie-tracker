# COMPLIANCE-SPEC — DPDP + CDSCO/ASCI Implementation Contract

**Status:** LOCKED for Phase 2 build. Dev builds from this without asking questions.
**Domain:** DPDP Act 2023 data-rights plumbing (delete / export / consent ledger / region pin / cross-border disclosure) + CDSCO/ASCI medical-claim discipline. Phase 2 backend spine.
**Owner doc:** This file owns the COMP-* requirement family + the consent-ledger *consumer* contract. It does NOT own the `consent_log` / `users` table DDL (that is **MODEL-SPEC.md**) nor the GitHub Actions runner / region-pin env wiring (that is **INFRA-OPS-SPEC.md**). Cross-linked, not duplicated.

**Requirements covered:** COMP-01, COMP-03, COMP-04, COMP-05, COMP-08, COMP-09 (Phase 2) + the Phase-3/4 hooks for COMP-02, COMP-06, COMP-07.
**Decisions honored:** D-01 (Render Singapore + DPDP monitor), D-02 (Supabase Mumbai), D-04 (R2 india jurisdiction), D-05 (Firebase ID token = Bearer), D-CEO-01 (WhatsApp Cloud API + `whatsapp_session` 24h TTL).
**Superseded items honored (per ARCHITECTURE.md banner):** cron = **GitHub Actions scheduled workflow**, NOT in-process APScheduler (Render free sleeps — a 3am in-process job never fires). Auth = Firebase ID token verified per-request, no app-minted JWT.

> **Sibling specs — read alongside this, do not duplicate:**
> - `MODEL-SPEC.md` — owns `users`, `consent_log`, `meal_photo`, `daily_summary`, `streak`, `push_event`, `correction_event`, `whatsapp_session`, `streak_event` DDL; the canonical `consent_type` enum; FK `ON DELETE` clauses + Alembic migration order. This spec consumes those; where this spec names a column or enum value, MODEL-SPEC is the source of truth and MUST match.
> - `INFRA-OPS-SPEC.md` — owns the GitHub Actions runner config, repo secrets, Render/Supabase/R2 region env vars, the cron-ping keep-alive (D-03), and the CI workflow shell. This spec defines *what the compliance jobs/lints do*; INFRA-OPS defines *where they run*.
> - `01-AI-SPEC.md` §6 G6/G7/G10/G11 — owns the *runtime* banned-words guardrail on live advice `text`. This spec (COMP-08) owns the *build-time string lint* that gates committed source/copy. Two layers, both required.

---

## 0. Constants — single source of truth

These are committed as literal constants. Do NOT re-type the strings inline anywhere; import the constant.

### 0.1 Canonical disclaimer (COMP-06, ONBOARD-05, ADVICE-06)

One string, three surfaces (advice-card footer + onboarding ack + Play Store listing). Locked from DESIGN.md §"Compliance copy (legal lock)".

```python
# server/app/compliance/constants.py
DISCLAIMER_TEXT: str = "Not medical advice. Consult a dietitian for medical conditions."
DISCLAIMER_VERSION: str = "v1"   # bump on any wording change; logged with onboarding ack
```

- Mobile imports the same literal via a generated `constants.ts` (build step copies the Python value; OPEN if founder prefers hand-sync — see §8). Until then, mobile hard-codes the identical string and the COMP-08 lint asserts byte-equality across both files.
- Rendering contract (DESIGN.md): mono 10px, muted, top-border separator inside the advice block. Owned by DESIGN.md; named here only so the dev knows the *same* constant feeds it.
- ADVICE-06: footer is **permanent** on every advice card — not conditional, not dismissable.
- ONBOARD-05: shown once during onboarding; on ack, write a `consent_log` row `consent_type='disclaimer_ack'` with `purpose_text_hash = sha256(DISCLAIMER_TEXT)` (see §3).

### 0.2 CDSCO/ASCI banned-words list (COMP-08, G6/G11)

Single canonical list, consumed by both the build-time string lint (this spec) and the runtime advice guardrail (`01-AI-SPEC.md` G6). Keep them importing the *same* module so they never drift.

```python
# server/app/compliance/banned_words.py
# Founder-mandated minimum set per task brief: {treat, cure, diagnose, medicine, drug}
# Extended per AI-SPEC §6 G6 for full CDSCO/SaMD coverage:
BANNED_WORDS: tuple[str, ...] = (
    "treat", "cure", "diagnose", "medicine", "drug",          # G11/COMP-08 mandated core
    "disease", "diabetes", "cholesterol", "medication",        # AI-SPEC G6 extension
)
# Compiled word-boundary, case-insensitive:
BANNED_RE = re.compile(r"\b(" + "|".join(BANNED_WORDS) + r")\b", re.IGNORECASE)
```

- **Scope split is deliberate:** COMP-08 build lint (§5) scans *committed strings* (in-app copy, onboarding text, store-listing files). AI-SPEC G6 scans *runtime LLM advice output*. Same list, two enforcement points.
- `"BP"` from AI-SPEC G6 is intentionally **excluded from the build-time word-boundary lint** (false-positives on "BP" substrings in unrelated copy); it stays a runtime-only token in G6. Documented so the dev does not "fix" the gap.
- `"deficiency"` is a runtime-only soft-flag (AI-SPEC F6) — NOT in the build lint (the word legitimately appears in privacy/onboarding copy like "protein deficiency target"). Do not add it to `BANNED_WORDS`.

---

## 1. Cross-border processor disclosure (COMP-02 input · D-01 · D-CEO-01)

The privacy policy (authored Phase 3 for COMP-02, but its processor list is **locked here now** so the dev wiring region-pin + WhatsApp knows the legal posture) MUST name every cross-border + third-party processor:

| Processor | Role | Region | DPDP posture | Source |
|---|---|---|---|---|
| **Render** (compute) | FastAPI request processing | **Singapore** | Cross-border. Lawful basis = consent + this disclosure. No final MeitY whitelist for Singapore as of 2026-05. Migration runbook §6 on trigger. | D-01 |
| **Supabase** (Postgres) | PII at rest (profile, logs, consent ledger) | **Mumbai, India** | In-country. DPDP residency satisfied. | D-02 |
| **Cloudflare R2** (photos) | Meal-photo blobs | **India jurisdiction** (`<acct>.in.r2.cloudflarestorage.com`) | In-country. | D-04 |
| **Google / Gemini** (AI Studio) | Vision + paid-fallback text inference | Google global (cross-border) | Photo bytes + de-identified context leave India for inference. Disclose. Prompts carry NO direct PII (AI-SPEC §Regulatory: only `user_id` + macros + diet pref). | CLAUDE.md AI stack |
| **Groq / OpenRouter** | Text advice inference (free-first + fallback) | US/global (cross-border) | De-identified context only. Disclose. | CLAUDE.md AI stack |
| **Firebase** (Google) | Phone OTP + FCM | Google global | Phone number is PII; processed by Google for auth. Disclose. | D-05 |
| **Meta** (WhatsApp Cloud API) | Inbound photo + phone of WhatsApp senders | Meta global (cross-border) | Disclose as named processor. **`whatsapp_session` 24h TTL** disclosed explicitly. Pre-install lawful basis = inline consent footer (§2). | D-CEO-01 |
| **Sentry / PostHog** | Crash + product analytics | global | Analytics consent toggle gates PostHog identify; disclose. | CLAUDE.md |

**Locked privacy-policy clauses (dev hands these to the founder/copy for COMP-02):**
1. Names Singapore (Render compute) as the cross-border processing region for app requests.
2. Names Meta (WhatsApp), Google/Gemini, Groq, OpenRouter as cross-border AI/messaging processors.
3. States the 24h `whatsapp_session` TTL: "WhatsApp photos and the sending number are auto-deleted within 24 hours."
4. States DPDP rights: access (export, COMP-05), erasure (delete, COMP-04), consent revoke (COMP-09), grievance contact.
5. Lists the alternative regions auto-migration would route to (Fly bom1 / Render-India) per D-01 monitoring contract.

COMP-02 (policy *live at bundled URL*) is Phase 3; the **content above is locked in Phase 2** so nothing blocks later.

---

## 2. WhatsApp pre-install consent (D-CEO-01 · COMP-03)

The `whatsapp_session` table + `POST /whatsapp/webhook` route are stubbed in Phase 2 (DDL owned by MODEL-SPEC), wired after Meta verification in Phase 4. Compliance contract for the message handler:

### 2.1 Inline consent footer (appended to every Bhog WhatsApp reply)

```python
WHATSAPP_CONSENT_FOOTER: str = (
    "By messaging you agree to Bhog processing this photo per privacy.bhog.app. "
    "Reply STOP to delete."
)
```

- **Posture decision (LOCKED, do not freelance):** D-CEO-01 frames this as DPDP §5 *legitimate-use* via inline footer. **This spec upgrades to RECOMMENDED EXPLICIT opt-in** because the legitimate-use basis for unsolicited inbound health-photo processing is legally untested under DPDP. Implementation: **first inbound message from a new number gets a consent gate** — Bhog replies with the footer + "Reply YES to continue or STOP to delete," and does NOT run the vision pipeline until a `YES`. Subsequent messages append the footer only. This is a one-extra-turn cost that hardens the lawful basis. If founder explicitly accepts pure legitimate-use risk, the gate collapses to footer-only — flag tracked in §8.

### 2.2 STOP keyword

- Inbound body matching `^\s*stop\s*$` (case-insensitive) → **immediate** `whatsapp_session` row cascade-delete for that sender's `phone_e164` (or hashed key per MODEL-SPEC) + any R2 objects written for that session + a `consent_log` row `consent_type='whatsapp_preinstall', action='revoke'` (enum name per §3.1 / MODEL-SPEC).
- Reply once: "Deleted. Reply with a meal photo anytime to start again." Then stop processing.
- STOP delete path reuses the §4 purge primitive scoped to one session (not the whole 30-day cron).

### 2.3 24h TTL purge

- `whatsapp_session` rows + their R2 photo objects auto-purge at `created_at + 24h`. Runs as a **dedicated job in the same GitHub Actions purge workflow** (§4), not a separate cron. Disclosed in privacy policy §1.4.

---

## 3. Consent ledger contract (COMP-03 · COMP-09)

`consent_log` is **append-only** — never UPDATE, never DELETE a consent row except via the §4 PII-strip on hard-delete (which rewrites `user_id` → hash, retaining the row as proof). DDL owned by MODEL-SPEC.md; this spec locks the *enum reconciliation* and the *write contract*.

### 3.1 `consent_type` enum reconciliation (LOCKED)

The onboarding consent toggles (ONBOARD-03) MUST be a **subset** of the `consent_log.consent_type` enum. **MODEL-SPEC.md owns the Postgres `ENUM` type and WINS on conflict; this is the reconciled value set (locked 2026-05-29, reconciliation G1):**

```
consent_type_t ∈ {           # consents / acknowledgements ONLY — 8 values
  'photo',              # ONBOARD-03 toggle — meal-photo processing
  'profile',            # ONBOARD-03 toggle — profile-data processing (height/weight/age/goal/diet/budget ALL covered by this ONE consent)
  'analytics',          # ONBOARD-03 toggle — PostHog/Sentry
  'ai_training',        # ONBOARD-03 toggle — DEFAULT OFF (COMP-09 / DPDP explicit opt-in)
  'age_18plus',         # AUTH-04 hard-gate attestation
  'disclaimer_ack',     # ONBOARD-05 CDSCO/ASCI disclaimer acknowledgement
  'whatsapp_preinstall',# D-CEO-01 inbound WhatsApp processing (NOTE: name is whatsapp_preinstall, NOT whatsapp_consent)
  'leaderboard'         # D-CEO-02 own-rank cohort opt-in — DEFAULT OFF
}
action ∈ { 'grant', 'revoke' }   # NO 'event' action
```

- **Onboarding subset** (ONBOARD-03 toggles) = `{photo, profile, analytics, ai_training, age_18plus, disclaimer_ack}` (6 toggles). `whatsapp_preinstall` + `leaderboard` are granted outside onboarding (WhatsApp first-inbound; Settings respectively).
- **`budget_bucket` / `diet_preference` / `goal` are NOT consent types** — they are profile *data* the user provides, stored as columns on `users` (MODEL-SPEC §3.1) and covered by the single `'profile'` consent. Do not log a consent row per profile field. (Reclassified from the earlier draft per G1.)
- **`delete_requested` / `data_exported` / `hard_deleted` are NOT consent types** — they are DSR audit *events*, logged to `consent_audit.event_type` (`audit_event_t`, MODEL-SPEC §3.10), NOT `consent_log`. (Reclassified per G1.)
- This 8-value enum is the **never-widen DPDP-critical set** — declared in full now (MODEL-SPEC §4). If you ever think you need a 9th, stop: it almost certainly belongs in `users` (profile data) or `consent_audit` (an event), not here.

### 3.2 Row write contract

Every consent grant / revoke writes one row. **Column shape is owned by MODEL-SPEC §3.2 — do not redefine here.** The fields (for reference): `id BIGSERIAL`, `user_id UUID` (FK→users, **ON DELETE SET NULL** — row survives PII-stripped, §4.3), `user_id_hash TEXT` (written at INSERT; the retained proof), `consent_type consent_type_t` (§3.1), `action consent_action_t` = `{grant, revoke}`, `policy_version`, `purpose_text_hash`, `app_version`, `source_screen`, `created_at`. **Append-only — no `updated_at`, never UPDATE except the §4.3 SET NULL.**

- **`purpose_text_hash` makes copy versionable.** The exact wording the user saw is hashed at write time. When copy changes, the schema does NOT change — only new rows get a new hash. This lets the privacy/onboarding *copy* lag the *schema*. Store the hash, not the full text; copy versions live in `server/app/compliance/consent_copy/{version}.json` (maps hash → full text for audit).
- **DSR events do NOT write here.** A delete-request, export, or hard-delete writes a `consent_audit` row (`event_type` ∈ `audit_event_t`), never a `consent_log` row. There is no `action='event'`. (G1 reconciliation.)
- COMP-09: `ai_training` defaults OFF — **no grant row** until the user toggles it on in Settings. Revoke writes `action='revoke'` AND triggers a purge of that user's data from any training-corpus export (§4.4).
- Every toggle change (onboarding or Settings) appends a new row. Current state = latest row per `(user_id, consent_type)` by `created_at`.

---

## 4. Hard-delete + 30-day purge (COMP-04 · AUTH-05)

### 4.1 Soft-delete (synchronous, on user action)

**User-facing route = `DELETE /me`** (API-SPEC §5.5 owns the route shape; this spec owns the behavior). Reconciliation G6: there is NO `POST /compliance/delete` user route — the user-facing verb is `DELETE /me`. `/internal/compliance/purge` (§4.2) is the separate internal cron endpoint.

```
DELETE /me                    # auth: Firebase ID token Bearer (fresh-OTP recency OPEN §8 — default any valid token)
  → users.soft_delete_at = now()
  → insert consent_audit { event_type:'delete_requested', user_id_hash:sha256(user_id+PURGE_SALT), policy_version }
  → 202 Accepted { status:"scheduled", hard_delete_after:<ts+30d ISO> }
```

- The delete-request is recorded as a **`consent_audit` event** (`audit_event_t='delete_requested'`), NOT a `consent_log` row (G1). `users.soft_delete_at` is the operative soft-delete marker.
- User immediately loses app access: `current_user` rejects any token whose `user.soft_delete_at IS NOT NULL` with **`403 account_deleted`** (matches API-SPEC §2 error enum — not a bespoke `ACCOUNT_PENDING_DELETION` code). Data physically remains ≤30 days (DPDP grace + backup integrity).

### 4.2 Hard-delete job — GitHub Actions scheduled workflow (NOT APScheduler)

**This is the load-bearing correction.** Render free sleeps after 15min idle; an in-process 3am cron never fires. The purge runs as a **GitHub Actions scheduled workflow** that calls an authenticated backend endpoint (which wakes Render via the call itself). Runner config + secret = INFRA-OPS-SPEC.md.

```yaml
# .github/workflows/dpdp-purge.yml   (shell owned by INFRA-OPS-SPEC; logic contract here)
on:
  schedule:
    - cron: "0 22 * * *"   # 22:00 UTC = 03:30 IST daily (off-peak, post keep-alive window)
  workflow_dispatch: {}     # manual trigger for the fixture test + ad-hoc
jobs:
  purge:
    steps:
      - run: |
          curl -fsS -X POST "$RENDER_BASE_URL/internal/compliance/purge" \
            -H "Authorization: Bearer $PURGE_JOB_TOKEN" \
            --max-time 180 --retry 3 --retry-delay 30
```

- **Auth on the endpoint:** a static `PURGE_JOB_TOKEN` shared secret (GitHub repo secret → Render env), NOT a Firebase user token (no user context). Endpoint path `/internal/compliance/purge` is gated by constant-time compare against `settings.PURGE_JOB_TOKEN`; 401 otherwise. INFRA-OPS owns secret rotation.
- Endpoint is **idempotent** — selects `users WHERE soft_delete_at IS NOT NULL AND soft_delete_at + interval '30 days' < now()`, purges each, safe to re-run.
- The `dpdp-purge.yml` workflow also runs the **24h WhatsApp TTL purge** (§2.3) as a second step in the same job.

### 4.3 Purge order — FK cascade (LOCKED · align with MODEL-SPEC migration order)

Per-user purge runs in a single DB transaction. Order MUST respect FK dependencies; MODEL-SPEC.md owns the `ON DELETE` clauses and the matching Alembic migration creation order. The agreed cascade:

**R2 first (external, no transaction):**
1. `R2.delete_objects(prefix=f"meals/{user_id}/")` — all photo blobs for the user (keys derived from `meal_photo` rows BEFORE Postgres delete).

**Postgres, child → parent (so FK never blocks):**
2. `correction_event`   (FK → meal_photo / user) — CASCADE
3. `meal_photo`         (FK → user; R2 keys already harvested in step 1) — CASCADE
4. `daily_summary`      (FK → user) — CASCADE
5. `streak_event`       (FK → user; Phase 3) — CASCADE   *(no bare `streak` table — it is derived; MODEL-SPEC §1)*
6. `push_event`         (FK → user; Phase 3) — CASCADE
7. `whatsapp_session`   (FK → linked_user_id, if linked) — CASCADE
8. **`consent_log` — NOT deleted; `user_id` → NULL (`ON DELETE SET NULL`).** The `user_id_hash` written at INSERT time already de-identifies the row; the full grant/revoke history survives as DPDP §6 verifiable-consent proof. (No in-place UPDATE needed — the FK SET NULL + pre-existing hash does it.) `ai_call_log` likewise SET NULL (cost ledger survives).
9. `users`              (parent, deleted last)

**Then audit:**
10. `INSERT INTO consent_audit { event_type:'hard_deleted', user_id_hash:sha256(user_id+PURGE_SALT), r2_objects_deleted:<n>, created_at:now() }` — retained **365 days** (COMP-04). Table is **`consent_audit`** (MODEL-SPEC §3.10, enum `audit_event_t`) — NOT a separate `audit_event` table.

> **Cascade design (reconciled with MODEL-SPEC §6, 2026-05-29 — supersedes the earlier `ON DELETE RESTRICT` proposal):** child FKs are declared `ON DELETE CASCADE` (steps 2-7) and `ON DELETE SET NULL` for `consent_log` + `ai_call_log` (step 8). The purge **service still does explicit ordered operations** — R2-harvest FIRST (step 1, before `meal_photo` rows vanish), then it may rely on cascade OR delete explicitly; the SET NULL on `consent_log`/`ai_call_log` guarantees those survive de-identified rather than cascading away. The CASCADE clauses are defense-in-depth so a bare `DELETE users` is still correct. The append-only guard trigger (MODEL-SPEC §7) permits the cascade via the `app.allow_purge` session GUC.

### 4.4 AI-training-corpus purge (COMP-09)

On `ai_training` revoke OR hard-delete: remove the user's rows from any training-corpus export (`evals/datasets/*.parquet` / `correction_event` exports tagged with `train_opt_in=true`). Phase 2 wires the flag; the export filter MUST exclude `user_id` once revoked. Since `correction_event` is purged at step 2 anyway on full delete, the standalone concern is the *revoke-but-keep-account* path.

### 4.5 Fixture test (REQUIRED — task-mandated)

`server/tests/compliance/test_hard_delete.py`:

```
def test_hard_delete_purges_r2_and_postgres_keeps_stripped_consent(db, r2_stub):
    # 1. seed a user with: 2 meal_photo (+ R2 objects), 1 correction_event,
    #    daily_summary, streak, push_event, 3 consent_log rows.
    # 2. back-date users.soft_delete_at = now() - interval '31 days'
    # 3. POST /internal/compliance/purge  (Bearer PURGE_JOB_TOKEN)
    # ASSERT:
    #   - r2_stub has zero objects under meals/{user_id}/
    #   - users / meal_photo / correction_event / daily_summary / streak
    #     / push_event rows for user_id == 0
    #   - consent_log rows for user STILL EXIST (count unchanged) BUT
    #       row.user_id IS NULL  AND  row.user_id_hash == sha256(orig+salt)
    #       AND consent_type/action/purpose_text_hash/created_at preserved
    #   - consent_audit has one {event_type:'hard_deleted', user_id_hash:...} row
    # 4. re-run purge → idempotent, no error, no double audit row for same hash/day
```

Runs in Phase 2 CI on `server/app/compliance/**` + `server/tests/compliance/**` PR paths.

---

## 5. Export my data (COMP-05 · DPDP Right to Access)

### 5.1 Endpoint

**User-facing route = `GET /me/export`** (API-SPEC §5.6 owns the route; G6 reconciliation — NOT `POST /compliance/export`). API-SPEC locks the **Phase-2 default = inline JSON** (`status:"ready"`, body populated, synchronous — no email dependency at alpha). The emailed-link variant below is the Phase-3 upgrade.

```
GET /me/export                # auth: Firebase ID token Bearer
  → build export JSON (§5.2) synchronously
  → write consent_audit { event_type:'export_generated', user_id_hash, created_at }
  → 200 { status:"ready", download:<inline JSON> }
```

Phase-3 emailed variant: upload to a short-TTL (15-min) presigned R2 GET URL under `exports/{user_id}/{ts}.json`, email the link (transport OPEN §5.3), return `status:"emailed"`. Export blob auto-purges via R2 lifecycle (1 day). The export event is a **`consent_audit` row** (`audit_event_t='export_generated'`), NOT a `consent_log` row (G1).

### 5.2 Export JSON shape (LOCKED)

```json
{
  "export_version": "1",
  "generated_at": "2026-05-29T11:16:00+05:30",
  "user": {
    "user_id": "uuid",
    "phone_e164": "+91XXXXXXXXXX",
    "created_at": "...",
    "goal": "muscle_gain",
    "height_cm": 175, "weight_kg": 72, "age": 24,
    "activity_level": "moderate",
    "diet_preference": "veg",
    "budget_bucket": "150-250"
  },
  "consents": [
    { "consent_type": "photo_upload", "action": "grant", "granted": true,
      "purpose_text_hash": "sha256:...", "created_at": "..." }
  ],
  "meals": [
    { "meal_id": "uuid", "logged_at": "...", "dish_name": "paneer butter masala",
      "portion_g": 200, "kcal": 480, "protein_g": 18, "carbs_g": 22, "fat_g": 34,
      "photo_url": "presigned-r2-get-15min", "advice_text": "...",
      "advice_prompt_version": "v1" }
  ],
  "corrections": [
    { "correction_id": "uuid", "meal_id": "uuid", "field": "protein_g",
      "old_value": 18, "new_value": 22, "created_at": "..." }
  ],
  "weights": [ { "weight_kg": 72.0, "logged_at": "..." } ],
  "water": [ { "ml": 250, "logged_at": "..." } ],
  "streaks": { "current": 5, "best": 7 }
}
```

- Includes profile + meal logs + corrections (task-required) + weight + water + streak for completeness. Excludes server-internal cost/provider attribution (`INFRA-04`) — not user PII, not in scope of Right to Access.
- `photo_url` values are fresh 15-min presigned R2 GET URLs, regenerated at export time (never store raw blob in JSON — keeps export small + respects R2 jurisdiction).

### 5.3 Email transport — **OPEN — needs founder**

Need a free-tier transactional email sender for the export download link (and §4 hard-delete confirmation email, PITFALLS line 282). Candidates, all zero-CC-friendly:
- **Resend** — 3,000 emails/mo free, 100/day; simplest API; React-email optional. **Recommended.**
- **AWS SES** — 3,000/mo free first 12mo then pay; needs AWS account + domain verify; heavier.
- **Brevo (Sendinblue)** — 300/day free, India-friendly.

**Recommendation: Resend** (lowest friction, no CC). Mark OPEN until founder confirms domain + picks. The endpoint codes against an `EmailTransport` Protocol (`server/app/compliance/email.py`) so the choice is one-file-swappable — do NOT hard-code the vendor SDK in the export service.

---

## 6. DPDP cross-border migration runbook (D-01 · Phase 2 Week 1 deliverable)

Deliverable file: `.planning/decisions/dpdp-migration-runbook.md` (this spec defines its required contents; the runbook itself is the Week-1 artifact).

- **Monitoring contract:** founder subscribes to **MeitY press releases + DPDP rules notifications** + one Indian privacy-tech newsletter; reviews monthly. (D-01 point 1.)
- **Trigger:** ANY MeitY notification under DPDP §16 that **restricts, qualifies, or fails to whitelist Singapore** as a permitted transfer destination → execute migration within the notification's compliance window.
- **Migration targets (in order of preference):**
  1. **Render India region** (if launched by trigger date) — same platform, minimal change: repoint region, redeploy. Zero code change.
  2. **Fly.io `bom1` (Mumbai)** — CC-gated (acceptable at trigger because this is a regulatory forcing function, not a budget choice). Recipe: `fly launch` with `primary_region = "bom1"`, port the Render env vars, swap `RENDER_BASE_URL` → Fly app URL in the GitHub Actions secrets (INFRA-OPS), redeploy. Postgres (Supabase Mumbai) + R2 (india) already in-country — only compute moves.
- **What does NOT move:** Supabase (already Mumbai), R2 (already india), Firebase/Gemini/Groq (these are independently-disclosed cross-border AI/auth processors, governed by consent + §1 disclosure, not by the compute-region notification).
- **DNS/secrets cutover checklist** (runbook enumerates): update `RENDER_BASE_URL`/Fly URL in GitHub secrets, update mobile API base URL via OTA (`expo-updates`), update privacy-policy region clause (§1.1), re-run COMP-01 boot check (§7) against the new region.

---

## 7. Region-pin boot check (COMP-01)

Automated check at FastAPI boot — **deploy fails (process exits non-zero) on mismatch.** Logic owned here; env vars owned by INFRA-OPS-SPEC.

**Env var names are owned by INFRA-OPS-SPEC §6b** (G2 reconciliation — use these exact names, NOT `R2_ENDPOINT`/`SUPABASE_REGION`): `R2_ENDPOINT_URL`, `SUPABASE_PROJECT_REF`, `ALLOWED_SUPABASE_REFS` (comma-separated Mumbai-project allow-list). The canonical implementation lives in INFRA-OPS §6b `assert_region_pin()`; this spec owns only the DPDP rationale. For reference, the check:

```python
# server/app/compliance/region_check.py — called in app lifespan startup
# (canonical source: INFRA-OPS-SPEC §6b; names MUST match there)
from urllib.parse import urlparse
def assert_region_pin(settings) -> None:
    # R2 endpoint must be the india JURISDICTION host (D-04) — bare *.r2.cloudflarestorage.com FAILS
    host = urlparse(settings.R2_ENDPOINT_URL).hostname or ""
    if not host.endswith(".in.r2.cloudflarestorage.com"):
        raise RuntimeError("COMP-01: R2 endpoint is not india-jurisdiction")
    # Supabase project ref must be in the founder-maintained Mumbai allow-list (D-02)
    allowed = {r.strip() for r in settings.ALLOWED_SUPABASE_REFS.split(",") if r.strip()}
    if settings.SUPABASE_PROJECT_REF not in allowed:
        raise RuntimeError("COMP-01: Supabase ref not in Mumbai allow-list")
    # fail-closed: any RuntimeError → uvicorn exits non-zero before serving
```

- This is the ONLY region assertion; it gates *storage residency*, not compute (compute-region cross-border is handled by §1 disclosure + §6 runbook, not by a hard fail — Render Singapore is a *known, disclosed* posture, not a misconfiguration).
- Runs on every boot including Render cold-start wakes (cheap, ~µs).

---

## 8. CDSCO/ASCI build-time string lint (COMP-08)

Gates **committed strings**, complementing the runtime advice guardrail (AI-SPEC G6, which gates LLM output). Both required — COMP-08 stops a banned word from ever being committed in copy; G6 stops the LLM from generating one at runtime.

### 8.1 What it scans

- In-app user-facing strings: `mobile/src/**/*.{ts,tsx}` string literals + `mobile/assets/copy/**`.
- Onboarding + disclaimer copy + Settings copy.
- Store-listing files: `store/play-listing/*.md` (description, short-description, what's-new).
- Marketing copy committed to repo: `marketing/**`.
- **Excludes:** test fixtures (`**/tests/**`, `**/__fixtures__/**`), `banned_words.py` itself, and this spec — they legitimately contain the words.

### 8.2 Where it runs

A Phase-2 **GitHub Actions workflow step** (shell owned by INFRA-OPS-SPEC.md) — so it gates *strings at PR time*, not just runtime. Same `BANNED_WORDS` core `{treat, cure, diagnose, medicine, drug}` (§0.2) via `BANNED_RE`.

```yaml
# step inside .github/workflows/ci.yml (INFRA-OPS owns the file)
- name: CDSCO/ASCI banned-words string lint (COMP-08)
  run: python tools/lint_rules/banned_words_strings.py   # exits 1 on any hit
```

- The script greps the scoped paths with `BANNED_RE`, prints `file:line: banned token "<word>"`, exits 1 on any hit → PR cannot merge.
- Also asserts §0.1 disclaimer byte-equality between `constants.py` and mobile `constants.ts` (or the single generated source).
- **Human ASCI review = Phase 4** (per task + AI-SPEC §131): an ASCI/CDSCO-aware reviewer audits the full launch-copy corpus before public launch (COMP-06 Phase 3 framing review + Phase 4 substantiation check). The build lint is the automated floor; human review is the Phase-4 ceiling. Not a Phase-2 blocker.

---

## 9. Phase-2 acceptance checklist (compliance slice)

- [ ] `DISCLAIMER_TEXT` + `DISCLAIMER_VERSION` constant exists; mobile mirrors byte-equal (COMP-06 hook).
- [ ] `BANNED_WORDS` module shared by build lint + runtime G6; `BANNED_RE` compiled once.
- [ ] `consent_log` write path live; `consent_type` enum matches MODEL-SPEC exactly; `purpose_text_hash` populated (COMP-03/09).
- [ ] `ai_training` default OFF — no grant row until Settings toggle (COMP-09).
- [ ] `POST /compliance/delete` soft-delete + 403 lockout + `delete_requested` ledger row (COMP-04/AUTH-05).
- [ ] `/internal/compliance/purge` endpoint: token-gated, idempotent, executes §4.3 ordered cascade + PII-strip + audit_event.
- [ ] `.github/workflows/dpdp-purge.yml` scheduled (22:00 UTC) + `workflow_dispatch`; hits purge endpoint (INFRA-OPS shell).
- [ ] `test_hard_delete.py` fixture test green: 31-day back-date → R2+PG purge, stripped consent_log retained, audit row written, idempotent (COMP-04).
- [ ] `POST /compliance/export` → §5.2 JSON shape → email link (transport OPEN); `data_exported` ledger row (COMP-05).
- [ ] `assert_region_pin()` in lifespan startup; fails closed on R2/Supabase mismatch (COMP-01).
- [ ] COMP-08 banned-words string lint step in CI; greps scoped paths; exits 1 on hit.
- [ ] `whatsapp_session` table stubbed (MODEL-SPEC DDL); STOP-keyword + 24h-TTL purge logic specced for Phase-4 wire (D-CEO-01).
- [ ] `dpdp-migration-runbook.md` authored (§6) — Phase 2 Week 1.

---

## OPEN — needs founder

1. **Email transport for COMP-05 export + hard-delete confirmation (§5.3).** Recommend Resend (3K/mo free, no CC). Needs founder to confirm + verify a sending domain. Endpoint codes against `EmailTransport` Protocol so swap is one file.
2. **WhatsApp consent posture (§2.1).** This spec RECOMMENDS explicit YES-gate on first inbound (one extra turn) over D-CEO-01's footer-only legitimate-use basis. Founder confirms whether to accept the one-turn UX cost for a harder lawful basis, or stay footer-only.
3. **Disclaimer constant sync mobile↔backend (§0.1).** Single generated `constants.ts` from Python vs hand-synced byte-equal pair. Trivial; founder/dev preference — defaulting to hand-synced + lint-asserted until a codegen step is wanted.
4. **Fresh-OTP re-auth on `POST /compliance/delete` (§4.1).** Recommended (prevents hijacked-session deletion) but adds a re-auth flow. Founder confirms whether Phase-2 delete requires re-OTP or accepts the standard Bearer token.
