/* ./setup/transformers.ts */
// Subtext: a line starting with `-# ` renders as <small>...</small> (fine print,
// source lines, side notes). Same syntax Discord uses. Lines inside fenced code
// blocks are left alone. Styled by `.slidev-layout small` in styles/base.css.
function subtext(ctx) {
  const src = ctx.s.original
  let inFence = false
  let pos = 0
  for (const line of src.split('\n')) {
    if (/^\s*(```|~~~)/.test(line)) {
      inFence = !inFence
    } else if (!inFence) {
      const m = line.match(/^-# (.*)$/)
      if (m) ctx.s.overwrite(pos, pos + line.length, `<small>${m[1]}</small>`)
    }
    pos += line.length + 1
  }
}

export default () => ({ pre: [subtext] })
