# Checkpoint · 2026-05-28

**Project:** Bhog · AI Personal Coach for Indian Youth
**Phase:** 1 — Validation Gates + Stack Lock (no production code yet)
**Status:** Design lock complete · awaiting Phase 1 gate execution OR more design rounds

---

## Where we are

All four V1 design tracks locked:

- **Name:** Bhog (भोग) — 1 syllable, food-offering meaning, no Play Store fitness collision
- **Mascot:** Bali — Hanuman langur, older-bhai voice, silver-grey + black face, copper-amber chest band. SVG v1 placeholder in spec (richer shading, catchlight eyes, fur gradients). Real render deferred to Ideogram + illustrator polish.
- **Palette:** Coach Dark — `#1A1612` bg / `#C9A26B` copper accent / `#F5EFE6` ivory / `#8A9D7F` sage. Light theme variant also tokenized.
- **Typography:** Inter (display + body, 400/500/600/700/800) + IBM Plex Mono 500 (numerics). Mukta reserved V2 Devanagari.

GSD scaffold complete: PROJECT.md, REQUIREMENTS.md (67 v1 REQ-IDs), ROADMAP.md (5 phases, vertical MVP, coarse), config.json (YOLO, quality model profile, research+plan-check+verifier enabled).

Phase 1 contracts complete: 01-AI-SPEC.md (937 lines, 12 eval dims, 12 guardrails, Arize Phoenix tracing), 01-CONTEXT.md (D-01..D-19 implementation decisions), 01-DISCUSSION-LOG.md (audit trail).

Research complete: STACK / FEATURES / ARCHITECTURE / PITFALLS / SUMMARY / VISUAL-IDENTITY / TYPOGRAPHY / MASCOT / NAME / NAME-V2 — all in `.planning/research/`.

Single source of truth HTML spec: `.planning/specs/bhog-v1-design-spec.html` — 3-pane layout (sidebar nav + main + TOC), 15 sections, dark/light theme toggle, sidebar Week-1 checklist with progress mirroring.

App page sketches complete: 4 sketches × 3 variants each in `.planning/sketches/` (001 camera-capture · 002 home-today · 003 meal-detail · 004 onboarding-flow). Embedded as section 15 of spec HTML with iframe thumbnails.

---

## Key decisions locked

**Stack:**
- Compute: Render free (Singapore) — Fly + Railway eliminated (CC required 2026)
- DB: Supabase Mumbai free + GitHub Actions cron-ping every 6hr
- Photos: Cloudflare R2 with `jurisdiction=india`
- Auth: Firebase Phone OTP (50K MAU free, no DLT)
- Mobile: Expo SDK 54 + RN 0.81 + EAS Build
- Backend: FastAPI 0.128 + Pydantic v2 + SQLAlchemy 2.0 async + asyncpg + Alembic
- AI: Direct SDKs + Pydantic v2 behind `ai_provider.py` (NOT LangChain). Vision = Gemini 2.5 Flash (NOT 2.0 — retires 2026-03-03). Text = Groq Llama 3.3 70B. Fallback chain wired.

**Product scope:**
- V1 persona: urban Indian youth 18-30, muscle-gain goal first
- V1 dietary: vegetarian-first content, non-veg supported
- V1 dish coverage: 50 pan-Indian whitelist (15 pan + 12 North + 12 South + 11 W/E)
- V1.1: add weight-loss goal (trigger-gated D7 ≥25% + advice 4/4 ≥75%)
- Housewife persona / pre-diabetic = V2 separate brand
- Inline advice on every macros card = LOCKED INVARIANT (never separate tab)

**Phase 1 gates remaining (Week 0 work, NO code yet):**
- Gate 0a: 30 stratified photos (10/10/10 single/mixed/thali), Opus 4.7 labels + founder verifies, ≥70% dish-name + ≥60% macros within ±35% per-bucket
- Gate 0b: 14 days founder meals + advice rubric ≥70% scoring 4/4
- Gate 0c: 20 named Trial Users + ≥10 commitments + ≥3 verbatim ₹299-WTP quotes
- Gate 0d: Stack lock + Play Developer account purchase ($25, 3-7d verification)

---

## Outstanding work (in priority order)

### Immediate
1. **Pick sketch winners.** Open `.planning/specs/bhog-v1-design-spec.html` section 15. Compare 3 variants per screen across 4 sketches. Pick winners. Message format: `001=B, 002=C, 003=C, 004=A`.
2. **Render Bali for real.** Paste Ideogram prompt (spec section 01) into ideogram.ai (free, no CC). Pick best of 4 variants. Save reference image.

### Next session (after sketch winners picked)
3. Run `/design-shotgun` on winning variants → AI-rendered visual mockups per screen.
4. Run `/design-html` to finalize production-grade HTML/CSS layouts.
5. Run `/plan-eng-review` for final architecture audit before any code begins.

### Phase 1 gate execution (Week 0 work, before any code)
6. Execute Gate 0a-0d per Week-1 Checklist in spec section 12 (23 checkbox items).
7. Commit each gate result to `.planning/decisions/YYYY-MM-DD-slug.md` (Phase 2 planner creates folder).
8. After all 4 gates pass: run `/gsd-plan-phase 2` to decompose backend spine + DPDP plumbing.

### Open Reviewer Concerns
- Circular-bias risk (Opus labels Gemini-under-test) — RD audit reserved as V1.5 trigger
- First-time RN shipper timeline drift — 14wk may stretch to 18-20
- Gemini 10 RPM caps at ~50 lunch-concurrent — fallback chain wired before alpha
- No verbatim ₹299 WTP quote captured yet — closes in Gate 0c Week 1
- Thali photo accuracy untested — Gate 0a thali bucket tests directly

---

## File locations

| Artifact | Path |
|---|---|
| **Single source of truth** | `.planning/specs/bhog-v1-design-spec.html` |
| Project | `.planning/PROJECT.md` |
| Requirements (67) | `.planning/REQUIREMENTS.md` |
| Roadmap (5 phases) | `.planning/ROADMAP.md` |
| Config | `.planning/config.json` |
| Research | `.planning/research/{STACK,FEATURES,ARCHITECTURE,PITFALLS,SUMMARY,VISUAL-IDENTITY,TYPOGRAPHY,MASCOT,NAME,NAME-V2}.md` |
| AI-SPEC | `.planning/phases/01-validation-gates-stack-lock/01-AI-SPEC.md` |
| Phase 1 CONTEXT | `.planning/phases/01-validation-gates-stack-lock/01-CONTEXT.md` |
| Sketches | `.planning/sketches/{001-camera-capture,002-home-today,003-meal-detail,004-onboarding-flow}/` |
| Office Hours design doc (source) | `~/.gstack/projects/ai-calorie-weight-loss/nitin-unknown-design-20260527-181050.md` |

---

## Git state

Branch: `master` (no remote yet — local-only)
Last commit: `5662cde` / latest sketch commit
All artifacts committed.

---

## Session memory saved at

- `~/.claude/projects/-home-nitin-Desktop-ai-calorie-weight-loss/memory/feedback_toolchain_gstack_gsd.md` — user wants both gstack + GSD active
- `~/.claude/projects/-home-nitin-Desktop-ai-calorie-weight-loss/memory/feedback_design_before_code.md` — lock all design decisions before any code

---

## Resume prompt

Paste this verbatim into a fresh Claude Code session:

```
Resume Bhog work. Read .planning/CHECKPOINT-2026-05-28.md for full context.
Caveman mode active.

Last session: design lock complete (name Bhog, mascot Bali Langur, palette Coach
Dark, type Inter+Plex Mono), 4 sketches done with 3 variants each, spec HTML at
.planning/specs/bhog-v1-design-spec.html. Phase 1 gates 0a-0d not yet executed.

Next: I will pick sketch winners (format: 001=X, 002=Y, 003=Z, 004=W). Once
picked, run /design-shotgun on the winning variants for AI-rendered mockups.
After that, /design-html for production-grade HTML/CSS.

Before code begins: Phase 1 gates 0a-0d still need execution per the Week-1
Checklist in spec section 12.

Confirm you've read the checkpoint, then ask me for sketch winners.
```
