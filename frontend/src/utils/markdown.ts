import MarkdownIt from 'markdown-it'
import katex from 'katex'
import 'katex/dist/katex.min.css'

// 配置 markdown-it（关闭 html，防止注入；关闭 breaks，避免单换行被转成 <br>）
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: false,
  breaks: false,
})

/**
 * 渲染单个 LaTeX 公式为 HTML
 */
function renderFormula(formula: string, displayMode: boolean): string {
  try {
    return katex.renderToString(formula.trim(), {
      displayMode,
      throwOnError: false,
      strict: false,
    })
  } catch {
    return `<code class="katex-error">${formula}</code>`
  }
}

/**
 * 将消息内容渲染为 HTML（支持 Markdown + LaTeX）
 *
 * 策略：
 * 1. 先手动扫描提取所有 $$...$$ 和 $...$ 公式，用唯一占位符替换（避免被 markdown-it 处理）
 * 2. 用 markdown-it 渲染 Markdown 结构
 * 3. 还原占位符为 KaTeX 渲染结果
 *
 * 占位符格式：\uFFFD数字\uFFFD（使用 Unicode 替换字符，markdown-it 不会对其做特殊处理）
 */
export function renderMessage(content: string): string {
  const DISPLAY_TOKEN = '\uFFFD\uFFFED\uFFFD'   // 块级公式标记前缀
  const INLINE_TOKEN  = '\uFFFD\uFFFEI\uFFFD'   // 行内公式标记前缀

  const displayBuf: string[] = []
  const inlineBuf:  string[] = []

  // 1. 手动扫描提取 $$...$$ 块（支持跨行，内部换行压成空格）
  let s = content
  let out = ''
  let p = 0
  while (p < s.length) {
    if (s[p] === '$' && s[p + 1] === '$') {
      const end = s.indexOf('$$', p + 2)
      if (end !== -1) {
        const inner = s.slice(p + 2, end).replace(/\n/g, ' ').trim()
        displayBuf.push(inner)
        out += `${DISPLAY_TOKEN}${displayBuf.length - 1}${DISPLAY_TOKEN}`
        p = end + 2
        continue
      }
    }
    out += s[p++]
  }
  s = out

  // 2. 正则提取 $...$ 行内公式（允许跨最多一个换行，适应多行等式）
  s = s.replace(/\$([^$]+?)\$/g, (_m, inner) => {
    inlineBuf.push(inner.replace(/\n/g, ' '))
    return `${INLINE_TOKEN}${inlineBuf.length - 1}${INLINE_TOKEN}`
  })

  // 3. markdown-it 渲染（此时文本中已无 $ 符号）
  let html = md.render(s)

  // 4. 还原块级公式
  html = html.replace(/\uFFFD\uFFFED\uFFFD(\d+)\uFFFD\uFFFED\uFFFD/g, (_m, idx) =>
    renderFormula(displayBuf[parseInt(idx)], true)
  )

  // 5. 还原行内公式
  html = html.replace(/\uFFFD\uFFFEI\uFFFD(\d+)\uFFFD\uFFFEI\uFFFD/g, (_m, idx) =>
    renderFormula(inlineBuf[parseInt(idx)], false)
  )

  return html
}

/**
 * 仅渲染 LaTeX 公式（不含 Markdown），用于题目内容、选项等纯文本场景
 */
export function renderLatexOnly(text: string): string {
  if (!text) return ''
  // 块级 $$...$$
  text = text.replace(/\$\$([\s\S]+?)\$\$/g, (_m, f) => renderFormula(f, true))
  // 行内 $...$
  text = text.replace(/\$([^\n$]+?)\$/g, (_m, f) => renderFormula(f, false))
  return text
}

/**
 * 安全渲染识别结果：逐字符扫描，公式渲染，普通文字 HTML 转义
 */
export function renderRecognizedText(content: string): string {
  if (!content) return ''
  const s = content
  let result = ''
  let i = 0
  while (i < s.length) {
    // $$...$$ 块级（跨行）
    if (s[i] === '$' && s[i + 1] === '$') {
      const end = s.indexOf('$$', i + 2)
      if (end !== -1) {
        result += renderFormula(s.slice(i + 2, end), true)
        i = end + 2
        continue
      }
    }
    // $...$ 行内（不跨行）
    if (s[i] === '$') {
      const nlPos = s.indexOf('\n', i + 1)
      const endDollar = s.indexOf('$', i + 1)
      if (endDollar !== -1 && endDollar > i + 1 && (nlPos === -1 || endDollar < nlPos)) {
        result += renderFormula(s.slice(i + 1, endDollar), false)
        i = endDollar + 1
        continue
      }
    }
    // 裸 LaTeX 命令序列
    if (s[i] === '\\' && /[a-zA-Z]/.test(s[i + 1] || '')) {
      const m = s.slice(i).match(
        /^((?:\\[a-zA-Z]+(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}|\[[^\]]*\])*\s*|[0-9+\-*/^_.,;:!?()[\]|<>=\s])*)/
      )
      if (m && m[1].length > 1 && /\\[a-zA-Z]/.test(m[1])) {
        const expr = m[1].replace(/\s+$/, '')
        if (expr) {
          result += renderFormula(expr, false)
          i += expr.length
          continue
        }
      }
    }
    // 普通字符
    const ch = s[i]
    if (ch === '\n') result += '<br>'
    else if (ch === '&') result += '&amp;'
    else if (ch === '<') result += '&lt;'
    else if (ch === '>') result += '&gt;'
    else result += ch
    i++
  }
  return result
}
