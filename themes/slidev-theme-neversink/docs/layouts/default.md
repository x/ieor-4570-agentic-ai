# `layout: default`

<img src="/screenshots/6.png" alt="Default slide example" width="600" class="screenshot mb-10 mt-10"/>

## Description

The `layout: default` layout is probably the most common slide type. It is a full screen slide with a title and content. The title is displayed in a large font size and the content is displayed in a smaller font size.

## Frontmatter

- `layout: default` (required).
- `color:` (optional) can be any of the [color scheme](/colors) options. If not provided, the default color is `white`.
- `align:` (optional) sets the text alignment of the optional title slot: `l` (left), `c` (center), or `r` (right). The default value is `l`. Only applies when a `:: title ::` slot is present.

Example:

```yaml
---
layout: default
color: white
---
```

## Slots

This `default` slide has an optional `:: title ::` slot in addition to the default slot. When present, the title renders at the top of the slide. Since the default slot is normally the content *before* any named slot, use an explicit `:: default ::` marker after the title to keep the body reading in natural order:

```md
---
layout: default
---

:: title ::

# Slide title

An optional subtitle — non-heading text right after a heading in a title slot renders gray, smaller, and tight against the heading.

:: default ::

Body content goes here.
```

If no `:: title ::` slot is used, the layout behaves exactly as before.

## Examples

### Basic example

```md
---
layout: default
---

# This is the `default` layout

This is kind of the basic slide. The main content is interpreted as
markdown and rendered in the center of the slide.

Speaking of markdown, you can use markdown to make things **bold** or
_italic_ or even `code` like `this`. In **Neversink** you can also
==highlight things using the double equals signs like this== thanks
to the `markdown-it-mark` plugin.

Of course you can make bullet lists:

- Hi
- There
- Bananas

and use all the Slidev [markdown features](https://sli.dev/guide/syntax) like LaTeX math $x^2$, etc...
```

Renders as:

<img src="/screenshots/6.png" alt="Cover slide example" width="600" class="screenshot"/>

### Dark and stormy

```md
---
layout: default
color: navy
---

# This is the `default` layout

This is kind of the basic slide. The main content is interpreted as
markdown and rendered in the center of the slide.

Speaking of markdown, you can use markdown to make things **bold** or
_italic_ or even `code` like `this`. In **Neversink** you can also
==highlight things using the double equals signs like this== thanks
to the `markdown-it-mark` plugin.

Of course you can make bullet lists:

- Hi
- There
- Bananas

and use all the Slidev [markdown features](https://sli.dev/guide/syntax) like LaTeX math $x^2$, etc...
```

Renders as:

<img src="/screenshots/7.png" alt="Cover slide example" width="600" class="screenshot"/>
