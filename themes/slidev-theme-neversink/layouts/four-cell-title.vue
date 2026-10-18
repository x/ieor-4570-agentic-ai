<script setup lang="js">
import { computed, useSlots } from 'vue'
import { compute_alignment, compute_margin_class } from '../layoutHelper'

const slots = useSlots()

const props = defineProps({
  // title - top-left - top-right - bottom-left - bottom-right
  align: {
    default: 'l-lt-lt-lt-lt',
  },
  color: {
    default: 'white',
  },
  titlepos: {
    default: 't',
    validator: (value) => {
      return ['t', 'b', 'n'].includes(value)
    },
  },
  margin: {
    default: 'normal',
  },
})

const alignment = computed(() => {
  const p = props.align.split('-')
  return {
    t: compute_alignment(p[0]),
    tl: compute_alignment(p[1]),
    tr: compute_alignment(p[2]),
    bl: compute_alignment(p[3]),
    br: compute_alignment(p[4]),
  }
})

const colorscheme = computed(() => {
  return `neversink-${props.color}-scheme`
})

const marginClass = computed(() => {
  return compute_margin_class(props.margin)
})

const flexclass = computed(() => {
  if (slots.title != undefined && props.titlepos == 't') {
    return 'slidev-layout four-cell-header'
  } else if (slots.title != undefined && props.titlepos == 'b') {
    return 'slidev-layout four-cell-footer'
  } else {
    return 'slidev-layout four-cell-grid'
  }
})
</script>

<template>
  <div
    v-if="alignment.t == 'error' || alignment.tl == 'error' || alignment.tr == 'error' || alignment.bl == 'error' || alignment.br == 'error'"
    class="slidev-layout default error"
  >
    <span class="ns-c-warning"><b>Error</b>: invalid layout params.</span>
    <hr />
    <p>
      There are four parameters: <code>align</code>, <code>color</code>, <code>titlepos</code>, and
      <code>margin</code>. Currently: <code>align: {{ props.align }}</code
      >, <code>color: {{ props.color }}</code
      >, <code>titlepos: {{ props.titlepos }}</code
      >, <code>margin: {{ props.margin }}</code>.
    </p>
    <p>
      The <code>align</code> parameter has five dash-separated parts:
      <code>title-topleft-topright-bottomleft-bottomright</code>. The title takes one letter
      (<code>l</code>/<code>c</code>/<code>r</code>); each cell takes two, a horizontal
      (<code>l</code>/<code>c</code>/<code>r</code>) and a vertical (<code>t</code>/<code>m</code>/<code>b</code>). e.g.
      <code>align: c-lt-lt-lt-lt</code>.
    </p>
    <p>
      Slots: <code>:: title ::</code>, <code>:: top-left ::</code>, <code>:: top-right ::</code>,
      <code>:: bottom-left ::</code>, and <code>:: bottom-right ::</code>. The two bottom cells share a grid row, so
      they always start at the same vertical position regardless of how tall the top cells are.
    </p>
  </div>
  <div v-else class="slidecolor" :class="flexclass + ' ' + colorscheme + ' ' + marginClass">
    <div v-if="$slots.title && props.titlepos != 'n'" class="title" :class="alignment.t">
      <slot name="title" />
    </div>
    <div v-if="$slots['top-left']" class="cell tl" :class="alignment.tl">
      <slot name="top-left" />
    </div>
    <div v-if="$slots['top-right']" class="cell tr" :class="alignment.tr">
      <slot name="top-right" />
    </div>
    <div v-if="$slots['bottom-left']" class="cell bl" :class="alignment.bl">
      <slot name="bottom-left" />
    </div>
    <div v-if="$slots['bottom-right']" class="cell br" :class="alignment.br">
      <slot name="bottom-right" />
    </div>
    <div v-if="$slots.default" class="end">
      <slot name="default" />
    </div>
  </div>
</template>

<style>
.slidev-layout.four-cell-header,
.slidev-layout.four-cell-footer,
.slidev-layout.four-cell-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  column-gap: 2rem;
  row-gap: 1rem;
}

/* Content rows are `auto`: each row grows to fit its tallest cell, so a long
   top cell never overflows into the bottom row. The two bottom cells share one
   grid row, so :: bottom-left :: and :: bottom-right :: still start at the same
   vertical line. The trailing `auto` row holds the optional default slot. */
.slidev-layout.four-cell-header {
  grid-template-rows: auto auto auto auto;
}
.slidev-layout.four-cell-footer {
  grid-template-rows: auto auto auto;
}
.slidev-layout.four-cell-grid {
  grid-template-rows: auto auto auto;
}

.slidev-layout.four-cell-header .title {
  grid-area: 1 / 1 / 2 / span 12;
  margin-bottom: 1rem;
}
.slidev-layout.four-cell-footer .title {
  grid-area: 3 / 1 / 4 / span 12;
  margin-top: 1rem;
}

.slidev-layout.four-cell-header .end {
  grid-area: 4 / 1 / 5 / span 12;
}
.slidev-layout.four-cell-grid .end {
  grid-area: 3 / 1 / 4 / span 12;
}

.slidev-layout.four-cell-header .title h1 + p,
.slidev-layout.four-cell-footer .title h1 + p,
.slidev-layout.four-cell-header .title h2 + p,
.slidev-layout.four-cell-footer .title h2 + p,
.slidev-layout.four-cell-header .title h3 + p,
.slidev-layout.four-cell-footer .title h3 + p {
  margin-top: 0.1em;
  margin-bottom: 0;
}

.slidev-layout.four-cell-header .title p,
.slidev-layout.four-cell-footer .title p {
  margin-top: 0.2em;
  margin-bottom: 0;
}

.slidev-layout.four-cell-header .cell,
.slidev-layout.four-cell-footer .cell,
.slidev-layout.four-cell-grid .cell {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}
</style>

<style scoped>
/* Header: title is row 1, cells fill rows 2 (top) and 3 (bottom). */
.four-cell-header .tl {
  grid-area: 2 / 1 / 3 / span 6;
}
.four-cell-header .tr {
  grid-area: 2 / 7 / 3 / span 6;
}
.four-cell-header .bl {
  grid-area: 3 / 1 / 4 / span 6;
}
.four-cell-header .br {
  grid-area: 3 / 7 / 4 / span 6;
}

/* No header (or footer title): cells fill rows 1 (top) and 2 (bottom). */
.four-cell-footer .tl,
.four-cell-grid .tl {
  grid-area: 1 / 1 / 2 / span 6;
}
.four-cell-footer .tr,
.four-cell-grid .tr {
  grid-area: 1 / 7 / 2 / span 6;
}
.four-cell-footer .bl,
.four-cell-grid .bl {
  grid-area: 2 / 1 / 3 / span 6;
}
.four-cell-footer .br,
.four-cell-grid .br {
  grid-area: 2 / 7 / 3 / span 6;
}
</style>
