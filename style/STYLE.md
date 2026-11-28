# lit1-lab style guide

The design language of lit1-lab, written so that Claude (or a person) can build another frontend that looks like it belongs to the same family. Pair this file with `style.css` (the tokens and components, ready to drop in) and `example.html` (every pattern on one page; open it in a browser).

> **For Claude:** read this whole file before writing UI. Use the tokens in `style.css` and never hard-code a colour, font or radius that isn't listed here. When unsure, pick the quieter option.

---

## 1. Character in one paragraph

Flat, minimal, editorial. It reads like a well-set notebook, not an app. Text does almost all the work: a warm grey-brown body colour on white (or soft light grey on near-black), one muted sage-green accent, 1px hairline borders and lots of whitespace. There are no shadows, no gradients, no filled buttons, no icons except where they're essential, and almost no animation. Hierarchy comes from **size, weight, muted colour and spacing**, never from boxes or colour fills.

## 2. Principles (in priority order)

1. **Typography first.** Every screen should still work with all borders removed. Size, weight and the muted colour carry the hierarchy.
2. **One accent, used sparingly.** Sage green (`--accent`) marks *interaction and emphasis only*: hovers, links inside long-form text, the active item, the left edge of a card, focus rings. It never fills large areas.
3. **Hairlines, not boxes.** Separate things with a 1px `--border` line (row dividers, section underlines, the footer rule). Use an outlined container only for cards, pills, inputs and dialogs.
4. **Flat.** `box-shadow`, gradients, blur, glassmorphism and coloured backgrounds on sections are all banned. The only "surface" colour is `--card`, a barely-there tint for code, selected rows and subtle panels.
5. **Calm motion.** Only colour and border-colour transitions, at 150ms. Nothing slides, scales or bounces. Respect `prefers-reduced-motion`.
6. **Generous whitespace.** Big vertical gaps between sections (3–5rem), comfortable line-height (1.5 for UI, 1.75 for reading), and wide side gutters on desktop.
7. **The OS decides light or dark.** Both themes come from the same tokens (`prefers-color-scheme`). The design must look right in both.

## 3. Colour tokens

| Token | Light | Dark | Use |
|---|---|---|---|
| `--background` | `#ffffff` | `#1a1a1a` | page background, dialog background |
| `--foreground` | `#5c5a56` (warm grey-brown) | `#e0e0e0` | body text, titles, active nav |
| `--muted` | `#888888` | `#888888` | secondary text: meta, dates, captions, inactive nav, labels |
| `--muted-light` | `#444444` | `#444444` | the TOC progress track only |
| `--border` | `#e0e0e0` | `#333333` | every hairline and outline |
| `--card` | `#f6f6f4` | `#232322` | code blocks, inline code, selected list row |
| `--accent` | `#8fa876` (sage) | same | hover colour, links in prose, active state, card left edge, focus ring, selection |
| `--highlight` | `#a8c090` | same | hover colour of a link that is already accent-coloured |
| `--dot-recent` | `#51cf66` | same | status dot: "new / last 30 days" |
| `--dot-fresh` | `#facc15` | same | status dot: "recent / last 90 days" |

Rules:
- Body text is **never pure black**. It's the warm `#5c5a56`. Headings use the same colour as body text; they stand out through size and weight.
- Text *on* the accent is `#fff` (the active TOC item). Selected text is `--accent` background with `#1a1a1a` text.
- If you need a semantic colour (error, success) in the new app, keep it as muted as the sage, use it only for text and 1px borders, and never use it as a filled banner.

## 4. Typography

- **Display/UI font:** `"Helvetica Neue", Helvetica, Inter, system-ui, sans-serif` (`--font-display`). This is set on `body`, so it's the default for everything. Helvetica Neue stands in for Neue Haas Grotesk.
- **Fallback sans:** Inter Variable (`--font-sans`), loaded via `@fontsource-variable/inter` or Google Fonts.
- **Mono:** the system mono stack (`--font-mono`) for code and keyboard hints.
- Turn on kerning and ligatures (`font-feature-settings: "kern" 1, "liga" 1`) and antialiasing.

| Role | Size / line-height | Weight | Extra |
|---|---|---|---|
| Page title (h1) | 2.25rem / 1.11 (1.875rem below 480px) | 600 | letter-spacing −.025em |
| List page heading (`.page-h`) | 1.5rem / 1.33 | 600 | −.025em. Small on purpose: list pages open quietly |
| Section heading (`.sec-h`) | 1.25rem / 1.4 | 600 | 1px bottom border, 3.5rem top margin |
| Article h2 | 1.875rem / 1.2 | **500** | −.025em, 3rem top margin |
| Article h3 / h4 | 1.5rem / 1.25rem | 500 | |
| Lede / subtitle | 1–1.25rem / 1.55 | 400 | `--muted` |
| Body (UI) | 1rem / 1.5 | 400 | |
| Body (reading) | 1.125rem / 1.75 | 400 | long-form only |
| Meta line | .875rem | 400 | `--muted`, parts joined with ` · ` or ` • ` |
| Eyebrow label (`.side-label`, `.sub`) | .75–.875rem | 400–500 | UPPERCASE, letter-spacing .05–.1em, `--muted` |
| Card title | 1rem | 600 | |
| Card text / tiny meta | .875rem / .75rem | 400 | `--muted` |

The weight scale is just **400 / 500 / 600**. Never use 700 or above, and never italics for emphasis in UI.

## 5. Layout and spacing

- **Gutters:** horizontal padding on `header`, `main` and `footer` is `1.5rem`, then `3rem` at ≥48rem, then `6rem` at ≥64rem. Content sits left-aligned in that frame; nothing is centred except dialogs.
- **Two widths:** `main.wide` is full width (lists, dashboards, articles with a sidebar). Plain `main` caps every child at `--width: 48rem` (prose, about pages, forms).
- **Detail page:** a header (back link, meta, title, lede, tags) taking 75% of the width. Below it, a 75/25 split at ≥64rem: content on the left, and on the right a sticky sidebar (`top: 3rem`) with small muted text. Below 64rem the sidebar is hidden and the content runs full width.
- **Two-column lists:** a grid `1fr 1fr` with `gap: 0 4.5rem` at ≥48rem, one column below that.
- **Vertical rhythm:** 2rem from the header to the page title, 3–3.5rem between sections, `margin-top: 5rem` before the footer. Inside lists, rows are 1rem tall with hairline separators.
- **Breakpoints:** 30rem (480px, phone type scale), 40rem (small reading size), 48rem (two columns, card split), 64rem (sidebar, widest gutters).
- **Radii:** 2px images, 3–4px inline code, code blocks, keyboard hints and small pills; 6px tag pills; 8px cards and dialogs; 999px round pills and dots. Nothing in between.

## 6. Components (classes are in `style.css`)

**Header (`.top`):** the nav on the left, search on the right, in one flex row. Nav links are plain text at 1.125rem in `--muted`. Hover changes them to `--foreground`. The current page is `--foreground` with a 1px underline, set with `border-bottom` and `aria-current="page"`. There's no logo, no background and no sticky bar.

**Search trigger (`.search`):** a bare button containing an 18px stroke magnifier (stroke-width 2, `currentColor`) and a `⌘K` keyboard hint (`.kbd`: mono .8rem, 1px border, 4px radius).

**Command palette (`.pal-back` + `.pal`):** a 50% black backdrop. The dialog sits 12vh from the top, max 36rem wide, with a 1px border and an 8px radius. The input has no border except a bottom hairline. The selected row gets a `--card` background. Section names are `small` and muted on the right. Keyboard: ⌘K toggles it, arrow keys move, Enter opens, Esc closes.

**Links:**
- In UI text they inherit the text colour, with an underline in `--muted` offset by 3px that turns `currentColor` on hover.
- Navigational rows have no underline and turn `--accent` on hover.
- Inside long-form text they're `--accent`, turning `--highlight` on hover.

**Dated row list (`.recent`):** the title on the left, a muted .875rem `<time>` on the right, a hairline under each row and 1rem of vertical padding. Hover turns the row accent-coloured.

**Plain link list (`.plain`):** compact rows (.3rem padding) with an optional status `.dot` on the right.

**Card (`.block-card`):** a 1px border with a **2px accent left border**, 8px radius on the right corners only and square on the left, 1rem padding. At ≥48rem it splits into a 1fr / 2fr grid: on the left the title (600), a muted description (.875rem) and a meta row (.75rem, items separated by `·`); on the right, pills. Hovering the main link turns it accent-coloured. There's no shadow and no hover lift.

**Pills:**
- `.pill` is round (999px), .875rem, with a 1px border. If it's a link, hovering turns its border and text accent-coloured.
- `.pills li` is the squarer tag variant: .75rem, 4px radius.

**Section heading (`.sec-h`):** semibold 1.25rem with a hairline under it. Lists hang directly beneath.

**Eyebrow (`.sub`, `.side-label`):** small uppercase muted text with wide letter-spacing, used to label groups.

**Accordion (`.about`):** a `<details>` element with hairlines above and below. The summary is an uppercase muted eyebrow with a `+` / `−` drawn by CSS on the right.

**Status dot (`.dot`):** an 8px circle in `--dot-recent` or `--dot-fresh`, with a small legend (`.legend`) beside the page title.

**Sidebar TOC (`.toc`):** a 6px rounded track in `--muted-light`. A 30%-opacity accent fill shows reading progress, and a `--foreground` block marks the current section. The active link is a filled accent chip with white text; this is the one place the accent fills something.

**Code:**
- Inline: mono at .875em on `--card`, 3px radius.
- Blocks: `--card` background with a 1px border, 4px radius, .85rem text and horizontal scroll. Syntax theme `github-dark`, background stripped.

**Tables:** full width, no outer border or zebra stripes, a hairline under each row, left-aligned cells, and a horizontal scroll wrapper.

**Footer:** a hairline above, muted .9rem text, the site name, and a row of plain text links spaced 1.25rem apart.

**Forms (not in the site yet; build them in the same spirit):**
- **Inputs:** transparent background, 1px `--border`, 4px radius, `.6rem .75rem` padding, `font: inherit`. Focus shows a 2px accent outline.
- **Buttons:** no filled buttons. The primary button is an outlined pill-shaped `button` (1px border, 4–6px radius) whose border and text turn accent on hover. The secondary button is plain text styled like a link.

## 7. Accessibility and behaviour

- Focus: `:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }` everywhere.
- Mark the current page with `aria-current="page"` and style that attribute, not a class.
- Use semantic HTML: `nav`, `main`, `article`, `aside`, `time`, `details`. The palette uses `role="dialog"`, `combobox` and `listbox`.
- Respect `prefers-reduced-motion` by turning off transitions.
- Reading text stays around 65–75 characters per line (48rem cap or the 75% column).

## 8. Don'ts

- Shadows, gradients, glow or blur.
- Filled or coloured buttons and banners, or coloured section backgrounds.
- More than one accent colour, or the accent on large surfaces.
- Pure black text, or bold above 600.
- Centred hero sections with big CTAs, stock illustrations, or emoji as UI.
- Icon-heavy UI. Use text labels and add an icon only when it's universal (search, close).
- Rounded corners above 8px, except fully round pills and dots.
- Motion beyond 150ms colour and border transitions.
- Component libraries that bring their own look (MUI, Bootstrap, shadcn defaults) unless they're restyled to these tokens.

## 9. Using it with Tailwind (if the new project uses it)

Map the tokens instead of using Tailwind's palette:

```js
// tailwind.config.js
theme: { extend: {
  colors: { bg: "var(--background)", fg: "var(--foreground)", muted: "var(--muted)", line: "var(--border)",
            card: "var(--card)", accent: "var(--accent)", highlight: "var(--highlight)" },
  fontFamily: { display: "var(--font-display)", sans: "var(--font-sans)", mono: "var(--font-mono)" },
  maxWidth: { prose: "48rem" },
  borderRadius: { sm: "2px", DEFAULT: "4px", md: "6px", lg: "8px" },
}}
```
Keep the `:root` token block from `style.css` in your global CSS. Then use `text-fg`, `text-muted`, `border-line` and `hover:text-accent` on 1px borders everywhere, and don't add `shadow-*` or `bg-gradient-*` classes.

## 10. Prompt snippet

Paste this into the new project's `CLAUDE.md`:

```
Frontend style: follow style/STYLE.md and use the tokens/classes in style/style.css.
Flat, minimal, editorial: warm grey text (#5c5a56) on white / #e0e0e0 on #1a1a1a, one sage accent (#8fa876)
for hover/active/emphasis only, 1px hairline borders, no shadows/gradients/filled buttons, Helvetica Neue/Inter,
weights 400/500/600 only, generous whitespace, 150ms colour transitions only, light/dark via prefers-color-scheme.
```
