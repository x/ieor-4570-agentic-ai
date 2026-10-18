<script setup lang="js">
import { computed } from 'vue'
import { compute_alignment, compute_column_size } from '../layoutHelper'

const props = defineProps({
  columns: {
    default: 'is-one-half',
  },
  // Alignment of the left (prose) column only, e.g. `lt`, `lm`.
  align: {
    default: 'lt',
  },
  color: {
    default: 'white',
  },
  // Optional filename label shown above the code in the right panel.
  filename: {
    default: null,
  },
  // Font size of the code, as a CSS length. Default matches Slidev's own code size.
  codesize: {
    default: '12px',
  },
  // Soft-wrap long code lines instead of scrolling them off the panel.
  wrap: {
    default: false,
  },
})

const alignment = computed(() => compute_alignment(props.align))
const colwidth = computed(() => compute_column_size(props.columns))
const colorscheme = computed(() => `neversink-${props.color}-scheme`)
</script>

<template>
  <div class="slidev-layout default code-right slidecolor" :class="colorscheme">
    <div class="left-col" :class="alignment">
      <slot name="left" />
    </div>

    <div class="right-col" :class="{ 'code-wrap': wrap }" :style="{ '--code-right-size': codesize }">
      <div v-if="filename" class="code-right-filename">{{ filename }}</div>
      <slot name="right" />
    </div>
  </div>
</template>

<style scoped>
.code-right {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  grid-template-rows: 1fr;
}

.code-right .left-col {
  grid-area: 1 / 1 / 2 / span v-bind(colwidth.l);
  margin-right: 2rem;
  display: flex;
  flex-direction: column;
}

/* The right column bleeds past the slide padding (px-14 py-10) so the code
   background fills the entire right half of the slide. */
.code-right .right-col {
  grid-area: 1 / v-bind(colwidth.l + 1) / 2 / span v-bind(colwidth.r);
  margin: -2.5rem -3.5rem -2.5rem 0;
  padding: 2rem 2.25rem;
  background: var(--neversink-bg-code-color);
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.code-right .code-right-filename {
  position: absolute;
  top: 1rem;
  right: 1.25rem;
  font-family: var(--neversink-mono-font);
  font-size: 0.8em;
  opacity: 0.55;
}

/* The panel is the code background; make the shiki block sit flush on it. */
.code-right .right-col :deep(pre),
.code-right .right-col :deep(.slidev-code) {
  background: transparent !important;
  padding: 0;
  margin: 0;
  /* !important: Slidev core sets .slidev-code font-size !important */
  font-size: var(--code-right-size) !important;
  line-height: 1.5 !important;
  /* long lines still scroll, but without a visible bar on stage */
  scrollbar-width: none;
}
.code-right .right-col :deep(pre)::-webkit-scrollbar {
  display: none;
}

.code-right .right-col :deep(.slidev-code-wrapper) {
  margin: 0;
}

/* wrap: true */
.code-right .right-col.code-wrap :deep(pre),
.code-right .right-col.code-wrap :deep(pre code),
.code-right .right-col.code-wrap :deep(.line) {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
</style>
