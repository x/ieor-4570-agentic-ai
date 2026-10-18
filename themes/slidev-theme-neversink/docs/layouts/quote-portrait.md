# `layout: quote-portrait`

## Description

`layout: quote-portrait` is [`quote`](/layouts/quote) with a circular portrait to the left of the quote box. The box itself (color scheme, rounded border, drop shadow, author line) is identical to `quote`; the only addition is a round image in a `pic` slot. Use it to put a face next to an attributed quote.

## Frontmatter

Same as [`quote`](/layouts/quote), plus `size`:

- `color:` (optional) any [color scheme](/colors). Default `light`.
- `author:` (optional) attribution line shown under the quote. Default none.
- `quotesize:` (optional) text size class for the quote. Default `text-2xl`.
- `authorsize:` (optional) text size class for the author line. Default `text-l`.
- `size:` (optional) the diameter of the portrait circle, as a CSS length. Default `180px`, roughly a third of the slide height.

## Slots

- `:: pic ::` holds the portrait. Put a normal Markdown image here; it is cropped to a circle (`object-fit: cover`), so any aspect ratio works. If the slot is omitted the layout falls back to a plain centered quote box.
- `:: default ::` (the implicit slot) holds the quote text.

## Example

```md
---
layout: quote-portrait
color: sky-light
author: 'Andrew Feldman - CEO, Cerebras Systems'
size: 200px
---

:: pic ::

![Andrew Feldman](./images/feldman.jpg)

:: default ::

When the internet was slow, Netflix delivered DVDs in envelopes. When the
internet got fast, Netflix became a movie studio.
```
