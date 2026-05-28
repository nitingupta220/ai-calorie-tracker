# Typography Research & Spec Lock

**Project:** AI Personal Coach — Indian gym youth (18–30), muscle-gain V1, Hinglish+English, ₹299/mo trainer-replacement.
**Stack:** React Native (Expo SDK 50+), Android-first, future Devanagari (V2).
**Decision date:** 2026-05-27
**Owner:** tarun.chaudhary@infrax.ai

---

## 1. Free + Open-Source Typefaces for React Native / Expo

The `@expo-google-fonts/*` packages cover the entire Google Fonts catalogue with one-line install, MIT license, and a `useFonts` hook that hides async load state. This eliminates EAS asset-pipeline pain and licensing complexity entirely. Every candidate below is available via this path; static TTFs are recommended over variable fonts because RN variable-font support is not uniform across the New Architecture and older Hermes builds — Expo docs explicitly warn that variable fonts "do not have support across all platforms" so the safe play is shipping 3–4 static weights.

**Candidate sans-serif families evaluated:**

| Family | Source / License | Strengths | Concerns |
|---|---|---|---|
| **Inter** | rsms.me — SIL OFL | Industry default (Notion, Linear, Strava, Shopify). Tabular figures (`tnum`), slashed zero (`ss02`), flat-top 3 (`cv09`), open digits (`ss01`). Highest x-height in class. | Generic; everyone uses it. |
| **Geist Sans** | Vercel — SIL OFL | Modern Swiss-influenced, slightly more character than Inter, pairs natively with Geist Mono. 9 weights. | Display-leaning; body legibility at 12sp on cheap Androids weaker than Inter. |
| **Manrope** | M. Sharanda — SIL OFL | Variable font, friendly humanist edges, strong numerals. | Slightly less neutral; not Devanagari. |
| **Plus Jakarta Sans** | Tokotype — SIL OFL | Geometric, contemporary, scales well. | Less battle-tested at small sizes on low-DPI Android. |
| **Onest** | OFL | Hybrid geometric+humanist. | Younger family, fewer optical sizes. |
| **Outfit** | OFL | Distinct geometric, popular with creators. | No matching italics; too round for data-dense UI. |
| **IBM Plex Sans/Mono** | IBM — SIL OFL | Engineering credibility, Plex Mono pairs perfectly. | Plex Sans feels "corporate IBM" — wrong for gym youth. |
| **Mukta** | ITF — SIL OFL | **Devanagari + Latin in one family.** 7 weights. | Latin side weaker than Inter; sized differently from Latin-first fonts. |
| **Hind** | ITF — SIL OFL | **Devanagari + Latin, UI-designed.** 5 weights. | Only 5 weights, less optical refinement than Inter. |
| **Noto Sans Devanagari** | Google — SIL OFL | Authoritative Devanagari coverage. Pairs with Noto Sans (Latin). | Two separate font files needed (script-pair Latin via Noto Sans). |

**RN/Expo verdict:** Inter + IBM Plex Mono is the safest pair. Both ship as official `@expo-google-fonts/inter` and `@expo-google-fonts/ibm-plex-mono` packages (MIT-licensed wrappers around OFL fonts). Static TTF, 4 weights each = ~600 KB total — well under app-size budget.

Sources: [expo/google-fonts](https://github.com/expo/google-fonts), [Expo Fonts docs](https://docs.expo.dev/develop/user-interface/fonts/), [Inter](https://rsms.me/inter/), [Hind](https://github.com/itfoundry/hind), [Mukta](https://fonts.google.com/specimen/Mukta).

---

## 2. 2026 Typography Trends in AI / Fitness / Wellness

**Variable fonts are mainstream on web but still risky on RN.** Across 2025–2026 the trend is single variable file + CSS axes; mobile RN apps continue shipping 3–4 static weights for predictable rendering on Android 9–13 devices (large in India).

**Display + body pairing patterns:**
- Vercel / dev-tools: Geist Sans + Geist Mono (matched optical metrics).
- Indian fintech (CRED): Gilroy + Cirka serif + Overpass Mono — three-font system signalling editorial depth.
- Mainstream SaaS: distinctive display + Inter body has become the dominant 2025–2026 recipe (Notion, Linear, Strava all converged on Inter for body).
- Wellness: softer humanist (Onest, Manrope, Quicksand) when calm; geometric grotesque (Inter, Geist, Plus Jakarta) when "performance" or "data".

**Numeric / tabular figures:** Tabular figures (`font-feature-settings: "tnum"`) are non-negotiable for macros, kcal, weight, and reps. They align decimal columns vertically — critical for the macros card (kcal + P/C/F + advice). Inter, IBM Plex, Geist, and Plus Jakarta all expose `tnum`. Bare `Text` in RN does **not** apply OpenType features by default — must set via `style={{ fontVariant: ['tabular-nums'] }}` (RN ≥ 0.65 supports this on iOS+Android).

**Letter-spacing trends (2026):**
- Display (24sp+): tight, -1% to -3% (-0.02em to -0.03em).
- Headline (18–22sp): slightly tight, -0.5% to -1%.
- Body (14–16sp): 0.
- Caption / micro (10–12sp): +0.5% to +1.5% (+0.005em to +0.015em) for legibility on low-DPI Androids.
- ALL CAPS labels: +6% to +8% — but avoid all-caps for premium feel; reserve for tab badges only.

Sources: [Untitled UI 2026 fonts](https://www.untitledui.com/blog/best-free-fonts), [Mockuups 2026 fonts](https://mockuuups.studio/blog/post/best-fonts-for-apps/), [DesignMonks 2026 UI fonts](https://www.designmonks.co/blog/best-fonts-for-ui-design).

---

## 3. What Comparable Apps Actually Use

| App | Display | Body | Mono | Why |
|---|---|---|---|---|
| **Cal AI** | SF Pro Display / system | SF Pro / system | — | Bootstrapped iOS-first; default Apple stack. |
| **WHOOP** | Custom-spaced sans (large primary metric ~72pt) | Clean sans, oversized hierarchy | — | Bureau Oberhaeuser-designed data viz; dark UI; size hierarchy carries info. |
| **Hevy** | System (SF / Roboto) | System | System mono | Lean indie team; focus on workout UX not type. |
| **Linear** | **Inter** | **Inter** | (rare) | "Inter UI in action on linear.app" — Inter is the entire system. |
| **Notion** | **Inter** | **Inter** Regular 400 / Medium 500 / Bold 700 | (mono for code) | Inter dominates SaaS. |
| **Strava** | Boathouse (custom Grilli Type, marketing) | **Inter** (in-app) | — | Inter for pace/distance metrics — chosen for clean geometric numerals. |
| **CRED** | **Cirka** (serif headings) | **Gilroy** sans | **Overpass Mono** | NeoPOP design system; editorial serif = premium feel. |
| **Cult.fit** | Custom geometric sans | System / Inter-like | — | Yoga + gym hybrid → softer. |
| **HealthifyMe** | System Roboto / Lato | Roboto | — | Mass-market generic feel. |
| **Stripe** | Söhne (Klim, paid) | Söhne | Söhne Mono | Institutional, paid licence — outside our budget. |

**Pattern observation:** Premium positioning either (a) goes Inter and earns trust through restraint (Linear, Notion, Strava), or (b) pairs a distinctive editorial display with a workhorse body (CRED, Stripe). Indian mass-market apps default to Roboto/system and look generic — this is the **anti-pattern** for our ₹299/mo positioning.

Sources: [SaaS Typography Playbook](https://fullstop360.com/blog/insights/branding/saas-typography-playbook-what-leading-companies-use), [Strava typography 2026](https://sensatype.com/what-font-does-strava-use-in-2026), [Notion font](https://www.designyourway.net/blog/what-font-does-notion-use/), [WHOOP design breakdown](https://www.925studios.co/blog/whoop-design-breakdown), [CRED typography](https://resources.indiefolio.com/how-the-design-team-at-cred-is-pushing-boundaries/).

---

## 4. Pairing Recommendations for THIS App

**Design constraints:**
- Data-dense macros card → tabular figures mandatory.
- Hinglish primary, Devanagari V2 → Latin-only OK now, but pick a family with a Devanagari-compatible sibling.
- "Restrained, modern, trustworthy, not over-stylized" → rules out Outfit, Plus Jakarta (too geometric-trendy), Cirka/serif displays (too editorial), Geist Mono as body (too narrow).
- Android-first, low-DPI Redmis common → high x-height + battle-tested rendering needed.
- Premium ₹299/mo positioning → no default Roboto.

**Display font candidate: Inter (Display optical) or Geist Sans.**
- Inter wins on Android rendering, tabular figures, and proven small-size legibility.
- Geist Sans is more distinctive but slightly worse at 12–14sp on cheap Androids.
- **Pick: Inter** — use weights 700/800 with -2% tracking for hero macros number, mascot speech bubble, hero headlines. Inter has a separate `Inter Display` optical for 28sp+, with tighter spacing and refined apertures.

**Body font candidate: Inter (same family).**
- Same-family display+body = simpler design system, smaller bundle, consistent metrics.
- Inter Regular 400 + Medium 500 covers UI labels, advice text, settings, captions.
- High x-height = readable at 12sp on 720p Androids.

**Mono font candidate: IBM Plex Mono vs Geist Mono vs JetBrains Mono.**
- For the macros card numbers (kcal, P/C/F grams) we don't actually need a mono — Inter with `tabular-nums` solves alignment.
- Use mono **only** for: kcal labels in advice cards ("`1,847 kcal · 142g P`"), workout log entries, debug strings.
- **Pick: IBM Plex Mono** — slightly warmer than JetBrains, more credible than Geist Mono for non-dev brand context, ships via `@expo-google-fonts/ibm-plex-mono`. Weight 500 only is sufficient.

**Devanagari V2 plan:** When Hindi UI is added, swap body font to **Mukta** (Devanagari + Latin, 7 weights, OFL). Mukta's Latin is acceptable but visually distinct from Inter — alternatively use Inter for Latin runs and Mukta only for Devanagari runs via `fontFamily` selection per text node (RN supports per-`Text` font). Decision deferred to V2; we won't lock Mukta now but design tokens will leave room for a per-script font override.

---

## 5. Spec Lock

```yaml
typography_spec_lock:
  version: 1.0.0
  locked_on: 2026-05-27
  rationale: >
    Inter (display + body) + IBM Plex Mono (selective numeric chrome).
    Restrained, modern, proven on Android, fast to ship, free, no licensing risk.
    Same-family display+body keeps the design system tight and bundle small.

  fonts:
    display:
      family: "Inter"
      optical: "Inter Display"   # for 28sp+ headlines if needed
      package: "@expo-google-fonts/inter"
      weights_loaded: [400, 500, 600, 700, 800]
      license: SIL_OFL_1.1
    body:
      family: "Inter"
      package: "@expo-google-fonts/inter"
      weights_loaded: [400, 500, 600, 700]
      license: SIL_OFL_1.1
    mono:
      family: "IBM Plex Mono"
      package: "@expo-google-fonts/ibm-plex-mono"
      weights_loaded: [500]
      license: SIL_OFL_1.1
      use_for: ["numeric chrome labels", "workout log lines", "debug strings"]
    devanagari_v2:
      family: "Mukta"
      package: "@expo-google-fonts/mukta"
      weights_loaded: [400, 500, 600, 700]
      license: SIL_OFL_1.1
      status: deferred_to_v2
      note: "Use per-Text fontFamily override when Devanagari runs detected; Latin stays Inter."

  weight_set:
    regular: 400      # body, captions
    medium: 500       # UI labels, buttons inline
    semibold: 600     # subtitles, emphasis, primary buttons
    bold: 700         # section headers
    extrabold: 800    # hero macros number, mascot punchline

  type_scale:
    # Android sp values. 4-point baseline grid.
    caption_xs: 10    # legal, timestamps
    caption: 12       # micro-labels (KCAL, PROTEIN under big number)
    body_sm: 14       # secondary body, advice text
    body: 16          # primary body, default Text
    body_lg: 18       # emphasized body
    title_sm: 20      # card titles
    title: 24         # screen titles
    display_sm: 32    # hero macros total
    display: 40       # onboarding hero
    display_lg: 56    # rare — single-screen hero numbers

  line_heights:
    # multiplier of font size
    tight: 1.1        # display 32sp+
    snug: 1.25        # titles 20-24sp
    normal: 1.4       # body 14-18sp
    relaxed: 1.55     # long-form advice text

  letter_spacing:
    display_lg: -0.03      # -3% on 40sp+
    display: -0.02         # -2% on 28-32sp
    title: -0.01           # -1% on 20-24sp
    body: 0                # 14-18sp
    caption: 0.005         # +0.5% on 12sp
    caption_xs: 0.015      # +1.5% on 10sp
    label_caps: 0.06       # +6% reserved (avoid; tab badges only)

  numeric_rules:
    macros_card:
      style: { fontVariant: ['tabular-nums'], fontFamily: 'Inter', fontWeight: '800' }
      reason: "Tabular figures align decimal columns; 800 weight gives macro-number authority."
    kcal_inline:
      style: { fontVariant: ['tabular-nums'], fontFamily: 'Inter', fontWeight: '600' }
    workout_log_lines:
      style: { fontFamily: 'IBMPlexMono_500Medium', fontVariant: ['tabular-nums'] }
    slashed_zero: true   # enable via fontFeatureSettings 'ss02' where supported

  rn_implementation_notes:
    - "Static TTF only. No variable fonts in V1 (RN+Hermes inconsistency)."
    - "Load via useFonts in app root; show SplashScreen until fontsLoaded."
    - "Always apply tabular-nums on any <Text> that renders a number a user compares."
    - "Never rely on system font fallback — explicitly set fontFamily on every Text via a Typography component."
    - "Wrap in a <Text variant='body'> abstraction so V2 Devanagari swap is one prop change."

  anti_patterns_avoid:
    - "Roboto / SF default system fonts — generic, kills premium positioning at ₹299/mo."
    - "Poppins — overused in Indian mass-market apps, signals 'startup template'."
    - "Outfit / Plus Jakarta Sans for body — too geometric, weak at 12sp on Android."
    - "Cirka or other serif headlines — wrong for gym/performance positioning."
    - "Variable fonts in RN V1 — rendering inconsistency on Android."
    - "ALL CAPS body text — bad for Hinglish mixed case."
    - "Mixing 3+ font families — Inter + IBM Plex Mono only."
    - "Mono as body — narrow widths kill data-dense screen density."

  test_devices_baseline:
    - "Redmi 9 (720x1600, Android 10) — verify 12sp caption legibility"
    - "Pixel 6 (1080x2400, Android 14) — verify display weight rendering"
    - "Samsung A14 (1080x2408, Android 13) — most common Indian Android"
```

---

## Sources

- [expo/google-fonts on GitHub](https://github.com/expo/google-fonts)
- [Expo Fonts documentation](https://docs.expo.dev/develop/user-interface/fonts/)
- [expo-google-fonts/geist npm](https://www.npmjs.com/package/@expo-google-fonts/geist)
- [Inter font family — rsms.me](https://rsms.me/inter/)
- [Inter on Google Fonts](https://fonts.google.com/specimen/Inter)
- [Inter stylistic sets and OpenType features](https://lexingtonthemes.com/blog/inter-stylistic-sets-css-tailwind)
- [Vercel Geist font](https://vercel.com/font)
- [IBM Plex Mono on Google Fonts](https://fonts.google.com/specimen/IBM+Plex+Mono)
- [IBM Plex on GitHub](https://github.com/IBM/plex)
- [Hind on GitHub (ITF)](https://github.com/itfoundry/hind)
- [Mukta on Google Fonts](https://fonts.google.com/specimen/Mukta)
- [Noto Sans Devanagari](https://fonts.google.com/noto/specimen/Noto%2BSans%2BDevanagari)
- [Plus Jakarta Sans on Google Fonts](https://fonts.google.com/specimen/Plus+Jakarta+Sans)
- [Onest on Google Fonts](https://fonts.google.com/specimen/Onest)
- [Best UI Design Fonts 2026 — DesignMonks](https://www.designmonks.co/blog/best-fonts-for-ui-design)
- [28 Best Free Fonts for Modern UI 2026 — Untitled UI](https://www.untitledui.com/blog/best-free-fonts)
- [30 Best Modern Fonts for Web and Apps 2026 — Mockuuups](https://mockuuups.studio/blog/post/best-fonts-for-apps/)
- [Best Fonts for Fitness & Wellness 2026 — FontAlternatives](https://fontalternatives.com/best-fonts-for/fitness-wellness/)
- [Most Used Google Fonts on Gym Websites 2026 — ILOVEWP](https://www.ilovewp.com/resources/wordpress-for-gyms/most-used-google-fonts-on-gym-websites/)
- [Best Monospace Fonts 2026 — Made Good Designs](https://madegooddesigns.com/best-monospace-fonts-2026/)
- [SaaS Typography Playbook — FullStop](https://fullstop360.com/blog/insights/branding/saas-typography-playbook-what-leading-companies-use)
- [What Font Does Strava Use in 2026 — Sensatype](https://sensatype.com/what-font-does-strava-use-in-2026)
- [What Font Does Notion Use — DesignYourWay](https://www.designyourway.net/blog/what-font-does-notion-use/)
- [WHOOP Design Breakdown — 925 Studios](https://www.925studios.co/blog/whoop-design-breakdown)
- [WHOOP Developer Design Guidelines](https://developer.whoop.com/docs/developing/design-guidelines/)
- [How CRED's Design Team Pushes Boundaries — IndieFolio](https://resources.indiefolio.com/how-the-design-team-at-cred-is-pushing-boundaries/)
- [CRED Storybook Typography](https://playground.cred.club/?path=/docs/foundation-typography--heading)
- [Font Strategies for Fintech — Telerik](https://www.telerik.com/blogs/font-strategies-fintech-websites-apps)
- [Adding Custom Variable Fonts in React Native — Medium/Timeless](https://medium.com/timeless/adding-custom-variable-fonts-in-react-native-47e0d062bcfc)
