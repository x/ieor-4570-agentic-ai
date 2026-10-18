<script setup lang="js">
import { computed } from 'vue'
import { compute_margin_class } from '../layoutHelper'

const props = defineProps({
  color: {
    default: 'white',
  },
  margin: {
    default: 'normal',
  },
})

const colorscheme = computed(() => {
  return `neversink-${props.color}-scheme`
})

const marginClass = computed(() => {
  return compute_margin_class(props.margin)
})
</script>
<template>
  <div class="slidev-layout full w-full h-full slidecolor" :class="[colorscheme, marginClass]">
    <slot />
  </div>
</template>
