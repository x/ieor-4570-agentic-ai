<script setup>
import { computed } from 'vue'
const props = defineProps({
  color: {
    default: 'light',
  },
  author: {
    default: null,
  },
  quotesize: {
    default: 'text-2xl',
  },
  authorsize: {
    default: 'text-l',
  },
  // Diameter of the portrait circle. Default is roughly a third of the slide height.
  size: {
    default: '180px',
  },
})

const colorscheme = computed(() => {
  return `neversink-${props.color}-scheme`
})
</script>
<template>
  <div class="slidev-layout quote-portrait">
    <div class="my-auto flex items-center justify-center gap-8 w-95% ml-auto mr-auto">
      <div
        v-if="$slots.pic"
        class="portrait-wrap shrink-0"
        :class="colorscheme"
        :style="{ '--portrait-size': size }"
      >
        <slot name="pic" />
      </div>
      <div class="p-5 flex-1 rounded-lg border-1px quotecolor" :class="colorscheme">
        <div class="leading-normal" :class="quotesize">
          <slot name="default" /><br />
          <div v-if="author !== null" class="quote_author" :class="authorsize">- {{ author }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.quote-portrait .quotecolor {
  background-color: var(--neversink-bg-color);
  color: var(--neversink-text-color);
  border-color: var(--neversink-border-color);
  /* add a drop shadow */
  box-shadow: 5px 4px 6px rgba(0, 0, 0, 0.1);
}

.quote-portrait .quote_author {
  font-family: var(--neversink-title-font);
  font-weight: 400;
  text-align: right;
}

.slidev-layout.quote-portrait {
  padding-left: 1em;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 100%;
}

.slidev-layout.quote-portrait p {
  font-size: 1.5em;
  font-family: var(--neversink-quote-font);
  line-height: 1.2em;
  font-weight: 400;
  text-align: left;
}

/* Circular portrait to the left of the quote box. The slotted markdown image
   fills a fixed-diameter circle. */
.quote-portrait .portrait-wrap {
  width: var(--portrait-size);
  height: var(--portrait-size);
}

.quote-portrait .portrait-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 9999px;
  margin: 0;
  /* match the quote box's border + drop shadow */
  border: 1px solid var(--neversink-border-color);
  box-shadow: 5px 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
