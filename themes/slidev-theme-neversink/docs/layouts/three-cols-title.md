# `layout: three-cols-title`

## Description

The `layout: three-cols-title` layout is the three-column sibling of [`two-cols-title`](/layouts/two-cols-title). It has an optional title along the top or bottom of the slide, and then the main section is divided into three columns (left, middle, right). The overall space is divided into 12 column units which are distributed across the three columns.

The position of the title on the slide can also be configured. It can be at the top or bottom of the slide, or hidden/missing entirely. The default position is at the top.

A default slot is provided for content that appears before a named slot. This content will appear at the bottom of the slide.

## Frontmatter

- `layout: three-cols-title` (required).
- `color:` (optional) can be any of the [color scheme](/colors) options. If not provided, the default color is `white`.
- `columns:` (optional) gives the widths of the left, middle, and right columns as 12 column units that must sum to 12. The default value is `is-thirds`, which is equivalent to `is-4-4-4` (three equal columns). Any `is-L-M-R` split that sums to 12 is allowed, e.g. `is-3-6-3`, `is-2-8-2`, `is-5-4-3`. The last number may be omitted, in which case the right column takes the remaining space (`is-3-6` resolves to `is-3-6-3`).
- `align:` (optional) determines the alignment of the content in different parts of the slide. The options are specified in four parts using kebab notation: `title-left-middle-right`. The first letter of each segment is either `l` for left, `c` for center, or `r` for right. This sets the text alignment of that section. The second letter of the column segments is either `t` for top, `m` for middle, or `b` for bottom. This sets the vertical alignment of the content in that column. **The title segment only can configure the `l/c/r` alignment.** The default value is `l-lt-lt-lt`.
- `titlepos:` (optional) is either `t` (top), `b` (bottom), or `n` (none). This determines the position of the title. The default value is `t`.

Example:

```yaml
---
layout: three-cols-title
columns: is-3-6-3
align: c-lt-cm-lt
color: light
titlepos: t
---
```

## Slots

This `three-cols-title` slide has four named slots which are all optional:
`:: title ::`, `:: left ::`, `:: middle ::`, and `:: right ::`. In addition, the `:: default ::` slot exists for any content that appears before a named slot. It will appear at the bottom of the slide.
If a column slot is not provided the space for it will remain according to the `columns:` frontmatter.

## Examples

### Basic example

```md
---
layout: three-cols-title
columns: is-thirds
align: l-lt-lt-lt
---

:: title ::

# This is `three-cols-title`

:: left ::

The left column.

:: middle ::

The middle column.

:: right ::

The right column.
```

### Wide middle column

```md
---
layout: three-cols-title
columns: is-3-6-3
align: c-lt-cm-lt
---

:: title ::

# A wide middle column

:: left ::

Notes on the left.

:: middle ::

The main content gets 6 of the 12 units and is centered.

:: right ::

Notes on the right.
```
