// smiles-drawer 没有官方类型声明，这里提供最小可用声明，避免 TS 报错。
declare module 'smiles-drawer' {
  // 解析 SMILES 字符串；成功回调返回解析树，失败回调返回错误
  export function parse(
    smiles: string,
    successCallback: (tree: unknown) => void,
    errorCallback?: (err: unknown) => void,
  ): void

  // Canvas 绘制器
  export class Drawer {
    constructor(options?: Record<string, unknown>)
    draw(tree: unknown, target: string | HTMLElement, theme?: string, infoOnly?: boolean): void
  }

  // SVG 绘制器
  export class SvgDrawer {
    constructor(options?: Record<string, unknown>)
    draw(tree: unknown, target: string | HTMLElement, theme?: string, infoOnly?: boolean): void
  }

  const _default: {
    parse: typeof parse
    Drawer: typeof Drawer
    SvgDrawer: typeof SvgDrawer
  }
  export default _default
}
