# StickyNote

<img src="/screenshots/36.png" alt="stickynotes slide example" width="600" class="screenshot mb-10 mt-10"/>

## Description

StickyNotes are a take on the classic computer metaphor of a sticknote. They are often used to provide notes or additional information to the viewer.

## `StickyNote`

The `StickyNote` component is used to create a colored box with an title and content. The StickyNote component has the following props:

- `title` (optional). Default value is ''
- `color` (optional) can be any of the [color scheme](/colors) options. If not provided, the default color is `amber-light`.
- `width` (optional) the width of the admonition. Default is `180px`.
- `textAlign` (optional) the text alignment of the content. Default is `left`.
- `custom` (optional) a custom CSS class to apply to the sticky note content. Default is empty.
- `customTitle` (optional) a custom CSS class to apply to the sticky note title. Default is `block text-xs font-mono tracking-normal font-bold`.
- `devOnly` (optional) when set to `true`, the sticky note will only be visible in development mode and will be hidden in production builds and exports. This is useful for personal notes or reminders that shouldn't appear in the final presentation. Default is `false`.

Example:

```vue
<StickyNote color="amber-light" textAlign="left" width="180px" title="Title">
  Hello, I'm a **sticky note**.
</StickyNote>
```

Renders as:
<StickyNote color="amber-light" textAlign="left" width="180px" title="Title">

Hello, I'm a **sticky note**.
</StickyNote>

You can also add custom CSS classes to style the sticky note content and title:

```vue
<StickyNote
  color="teal-light"
  width="200px"
  title="Custom Styled"
  custom="text-lg font-bold text-center"
  customTitle="text-red-500 text-lg"
>
  This content has custom styling applied.
</StickyNote>
```

Renders as:
<StickyNote color="teal-light" width="200px" title="Custom Styled" custom="text-lg font-bold text-center" customTitle="text-red-500 text-lg">
This content has custom styling applied.
</StickyNote>

If you want to position it somewhere arbitrary on the slide add v-drag to the admonition and also set the width to something fixed (e.g., `300px`):

```vue
<StickyNote color="amber-light" textAlign="left" width="180px" title="Title" v-drag>

Hello, I'm a **sticky note**.
</StickyNote>
```

Another color:

```vue
<StickyNote color="pink-light" textAlign="left" width="180px" title="Title">
  Hello, I'm a **sticky note**.
</StickyNote>
```

<StickyNote color="pink-light" textAlign="left" width="180px" title="Title">

Hello, I'm a **sticky note**.
</StickyNote>

## Dev-Only Notes

Use the `devOnly` prop to create sticky notes that only appear during development. These are perfect for speaker notes, reminders, or TODOs that you don't want in your exported presentation:

```vue
<StickyNote color="amber-light" width="180px" title="Note to self" devOnly>
  Remember to add more examples here before the talk!
</StickyNote>
```

When `devOnly` is set to `true`:

- The sticky note is visible when running `slidev dev`
- The sticky note is **hidden** when running `slidev build` or `slidev export`
