# API-SPEC — Bhog Backend HTTP Contract (Phase 2)

**Status:** LOCKED for Phase 2 build. Author against this verbatim; do not freelance route shapes.
**Scope:** The canonical HTTP API contract for the Phase 2 backend spine (Photo → Macros end-to-end + DSR + auth + health). Mobile (Phase 3) is the only consumer.
**Last updated:** 2026-05-29

> **Read order (priority, highest wins on conflict):** `CLAUDE.md` > `.planning/phases/01-validation-gates-stack-lock/01-CONTEXT.md` (D-01..D-19) > `.planning/decisions/*.md` (D-CEO-01..03) > `.planning/phases/01-validation-gates-stack-lock/01-AI-SPEC.md` > `.planning/REQUIREMENTS.md` > `.planning/research/ARCHITECTURE.md` (top banner supersedes 5 items).
>
> **Sibling specs (cross-link, do NOT duplicate here):**
> - `MODEL-SPEC.md` — SQLAlchemy table shapes (`users`, `meal_photo`, `correction_event`, `consent_log`, `ai_call_log`, `vision_cache`, `veg_protein_prices`, `whatsapp_session`, `streak_event`, …), columns, enums-at-rest, Alembic baseline. **This doc references tables by name; their column definitions live there.**
> - `AI-PROVIDER-SPEC.md` — `analyze` internals: `ai_provider.py` routing, vision/text fallback chains, Pydantic `VisionResult` / `Advice` schemas, 4/4 rubric validator, banned-words guardrails, cost/latency telemetry. **This doc references the analyze pipeline as a black box returning `MealResponse`.**

---

## 0. Conventions (apply to every route)

- **Base URL:** `https://<render-app>.onrender.com` (Render free, Singapore — D-01). No `/api` prefix; no versioning prefix in V1 (single client, single version; add `/v1` only at first breaking-change need).
- **Transport:** HTTPS JSON only. `Content-Type: application/json` on all request/response bodies except the R2 PUT (which is `image/jpeg` direct to R2, not this API).
- **Framework:** FastAPI 0.128 + Pydantic v2 + SQLAlchemy 2.0 async + asyncpg (INFRA-05). Every handler is `async def`. Routes are thin (≤10 LOC) and delegate to `services/` (per ARCHITECTURE structure rationale).
- **Auth:** `Authorization: Bearer <firebase_id_token>` on every route except `/healthz`, `/readyz`, and `POST /whatsapp/webhook` (Phase 4+, out of Phase 2 scope here). See §1.
- **Timestamps:** ISO-8601 UTC with `Z` suffix on the wire (e.g. `2026-05-29T05:45:00Z`). IST is a render-side concern (mobile), never a wire concern.
- **IDs:** all resource IDs are UUIDv4 strings. `meal_id` = `meal_photo.id`. The R2 object `key` is a separate opaque string (see §3).
- **Money:** `cost_inr` is a number (float, 2dp), Indian Rupees. Never a localized string.
- **Idempotency / dedup:** `(image_sha256, user_goal_hash)` dedup is internal to the analyze pipeline (AI-SPEC §4b `vision_cache`); not a client-facing header in V1.
- **CORS:** locked to the Expo dev client origin + production app; no wildcard. Not security-load-bearing (native app, no browser), but set anyway.

---

## 1. Authentication Model (D-05, D-CEO banner, AUTH-01/02/04/05)

**Decision (LOCKED, supersedes ARCHITECTURE's "app-minted JWT"):** The **Firebase ID token is used DIRECTLY as the `Bearer` credential.** There is **no separate app-minted JWT**, no `/auth/login` that returns a Bhog token, no refresh endpoint on this API.

- Mobile obtains + refreshes the Firebase ID token via the Firebase SDK (`@react-native-firebase/auth`, AUTH-02). The backend never issues or refreshes tokens.
- Every authenticated route verifies the token **per-request** via `firebase-admin.auth.verify_id_token(token)` inside a `current_user` FastAPI dependency (`app/deps.py`).
- **NEVER trust a client-submitted phone number / uid in the body** — derive the uid from the verified token only (CLAUDE.md anti-pattern #6).

### `current_user` dependency contract (`app/deps.py`)

On every authenticated route, in order:
1. Extract `Authorization: Bearer <token>`. Missing/malformed → `401 auth_invalid`.
2. `verify_id_token(token)` (checks signature + expiry + audience). Raises (`ExpiredIdTokenError`, `InvalidIdTokenError`, `RevokedIdTokenError`) → `401 auth_invalid`.
3. Look up / lazily-create the `users` row keyed by `firebase_uid` (token `uid` claim).
4. **Reject soft-deleted users (AUTH-05):** if `users.soft_delete_at IS NOT NULL` → `403 account_deleted`. (A user who requested deletion cannot keep using the app during the 30-day window.)
5. **Enforce 18+ age gate (AUTH-04):** if the user's stored `is_adult` flag is false / age-gate not yet cleared → `403 age_under_18`. (The age gate itself is collected at onboarding in Phase 3; this dependency enforces the stored verdict on every Phase-2 call so a non-adult token can never analyze a meal.)
6. Return the `User` ORM object to the handler.

> The login step is **implicit** — there is no `POST /auth/verify` route in V1. Auth happens transparently on the first authenticated call (lazy user-row creation in step 3). A dedicated `POST /auth/verify` is **OPEN — needs founder** only if Phase 3 onboarding wants an explicit "register device + create profile" handshake before the first meal; for the Phase 2 spine, implicit is sufficient and TRACK/HISTORY/DSR routes are the surface. Cross-link `MODEL-SPEC.md` for the `users` row shape (`firebase_uid`, `is_adult`, `soft_delete_at`, `goal`, `diet_preference`, `budget_bucket`, …).

---

## 2. Error Envelope (FROZEN — Phase 3 mobile switches on `error` codes)

**Every non-2xx response** (including FastAPI's auto-422) returns this exact shape:

```json
{
  "error": "<stable_code>",
  "message": "<human-readable, English, dev-facing>",
  "retry_after": 30,
  "details": { }
}
```

- `error` — **stable machine code** from the FROZEN enum below. Mobile branches on this. Never localized, never renamed.
- `message` — human-readable string for logs/dev. Mobile may show it as a fallback but should prefer its own localized copy keyed off `error`.
- `retry_after` — optional, integer seconds. Present on `vision_unavailable` and `quota_exceeded`.
- `details` — optional object. On `validation_failed` carries the Pydantic error list (`details.errors`). Otherwise omitted.

### FROZEN error code enum

| `error` code | HTTP | Meaning | Emitted by |
|---|---|---|---|
| `auth_invalid` | 401 | Missing/expired/invalid/revoked Firebase token | `current_user` (§1 steps 1-2) |
| `age_under_18` | 403 | Authenticated user fails 18+ gate (AUTH-04) | `current_user` (§1 step 5) |
| `account_deleted` | 403 | User is soft-deleted, in 30-day purge window (AUTH-05) | `current_user` (§1 step 4) |
| `image_too_large` | 413 | Fetched R2 object > 600KB (G12 / AI-SPEC §4b) | `POST /meals/{key}/analyze` |
| `vision_unavailable` | 502 | Vision failed across ALL providers (AI-SPEC §4b retry #3) | `POST /meals/{key}/analyze` |
| `advice_degraded` | 200 | Advice fell back to template; macros are still valid (NOT an error status — see note) | `POST /meals/{key}/analyze` |
| `validation_failed` | 422 | Request body failed Pydantic validation | FastAPI exception handler (all routes) |
| `quota_exceeded` | 429 | Per-user / global free-tier RPD ceiling hit before fallback could serve | `POST /meals/{key}/analyze` |

> **`advice_degraded` is special:** it is **NOT a failure status**. When advice times out (6s) or fails the 4/4 rubric across retries, the analyze pipeline ships macros + a template advice line (AI-SPEC §4b retry #3) with HTTP **200**. The `MealResponse.advice.degraded` boolean (see §5 schema) is the real signal; the `advice_degraded` enum value exists so Phase-3 mobile can render the "Bali couldn't think of a tip this time" microcopy without parsing prose. Macros are never blocked on advice (ADVICE-03, ARCHITECTURE Pattern 3, TRACK-08).

### FastAPI exception-handler requirement

Register a custom `RequestValidationError` handler so FastAPI's default 422 body is **reshaped into the envelope above** (`error: "validation_failed"`, `details.errors: <pydantic_errors>`). Also register a handler for the typed domain exceptions (`AuthInvalid`, `AgeUnder18`, `AccountDeleted`, `ImageTooLarge`, `VisionUnavailable`, `QuotaExceeded`) → envelope. No raw FastAPI/Starlette default error bodies may leak. Implement in `app/main.py` via `app.add_exception_handler(...)`.

---

## 3. Upload Pipeline — PRESIGN-FIRST (resolves the verified conflict)

**LOCKED:** The flow is **two-step presign-first**, NOT inline `POST /meals/analyze` with bytes. This honors TRACK-04 ("backend never proxies bytes"), D-04 (R2 jurisdictional bucket — Local Uploads unsupported, standard S3 multipart only), and ARCHITECTURE Pattern 2 + Anti-Pattern 4.

```
[Mobile] compress → JPEG ≤1280px q0.7, EXIF stripped (client best-effort)   (TRACK-03)
   │
   ├─(1)→ POST /uploads/presign            → { upload_url, key, expires_in }
   │
   ├─(2)→ PUT bytes DIRECT to R2 (upload_url)   [NOT this API — S3-compatible PUT]
   │
   └─(3)→ POST /meals/{key}/analyze        → MealResponse (macros + advice)
```

### Presigned-PUT contract (LOCKED)

The presign route pins, on the R2 presigned PUT, **both**:
- `Content-Type = image/jpeg` (signed; R2 rejects any other content-type on PUT).
- `content-length-range` upper bound **≤ 600KB** (G12 / AI-SPEC §4b). The signed policy refuses oversize bytes at R2, so adversarial/raw-photo uploads fail at the edge, not at our compute.
- TTL = **300s** (5-min, D-04).
- Key format: `meals/{user_id}/{uuid4}.jpg` (ARCHITECTURE Pattern 2; user_id namespacing lets the hard-delete cron walk `meals/{user_id}/` — Anti-Pattern 5).

On presign, insert a `meal_photo` row with `status = 'pending'` (cross-link `MODEL-SPEC.md` for `meal_photo` shape + `status` enum `{pending, analyzing, done, failed}`).

### Server-side validation + AUTHORITATIVE EXIF strip (at analyze time)

The client EXIF strip (TRACK-03) is **best-effort only**. The **authoritative** strip + validation happens server-side inside `POST /meals/{key}/analyze`:
1. Fetch bytes from R2 via `httpx.AsyncClient` GET on a presigned-GET URL (NOT passed to Gemini as a URL — bytes are downloaded server-side then handed to the vision provider as inline bytes; AI-SPEC §3 Pitfall 4, DPDP region discipline).
2. **Pillow validate:** confirm it decodes as a real JPEG, dimensions sane (reject absurd) — corrupt/non-image → `422 validation_failed`.
3. **Re-assert size:** if fetched bytes > 600KB → `413 image_too_large` (defense-in-depth even though R2 policy already capped it).
4. **AUTHORITATIVE EXIF/GPS strip** via Pillow (re-encode, drop all metadata) before the bytes touch any AI provider — GPS in metadata is PII (DPDP, CLAUDE.md India checklist, ARCHITECTURE Anti-Pattern 5). This is the server's guarantee; never trust the client's strip.

### Orphan janitor cron (LOCKED)

A scheduled job (GitHub Actions, per D-03 cron pattern — **NOT** in-process APScheduler, which won't fire on sleeping Render free; ARCHITECTURE banner) deletes:
- `meal_photo` rows still `status = 'pending'` **> 24h** old, AND
- their corresponding R2 objects under `meals/{user_id}/{key}`.

This collects presigned uploads that were issued but the analyze step never landed (ARCHITECTURE Pattern 2 con: "orphan photos possible if confirm never lands — need janitor cron"). Idempotent; safe to re-run. Cross-link `MODEL-SPEC.md` for `meal_photo.status` + `created_at`.

---

## 4. Phase-2 Route Set (LOCKED)

| Method | Path | Auth | REQ-ID(s) |
|---|---|---|---|
| POST | `/uploads/presign` | Bearer | TRACK-04, INFRA-07 |
| POST | `/meals/{key}/analyze` | Bearer | TRACK-05..09, ADVICE-01..06, TRACK-08 |
| PATCH | `/meals/{id}` | Bearer | HISTORY-03, HISTORY-04 |
| GET | `/meals` | Bearer | (serves last-3-day context; ADVICE-02 dependency) |
| DELETE | `/me` | Bearer | AUTH-05, COMP-04 |
| GET | `/me/export` | Bearer | COMP-05 |
| GET | `/healthz` | none | INFRA-05, D-03 |
| GET | `/readyz` | none | INFRA-05, COMP-01 |
| GET | `/admin/cost` | Bearer + founder | INFRA-04, AI-SPEC D11 |

**DEFERRED to Phase 3** (not in this contract; named so the dev does NOT build them now): daily-summary route (`GET /summary/today`), streak route (own-rank pill, D-CEO-02), push registration (`RETAIN-01`), WhatsApp webhook (`POST /whatsapp/webhook`, D-CEO-01 — table stub only in Phase 2 per `MODEL-SPEC.md`), budget-optimizer query (D-CEO-03). These are Phase-3 surfaces per REQUIREMENTS traceability.

---

## 5. Route Details

### 5.1 `POST /uploads/presign`

**Auth:** Bearer. **Satisfies:** TRACK-04, INFRA-07.

**Request body:** none required. Optional `capture_mode` hint may be sent here OR on analyze; the **authoritative** capture_mode is carried on analyze (§5.2). Keep this body empty in V1.

```python
class PresignResponse(BaseModel):
    upload_url: str        # R2 presigned PUT URL, content-type + length pinned
    key: str               # "meals/{user_id}/{uuid4}.jpg" — opaque to client
    expires_in: int = 300  # seconds (D-04, 5-min TTL)
```

**Behavior:** generate key → presign PUT (content-type `image/jpeg`, content-length-range ≤600KB, 300s) → insert `meal_photo{user_id, key, status:'pending'}` → return.

**Errors:** `401 auth_invalid`, `403 account_deleted`, `403 age_under_18`.

---

### 5.2 `POST /meals/{key}/analyze`

**Auth:** Bearer. **Satisfies:** TRACK-05, TRACK-06, TRACK-07, TRACK-08, TRACK-09, ADVICE-01..06.
**Path param:** `key` — the exact `key` returned by `/uploads/presign` (URL-encoded; it contains slashes — accept it as a path-tail / wildcard segment, e.g. FastAPI `{key:path}`).

```python
class AnalyzeRequest(BaseModel):
    capture_mode: Literal["food", "thali"] = "food"   # portion-scaling hint (FROZEN enum)
    reference_object: bool = False                     # coin/palm in frame → portion scaling (TRACK-02)
```

> **Why these two fields now (cheap-now, expensive-post-freeze):** Phase-3 mobile will send `capture_mode` (single-dish/food vs full thali) and `reference_object` (was a scale reference in frame) so the pipeline can scale portions. Both are **optional with defaults**, so the Phase-2 backend can ignore them or pass them into the vision pipeline without breaking when Phase 3 starts sending them. Adding them after the contract freeze would force a mobile+backend lockstep change. The `capture_mode` enum is **FROZEN at `{food, thali}`**; do not add values without a contract bump.

**Response — `MealResponse` (FROZEN outer shape; inner `macros`/`dishes`/`advice` schemas owned by `AI-PROVIDER-SPEC.md`):**

```python
class MacroTotals(BaseModel):
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float

class DishItemOut(BaseModel):       # mirrors VisionResult.DishItem (AI-PROVIDER-SPEC.md)
    name: str                       # whitelist slug OR "unknown"
    portion_g: int
    confidence: float               # [0,1]

class AdviceOut(BaseModel):
    text: str                       # 1-2 sentences, inline on MacrosCard (ADVICE-01)
    referenced_food: str            # rubric R1
    referenced_quantity_g: int      # rubric R2
    cost_inr: float                 # rubric R3
    log_reference: str              # rubric R4
    degraded: bool = False          # True → template fallback used (see §2 advice_degraded)
    disclaimer: str                 # CDSCO/ASCI footer (ADVICE-06) — always present

class MealResponse(BaseModel):
    meal_id: str                    # meal_photo.id (UUID) — use for PATCH /meals/{id}
    key: str
    macros: MacroTotals
    dishes: list[DishItemOut]       # 1..5
    advice: AdviceOut
    needs_confirmation: bool        # TRACK-09: True if >3 items OR any confidence <0.6
    prompt_version: str             # advice prompt semver (ADVICE-04 traceability)
    created_at: str                 # ISO-8601 UTC
```

**Behavior (delegates to `services/vision_pipeline.py` — internals in `AI-PROVIDER-SPEC.md`):**
1. Load `meal_photo` by `key`; assert it belongs to `current_user` (else `404`/`auth_invalid`). Set `status='analyzing'`.
2. Fetch bytes from R2; Pillow validate; size re-check (`413 image_too_large`); **authoritative EXIF strip** (§3).
3. Stage 1 vision (Gemini 2.5 Flash → fallback chain) → Stage 2 macros (deterministic IFCT lookup, NO LLM math — D-07) ∥ Stage 3 advice (Groq) via `asyncio.gather`, advice hard-timeout 6s (TRACK-08).
4. `needs_confirmation = (len(dishes) > 3) or any(d.confidence < 0.6 for d in dishes)` (TRACK-09).
5. Out-of-whitelist → vision returns `unknown`; respond with `dishes:[{name:"unknown"}]` + `needs_confirmation:true` so mobile shows "Not recognized — log manually" free-text fallback (TRACK-07).
6. Persist macros + dishes on `meal_photo`, `status='done'`; record `ai_call_log` rows (INFRA-04).

**Errors:** `401 auth_invalid`, `403 account_deleted`, `403 age_under_18`, `413 image_too_large`, `502 vision_unavailable` (+`retry_after`), `429 quota_exceeded` (+`retry_after`), `422 validation_failed` (bad `capture_mode`). Advice failure does **NOT** error — ships `200` with `advice.degraded=true` (§2).

---

### 5.3 `PATCH /meals/{id}`

**Auth:** Bearer. **Satisfies:** HISTORY-03, HISTORY-04.
**Path param:** `id` — `meal_photo.id` (UUID, from `MealResponse.meal_id`).

```python
class MealCorrection(BaseModel):
    dish_name: str | None = None        # corrected whitelist slug or free-text
    portion_g: int | None = None
    macros: MacroTotals | None = None   # user-overridden macros (TRACK-07 manual entry)
    # at least one field must be non-null → else 422 validation_failed
```

**Behavior (ARCHITECTURE Correction Flow):**
1. Load `meal_photo` by `id`, assert ownership.
2. **Append** a `correction_event` row `{user_id, meal_photo_id, before:<json>, after:<json>, created_at}` — **append-only, never overwritten** (HISTORY-04, ARCHITECTURE Pattern 5 — the V1.5 fine-tuning corpus). Cross-link `MODEL-SPEC.md` for `correction_event` shape.
3. Update `meal_photo` with corrected values.
4. Return the updated `MealResponse` (recomputed macros/advice if needed — advice re-gen is OPTIONAL in V1; default = keep prior advice, just return corrected macros).

**Errors:** `401 auth_invalid`, `403 account_deleted`, `404` (not found / not owned), `422 validation_failed` (empty patch).

---

### 5.4 `GET /meals`

**Auth:** Bearer. **Satisfies:** the last-3-day log that ADVICE-02 consumes (also backs Phase-3 HISTORY-02).
**Query params:** none in V1 — the window is **fixed at last 3 days** server-side (`WHERE user_id=? AND created_at > now() - interval '3 days'`, AI-SPEC §4b SQL `LIMIT 9`). Do NOT expose a `days` param in V1 (14-day window is V15-02, deferred).

```python
class MealListItem(BaseModel):
    meal_id: str
    key: str
    macros: MacroTotals
    dishes: list[DishItemOut]
    advice_text: str            # the rendered advice line for history thumbnails (HISTORY-02)
    created_at: str             # ISO-8601 UTC

class MealListResponse(BaseModel):
    meals: list[MealListItem]   # newest-first, last 3 days, status='done' only
    day_totals: MacroTotals     # today's running totals (HISTORY-01 backing)
```

**Errors:** `401 auth_invalid`, `403 account_deleted`, `403 age_under_18`.

> Photo bytes are **not** returned inline. If mobile needs a thumbnail it requests a short-TTL presigned GET — that endpoint is **OPEN — needs founder** (Phase 3 history UI decision); Phase 2 returns macros + advice text only, which is sufficient for the analyze flow and the advice-context fetch.

---

### 5.5 `DELETE /me` (DSR delete)

**Auth:** Bearer. **Satisfies:** AUTH-05, COMP-04.

**Request body:** none. (ARCHITECTURE shows a "fresh OTP re-auth" gate; in this token-direct model the **fresh, unexpired Firebase ID token IS the re-auth proof** — no extra body. Whether to force a *recently-issued* token, `auth_time` freshness check, is **OPEN — needs founder**; default V1 = any valid token.)

**Behavior (ARCHITECTURE Account Deletion Flow):**
1. Set `users.soft_delete_at = now()` (soft-delete — AUTH-05).
2. Append a **`consent_audit`** row `{event_type:'delete_requested', user_id_hash, policy_version, created_at}` (COMP-04 audit trail — NOT a `consent_log` row; `consent_log` is grant/revoke consents only. G1 reconciliation 2026-05-29; see COMPLIANCE-SPEC §4.1).
3. Return `202 Accepted` with `{ "status": "scheduled", "hard_delete_after": "<ts+30d ISO>" }`.

The **30-day hard-delete** (purge R2 `meals/{user_id}/` + cascade Postgres + keep PII-stripped `consent_log` proof + 365-day audit row, COMP-04) runs on the **GitHub Actions cron** (NOT in-process; ARCHITECTURE banner + D-03). That cron is a Phase-2 deliverable but not an HTTP route. Cross-link `MODEL-SPEC.md` for cascade scope + audit row.

After soft-delete, every subsequent `current_user` call by this user returns `403 account_deleted` (§1 step 4).

**Errors:** `401 auth_invalid`.

---

### 5.6 `GET /me/export` (DSR export / Right to Access)

**Auth:** Bearer. **Satisfies:** COMP-05.

**Behavior:** generate a JSON export of `{profile, meal_logs, corrections, consent_history}` for `current_user`.

```python
class ExportResponse(BaseModel):
    status: Literal["ready", "emailed"]   # see delivery note
    download: ExportPayload | None = None # inline JSON if status=="ready"

class ExportPayload(BaseModel):
    profile: dict          # de-identified-safe profile fields
    meals: list[MealListItem]
    corrections: list[dict]
    consents: list[dict]
    generated_at: str
```

> REQUIREMENTS COMP-05 says "emailed to user". Email delivery needs an email channel the Phase-2 spine does not otherwise have (phone-OTP auth, no email on file). **Resolution for Phase 2:** return the export **inline as JSON** (`status:"ready"`, `download` populated) — synchronous, no email dependency. The **email-delivery variant** (`status:"emailed"`) is **OPEN — needs founder** (needs an email-capture step + transactional-email provider, neither in Phase-2 zero-CC scope). Inline JSON satisfies the DPDP Right-to-Access obligation for the alpha; email is a Phase-3+ nicety.

**Errors:** `401 auth_invalid`, `403 account_deleted` (a deleting user may still export during the window — **OPEN — needs founder**; default V1 = allow export until hard-delete, deny after).

---

### 5.7 `GET /healthz` (shallow)

**Auth:** none. **Satisfies:** INFRA-05, D-03 (cron-ping keep-alive target).

**Behavior:** **shallow** — process is up. NO DB call, NO external call (the D-03 GitHub Actions cron hits this every 10 min in active hours to keep Render warm; it must be cheap and never wake the DB).

```json
{ "status": "ok" }
```
Always `200` if the process is alive.

---

### 5.8 `GET /readyz` (deep)

**Auth:** none. **Satisfies:** INFRA-05, COMP-01 (region-pinning boot check).

**Behavior:** **deep** dependency check — used by deploy gate / manual ops, NOT the keep-alive cron.
1. Postgres reachable (`SELECT 1` on async pool).
2. R2 reachable + bucket jurisdiction == `india` (COMP-01 — deploy fails if mismatch; D-04).
3. Supabase region == Mumbai assertion (COMP-01).
4. firebase-admin initialized.

```python
class ReadyzResponse(BaseModel):
    status: Literal["ready", "degraded"]
    checks: dict[str, bool]   # {"postgres":true,"r2_jurisdiction_india":true,"db_region_mumbai":true,"firebase":true}
```
`200` when all true; `503` (envelope `error:"validation_failed"` is wrong here — use a plain `{status:"degraded",checks:{...}}` body with `503`) when any check fails. The region checks are the COMP-01 "deploy fails if mismatch" mechanism.

---

### 5.9 `GET /admin/cost` (founder-only)

**Auth:** Bearer **+ founder allowlist.** **Satisfies:** INFRA-04, AI-SPEC D11 (cost gate gauge).

**Founder gate:** after `current_user`, assert the user's `firebase_uid` is in a `FOUNDER_UIDS` env allowlist (`app/config.py`). Not in allowlist → `403 auth_invalid` (do not leak existence; reuse `auth_invalid`). A full RBAC role system is **OPEN — needs founder** (overkill for one founder in V1; env allowlist is the locked V1 mechanism).

**Behavior:** daily SQL rollup over `ai_call_log` (AI-SPEC §4b telemetry hook) — cost per provider, per-active-user rolling 30-day cost, fallback rate.

```python
class CostRollupResponse(BaseModel):
    window_days: int = 1
    by_provider: list[ProviderCost]     # {provider, model, calls, input_tokens, output_tokens, cost_inr}
    cost_per_active_user_30d_inr: float # the ≤₹15 gate gauge (AI-SPEC D11)
    fallback_rate_pct: float            # >15% → investigate (AI-SPEC D11)
```

**Errors:** `401 auth_invalid`, `403 auth_invalid` (non-founder).

---

## 6. REQ-ID Coverage Map (Phase-2 API surface)

| REQ-ID | Where satisfied |
|---|---|
| INFRA-04 | `ai_call_log` writes on analyze; `GET /admin/cost` |
| INFRA-05 | FastAPI skeleton + `/healthz` + `/readyz` |
| INFRA-07 | `POST /uploads/presign` (R2 india-jurisdiction presigned PUT) |
| AUTH-01/02 | §1 Firebase-ID-as-Bearer (implicit verify per-request) |
| AUTH-04 | `current_user` 18+ gate → `403 age_under_18` |
| AUTH-05 | `current_user` soft-delete gate + `DELETE /me` |
| TRACK-04 | presign-first; backend never proxies bytes |
| TRACK-05/06/07/08/09 | `POST /meals/{key}/analyze` |
| ADVICE-01..06 | `MealResponse.advice` (inline, rubric, disclaimer, versioned) — internals in `AI-PROVIDER-SPEC.md` |
| HISTORY-03/04 | `PATCH /meals/{id}` + append-only `correction_event` |
| COMP-01 | `GET /readyz` region-pin checks |
| COMP-03 | `consent_log` grant/revoke writes (onboarding + Settings, Phase 3); enum + write contract in COMPLIANCE-SPEC §3 |
| COMP-04 | `DELETE /me` soft-delete + `consent_audit` delete_requested event + GitHub-Actions hard-delete cron |
| COMP-05 | `GET /me/export` |
| COMP-08/09 | banned-words + AI-training-opt-in — enforced in pipeline/prompt layer (`AI-PROVIDER-SPEC.md`) + onboarding (Phase 3); no Phase-2 route |

---

## 7. Open Items (needs founder)

1. **`POST /auth/verify` explicit handshake** — implicit lazy-create is the V1 lock; an explicit register-device/create-profile route is only needed if Phase-3 onboarding wants it. Default: none.
2. **Thumbnail presigned-GET endpoint** for `GET /meals` history UI — deferred to Phase-3 history-UI decision.
3. **`GET /me/export` email delivery** (`status:"emailed"`) — needs email channel; V1 returns inline JSON.
4. **Export allowed during 30-day delete window?** — default V1: allow until hard-delete, deny after.
5. **`DELETE /me` fresh-token (`auth_time`) freshness requirement** — default V1: any valid token; founder may want a re-auth recency gate.
6. **Founder RBAC** beyond the `FOUNDER_UIDS` env allowlist for `/admin/cost` — overkill for V1; locked as env allowlist.
