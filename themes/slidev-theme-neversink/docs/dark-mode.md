# Dark Mode

Neversink supports Slidev's built-in dark mode feature, allowing your presentations to adapt to light and dark viewing preferences.

## Enabling Dark Mode

To enable dark mode support in your presentation, set the `colorSchema` option in your first slide's frontmatter:

```md
---
theme: neversink
colorSchema: auto
---
```

### Color Schema Options

| Value | Description |
|-------|-------------|
| `auto` | Automatically switches based on system preference (recommended) |
| `light` | Forces light mode only |
| `dark` | Forces dark mode only |

## Toggling Dark Mode

When `colorSchema` is set to `auto` or when both modes are available, you can toggle between light and dark mode using:

- **Keyboard shortcut**: Press `d` to toggle dark mode
- **Navigation controls**: Click the dark mode toggle in Slidev's navigation panel
- **System preference**: The presentation will automatically follow your OS dark mode setting when using `auto`

## How Color Schemes Work in Dark Mode

Neversink's [color schemes](/colors) automatically adapt when dark mode is enabled. Each scheme has been roughly designed to maintain readability and visual appeal in both modes.  Suggested improvements are welcome!

For example, when you use a layout with `color: amber`:

```md
---
layout: side-title
color: amber
---
```

The amber colors will automatically adjust to appropriate dark mode variants when the user toggles dark mode.

### CSS Variables in Dark Mode

The theme's CSS variables are redefined in dark mode to ensure proper contrast:

```css
/* Light mode (default) */
--neversink-bg-color: /* light background */
--neversink-text-color: /* dark text */

/* Dark mode (html.dark) */
--neversink-bg-color: /* dark background */
--neversink-text-color: /* light text */
```

## Conditional Content with LightOrDark

Slidev provides a built-in `<LightOrDark>` component for showing different content based on the current mode:

```vue
<LightOrDark>
  <template #light>
    <img src="/logo-light.png" />
  </template>
  <template #dark>
    <img src="/logo-dark.png" />
  </template>
</LightOrDark>
```

This is useful for:

- Showing different logo versions
- Displaying images optimized for each mode
- Any content that needs to differ between modes

## Images in Dark Mode

Some images designed for light backgrounds may look odd on dark backgrounds. You have several options:

### 1. Use the `.invert` Class

Add the `invert` class to invert image colors in dark mode:

```html
<img src="/diagram.png" class="invert" />
```

### 2. Use Conditional Images

Use the `<LightOrDark>` component to show different images:

```vue
<LightOrDark>
  <template #light>
    <img src="/chart-light.png" />
  </template>
  <template #dark>
    <img src="/chart-dark.png" />
  </template>
</LightOrDark>
```

## Components in Dark Mode

All Neversink components (StickyNote, Admonition, SpeechBubble, etc.) automatically adapt to dark mode when using color schemes:

```vue
<StickyNote color="amber-light" title="Note">
  This sticky note will look great in both modes!
</StickyNote>
```

## Programmatic Dark Mode Access

For advanced use cases, you can access the dark mode state in Vue components:

```vue
<script setup>
import { isDark, toggleDark } from '@slidev/client/logic/dark'
</script>

<template>
  <button @click="toggleDark()">
    {{ isDark ? 'Switch to Light' : 'Switch to Dark' }}
  </button>
</template>
```

