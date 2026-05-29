# FRONTEND-HANDOFF — Bhog React Native (Expo) Mobile

**Status:** Decision-level handoff. Phase-3 build guidance.
**Audience:** Mobile dev building the Bhog Android app (Expo SDK 54 / RN 0.81).
**Authored:** 2026-05-29
**Token contract:** `DESIGN.md` (Coach Dark). All colors/type/spacing come from there — this doc does not redefine them.

---

## 0. READ-THIS-FIRST scope banner

- **This is Phase 3 work.** It does **NOT** block Phase 2 (backend spine). The mobile app is built only after the backend API is stable (end of Phase 2 / ROADMAP Phase 2 → 3 boundary). Per `ARCHITECTURE.md` Build Order, mobile starts Week 4.
- **EXCEPTION — the one Phase-2 dependency:** §8 (correction edit surface) defines a payload contract the mobile UI and the backend `correction_event` table must agree on. Backend authors `correction_event` in Phase 2 (HISTORY-04). This doc flags the shape so they do not drift. See §8.
- **This doc is decision-level, not the build plan.** The full Phase-3 RN build plan = a future `/gsd-ui-phase` UI-SPEC.md. That doc expands screen-by-screen states, component props, and the full onboarding step list. Here we lock the *decisions* (routes, state split, libs, pipelines) so the UI-SPEC author and the mobile dev never re-litigate them.
- **The 5 mockups are WEB HTML reference only.** `~/.gstack/projects/ai-calorie-weight-loss/designs/00{1..5}-*`. They are vanilla HTML/CSS built for browser preview. The RN build **ports the layout and tokens, not the HTML**. Specific web-isms to drop are called out in §10.

### Source of truth precedence (highest first)
`CLAUDE.md` (stack) > `01-CONTEXT.md` (D-01..D-19) > `.planning/decisions/*` (D-CEO-01..03) > `01-AI-SPEC.md` > `REQUIREMENTS.md` (67 REQ) > `ARCHITECTURE.md` (honor its SUPERSEDED banner: Render not Railway, Gemini 2.5 not 2.0, GitHub-Actions-cron not APScheduler, **Firebase-ID-as-Bearer not app-JWT**, **Zustand+TanStack not Redux**).

### Cross-linked sibling specs (same `.planning/handoff/` dir, authored in parallel)
- `MODEL-SPEC.md` — DB tables + `correction_event` payload (the §8 contract).
- `API-SPEC.md` — route paths, request/response shapes, auth header.
- `COMPLIANCE-SPEC.md` — `consent_log` enum, DPDP consent surfaces (the §7 contract).
- `DESIGN.md` — design tokens (root of repo).

---

## 1. Stack (locked — do not substitute)

Per `CLAUDE.md` "Recommended Stack → Mobile" + `ARCHITECTURE.md` banner.

| Concern | Locked choice | REQ / source |
|---|---|---|
| Framework | Expo SDK **54**, RN **0.81**, New Architecture on | CLAUDE.md |
| Navigation | **expo-router ~5.0** (file-based) | CLAUDE.md |
| Server state | **TanStack Query (React Query) v5** | CLAUDE.md, anti-pattern #12 |
| Client state | **Zustand v5** | CLAUDE.md, anti-pattern #12 |
| Camera | **expo-camera** `CameraView` (SDK 54 bundled) | TRACK-01 |
| Image pipeline | **expo-image-manipulator** (SDK 54 bundled) | TRACK-03, anti-pattern #5 #19 |
| Gallery | **expo-image-picker** (SDK 54 bundled) | TRACK-01 |
| Auth | **@react-native-firebase/auth 21.x** phone OTP; custom dev client (no Expo Go) | D-05, AUTH-01 |
| Push | **expo-notifications** + FCM HTTP v1 | RETAIN-01 |
| Persisted cache | **react-native-mmkv** + `@tanstack/react-query-persist-client` | §6 |
| SVG (mascot) | **react-native-svg** | §5 |
| Fonts | **@expo-google-fonts/inter** + **@expo-google-fonts/ibm-plex-mono** | §9 |
| Safe area | **react-native-safe-area-context** `SafeAreaProvider` | §9 |
| App-bar blur | **expo-blur** `BlurView` | §9 |
| Crash/analytics | **@sentry/react-native**, **posthog-react-native** | ALPHA-04 |

**Auth header (critical, do not re-invent):** the Firebase ID token is sent **directly** as `Authorization: Bearer <firebase_id_token>`. There is **no separate app-minted JWT** (ARCHITECTURE banner override of D8). Backend verifies via `firebase-admin.verify_id_token`. The API client refreshes the token via the Firebase SDK before expiry. Confirm exact header against `API-SPEC.md`.

---

## 2. expo-router file layout (route map)

Three route groups: `(auth)`, `(onboarding)`, `(tabs)`, plus stack/modal screens at the root. Bottom tabs = **Today / History / Tools / Settings** (4 tabs). Camera, Weight, meal-detail, and budget-optimizer are **stack/modal** screens pushed over the tabs (camera is launched from the Today-tab FAB, not a 5th tab — keeps the 4-tab bar clean).

```
mobile/app/
├── _layout.tsx                  # root Stack; SafeAreaProvider + QueryClientProvider + auth gate
├── (auth)/
│   ├── _layout.tsx              # stack, no header
│   ├── phone.tsx                # +91 phone entry  (AUTH-01)
│   └── otp.tsx                  # 6-digit OTP verify (AUTH-01, AUTH-02)
├── (onboarding)/                # see §7 — steps are a SUBSET superset of the 6-step mockup
│   ├── _layout.tsx              # stack + progress-track header
│   ├── goal.tsx                 # muscle-gain only V1 (ONBOARD-01)
│   ├── body.tsx                 # height / weight / age / activity (ONBOARD-01)
│   ├── diet.tsx                 # veg / veg+eggs / non-veg / vegan + budget bucket (ONBOARD-01)
│   ├── targets.tsx              # computed macros reveal (ONBOARD-02)
│   ├── notifications.tsx        # push rationale pre-prompt (ONBOARD-04)
│   ├── consent.tsx              # granular DPDP toggles (ONBOARD-03) — see §7
│   └── disclaimer.tsx           # CDSCO/ASCI ack once (ONBOARD-05)
├── (tabs)/
│   ├── _layout.tsx              # Tabs navigator (4 tabs); BlurView tab-bar bg
│   ├── index.tsx                # TAB 1 · Today   → mockup 002  (HISTORY-01, -06, RETAIN-03)
│   ├── history.tsx              # TAB 2 · History → last-3-days log (HISTORY-02)
│   ├── tools.tsx                # TAB 3 · Tools   → hub: Budget Optimizer entry (D-CEO-03)
│   └── settings.tsx             # TAB 4 · Settings → sign-out, delete-data, push, training opt-in
├── camera.tsx                   # MODAL (fullscreen) → mockup 001 (TRACK-01..03)
├── meal/[id].tsx                # STACK push → mockup 003 (HISTORY-03, ADVICE-01)
├── weight.tsx                   # STACK push → manual weight log (HISTORY-05)
└── tools/budget-optimizer.tsx   # STACK push from Tools tab → mockup 005 (D-CEO-03)
```

### Mockup → route mapping

| Mockup | Screen | Route | Presentation | REQ |
|---|---|---|---|---|
| 001-camera-capture | Camera capture | `app/camera.tsx` | modal, fullscreen, no tab-bar | TRACK-01..03 |
| 002-home-today | Today | `app/(tabs)/index.tsx` | tab 1 | HISTORY-01, -06, RETAIN-03 |
| 003-meal-detail | Meal detail + correction | `app/meal/[id].tsx` | stack push | HISTORY-03, ADVICE-01..06 |
| 004-onboarding-flow | Onboarding | `app/(onboarding)/*` | stack group | ONBOARD-01..05 |
| 005-budget-optimizer | Budget Optimizer | `app/tools/budget-optimizer.tsx` | stack push from Tools | D-CEO-03 |
| (no mockup yet) | History list | `app/(tabs)/history.tsx` | tab 2 | HISTORY-02 — **UI-SPEC to design** |
| (no mockup yet) | Weight log | `app/weight.tsx` | stack push | HISTORY-05 — **UI-SPEC to design** |
| (no mockup yet) | Settings | `app/(tabs)/settings.tsx` | tab 4 | AUTH-03,05; RETAIN-05; COMP-09 — **UI-SPEC to design** |
| (no mockup yet) | Tools hub + own-rank streak pill | `app/(tabs)/tools.tsx` | tab 3 | D-CEO-02, D-CEO-03 — **UI-SPEC to design** |

**Auth gate:** root `_layout.tsx` reads Firebase auth state + onboarding-complete flag from Zustand. Unauthed → `(auth)`. Authed but onboarding incomplete → `(onboarding)`. Both done → `(tabs)`.

**Camera-as-modal rationale:** mockup 002's FAB ("Log dinner") opens the camera. Camera is a transient capture surface, not a destination — modal presentation lets it cover the tab-bar and return cleanly to Today. Do not add a 5th "Camera" tab.

**D-CEO-02 own-rank streak pill** ("47th in Mumbai · 7-day streak") lives on the **Tools** tab (and/or Today header), opt-in, default OFF, hides if cohort < 5. It is **server-computed** (nightly cron) — mobile renders the rank from a TanStack Query, never computes it. Top-N leaderboard is V1.1.

---

## 3. State split — TanStack Query vs Zustand

Hard rule (anti-pattern #12 bans Redux): **server-owned data = TanStack Query; ephemeral client/UI data = Zustand.** Never duplicate server data into Zustand.

### TanStack Query (server state — `useQuery` / `useMutation`)
| Query key | Source | Screens |
|---|---|---|
| `['summary','today']` | `GET /summary/today` | Today (002) |
| `['meals', date]` | `GET` meals for last-3-days | History (002 history list) |
| `['meal', id]` | `GET /meals/{id}` | Meal detail (003) |
| `['streak']` | `GET /streak` | Today, Tools |
| `['rank']` | `GET` own-rank (D-CEO-02) | Tools |
| `['budget', {budget,diet}]` | `GET` budget-optimize (D-CEO-03) | Budget optimizer (005) |
| `['weight']` | `GET` weight history | Weight (HISTORY-05) |

Mutations: `analyzeMeal` (POST analyze), `correctMeal` (PATCH /meals/{id} — §8), `logWater`, `logWeight`, `registerFcmToken`, `updateConsent`. **All API route paths come from `API-SPEC.md`** — placeholders above.

### Zustand (client/UI state only)
| Store | Holds | Persisted? |
|---|---|---|
| `useAuthStore` | firebase user ref, onboarding-complete flag | yes (MMKV) |
| `useOnboardingDraft` | in-progress onboarding answers (goal, body, diet, budget, consent toggles) before final submit | yes (MMKV) — survive app kill mid-flow |
| `useDraftPhoto` | captured photo URI + EXIF-strip/compress status before upload | no (transient) |
| `usePendingUploads` | queued upload jobs (see §6) | yes (MMKV) |
| `useStreakUi` | local optimistic streak-counter animation state | no |
| `useColdStartUi` | upload-start timer + Bali "waking up" banner stage (see §11) | no |

**Why the split:** TanStack handles cache-first reads, background refetch on Indian flaky 4G, and optimistic correction updates (§8). Zustand holds only what the server doesn't own — draft state and UI flags. This is the locked pairing from `CLAUDE.md`.

---

## 4. Pretext is WEB-ONLY — do NOT port

The mockups carry `data-pretext` attributes and ship a `pretext.js` bundle (`~/.claude/skills/gstack/design-html/vendor/pretext.js`). **Pretext is a browser text-reflow / height-precompute hack for HTML where text length varies. React Native `<Text>` reflows natively** — it measures and wraps on its own, no `min-height` precompute needed.

**Action for the dev:** Ignore every `data-pretext` attribute, the `pretext.js` file, the `document.fonts.ready` / `ResizeObserver` / `MutationObserver` wiring in DESIGN.md §"Pretext wiring", and the `prepare/layout` calls. There is **nothing to port**. Render advice/dish text in plain `<Text>` and let RN handle reflow. This note exists so you don't waste time hunting for a Pretext equivalent — there isn't one and you don't need one.

---

## 5. Mascot — Bali (V1 = single SVG)

Per `DESIGN.md` §Mascot + all 5 mockups' `finalized.json` notes ("Bali avatar SVG placeholder; swap with Ideogram PNG when rendered").

- **V1 ships ONE `default` Bali expression** as an inline SVG via `react-native-svg` — the same langur-silhouette placeholder embedded in mockup 003 (`.bali-avatar`: 44×44 circle, silver-grey gradient fur, 1.5px copper-amber `--accent` border).
- Build it as `<BaliAvatar size={44} />` reusable component. Used in: advice block (003, 005 insight card), cold-start banner (§11).
- **6-expression Ideogram PNG set (default, thinking, celebrating, concerned, sleepy, pointing) is DEFERRED to V1.1** (`DESIGN.md`). Do not block on the art asset. Build the component so swapping SVG→PNG later is a one-prop change (`expression="thinking"` falls back to `default` in V1).
- Anti-mascot rules still apply: no Duolingo energy, no neon, no childish proportions (`DESIGN.md` locked invariant #7/#8).

---

## 6. Offline cache + queued upload

Indian-network reality (`ARCHITECTURE.md` offline-queue note): a meal photo captured on a dropped connection must not be lost. 24-hour queue, no offline writes beyond that.

- **Cache layer:** `persistQueryClient` (`@tanstack/react-query-persist-client`) backed by **MMKV** (`react-native-mmkv` — synchronous, fast, no async-storage jank). Persist `['summary','today']`, `['meals',*]`, `['streak']` so Today/History render instantly offline from last-known state.
- **Pending-upload queue:** `usePendingUploads` Zustand store (MMKV-persisted). Each job = `{ localUri, compressedUri, photoKey?, status: 'pending'|'uploading'|'analyzing'|'done'|'failed', createdAt }`. On capture, push a job; a queue-runner (foreground, retries on reconnect via NetInfo) walks: presign → PUT to R2 → POST analyze. On success, invalidate `['summary','today']` + `['meals',today]`.
- **24h TTL:** queue-runner drops jobs older than 24h and surfaces a Bali "ye photo purana ho gaya, dobara click kar" toast. No write-back beyond 24h.
- MMKV is the single persistence primitive for both the query cache and the Zustand stores marked persisted in §3.

---

## 7. Onboarding (004) — consent must subset the `consent_log` enum

Per ONBOARD-03, COMP-03, D-05, and `COMPLIANCE-SPEC.md`.

- The mockup 004 is a **6-step conversational flow** (winner variant C). V1 needs **more** steps than the mockup shows. The route group in §2 lists the full set (goal → body → diet → targets → notifications → consent → disclaimer). **The future UI-SPEC owns the final step list and per-step copy** — do not freeze it here beyond the route stubs.
- **Consent toggles are granular** (ONBOARD-03): photo-upload, profile-data, analytics — each a separate toggle. **AI-training opt-in defaults OFF** (ONBOARD-03, COMP-09).
- **HARD CONTRACT:** every consent toggle on `consent.tsx` MUST map to a value in the `consent_log` enum defined in `COMPLIANCE-SPEC.md`. The UI consent set is a **subset** of that enum (the enum may carry extra server-side actions like `delete_requested`). Mobile sends each grant/revoke as a `consent_log` event via `updateConsent` mutation. **Do not invent consent labels the backend enum doesn't have** — cross-check `COMPLIANCE-SPEC.md` before wiring toggles.
- Age gate (18+, AUTH-04) and CDSCO/ASCI disclaimer ack (ONBOARD-05) are onboarding steps; disclaimer ack persists as acknowledged. Disclaimer copy is the locked string in `DESIGN.md` §Compliance copy: "Not medical advice. Consult a dietitian for medical conditions."

---

## 8. THE PHASE-2 DEPENDENCY — correction edit surface (003)

This is the one place mobile and backend must agree **before** Phase 3, because the backend builds `correction_event` in Phase 2 (HISTORY-04, MODEL-SPEC.md). Flag for both teams.

### Locked UX decisions (override the mockup's web pattern)
- **Advice is READ-ONLY in RN.** The mockup 003 marks advice `.copy` as `contenteditable` and `DESIGN.md` §Advice-block says "contenteditable for correction flow." **That is a web-only affordance. In RN, advice renders as plain read-only `<Text>`.** Advice is generated, not user-edited — do not build an editable advice field.
- **Corrections happen on dish-chips and macro values, NOT on advice, and NOT inline.** User taps a dish-chip or a macro value → a **bottom-sheet** opens prefilled with current values → user edits dish-name / portion / per-macro → save. (`@gorhom/bottom-sheet` or RN `Modal` — UI-SPEC picks; either is fine.) No inline contenteditable anywhere.
- **Save = `PATCH /meals/{id}`** via a TanStack **optimistic mutation**: snapshot `['meal',id]` + `['summary','today']`, apply edit immediately, roll back on error, invalidate on settle. This makes correction feel instant on slow networks.

### Payload contract (must match MODEL-SPEC.md `correction_event`)
The PATCH body and the resulting `correction_event` row are the same conceptual shape. Confirm exact field names + types against `MODEL-SPEC.md` and `API-SPEC.md`; the mobile mutation body MUST be a subset of these fields:

```
PATCH /meals/{id}
{
  "dish_name":  string?,    // corrected dish label, if changed
  "portion_g":  number?,    // corrected portion grams, if changed
  "macros":     { "kcal": number, "protein_g": number, "carbs_g": number, "fat_g": number }?  // if user overrode macros
}
```
Backend persists an **append-only** `correction_event { before, after, photo_key/meal_id, user_id, ts }` (never overwritten — V1.5 fine-tuning corpus, HISTORY-04 / ARCHITECTURE Pattern 5), updates the meal, recomputes `daily_summary`, returns the updated meal. **Mobile must not send fields not in the agreed shape.** If `MODEL-SPEC.md` names fields differently (e.g. `protein` vs `protein_g`), MODEL-SPEC wins — align the mutation to it.

**OPEN — needs founder / backend confirm:** exact field names + nullability in `correction_event` (MODEL-SPEC.md) and exact PATCH route path (API-SPEC.md). Mobile blocks on these two specs landing.

---

## 9. Fonts, theme, layout primitives

### Fonts
- Load **Inter** (400/500/600/700/800) via `@expo-google-fonts/inter` and **IBM Plex Mono** (400/500/600) via `@expo-google-fonts/ibm-plex-mono` with `useFonts()`; gate first render on `fontsLoaded`.
- **Tabular numerics:** all numbers (kcal, macros, time, confidence, ₹) render in IBM Plex Mono with `style={{ fontVariant: ['tabular-nums'] }}` (RN equivalent of CSS `"tnum" 1`). This is `DESIGN.md` locked invariant #2 — IBM Plex Mono for ALL numbers, no exceptions including timestamps.
- `Mukta` (Devanagari) is V2 — do NOT load in V1.

### Theme
- **Coach Dark only.** Light theme is tokenized in `DESIGN.md` but **deferred** — ship dark only. Hardcode the Coach Dark token set into an RN theme object (`src/theme/`) mirroring the `DESIGN.md` color/spacing/radii/type tables. No theme switcher in V1.

### Layout primitives (RN ports)
- Wrap the app in `SafeAreaProvider`; apply safe-area insets at the **root container only** (`DESIGN.md` §Safe areas), via `useSafeAreaInsets()` — not nested.
- **App-bar:** 52px height, `expo-blur` `BlurView` (intensity ~ web `blur(12px)`) over `rgba(26,22,18,0.85)`, 1px `--border` bottom. Sticky/pinned in RN = a fixed header outside the scroll view.
- **Photo hero:** `aspect-ratio: 4/3` (RN `Image` supports `aspectRatio` style). Bottom gradient grade via `expo-linear-gradient`.
- Tab-bar uses `BlurView` background too.

---

## 10. Web-isms to DROP when porting

The mockups are browser HTML. Strip these — they don't apply to a native phone app:

| Web mockup thing | RN action |
|---|---|
| `max-width: 480px` app container + centering `margin: 0 auto` | DROP — RN fills the device width natively |
| `@media (min-width:768px)` **phone-frame card** (border-radius, shadow, fixed height) | DROP — that frame only existed to preview a phone shape in a desktop browser |
| **Status bar** mock (`9:41` · `5G · 84%`, the `.status-bar` 32px row) | DROP — use the real OS status bar via `expo-status-bar` |
| `data-pretext` / `pretext.js` / fonts-ready reflow wiring | DROP — see §4 |
| `contenteditable` advice | DROP — read-only `<Text>`, corrections via bottom-sheet (§8) |
| CSS `:hover` states | DROP — use RN `Pressable` press states; tap feedback `transform: scale(0.97)` per `DESIGN.md` motion |
| `env(safe-area-inset-*)` CSS | REPLACE with `react-native-safe-area-context` |
| `backdrop-filter: blur()` | REPLACE with `expo-blur` `BlurView` |
| `linear-gradient()` CSS bg | REPLACE with `expo-linear-gradient` |
| `prefers-reduced-motion` media query | REPLACE with RN `AccessibilityInfo.isReduceMotionEnabled()` gating animations |

---

## 11. Camera (001) + upload pipeline

### CameraView mapping (mockup 001 → RN overlay)
Use `expo-camera` `CameraView`. The mockup's overlay elements port as **absolutely-positioned RN views over the `CameraView`** (RN supports children over CameraView):

| Mockup element | RN port | REQ |
|---|---|---|
| `.reticle` framing box (variant A "Reticle overlay") | absolute-positioned framing-guide View, copper-amber border | TRACK-02 |
| `.coin` / `.ref-hint` reference-object guide ("Plate poora frame mein le bhai — coin ke saath") | overlay hint + coin/palm visual cue | TRACK-02 |
| Capture-mode pills **FOOD / THALI** | segmented control overlay; passes mode hint to backend | TRACK-06 (thali stratification) |
| Flash control (auto) | `CameraView` `flash` prop toggle (auto/on/off) | — |
| Flip camera | `CameraView` `facing` toggle | — |
| `.shutter` button | capture → `takePictureAsync()` | TRACK-01 |
| Gallery button | `expo-image-picker` `launchImageLibraryAsync` | TRACK-01 |
| Bali coach-tip bubble | `<BaliAvatar>` + tip text overlay | — |

### Upload pipeline (`src/lib/compress.ts` + `upload.ts`) — MANDATORY, do not skip
Per TRACK-03, TRACK-04, `CLAUDE.md` anti-patterns #5 #19, `ARCHITECTURE.md` Pattern 2:

1. Capture (or pick from gallery) → get local URI.
2. **`expo-image-manipulator`**: resize to **≤1280px longest edge**, **JPEG**, **quality 0.7**. SDK 54 gallery picks can return **HEIC/AVIF** — the manipulate-to-JPEG step is what converts them; **never upload raw HEIC** (backend expects JPEG; anti-pattern #5 = ~30% upload failures). Compression also cuts R2 storage ~5x and vision token cost ~3x (anti-pattern #19).
3. **EXIF strip:** the manipulator re-encode drops EXIF (GPS = PII, DPDP). Verify the output has no GPS. Backend also strips server-side (Pillow) as defense-in-depth — but mobile strips first (TRACK-03).
4. **Presigned PUT direct to R2** (`jurisdiction=india`, D-04): `POST` presign → `{ upload_url, key }` → `PUT` bytes straight to R2. **Backend never proxies photo bytes** (anti-pattern, ARCHITECTURE Pattern 2). Exact presign route = `API-SPEC.md`.
5. `POST` analyze with the `key` → returns `MealResponse { macros, dishes, advice, day_totals, streak }` → render meal detail (003).

### TRACK-09 confidence gate (UI)
If backend response flags `>3 items` OR any item `confidence < 0.6`, render a "Tap each item to confirm" step before locking macros. Confidence pills use the sage-dim style from `DESIGN.md` §Confidence pill (`conf 0.91`).

### Cold-start UX (D-03b) — Bali "waking up" banner
Render backend (Render free tier) sleeps after 15 min idle (~60s wake). Mobile must mask this honestly (D-03b):
- Start an upload-elapsed timer when analyze begins (`useColdStartUi`).
- **At 5s elapsed:** insert a Bali speech bubble in the `MacrosCard` skeleton: *"Ek second bhai, coach jaag raha hai... ~30s."*
- **At 30s:** *"Thoda aur bhai, server start ho raha hai."*
- **At 60s:** *"Server slow hai, ek baar phir try kar."* + Retry button.
- Wires through the `<MacrosCard />` skeleton state (~1h Phase-3 work per D-03b). This pairs with TRACK-08's 8s P95 target + 6s advice-timeout (macros-only fallback): on advice timeout, render macros and a "coach soch raha hai" advice placeholder rather than blocking.

---

## 12. Component inventory (build targets, names from ARCHITECTURE)

Co-locate the moat. Per `ARCHITECTURE.md` mobile structure + locked invariant: `<AdviceInline />` is a **child of `<MacrosCard />>`, never its own tab/screen (anti-pattern #1, ADVICE-01, DESIGN.md invariant #1).

- `MacrosCard.tsx` — meal result surface; hosts macros-row + dish-chips + `<AdviceInline>` + skeleton/cold-start state.
- `AdviceInline.tsx` — read-only advice block (Bali avatar + copy + DPDP disclaimer footer). Disclaimer is mandatory on every advice surface (DESIGN.md invariant #5, ADVICE-06).
- `CorrectionSheet.tsx` — bottom-sheet for dish/macro edits (§8).
- `BaliAvatar.tsx` — single-SVG mascot (§5).
- `ConfidencePill.tsx`, `DishChip.tsx`, `MacrosRow.tsx`, `SectionHeader.tsx`, `PrimaryButton.tsx` / `SecondaryButton.tsx` / `IconButton.tsx` — direct ports of `DESIGN.md` §Component primitives.
- `CameraOverlay.tsx` — reticle + reference-object + mode pills (§11).
- `StreakPill.tsx` — own-rank + streak (D-CEO-02, server-fed).
- `ColdStartBanner.tsx` — D-03b stages (§11).

**Touch targets ≥44px** everywhere (DESIGN.md invariant #6). **No emoji as UI element** (invariant #7) — emoji only as photo-placeholder while a real photo loads.

---

## 13. Things this doc deliberately does NOT decide (deferred to UI-SPEC)

- Full per-step onboarding copy + the final step ordering (§7).
- Screen-by-screen loading/empty/error states for History, Weight, Settings, Tools-hub (no mockups exist yet).
- Bottom-sheet library pick (`@gorhom/bottom-sheet` vs RN `Modal`).
- Animation specifics (stagger timings, skeleton shimmer) beyond the `DESIGN.md` motion token.
- Exact API route strings + payload field names — owned by `API-SPEC.md` / `MODEL-SPEC.md`.
- `consent_log` enum values — owned by `COMPLIANCE-SPEC.md`.

These are the future `/gsd-ui-phase` UI-SPEC's job.

---

## Cross-references
- `DESIGN.md` — tokens, primitives, mascot, invariants.
- `MODEL-SPEC.md` — `correction_event` shape (§8 contract), tables.
- `API-SPEC.md` — route paths, auth header, response shapes.
- `COMPLIANCE-SPEC.md` — `consent_log` enum (§7 contract), DPDP surfaces.
- `ARCHITECTURE.md` — component topology, Patterns 1-6, build order (honor SUPERSEDED banner).
- Mockups: `~/.gstack/projects/ai-calorie-weight-loss/designs/00{1..5}-*/finalized.html`.
