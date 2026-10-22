# Vendored from slidev-theme-neversink

This theme started as a copy of https://github.com/gureckis/slidev-theme-neversink
at commit `54166fedef7fc75438639b6c7468819bcaa38a7a` (v0.4.1), vendored on 2026-08-02.

It is tracked directly in this repository (the clone's `.git` was removed) so it can
be customized freely. Local additions so far:

- `layouts/three-cols-title.vue` — three-column version of `two-cols-title`, with
  slots `:: title ::`, `:: left ::`, `:: middle ::`, `:: right ::` and a
  `columns: is-L-M-R` twelve-unit split (default `is-thirds` = `is-4-4-4`).
- `compute_three_column_size()` in `layoutHelper.ts`.
- `layouts/four-cols-title.vue` — four-column version of the same, with slots
  `:: title ::`, `:: one ::`, `:: two ::`, `:: three ::`, `:: four ::` and a
  `columns: is-A-B-C-D` twelve-unit split (default `is-quarters` = `is-3-3-3-3`).
  `align` takes five parts: title, then one per column (e.g. `l-lt-lt-lt-lt`).
- `compute_four_column_size()` in `layoutHelper.ts`.
- Removed `top-title` and `top-title-two-cols` layouts (unused) along with their
  docs pages, example/screenshot slides, and sidebar entries. Note: regenerating
  docs screenshots (`pnpm screenshot`) will renumber `docs/public/screenshots/*.png`
  and desync the numbers hardcoded in the docs pages.
- `layouts/default.vue` — optional `:: title ::` slot (with `align: l/c/r`);
  slides without the slot are unaffected.
- `styles/layouts.css` — in any `:: title ::` slot, non-heading text immediately
  after a heading renders as a muted subtitle (0.9em, 50% opacity, tight to the
  heading).
- `styles/base.css` — global density tweaks: base slide font 1.05rem (Slidev
  default is 1.1rem; em-sized headings scale with it), bullet spacing reduced
  (`li` margin-bottom 1em → 0.4em, line-height 1.5em → 1.4em), the gap
  between a heading and a following list or paragraph reduced (1.5em → 0.5em),
  and no top margin on a list that is the first element in its container. A list
  directly after a paragraph sits 0.4em below it (same as the inter-bullet gap).
  h4 weight reduced 600 → 500 (was rendering heavier than the larger h3, which
  inherits 400), and h4 gets 1rem space above when following a content block
  (p/ul/ol/blockquote/pre/table/div — same convention as the existing h2 rule).
- `layouts/code-right.vue` — added `wrap` frontmatter option (default false).
  `wrap: true` soft-wraps long code lines (`white-space: pre-wrap`,
  `overflow-wrap: anywhere`) instead of scrolling them off the panel.
- `setup/transformers.ts` + `styles/base.css` — subtext syntax: a line starting
  with `-# ` renders as `<small>` (0.8em, 60% opacity). For source lines, captions,
  side notes. Skips fenced code. Plain `<small>` also works.
- `styles/base.css` — `{class:'wrap'}` on a fenced code block soft-wraps long
  lines (same effect as `wrap: true` on the code-right layout).
- `styles/base.css` — `{class:'plain'}` on a fenced code block removes the gray
  background. Combine with wrap: `{class:'wrap plain'}`.
- `styles/base.css` — `class: code-bg` in slide frontmatter paints the slide in the
  code-block background color, so code boxes blend into the slide.
- `setup/shiki.ts` + `styles/base.css` — `==foo==` inside any fenced code block is
  highlighted with the markers hidden (Shiki `preprocess` transformer + decorations,
  class `code-mark`). Syntax highlighting is unaffected.
- `styles/base.css` — Victor Mono replaces Fira Code: `--neversink-quote-font`
  points at the mono font (Fira Code was never imported, so quotes fell back to
  the system monospace), and `strong`/`b` inherit the surrounding font instead of
  forcing Inter, so bold in titles and quotes stays Victor Mono.
- `components/Quote.vue` — `<Quote author="…" source="…" href="…">` wraps an inline
  quote in the quote layout's box (color scheme, border, shadow, quote font) at a size that
  fits in a column, with a right-aligned "— author, source" line. `color` and `width` work
  like `AdmonitionType`'s.
- `layouts/two-cols-title.vue`, `three-cols-title.vue`, `four-cols-title.vue` — a bottom row of
  optional cells, one under each column, lined up across columns: `::left-bottom::`,
  `::middle-bottom::`, `::right-bottom::` (`::one-bottom::`…`::four-bottom::` in four-cols).
  Each spans its column's width and takes its alignment. Empty, the row takes no height. With
  a top title the column row is `1fr`, so the bottom cells sit at the bottom of the slide; the
  footer-title variant's title and full-width `end` row each move down one row to make room.
- `vite.config.ts` + `styles/definitions.css`: definition lists via `@mdit/plugin-dl` (0.19.0;
  1.x needs markdown-it 15). `Term` on one line, `: definition` on the next, a blank line between
  entries. Terms render bold in a left column sized to the longest term, rows packed tight.
  Registered in `markdownSetup`, the hook Slidev 52 calls, along with sub (`H~2~O`) and mark
  (`==highlight==`), which had stopped working under the old `markdownItSetup` key. The
  marker-aware list rule is still under `markdownItSetup`, which Slidev 52 ignores.

To pull in upstream changes later, diff against a fresh checkout of the upstream
repo at a newer tag and apply what you want by hand.
