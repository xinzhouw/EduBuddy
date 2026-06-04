/**
 * 动态学科示意图水合（hydration）
 *
 * renderMessage() 会把 ```funcplot``` / ```smiles``` 代码块渲染成带 data-* 的占位 <div>，
 * 本模块在组件用 v-html 把 HTML 插入 DOM 之后，扫描这些占位元素并用专业库异步绘制：
 *   - funcplot → ECharts 数学函数图像（坐标轴、网格、曲线）
 *   - smiles   → smiles-drawer 化学分子结构式
 *
 * 用法（在 Vue 组件中）：
 *   import { hydrateDynamicFigures } from '@/utils/dynamicFigures'
 *   // v-html 内容更新后（nextTick 内）：
 *   hydrateDynamicFigures(containerEl)
 */
import * as echarts from 'echarts'
import SmilesDrawer from 'smiles-drawer'

// 已水合过的元素打标记，避免重复绘制
const HYDRATED = 'data-hydrated'

/**
 * 安全地把数学表达式编译成 (x) => number 的函数。
 * 只允许数字、运算符、括号、x 变量以及一组白名单 Math 函数，杜绝任意代码执行。
 */
function compileMathFn(expr: string): ((x: number) => number) | null {
  // 允许的标识符（会被映射到 Math.*）
  const allowed = [
    'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2', 'sinh', 'cosh', 'tanh',
    'exp', 'log', 'log2', 'log10', 'sqrt', 'cbrt', 'abs', 'pow', 'min', 'max',
    'floor', 'ceil', 'round', 'sign', 'PI', 'E',
  ]
  let e = expr.trim()
  // 常见写法转换：^ → **，ln → log，π → PI
  e = e.replace(/\bln\b/g, 'log').replace(/π/g, 'PI').replace(/\^/g, '**')
  // 校验：仅允许白名单字符与标识符
  const stripped = e.replace(/[0-9.+\-*/%() ,]/g, ' ')
  const idents = stripped.match(/[A-Za-z_][A-Za-z0-9_]*/g) || []
  for (const id of idents) {
    if (id !== 'x' && !allowed.includes(id)) return null
  }
  // 把白名单函数/常量映射到 Math.*
  let body = e
  for (const name of allowed) {
    body = body.replace(new RegExp(`\\b${name}\\b`, 'g'), `M.${name}`)
  }
  try {
    // eslint-disable-next-line no-new-func
    const fn = new Function('x', 'M', `"use strict"; return (${body});`) as (
      x: number,
      M: Math,
    ) => number
    // 试算一次，确保可用
    const test = fn(1, Math)
    if (typeof test !== 'number') return null
    return (x: number) => fn(x, Math)
  } catch {
    return null
  }
}

interface FuncPlotSpec {
  // 单函数
  fn?: string
  label?: string
  // 多函数
  fns?: Array<{ fn: string; label?: string }>
  xMin?: number
  xMax?: number
  yMin?: number
  yMax?: number
  title?: string
  samples?: number
}

const LINE_COLORS = ['#2563eb', '#dc2626', '#16a34a', '#d97706', '#7c3aed', '#0891b2']

/** 渲染单个函数图占位元素 */
function renderFuncPlot(el: HTMLElement, rawSpec: string) {
  let spec: FuncPlotSpec
  try {
    // 兼容两种写法：JSON 对象，或单行直接写表达式（如 "y = x^2"）
    const trimmed = rawSpec.trim()
    if (trimmed.startsWith('{')) {
      spec = JSON.parse(trimmed)
    } else {
      spec = { fn: trimmed.replace(/^y\s*=\s*/i, '') }
    }
  } catch {
    el.textContent = '⚠️ 函数图配置解析失败'
    return
  }

  const xMin = typeof spec.xMin === 'number' ? spec.xMin : -10
  const xMax = typeof spec.xMax === 'number' ? spec.xMax : 10
  const samples = Math.min(Math.max(spec.samples || 240, 60), 1000)

  const series: any[] = []
  const defs = spec.fns && spec.fns.length ? spec.fns : spec.fn ? [{ fn: spec.fn, label: spec.label }] : []
  if (!defs.length) {
    el.textContent = '⚠️ 未提供函数表达式'
    return
  }

  defs.forEach((d, i) => {
    const f = compileMathFn(d.fn)
    if (!f) return
    const data: Array<[number, number]> = []
    const step = (xMax - xMin) / samples
    for (let k = 0; k <= samples; k++) {
      const x = xMin + step * k
      const y = f(x)
      if (typeof y === 'number' && isFinite(y)) data.push([x, y])
      else data.push([x, NaN])
    }
    series.push({
      name: d.label || `y${i + 1}`,
      type: 'line',
      showSymbol: false,
      smooth: true,
      data,
      lineStyle: { width: 2, color: LINE_COLORS[i % LINE_COLORS.length] },
      itemStyle: { color: LINE_COLORS[i % LINE_COLORS.length] },
    })
  })

  if (!series.length) {
    el.textContent = '⚠️ 函数表达式不合法（仅支持基础数学函数）'
    return
  }

  // 准备绘图容器
  el.textContent = ''
  el.style.width = '100%'
  el.style.maxWidth = '460px'
  el.style.height = '300px'
  el.style.margin = '0.6rem auto'

  const chart = echarts.init(el)
  chart.setOption({
    title: spec.title ? { text: spec.title, left: 'center', textStyle: { fontSize: 14, fontWeight: 'normal' } } : undefined,
    grid: { left: 44, right: 18, top: spec.title ? 38 : 18, bottom: 32 },
    tooltip: { trigger: 'axis' },
    legend: defs.length > 1 ? { top: spec.title ? 22 : 4, type: 'scroll' } : undefined,
    xAxis: {
      type: 'value',
      name: 'x',
      min: xMin,
      max: xMax,
      axisLine: { onZero: true, lineStyle: { color: '#555' } },
      splitLine: { lineStyle: { color: '#eee' } },
    },
    yAxis: {
      type: 'value',
      name: 'y',
      min: typeof spec.yMin === 'number' ? spec.yMin : undefined,
      max: typeof spec.yMax === 'number' ? spec.yMax : undefined,
      axisLine: { show: true, onZero: true, lineStyle: { color: '#555' } },
      splitLine: { lineStyle: { color: '#eee' } },
    },
    series,
  })
}

// smiles-drawer 实例（SVG 输出）复用
let _smilesDrawer: any = null
function getSmilesDrawer() {
  if (!_smilesDrawer) {
    _smilesDrawer = new SmilesDrawer.SvgDrawer({ width: 280, height: 220 })
  }
  return _smilesDrawer
}

/** 渲染单个分子结构式占位元素 */
function renderSmiles(el: HTMLElement, smiles: string) {
  const code = smiles.trim()
  if (!code) {
    el.textContent = '⚠️ 未提供 SMILES'
    return
  }
  // 准备一个 svg 容器
  el.textContent = ''
  el.style.maxWidth = '300px'
  el.style.margin = '0.6rem auto'
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  svg.setAttribute('width', '280')
  svg.setAttribute('height', '220')
  const svgId = `smiles-${Math.random().toString(36).slice(2)}`
  svg.id = svgId
  el.appendChild(svg)

  try {
    SmilesDrawer.parse(
      code,
      (tree: any) => {
        try {
          getSmilesDrawer().draw(tree, svgId, 'light', false)
        } catch {
          el.textContent = '⚠️ 分子结构绘制失败'
        }
      },
      () => {
        el.textContent = `⚠️ 无法解析 SMILES：${code}`
      },
    )
  } catch {
    el.textContent = '⚠️ 分子结构绘制失败'
  }
}

/**
 * 扫描容器内所有动态图占位元素并完成绘制。
 * 应在 v-html 内容渲染到 DOM 之后（nextTick）调用。
 */
export function hydrateDynamicFigures(root: HTMLElement | null | undefined) {
  if (!root) return
  const nodes = root.querySelectorAll<HTMLElement>('.dyn-figure[data-spec]')
  nodes.forEach((el) => {
    if (el.getAttribute(HYDRATED) === '1') return
    const type = el.getAttribute('data-type')
    const spec = decodeURIComponent(el.getAttribute('data-spec') || '')
    el.setAttribute(HYDRATED, '1')
    if (type === 'funcplot') renderFuncPlot(el, spec)
    else if (type === 'smiles') renderSmiles(el, spec)
  })
}
