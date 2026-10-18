<script setup lang="js">
import { computed } from 'vue'
import { compute_alignment, compute_margin_class } from '../layoutHelper'

const props = defineProps({
  color: {
    default: 'white',
  },
  margin: {
    default: 'normal',
  },
  align: {
    default: 'l',
  },
})

const colorscheme = computed(() => {
  return `neversink-${props.color}-scheme`
})

const marginClass = computed(() => {
  return compute_margin_class(props.margin)
})

const titleAlignment = computed(() => compute_alignment(props.align))
</script>
<template>
  <div class="slidev-layout default slidecolor" :class="[colorscheme, marginClass]">
    <div v-if="$slots.title" class="title" :class="titleAlignment">
      <slot name="title" />
    </div>
    <slot />
  </div>
</template>

<style>
.slidev-layout.default .title {
  margin-bottom: 1rem;
}
</style>
