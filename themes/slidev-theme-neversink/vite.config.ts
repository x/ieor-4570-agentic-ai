import { defineConfig } from 'vite'
//import MarkdownItMagicLink from 'markdown-it-magic-link'
import { sub } from '@mdit/plugin-sub'
import Mark from 'markdown-it-mark'
import pkg from './package.json' with { type: 'json' }
const { version } = pkg

console.log(`Loading Neversink ${version} theme vite.config.ts...`)
export default defineConfig({
  slidev: {
    markdown: {
      markdownItSetup(md) {
        md.use(sub)
        md.use(Mark)

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
