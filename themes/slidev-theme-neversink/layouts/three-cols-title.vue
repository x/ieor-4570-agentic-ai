<script setup lang="js">
import { computed, useSlots } from 'vue'
import { compute_alignment, compute_three_column_size, compute_margin_class } from '../layoutHelper'

const slots = useSlots()

const props = defineProps({
  columns: {
    default: 'is-thirds',
  },
  align: {
    default: 'l-lt-lt-lt',
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
  const parts = props.align.split('-')
  return {
    t: compute_alignment(parts[0]),
    l: compute_alignment(parts[1]),
    m: compute_alignment(parts[2]),
    r: compute_alignment(parts[3]),
  }
})

const colwidth = computed(() => compute_three_column_size(props.columns))

const colorscheme = computed(() => {
  return `neversink-${props.color}-scheme`
})

const marginClass = computed(() => {
  return compute_margin_class(props.margin)
})

const flexclass = computed(() => {
  if (slots.title != undefined) {
    if (props.titlepos == 't') {
      return 'slidev-layout three-cols-header'
    } else if (props.titlepos == 'b') {
      return 'slidev-layout three-cols-footer'
    } else {
      return 'slidev-layout three-cols'
    }
  } else {
    return 'slidev-layout three-cols'
  }
})
</script>

<!-- three-cols-title.vue -->
<template>
  <div
    v-if="
      colwidth == 'error' ||
      alignment.t == 'error' ||
      alignment.l == 'error' ||
      alignment.m == 'error' ||
      alignment.r == 'error'
    "
    class="slidev-layout default error"
  >
    <span class="ns-c-warning"><b>Error</b>: invalid layout params.</span>
    <hr />
    <p>
      There are four parameters: <code>columns</code>, <code>align</code>, <code>color</code>, and
      <code>titlepos</code>. Currently: <code>columns: {{ props.columns }}</code
      >, <code>align: {{ props.align }} </code>, <code>color: {{ props.color }} </code>, and
      <code>titlepos: {{ props.titlepos }} </code>.
    </p>
    <p>
      Options for <code>columns</code> are divided into 12 column units across three columns which must sum to 12. Use
      <code>columns: is-4-4-4</code> for equal thirds (also the meaning of the default <code>is-thirds</code>), or
      uneven splits like <code>is-3-6-3</code> or <code>is-2-8-2</code>. The last number may be omitted
      (<code>is-3-6</code> resolves to <code>is-3-6-3</code>).
    </p>
    <p>
      In addition you can specify "slots" of the page with <code>:: title ::</code>, <code>:: left ::</code>,
      <code>:: middle ::</code>, and <code>:: right ::</code>. Title is optional.
    </p>
    <p>
      The <code>align</code> parameter determines how the columns look. The notation is for example
      <code>align: c-cm-cm-cm</code>. The first part is for the title, then one part each for the left, middle, and
      right columns. The first letter is (<code>c</code> for center, <code>l</code> for left, <code>r</code> for
      right). For the columns the second letter is vertical alignment (<code>t</code> for top, <code>m</code> for
      middle, <code>b</code> for bottom).
    </p>
  </div>
  <div v-else class="slidecolor" :class="flexclass + ' ' + colorscheme + ' ' + marginClass">
    <div v-if="$slots.title && props.titlepos != 'n'" class="title" :class="alignment.t">
      <slot name="title" />
    </div>
    <div v-if="$slots.left" class="left-col" :class="alignment.l">
      <slot name="left" />
    </div>

    <div v-if="$slots.middle" class="middle-col" :class="alignment.m">
      <slot name="middle" />
    </div>

    <div v-if="$slots.right" class="right-col" :class="alignment.r">
      <slot name="right" />
    </div>
    <div v-if="$slots.default" class="end">
      <slot name="default" />
    </div>
  </div>
</template>

<style>
.slidev-layout.three-cols-header,
.slidev-layout.three-cols-footer {
  display: grid;
  grid-template-columns: repeat(12, 1fr); /* 12 columns */
  grid-template-rows: auto 1fr auto; /* top header and content */
}

.slidev-layout.three-cols {
  display: grid;
  grid-template-columns: repeat(12, 1fr); /* 12 columns */
  grid-template-rows: auto auto; /* top header and content */
}

.slidev-layout.three-cols-header .title {
  grid-area: 1 / 1 / 2 / span 12; /* full width */
  margin-bottom: 1rem;
}

.slidev-layout.three-cols-footer .title {
  grid-area: 3 / 1 / 4 / span 12; /* full width */
  margin-bottom: 1rem;
}

.slidev-layout.three-cols-header .title h1 + p,
.slidev-layout.three-cols-footer .title h1 + p,
.slidev-layout.three-cols-header .title h2 + p,
.slidev-layout.three-cols-footer .title h2 + p,
.slidev-layout.three-cols-header .title h3 + p,
.slidev-layout.three-cols-footer .title h3 + p {
  margin-top: 0.1em;
  margin-bottom: 0;
}

.slidev-layout.three-cols-header .title p,
.slidev-layout.three-cols-footer .title p {
  margin-top: 0.2em;
  margin-bottom: 0;
}

.slidev-layout.three-cols .left-col,
.slidev-layout.three-cols-header .left-col,
.slidev-layout.three-cols-footer .left-col,
.slidev-layout.three-cols .middle-col,
.slidev-layout.three-cols-header .middle-col,
.slidev-layout.three-cols-footer .middle-col {
  margin-right: 2rem;
  display: flex;
  flex-direction: column;
}

.slidev-layout.three-cols .right-col,
.slidev-layout.three-cols-header .right-col,
.slidev-layout.three-cols-footer .right-col {
  display: flex;
  flex-direction: column;
}

.slidev-layout.three-cols-header .end,
.slidev-layout.three-cols-footer .end {
  grid-area: 4 / 1 / 5 / span 12; /* full width */
}

.slidev-layout.three-cols .end {
  grid-area: 3 / 1 / 4 / span 12; /* full width */
}
</style>

<style scoped>
.three-cols-footer .left-col,
.three-cols-header .left-col {
  grid-area: 2 / 1 / 3 / span v-bind(colwidth.l);
}

.three-cols-footer .middle-col,
.three-cols-header .middle-col {
  grid-area: 2 / v-bind(colwidth.l + 1) / 3 / span v-bind(colwidth.m);
}

.three-cols-footer .right-col,
.three-cols-header .right-col {
  grid-area: 2 / v-bind(colwidth.l + colwidth.m + 1) / 3 / span v-bind(colwidth.r);
}

.three-cols .left-col {
  grid-area: 1 / 1 / 2 / span v-bind(colwidth.l);
}

.three-cols .middle-col {
  grid-area: 1 / v-bind(colwidth.l + 1) / 2 / span v-bind(colwidth.m);
}

.three-cols .right-col {
  grid-area: 1 / v-bind(colwidth.l + colwidth.m + 1) / 2 / span v-bind(colwidth.r);
}
</style>
