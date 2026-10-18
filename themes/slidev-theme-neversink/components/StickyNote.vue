<script setup>
import { computed } from 'vue'

const props = defineProps({
  color: {
    type: String,
    default: 'amber-light',
  },
  textAlign: {
    type: String,
    default: 'left',
  },
  width: {
    type: String,
    default: '180px',
  },
  title: {
    type: String,
    default: '',
  },
  custom: {
    // add a custom class if you want
    type: String,
    default: '',
  },
  customTitle: {
    // add a custom class if you want
    type: String,
    default: 'block text-xs font-mono tracking-normal font-bold',
  },
  devOnly: {
    // only show in dev mode (useful for notes that shouldn't appear in exports)
    type: Boolean,
    default: false,
  },
})

const isVisible = computed(() => {
  if (!props.devOnly) return true
  return import.meta.env.DEV
})

const colorscheme = computed(() => {
  return `neversink-${props.color}-scheme`
})

const stickyClasses = computed(() => {
  return [colorscheme.value, 'sticky-note']
})

const stickyStyles = computed(() => ({
  '--sticky-color': 'var(--neversink-bg-color)',
  '--border-color': 'var(--neversink-fg-color)',
  '--text-color': 'var(--neversink-text-color)',
  '--text-align': props.textAlign,
  '--width': props.width,
}))
</script>

<template>
  <div v-if="isVisible" :class="stickyClasses" :style="stickyStyles">
    <template v-if="props.title !== ''"
      ><span :class="props.customTitle">{{ props.title }}</span></template
    >
    <div :class="props.custom"><slot></slot></div>
  </div>
</template>

<style scoped>
.sticky-note {
  width: var(--width);
  height: var(--width);
  background-color: var(--sticky-color, yellow);
  text-align: var(--text-align, left);
  max-width: 100%;
  padding: 1em;
  position: relative;
  box-shadow: 5px 4px 6px rgba(0, 0, 0, 0.1);
  font-weight: 400;
  font-size: 0.8rem;
  color: var(--text-color);
  border: 0.4px solid var(--border-color);
}
</style>
