/* ./setup/shiki.ts */
import { defineShikiSetup } from '@slidev/types'

// ==foo== inside any fenced code block renders as highlighted `foo`, markers hidden.
// The markers are stripped before the grammar runs, so syntax colors are untouched.
// ponytail: `a==b==c` with no spaces would be read as a mark. Write `a == b == c`,
// or switch to a rarer marker here if that ever bites.
const MARK = /==(\S(?:[^\n]*?\S)?)==/g

const transformerInlineMark = {
  name: 'neversink:inline-mark',
  preprocess(code, options) {
    const decorations = []
    let out = ''
    let last = 0
    for (const m of code.matchAll(MARK)) {
      out += code.slice(last, m.index)
      const start = out.length
      out += m[1]
      decorations.push({ start, end: out.length, properties: { class: 'code-mark' } })
      last = m.index + m[0].length
    }
    if (!decorations.length) return
    options.decorations = [...(options.decorations || []), ...decorations]
    return out + code.slice(last)
  },
}

export default defineShikiSetup(() => {
  return {
    themes: {
      dark: 'slack-dark',
      light: 'snazzy-light',
    },
    transformers: [transformerInlineMark],
  }
})
