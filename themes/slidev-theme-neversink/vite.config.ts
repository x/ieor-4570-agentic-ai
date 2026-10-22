import { defineConfig } from 'vite'
//import MarkdownItMagicLink from 'markdown-it-magic-link'
import { dl } from '@mdit/plugin-dl'
import { sub } from '@mdit/plugin-sub'
import Mark from 'markdown-it-mark'
import pkg from './package.json' with { type: 'json' }
const { version } = pkg

console.log(`Loading Neversink ${version} theme vite.config.ts...`)
export default defineConfig({
  slidev: {
    markdown: {
      // Slidev 52 calls `markdownSetup`.
      markdownSetup(md) {
        md.use(sub) // H~2~O
        md.use(Mark) // ==highlight==
        // Definition lists (`Term` then `: definition`). Styled in styles/definitions.css.
        md.use(dl)
      },
      // ponytail: Slidev 52 ignores `markdownItSetup`, so the marker-aware list classes
      // below are off. Moving them into `markdownSetup` turns every `-` list in every deck
      // tight (styles/lists.css); check deck layouts before doing that.
      markdownItSetup(md) {
        // Marker-aware lists: `*` bullets get .ul-loose, `-` bullets get
        // .ul-tight. Styled in styles/lists.css.
        const render = md.renderer.renderToken.bind(md.renderer)
        md.renderer.rules.bullet_list_open = (tokens, idx, options, _env, self) => {
          tokens[idx].attrJoin('class', tokens[idx].markup === '*' ? 'ul-loose' : 'ul-tight')
          return render(tokens, idx, options)
        }
      },
    },
  },
})
