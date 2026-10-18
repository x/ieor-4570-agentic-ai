# `layout: four-cell-title`

## Description

The `layout: four-cell-title` layout is a titled 2×2 grid. It has an optional title along the top (or bottom) of the slide, and the main area is divided into four quadrants: `top-left`, `top-right`, `bottom-left`, and `bottom-right`. It is the four-cell sibling of [`two-cols-title`](/layouts/two-cols-title), and is handy for comparisons, matrices, or splitting a long list (like a course schedule) across even cells.

The two content rows are equal height (`1fr 1fr`), and because the two bottom cells **share a single grid row**, `bottom-left` and `bottom-right` always begin at the same vertical position regardless of how tall the top cells are. Likewise the two top cells share a row. This keeps the grid visually aligned even when the cells hold different amounts of content.

An optional `default` slot renders as a full-width footer below the grid (0 tall when empty), useful for a caption or a note.

## Frontmatter

- `layout: four-cell-title` (required).
- `color:` (optional) any of the [color scheme](/colors) options. Applies one scheme to the whole slide. Default is `white`.
- `align:` (optional) alignment of each region, in **five** dash-separated parts: `title-topleft-topright-bottomleft-bottomright`. The title segment takes a single letter (`l`/`c`/`r`) for horizontal alignment. Each cell segment takes two letters: horizontal (`l`/`c`/`r`) then vertical (`t`/`m`/`b`). Default is `l-lt-lt-lt-lt` (title left; every cell left-top).
- `titlepos:` (optional) `t` (top), `b` (bottom), or `n` (none). Default is `t`.
- `margin:` (optional) `normal` or `tight`. `tight` reduces the outer margins to fit denser content. Default is `normal`.

Example:

```yaml
---
layout: four-cell-title
color: light
align: c-lt-lt-lt-lt
titlepos: t
margin: tight
---
```

## Slots

This layout has five named slots, all optional: `:: title ::`, `:: top-left ::`, `:: top-right ::`, `:: bottom-left ::`, and `:: bottom-right ::`. In addition, the implicit `:: default ::` slot (any content before the first named slot) renders as a full-width footer under the grid.

## Example

```md
---
layout: four-cell-title
margin: tight
align: l-lt-lt-lt-lt
---

:: title ::

## Course Schedule

:: top-left ::

#### 9/10 · Introduction & Large Language Models

- Syllabus, grading, expectations
- History and inner workings of modern LLMs

:: top-right ::

#### 9/17 · Chatbots, Prompting, and Reasoning

- How does an LLM become a chatbot?
- Classic prompt engineering techniques

:: bottom-left ::

#### 9/24 · Agents that Live and Do

- Tool calling: how it works and best practices
- Deploying to GCP

:: bottom-right ::

#### 10/1 · Agents in Production and Evaluated

- OpenAI Agents SDK
- Agent traces (OTEL), guardrails

:: default ::

A footer note spanning the full width.
```

Because the two bottom cells share a grid row, `bottom-left` and `bottom-right` stay aligned even though `top-left` above has fewer lines than `top-right`.
