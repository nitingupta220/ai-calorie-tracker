# Bhog · Design System Tokens

Design contract for the Bhog AI Personal Coach app. Locked 2026-05-28 from
`.planning/specs/bhog-v1-design-spec.html` and the sketch winners at
`.planning/sketches/00X-*/index.html` (001=A, 002=A, 003=B, 004=C).

All Pretext-native HTML, React Native (Expo), and future variants MUST consume these tokens.

---

## Theme: Coach Dark (primary)

Light theme variant is tokenized but the V1 ship is Coach Dark.

### Color

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#1A1612` | Page background, status bar |
| `--bg-elevated` | `#211C18` | Elevated panels |
| `--bg-card` | `#2B2520` | Cards, chips, buttons |
| `--bg-card-hover` | `#332C26` | Card hover/pressed |
| `--bg-sidebar` | `#14110E` | Deep panels (drawer, modal scrim base) |
| `--border` | `#3A3128` | Default card/chip border |
| `--border-strong` | `#4A4036` | Focus, hover border |
| `--text-primary` | `#F5EFE6` | Ivory body text |
| `--text-secondary` | `#B9AE9F` | Secondary body |
| `--text-muted` | `#7A7165` | Tertiary, captions, timestamps |
| `--accent` | `#C9A26B` | Copper-amber. Primary CTA, mascot accent band, key emphasis |
| `--accent-hover` | `#D4B07A` | Accent hover |
| `--accent-dim` | `rgba(201,162,107,0.12)` | Accent tinted bg, focus ring |
| `--sage` | `#8A9D7F` | Confidence-pass, protein highlight, success-soft |
| `--sage-dim` | `rgba(138,157,127,0.14)` | Sage tinted bg |
| `--success` | `#7DA86E` | Strong success states |
| `--warning` | `#D4A24A` | Warning states |
| `--error` | `#C26B5C` | Error, destructive |
| `--info` | `#6B8DA8` | Informational tone |

**Anti-palette:** No neon greens, no Duolingo orange, no saffron (political/religious connotation in India). No royal blue. No high-saturation colors. Coach Dark stays warm, grounded, restrained.

### Typography

Loaded via Google Fonts `family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600`.

| Stack | Use |
|---|---|
| `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` | All display + body text |
| `"IBM Plex Mono", ui-monospace, "SF Mono", monospace` (with `font-feature-settings: "tnum" 1, "lnum" 1`) | All numerics (kcal, macros, time, confidence), small-caps labels |
| `Mukta` (reserved) | Devanagari V2 only — do NOT load until V2 |

**Size scale (rem-based, base = 16px):**

`--t-10` (0.625rem) · `--t-11` (0.6875rem) · `--t-12` (0.75rem) · `--t-13` (0.8125rem) · `--t-14` (0.875rem) · `--t-15` (0.9375rem) · `--t-16` (1rem) · `--t-18` (1.125rem) · `--t-20` (1.25rem) · `--t-24` (1.5rem) · `--t-28` (1.75rem) · `--t-32` (2rem) · `--t-40` (2.5rem) · `--t-56` (3.5rem)

**Weight conventions:**
- 400 — body copy
- 500 — IBM Plex Mono numerics, secondary labels
- 600 — IBM Plex Mono small-caps section labels, primary CTAs, dish titles
- 700 — kcal hero numerals, dish-detail H1
- 800 — reserved for future hero moments

**Letter-spacing:**
- Display: `-0.025em` (large kcal) · `-0.02em` (H1) · `-0.01em` (H2, dish-title)
- Body: 0
- Mono small-caps labels: `0.06em` (medium) · `0.08em` (strong) · `0.10em` to `0.12em` (section headers)

### Spacing scale (px)

`--s-1: 4` · `--s-2: 8` · `--s-3: 12` · `--s-4: 16` · `--s-5: 20` · `--s-6: 24` · `--s-8: 32` · `--s-10: 40` · `--s-12: 48`

### Radii

`--radius-sm: 6px` · `--radius-md: 10px` · `--radius-lg: 16px` · `--radius-xl: 24px`

Pill-shaped: `border-radius: 999px` for chips, confidence pills, FABs.

### Motion

`--transition: 220ms cubic-bezier(0.2, 0.7, 0.2, 1)` — universal ease.

Tap feedback: `transform: scale(0.97-0.98)` for 80-90ms on `:active`.

`@media (prefers-reduced-motion: reduce)` disables all transitions + animations.

### Safe areas

`--safe-top: env(safe-area-inset-top, 0)`
`--safe-bottom: env(safe-area-inset-bottom, 0)`

Apply to root app container, not nested elements.

---

## Component primitives

### Confidence pill

Sage-tinted pill with dot prefix.

```
background: var(--sage-dim);
color: var(--sage);
font: 600 var(--t-10) "IBM Plex Mono";
letter-spacing: 0.06em;
padding: 4px 10px;
border-radius: 999px;
```

Dot prefix is `6×6` sage filled circle, 6px gap. Label like `conf 0.91`.

### Dish chip

`<button>` semantic, 44px+ touch target via padding.

```
background: var(--bg-card);
border: 1px solid var(--border);
color: var(--text-secondary);
font-size: var(--t-12);
padding: 6px 12px;
border-radius: 999px;
gap: 8px;
```

Mono numeric inside (`152 kcal`) in `var(--accent)`.

### Macros row (compact)

Mono letters + values inline. Protein row gets sage color; carbs + fat stay secondary. Pattern: `<lbl>P</lbl> 22g` `<lbl>C</lbl> 54g` `<lbl>F</lbl> 22g`.

### Section header (small-caps mono)

```
font: 600 var(--t-10) "IBM Plex Mono";
color: var(--text-muted);
letter-spacing: 0.12em;
text-transform: uppercase;
```

E.g., "DECOMPOSED VIA IFCT 2017", "DAILY TARGET".

### Advice block (the moat)

Locked invariant: always inline on the macros surface, never a separate tab.

```
background: linear-gradient(135deg, var(--bg-card), var(--bg-elevated));
border: 1px solid var(--border);
border-left: 3px solid var(--accent);
border-radius: var(--radius-lg);
padding: var(--s-4);
display: flex; gap: var(--s-3); align-items: flex-start;
```

Children:
1. `.bali-avatar` — 44×44 circle, silver-grey gradient fur, 1.5px copper-amber border, langur SVG silhouette (placeholder until Ideogram render)
2. `.body` — `.who` (mono uppercase copper) + optional `.sub` (mono muted) on same line. `.copy` ivory body, `<strong>` is `var(--accent)`. `.disclaim` mono 10px muted, top-border separator.

Advice `.copy` is contenteditable for correction flow + Pretext-wired for reflow.

### Primary button

```
background: var(--accent);
color: #1A1612;
font: 600 var(--t-14) Inter;
min-height: 48px;
border-radius: var(--radius-md);
```

Hover/focus: `--accent-hover`. Focus-visible: `outline: 2px solid var(--accent); outline-offset: 2px`.

### Secondary / ghost button

```
background: var(--bg-card);
border: 1px solid var(--border);
color: var(--text-primary);
```

Ghost: `background: transparent; border: transparent; hover → var(--bg-card)`.

### Icon button (back, more, close)

`36×36` circle. `border: 1px solid var(--border); background: var(--bg-card);`. SVG glyph at 18×18, stroke 2, currentColor.

### App bar

`52px` height. `padding: 0 var(--s-3)`. `border-bottom: 1px solid var(--border)`. `background: rgba(26,22,18,0.85); backdrop-filter: blur(12px); position: sticky; top: 0`. Layout: icon-btn · `.title` (flex 1, semibold 14, ellipsis) · icon-btn.

### Status bar (preview-only)

`32px` height. Mono 11px, `var(--text-muted)`. Format: `9:41` left, `5G · 84%` right.

---

## Layout primitives

### App container

```
max-width: 480px (mobile);
margin: 0 auto;
min-height: 100vh;
display: flex; flex-direction: column;
padding-top: var(--safe-top);
padding-bottom: var(--safe-bottom);
```

`@media (min-width: 768px)` wraps app in phone-frame card: `max-width: 420px; border-radius: var(--radius-xl); border: 1px solid var(--border); box-shadow: 0 24px 64px rgba(0,0,0,0.5); height: calc(100vh - 64px)`.

### Photo hero

Always `aspect-ratio: 4/3` for meal photos. Background: radial gradient from copper-charcoal to bg, SVG turbulence noise overlay at 0.75 opacity blend-mode overlay, bottom grade `linear-gradient(180deg, transparent 55%, rgba(26,22,18,0.85) 100%)`.

### Scroll region

`<main>` with `overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--border) transparent`. Thumb `width: 4px`.

---

## Brand voice (copy tokens)

### Bali persona

- Older-bhai gym coach, Hindi-English code-switch (Hinglish)
- Encouraging not condescending; direct not chatty
- Indian context-aware: `₹` for prices, `katori`/`roti × 2` for portions, `dal`/`paneer`/`chana` for examples
- Never uses childish exclamations ("Yay!", "Awesome!"). Never uses corporate (`I understand your concern...`). Never uses emoji as standalone visual elements.

**Examples:**
- "You're at 42g protein, target 88g. Add 50g paneer to evening dal → +15g for ₹18."
- "Plate poora frame mein le bhai — coin ke saath."
- "Sahi sources: chana 80g (₹12), soya 30g (₹6)."

### Compliance copy (legal lock)

Every advice surface ends with:
> Not medical advice. Consult a dietitian for medical conditions.

Format: mono 10px, muted color, top-border separator inside advice block.

---

## Mascot · Bali

Hanuman langur (Semnopithecus). Silver-grey fur, distinctive black face, copper-amber chest band.

V1 ships as SVG placeholder (see `.planning/sketches/003-meal-detail/index.html` — winner B).

V1.1 swap: Ideogram-rendered PNG asset, 6-expression set (default, thinking, celebrating, concerned, sleepy, pointing).

Anti-mascot: NO Duolingo-cartoon energy. NO childish proportions. NO neon. Restrained Whoop + CRED + Linear lane.

---

## Pretext wiring (text reflow contract)

All text blocks that vary in length per user/session MUST carry `data-pretext` attribute. The wiring script:

1. After `document.fonts.ready`: `prepare(text, fontString)` per element
2. ResizeObserver on body + each element → `layout(handle, width, lineHeight)` → set `min-height`
3. For `contenteditable` elements: MutationObserver re-prepares + re-layouts on input

Pretext bundle vendored at `~/.claude/skills/gstack/design-html/vendor/pretext.js`. Copy alongside each finalized HTML.

---

## Locked invariants (do NOT violate)

1. **Inline advice on every macros card.** Never a separate "advice" tab.
2. **IBM Plex Mono for all numbers.** No exceptions, including timestamps.
3. **Copper accent for emphasis, not decoration.** Reserved for: CTA, mascot band, strong-text in advice, confidence-meter active pill.
4. **Sage for confidence + protein highlight, never decoration.**
5. **DPDP disclaimer inside every advice block.**
6. **44px minimum touch target on mobile.**
7. **No emoji as UI element.** Emoji only as photo-placeholder while real photo loads.
8. **No saffron, no Duolingo orange, no neon.**

---

## References

- `bhog-v1-design-spec.html` — full spec with sketches embedded
- `.planning/research/VISUAL-IDENTITY.md` — research basis (Whoop/CRED/Linear)
- `.planning/research/TYPOGRAPHY.md` — Inter + Plex Mono rationale
- `.planning/research/MASCOT.md` — Bali persona research
- `.planning/sketches/003-meal-detail/index.html` — sketch winner B for the meal-detail screen, reference for token usage (production-finalized HTML pending /design-html)
