/**
 * 移动端表单交互优化工具
 */

/**
 * 检查是否为移动设备
 */
export function isMobileDevice(): boolean {
  return window.innerWidth < 768
}

/**
 * 监听表单输入框聚焦时的键盘弹出
 * 确保输入框在键盘上方
 */
export function setupFormInputFocus(element: HTMLElement): void {
  if (!element) return

  const inputs = element.querySelectorAll('input, textarea, select')
  inputs.forEach((input) => {
    input.addEventListener('focus', () => {
      if (!isMobileDevice()) return

      // 延迟滚动，等待键盘完全弹出
      setTimeout(() => {
        input.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }, 300)
    })
  })
}

/**
 * 优化下拉菜单在移动端的显示
 * 增大点击区域和选项高度
 */
export function enhanceMobileSelectOptions(): void {
  if (!isMobileDevice()) return

  // 添加全局样式以增大选项尺寸
  const style = document.createElement('style')
  style.innerHTML = `
    /* 移动端下拉菜单优化 */
    @media (max-width: 767px) {
      .el-select-dropdown__item {
        padding: 12px 16px;
        height: auto;
        min-height: 44px;
        display: flex;
        align-items: center;
      }

      .el-popper {
        max-height: 70vh !important;
      }

      .el-picker-panel {
        width: 100% !important;
        max-width: calc(100vw - 16px);
        left: 8px !important;
      }
    }
  `
  document.head.appendChild(style)
}

/**
 * 禁用 iOS 中的自动缩放和默认行为
 */
export function disableIOSDefaultBehaviors(): void {
  // 禁止双击缩放
  let lastTouchEnd = 0
  document.addEventListener(
    'touchend',
    (event) => {
      const now = Date.now()
      if (now - lastTouchEnd <= 300) {
        event.preventDefault()
      }
      lastTouchEnd = now
    },
    false
  )

  // 禁用长按弹出菜单（保留复制功能）
  document.addEventListener(
    'contextmenu',
    (e) => {
      // 只在非文本输入框时禁用
      const target = e.target as HTMLElement
      if (!['input', 'textarea'].includes(target.tagName?.toLowerCase() || '')) {
        // e.preventDefault() // 保留注释，允许默认长按菜单
      }
    },
    false
  )
}

/**
 * 设置表单在移动端的高度，防止键盘遮挡
 */
export function setupFormHeightAdjustment(formSelector: string): void {
  if (!isMobileDevice()) return

  const form = document.querySelector(formSelector) as HTMLElement
  if (!form) return

  const adjustHeight = () => {
    const visualViewport = (window as any).visualViewport
    if (!visualViewport) return

    const keyboardHeight = window.innerHeight - visualViewport.height
    if (keyboardHeight > 100) {
      // 键盘显示
      form.style.maxHeight = `${visualViewport.height - 60}px`
      form.style.overflow = 'auto'
    } else {
      // 键盘隐藏
      form.style.maxHeight = ''
      form.style.overflow = ''
    }
  }

  ;(window as any).visualViewport?.addEventListener('resize', adjustHeight)
}

/**
 * 为移动端表单按钮添加正确的尺寸
 */
export function optimizeFormButtons(containerSelector: string): void {
  if (!isMobileDevice()) return

  const container = document.querySelector(containerSelector)
  if (!container) return

  const buttons = container.querySelectorAll('button, .el-button')
  buttons.forEach((btn) => {
    // 确保按钮最小高度 44px
    const style = window.getComputedStyle(btn)
    const height = parseInt(style.height)
    if (height < 44) {
      ;(btn as HTMLElement).style.minHeight = '44px'
      ;(btn as HTMLElement).style.padding = '10px 16px'
    }
  })
}

/**
 * 初始化所有移动端表单优化
 */
export function initializeMobileFormOptimizations(formSelector?: string): void {
  if (!isMobileDevice()) return

  enhanceMobileSelectOptions()
  disableIOSDefaultBehaviors()

  if (formSelector) {
    setupFormHeightAdjustment(formSelector)
    optimizeFormButtons(formSelector)

    // 等待 DOM 完全加载后执行
    setTimeout(() => {
      setupFormInputFocus(document.querySelector(formSelector) as HTMLElement)
    }, 100)
  }
}
