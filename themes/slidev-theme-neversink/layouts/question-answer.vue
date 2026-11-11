<script setup lang="js">
import SideTitle from './side-title.vue'

defineProps({
  side: {
    default: 'l',
  },
  color: {
    default: 'light',
  },
  align: {
    default: 'cm-lm',
  },
  margin: {
    default: 'normal',
  },
})
</script>
<template>
  <SideTitle titlewidth="is-one-half" :side="side" :color="color" :align="align" :margin="margin">
    <template #title><slot name="question" /></template>
    <template #content>
      <div v-click>
        <slot name="answer" />
        <slot name="default" />
      </div>
    </template>
  </SideTitle>
</template>
