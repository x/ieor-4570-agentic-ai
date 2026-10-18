# `layout: code-right`

## Description

`layout: code-right` is a two-column slide where the right column is a full-height code panel. The panel's gray background bleeds to the slide edges, the code sits inside with a comfortable margin, and an optional filename label appears above it. Because the panel uses the slide's full height and no card chrome, it fits more lines of code than a code block inside `two-cols`.

The left column is ordinary prose with the usual `align` control.

## Frontmatter

- `layout: code-right` (required).
- `columns:` (optional) width split, same shorthands as [`two-cols`](/layouts/two-cols). Default `is-one-half`.
- `align:` (optional) alignment of the **left** column only, e.g. `lt`, `lm`, `cm`. Default `lt`.
- `color:` (optional) any [color scheme](/colors) for the left column. Default `white`. The code panel uses that scheme's code background color.
- `filename:` (optional) muted monospace label pinned to the top-right corner of the panel, e.g. `train.py`. Default none. The code itself is vertically centered in the panel.
- `codesize:` (optional) font size of the code as a CSS length. Default `12px` (Slidev's normal code size). Drop it to fit more lines.

## Slots

- `:: left ::` prose.
- `:: right ::` the code. Put a normal fenced code block here. Its own background is removed so the panel reads as one continuous surface.

## Example

~~~md
---
layout: code-right
filename: train.py
codesize: 0.85rem
---

:: left ::

## Training Markov Chains

1. Define tokens
2. Count transitions
3. Normalize to probabilities

:: right ::

```python
transitions = {}
for document in corpus:
    ...
```
~~~
