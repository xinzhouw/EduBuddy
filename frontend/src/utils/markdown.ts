import MarkdownIt from 'markdown-it'
import katex from 'katex'
import 'katex/dist/katex.min.css'
// mhchem：为 KaTeX 增加化学方程式支持，使 \ce{...}、\pu{...} 可被渲染
import 'katex/dist/contrib/mhchem.mjs'


// 配置 markdown-it（关闭 html，防止注入；关闭 breaks，避免单换行被转成 <br>）
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: false,
  breaks: false,
})

/**
 * 清洗 AI 生成的 LaTeX 公式，去除常见畸形：
 * 1. 末尾孤立反斜杠（LaTeX 换行符 \\ 被截断）
 * 2. 夹在空白间的孤立 \（如 `{2} \ $$` 中的 `\`）
 * 3. 公式内残留的 $ 符号（AI 用多余 $/$$ 拦腰截断公式）
 * 4. 不平衡的多余右花括号
 */
function cleanFormula(formula: string): string {
  let f = formula
  // 去除末尾孤立反斜杠（一个或多个 \，后面只有空白）
  f = f.replace(/\\+\s*$/, '')
  // 去除夹在空白之间的孤立单反斜杠（非命令，如 `{2} \ `）
  f = f.replace(/(?<!\S)\\\s*(?=\s|$)/g, '')
  // 公式内残留 $ → LaTeX 中等间隔 \;
  f = f.replace(/\$/g, '\\;')
  // 平衡花括号：删除多余的右花括号
  let depth = 0
  let result = ''
  for (const ch of f) {
    if (ch === '{') { depth++; result += ch }
    else if (ch === '}') {
      if (depth > 0) { depth--; result += ch }
      // else: 多余的 }，丢弃
    } else {
      result += ch
    }
  }
  return result.trim()
}

/**
 * 渲染单个 LaTeX 公式为 HTML
 */
function renderFormula(formula: string, displayMode: boolean): string {
  const cleaned = cleanFormula(formula)
  try {
    return katex.renderToString(cleaned, {
      displayMode,
      throwOnError: false,
      strict: false,
    })
  } catch {
    return `<code class="katex-error">${cleaned}</code>`
  }
}

/**
 * 安全清洗 AI 生成的 SVG 代码：
 * - 移除 <script>、外部引用（<image>/<foreignObject>）、事件处理属性（on*）、javascript: 链接
 * - 仅保留矢量几何绘图所需的基础元素，避免 XSS 风险
 * 用于把 AI 生成的几何图（SVG 代码块）渲染成清晰的矢量图。
 */
function sanitizeSvg(svg: string): string {
  let s = svg
  // 去除注释、DOCTYPE、xml 声明
  s = s.replace(/<!--[\s\S]*?-->/g, '')
  s = s.replace(/<\?[\s\S]*?\?>/g, '')
  s = s.replace(/<!DOCTYPE[^>]*>/gi, '')
  // 移除危险元素（含内容）
  s = s.replace(/<script[\s\S]*?<\/script>/gi, '')
  s = s.replace(/<foreignObject[\s\S]*?<\/foreignObject>/gi, '')
  s = s.replace(/<(image|use|iframe|object|embed|a)\b[\s\S]*?(\/>|<\/\1>)/gi, '')
  // 移除事件处理属性 on*="..."
  s = s.replace(/\son\w+\s*=\s*"[^"]*"/gi, '')
  s = s.replace(/\son\w+\s*=\s*'[^']*'/gi, '')
  // 移除 javascript: 协议
  s = s.replace(/javascript:/gi, '')
  return s.trim()
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
  const SVG_TOKEN     = '\uFFFD\uFFFES\uFFFD'   // SVG 几何图标记前缀
  const FIG_TOKEN     = '\uFFFD\uFFFEF\uFFFD'   // 动态图（函数图/分子式）标记前缀

  const displayBuf: string[] = []
  const inlineBuf:  string[] = []
  const svgBuf:     string[] = []
  // 动态图占位 HTML（函数图 funcplot、分子结构 smiles），由 hydrateDynamicFigures 异步渲染
  const figBuf:     string[] = []

  let s = content

  // -1. 提取专业学科图代码块（在 SVG/公式之前处理）：
  //     ```funcplot ...```  → 数学函数图像（ECharts 异步渲染）
  //     ```smiles ...```     → 化学分子结构式（smiles-drawer 异步渲染）
  //     这里仅生成带 data-* 的占位 div，真正绘制在组件挂载后调用 hydrateDynamicFigures()。
  s = s.replace(/```\s*funcplot\s*\n?([\s\S]*?)```/gi, (_m, code: string) => {
    const payload = encodeURIComponent(code.trim())
    figBuf.push(
      `<div class="dyn-figure func-plot" data-type="funcplot" data-spec="${payload}">📈 正在绘制函数图…</div>`
    )
    return `\n\n${FIG_TOKEN}${figBuf.length - 1}${FIG_TOKEN}\n\n`
  })
  s = s.replace(/```\s*smiles\s*\n?([\s\S]*?)```/gi, (_m, code: string) => {
    const payload = encodeURIComponent(code.trim())
    figBuf.push(
      `<div class="dyn-figure smiles-figure" data-type="smiles" data-spec="${payload}">⚛️ 正在绘制分子结构…</div>`
    )
    return `\n\n${FIG_TOKEN}${figBuf.length - 1}${FIG_TOKEN}\n\n`
  })


  // 0b. 预处理：若存在未闭合的 ```svg 代码块（流式截断或 AI 漏写结尾 ```），
  //     补上缺失的 ``` 结尾，确保后续步骤 0 的正则可以正常匹配。
  //     注意：不扫描裸 <svg，因为 AI 描述文字中也可能出现 "<svg" 字样。
  {
    const openFence = s.search(/```\s*svg\b/i)
    if (openFence !== -1) {
      const afterFenceLine = s.indexOf('\n', openFence)
      const closeFence = s.indexOf('\n```', afterFenceLine !== -1 ? afterFenceLine : openFence + 6)
      if (closeFence === -1) {
        // 未闭合：补全结尾 ``` 使步骤 0 可以正常提取 SVG
        s = s + '\n```'
      }
    }
  }

  // 0. 提取 SVG 几何图：支持 ```svg ... ``` 代码块，以及裸 <svg>...</svg>
  //    用占位符替换，避免被 markdown-it 转义成代码文本或被公式逻辑破坏。
  s = s.replace(/```\s*svg\s*\n?([\s\S]*?)```/gi, (_m, code) => {
    svgBuf.push(sanitizeSvg(code))
    return `\n\n${SVG_TOKEN}${svgBuf.length - 1}${SVG_TOKEN}\n\n`
  })
  s = s.replace(/<svg[\s\S]*?<\/svg>/gi, (m) => {
    svgBuf.push(sanitizeSvg(m))
    return `\n\n${SVG_TOKEN}${svgBuf.length - 1}${SVG_TOKEN}\n\n`
  })

  // 0a. 兜底：个别情况下 AI 仍会用 ASCII 字符（+ - | / \ 等）在普通代码块里"画图"，
  //     这种字符画又粗糙又难看。检测此类代码块并替换为提示，避免暴露给用户。
  s = s.replace(/```[^\n]*\n([\s\S]*?)```/g, (whole, body: string) => {
    const lines = body.split('\n').filter((l) => l.trim().length > 0)
    if (lines.length < 3) return whole
    // 统计"制图字符"占比：+ - | / \ _ 以及空格
    const drawingChars = (body.match(/[+\-|/\\_]/g) || []).length
    const total = body.replace(/\s/g, '').length || 1
    const ratio = drawingChars / total
    // 多行、且制图字符占比高 → 判定为 ASCII 字符画
    if (ratio > 0.35) {
      return '\n\n*（此处为示意图，已省略粗略的字符草图）*\n\n'
    }
    return whole
  })


  // 1. 手动扫描提取 $$...$$ 块（支持跨行，内部换行压成空格）
  //    修复：使用"向后查找所有候选闭合 $$"并验证内容合理性，
  //    避免 AI 在公式行末误插 $$ 导致后续所有公式配对错位。
  let out = ''
  let p = 0

  // 判断一段文本是否"看起来像合法的公式内容"而非被错误截取的正文段落
  function isLikelyFormula(inner: string): boolean {
    // 超过 400 字符，极可能是错误配对（正常公式很少超过这个长度）
    if (inner.length > 400) return false
    // 包含 Markdown 块级结构特征，说明截到了正文
    if (/\n#{1,6}\s/.test(inner)) return false
    if (/\n---/.test(inner)) return false
    if (/\n\*\*/.test(inner)) return false
    // 包含超过 3 个换行，极可能是段落文字
    if ((inner.match(/\n/g) || []).length > 3) return false
    return true
  }

  while (p < s.length) {
    if (s[p] === '$' && s[p + 1] === '$') {
      // 向后逐个寻找候选闭合 $$，取第一个"内容合理"的
      let searchFrom = p + 2
      let matched = false
      while (searchFrom < s.length) {
        const end = s.indexOf('$$', searchFrom)
        if (end === -1) break
        const inner = s.slice(p + 2, end).replace(/\n/g, ' ').trim()
        if (isLikelyFormula(inner)) {
          displayBuf.push(inner)
          out += `${DISPLAY_TOKEN}${displayBuf.length - 1}${DISPLAY_TOKEN}`
          p = end + 2
          matched = true
          break
        }
        // 当前候选不合理，跳过这个 $$ 继续往后找
        searchFrom = end + 2
      }
      if (matched) continue
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

  // 6. 还原 SVG 几何图（包裹在居中容器中，类似教科书插图）
  html = html.replace(/\uFFFD\uFFFES\uFFFD(\d+)\uFFFD\uFFFES\uFFFD/g, (_m, idx) =>
    `<div class="svg-figure">${svgBuf[parseInt(idx)] || ''}</div>`
  )

  // 7. 还原动态图占位（函数图 / 分子结构），真正绘制由 hydrateDynamicFigures 完成
  html = html.replace(/\uFFFD\uFFFEF\uFFFD(\d+)\uFFFD\uFFFEF\uFFFD/g, (_m, idx) =>
    figBuf[parseInt(idx)] || ''
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
