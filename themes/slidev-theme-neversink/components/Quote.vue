<script setup>
// An inline quote: the quote layout's box, sized to sit inside a slide.
//   <Quote author="Chamberlin & Boyce (1974)" source="SEQUEL: ..." href="https://...">
//   "These rules are intended to ..."
//   </Quote>
import { computed } from 'vue'

const props = defineProps({
  author: { type: String, default: null },
  source: { type: String, default: null },
  href: { type: String, default: null },
  color: { type: String, default: 'light' },
  width: { type: String, default: '100%' },
})

const colorscheme = computed(() => `neversink-${props.color}-scheme`)
</script>

<template>
  <figure class="ns-quote rounded-lg border-1px" :class="colorscheme" :style="{ width }">
    <blockquote class="ns-quote-text"><slot /></blockquote>
    <figcaption v-if="author || source" class="ns-quote-source">
      &mdash;
      <span v-if="author">{{ author }}</span><span v-if="author && source">, </span>
      <a v-if="source && href" :href="href" target="_blank">{{ source }}</a>
      <span v-else-if="source">{{ source }}</span>
    </figcaption>
  </figure>
</template>

<style scoped>
.ns-quote {
  margin: 0.75em 0;
  padding: 0.75em 1em;
  background-color: var(--neversink-bg-color);
  color: var(--neversink-text-color);
  border-color: var(--neversink-border-color);
  box-shadow: 5px 4px 6px rgba(0, 0, 0, 0.1);
}

/* Undo the global blockquote styling: the box is the quote's frame. */
.ns-quote-text {
  margin: 0;
  padding: 0;
  border: none;
  background: none;
  font-family: var(--neversink-quote-font);
  font-size: 1.05em;
  line-height: 1.35;
}

.ns-quote-text :deep(p) {
  margin: 0;
}

.ns-quote-source {
  margin-top: 0.5em;
  text-align: right;
  font-size: 0.8em;
  opacity: 0.75;
}

.ns-quote-source a {
  color: inherit;
}
</style>
