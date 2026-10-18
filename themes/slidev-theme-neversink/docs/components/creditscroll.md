# CreditScroll

## Description

The `CreditScroll` component creates a scrolling container similar to movie credits. Content placed inside will automatically scroll upward when the slide is entered. This component is used internally by the [`layout: credits`](/layouts/credits) layout, but can also be used standalone.

## Props

- `speed` (optional) controls how fast the content scrolls. Default is `0.5`. Higher numbers scroll faster.
- `loop` (optional) whether the credits should loop back to the beginning after scrolling completes. Default is `false`.

## Usage

The component uses a default slot for content.

```vue
<CreditScroll speed="1.0" loop>
  <div class="text-center">
    <h2>Credits</h2>
    <p>Person 1</p>
    <p>Person 2</p>
  </div>
</CreditScroll>
```

## Behavior

- Scrolling automatically starts when you navigate to the slide
- Scrolling resets when re-entering the slide
- If `loop` is `true`, the content will restart from the beginning after completing
- If `loop` is `false`, scrolling stops when the content has fully scrolled through

## Note

For most use cases, it's easier to use the [`layout: credits`](/layouts/credits) layout which wraps this component and provides frontmatter options for `speed` and `loop`.
