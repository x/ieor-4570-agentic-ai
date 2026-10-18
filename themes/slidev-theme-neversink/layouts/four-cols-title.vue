<script setup lang="js">
import { computed, useSlots } from 'vue'
import { compute_alignment, compute_four_column_size, compute_margin_class } from '../layoutHelper'

const slots = useSlots()

const props = defineProps({
  columns: {
    default: 'is-quarters',
  },
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
  const parts = props.align.split('-')
  return {
    t: compute_alignment(parts[0]),
    a: compute_alignment(parts[1]),
    b: compute_alignment(parts[2]),
    c: compute_alignment(parts[3]),
    d: compute_alignment(parts[4]),
  }
})

const colwidth = computed(() => compute_four_column_size(props.columns))

const colorscheme = computed(() => {
  return `neversink-${props.color}-scheme`
})

const marginClass = computed(() => {
  return compute_margin_class(props.margin)
})

const flexclass = computed(() => {
  if (slots.title != undefined) {
    if (props.titlepos == 't') {
      return 'slidev-layout four-cols-header'
    } else if (props.titlepos == 'b') {
      return 'slidev-layout four-cols-footer'
    } else {
      return 'slidev-layout four-cols'
    }
  } else {
    return 'slidev-layout four-cols'
  }
})
</script>

<!-- four-cols-title.vue -->
<template>
  <div
    v-if="
      colwidth == 'error' ||
      alignment.t == 'error' ||
      alignment.a == 'error' ||
      alignment.b == 'error' ||
      alignment.c == 'error' ||
      alignment.d == 'error'
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
      <code>columns</code> splits 12 units across four columns which must sum to 12. Use
      <code>columns: is-3-3-3-3</code> for equal quarters (also the meaning of the default
      <code>is-quarters</code>), or uneven splits like <code>is-2-4-4-2</code>. The last number may be
      omitted (<code>is-3-3-3</code> resolves to <code>is-3-3-3-3</code>).
    </p>
    <p>
      Slots are <code>:: title ::</code>, <code>:: one ::</code>, <code>:: two ::</code>,
      <code>:: three ::</code>, and <code>:: four ::</code>. Title is optional.
    </p>
    <p>
      <code>align</code> has five dash-separated parts: the title, then one per column, e.g.
      <code>align: c-lt-lt-lt-lt</code>. The first letter is horizontal (<code>c</code>, <code>l</code>,
      <code>r</code>); for the columns the second letter is vertical (<code>t</code>, <code>m</code>,
      <code>b</code>).
    </p>
  </div>
  <div v-else class="slidecolor" :class="flexclass + ' ' + colorscheme + ' ' + marginClass">
    <div v-if="$slots.title && props.titlepos != 'n'" class="title" :class="alignment.t">
      <slot name="title" />
    </div>
    <div v-if="$slots.one" class="col-a" :class="alignment.a">
      <slot name="one" />
    </div>
    <div v-if="$slots.two" class="col-b" :class="alignment.b">
      <slot name="two" />
    </div>
    <div v-if="$slots.three" class="col-c" :class="alignment.c">
      <slot name="three" />
    </div>
    <div v-if="$slots.four" class="col-d" :class="alignment.d">
      <slot name="four" />
    </div>
    <div v-if="$slots.default" class="end">
      <slot name="default" />
    </div>
  </div>
</template>

<style>
.slidev-layout.four-cols-header,
.slidev-layout.four-cols-footer {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  grid-template-rows: auto 1fr auto;
}

.slidev-layout.four-cols {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  grid-template-rows: auto auto;
}

.slidev-layout.four-cols-header .title {
  grid-area: 1 / 1 / 2 / span 12;
  margin-bottom: 1rem;
}

.slidev-layout.four-cols-footer .title {
  grid-area: 3 / 1 / 4 / span 12;
  margin-bottom: 1rem;
}

.slidev-layout.four-cols-header .title h1 + p,
.slidev-layout.four-cols-footer .title h1 + p,
.slidev-layout.four-cols-header .title h2 + p,
.slidev-layout.four-cols-footer .title h2 + p,
.slidev-layout.four-cols-header .title h3 + p,
.slidev-layout.four-cols-footer .title h3 + p {
  margin-top: 0.1em;
  margin-bottom: 0;
}

.slidev-layout.four-cols-header .title p,
.slidev-layout.four-cols-footer .title p {
  margin-top: 0.2em;
  margin-bottom: 0;
}

.slidev-layout.four-cols .col-a,
.slidev-layout.four-cols-header .col-a,
.slidev-layout.four-cols-footer .col-a,
.slidev-layout.four-cols .col-b,
.slidev-layout.four-cols-header .col-b,
.slidev-layout.four-cols-footer .col-b,
.slidev-layout.four-cols .col-c,
.slidev-layout.four-cols-header .col-c,
.slidev-layout.four-cols-footer .col-c {
  margin-right: 1.5rem;
  display: flex;
  flex-direction: column;
}

.slidev-layout.four-cols .col-d,
.slidev-layout.four-cols-header .col-d,
.slidev-layout.four-cols-footer .col-d {
  display: flex;
  flex-direction: column;
}

.slidev-layout.four-cols-header .end,
.slidev-layout.four-cols-footer .end {
  grid-area: 4 / 1 / 5 / span 12;
}

.slidev-layout.four-cols .end {
  grid-area: 3 / 1 / 4 / span 12;
}
</style>

<style scoped>
.four-cols-footer .col-a,
.four-cols-header .col-a {
  grid-area: 2 / 1 / 3 / span v-bind(colwidth.a);
}
.four-cols-footer .col-b,
.four-cols-header .col-b {
  grid-area: 2 / v-bind(colwidth.a + 1) / 3 / span v-bind(colwidth.b);
}
.four-cols-footer .col-c,
.four-cols-header .col-c {
  grid-area: 2 / v-bind(colwidth.a + colwidth.b + 1) / 3 / span v-bind(colwidth.c);
}
.four-cols-footer .col-d,
.four-cols-header .col-d {
  grid-area: 2 / v-bind(colwidth.a + colwidth.b + colwidth.c + 1) / 3 / span v-bind(colwidth.d);
}

.four-cols .col-a {
  grid-area: 1 / 1 / 2 / span v-bind(colwidth.a);
}
.four-cols .col-b {
  grid-area: 1 / v-bind(colwidth.a + 1) / 2 / span v-bind(colwidth.b);
}
.four-cols .col-c {
  grid-area: 1 / v-bind(colwidth.a + colwidth.b + 1) / 2 / span v-bind(colwidth.c);
}
.four-cols .col-d {
  grid-area: 1 / v-bind(colwidth.a + colwidth.b + colwidth.c + 1) / 2 / span v-bind(colwidth.d);
}
</style>
