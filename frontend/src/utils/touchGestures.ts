/**
 * 移动端触摸手势工具
 */

interface TouchPoint {
  x: number
  y: number
  time: number
}

export interface GestureOptions {
  minDistance?: number      // 最小滑动距离（px）
  maxDuration?: number      // 最大滑动时间（ms）
  minSwipeDistance?: number // 最小滑动距离用于判断为有效手势
}

const defaultOptions: GestureOptions = {
  minDistance: 10,
  maxDuration: 1000,
  minSwipeDistance: 50,
}

/**
 * 长按手势处理
 */
export function setupLongPressGesture(
  element: HTMLElement,
  callback: () => void,
  duration: number = 500
): () => void {
  let timeout: number | null = null
  let startX = 0
  let startY = 0

  const handleTouchStart = (e: TouchEvent) => {
    startX = e.touches[0].clientX
    startY = e.touches[0].clientY

    timeout = window.setTimeout(() => {
      callback()
    }, duration)
  }

  const handleTouchEnd = () => {
    if (timeout) clearTimeout(timeout)
  }

  const handleTouchMove = (e: TouchEvent) => {
    const moveX = Math.abs(e.touches[0].clientX - startX)
    const moveY = Math.abs(e.touches[0].clientY - startY)

    // 如果移动距离超过 10px，取消长按
    if (moveX > 10 || moveY > 10) {
      if (timeout) clearTimeout(timeout)
    }
  }

  element.addEventListener('touchstart', handleTouchStart)
  element.addEventListener('touchend', handleTouchEnd)
  element.addEventListener('touchmove', handleTouchMove)

  // 返回清理函数
  return () => {
    element.removeEventListener('touchstart', handleTouchStart)
    element.removeEventListener('touchend', handleTouchEnd)
    element.removeEventListener('touchmove', handleTouchMove)
    if (timeout) clearTimeout(timeout)
  }
}

/**
 * 侧滑返回手势
 */
export function setupSwipeBackGesture(
  onSwipeBack: () => void,
  options: GestureOptions = {}
): () => void {
  const opt = { ...defaultOptions, ...options }
  let startPoint: TouchPoint | null = null

  const handleTouchStart = (e: TouchEvent) => {
    // 只在屏幕左侧 50px 内开始检测
    if (e.touches[0].clientX > 50) return

    startPoint = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
      time: Date.now(),
    }
  }

  const handleTouchEnd = (e: TouchEvent) => {
    if (!startPoint) return

    const endX = e.changedTouches[0].clientX
    const endY = e.changedTouches[0].clientY
    const duration = Date.now() - startPoint.time

    const distanceX = endX - startPoint.x
    const distanceY = Math.abs(endY - startPoint.y)

    // 检查是否为有效的右滑手势
    if (
      duration < opt.maxDuration! &&
      distanceX > opt.minSwipeDistance! &&
      distanceY < 50
    ) {
      onSwipeBack()
    }

    startPoint = null
  }

  document.addEventListener('touchstart', handleTouchStart, { passive: true })
  document.addEventListener('touchend', handleTouchEnd, { passive: true })

  // 返回清理函数
  return () => {
    document.removeEventListener('touchstart', handleTouchStart)
    document.removeEventListener('touchend', handleTouchEnd)
  }
}

/**
 * 通用滑动手势检测
 */
export function setupSwipeGesture(
  element: HTMLElement,
  callbacks: {
    onSwipeLeft?: () => void
    onSwipeRight?: () => void
    onSwipeUp?: () => void
    onSwipeDown?: () => void
  },
  options: GestureOptions = {}
): () => void {
  const opt = { ...defaultOptions, ...options }
  let startPoint: TouchPoint | null = null

  const handleTouchStart = (e: TouchEvent) => {
    startPoint = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
      time: Date.now(),
    }
  }

  const handleTouchEnd = (e: TouchEvent) => {
    if (!startPoint) return

    const endX = e.changedTouches[0].clientX
    const endY = e.changedTouches[0].clientY
    const duration = Date.now() - startPoint.time

    const distanceX = endX - startPoint.x
    const distanceY = endY - startPoint.y

    // 只在时间和距离都符合条件时触发回调
    if (duration > opt.maxDuration! || Math.abs(distanceX) + Math.abs(distanceY) < opt.minDistance!) {
      startPoint = null
      return
    }

    // 判断滑动方向
    if (Math.abs(distanceX) > Math.abs(distanceY)) {
      // 水平滑动
      if (distanceX > opt.minSwipeDistance!) {
        callbacks.onSwipeRight?.()
      } else if (distanceX < -opt.minSwipeDistance!) {
        callbacks.onSwipeLeft?.()
      }
    } else {
      // 竖直滑动
      if (distanceY > opt.minSwipeDistance!) {
        callbacks.onSwipeDown?.()
      } else if (distanceY < -opt.minSwipeDistance!) {
        callbacks.onSwipeUp?.()
      }
    }

    startPoint = null
  }

  element.addEventListener('touchstart', handleTouchStart, { passive: true })
  element.addEventListener('touchend', handleTouchEnd, { passive: true })

  // 返回清理函数
  return () => {
    element.removeEventListener('touchstart', handleTouchStart)
    element.removeEventListener('touchend', handleTouchEnd)
  }
}

/**
 * 为元素添加复制文本的长按菜单（iOS 长按）
 */
export function setupLongPressCopyGesture(element: HTMLElement): () => void {
  return setupLongPressGesture(element, () => {
    const text = element.textContent || ''
    if (text) {
      // 复制到剪贴板
      navigator.clipboard
        .writeText(text)
        .then(() => {
          // 显示短暂提示
          const toast = document.createElement('div')
          toast.textContent = '已复制'
          toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
            z-index: 9999;
          `
          document.body.appendChild(toast)
          setTimeout(() => toast.remove(), 1500)
        })
        .catch(() => {
          // 降级方案：使用 execCommand
          const textArea = document.createElement('textarea')
          textArea.value = text
          textArea.style.position = 'fixed'
          textArea.style.opacity = '0'
          document.body.appendChild(textArea)
          textArea.select()
          try {
            document.execCommand('copy')
          } catch (err) {
            console.error('复制失败:', err)
          }
          document.body.removeChild(textArea)
        })
    }
  })
}

/**
 * 初始化所有触摸手势
 */
export function initializeTouchGestures(): () => void {
  const cleanups: Array<() => void> = []

  // 为消息内容添加长按复制功能
  const messages = document.querySelectorAll('.markdown-body, .ai-message-content, .user-message-content')
  messages.forEach((msg) => {
    const cleanup = setupLongPressCopyGesture(msg as HTMLElement)
    cleanups.push(cleanup)
  })

  // 为路由返回添加侧滑支持
  const cleanup = setupSwipeBackGesture(() => {
    window.history.back()
  })
  cleanups.push(cleanup)

  // 返回清理所有手势的函数
  return () => {
    cleanups.forEach((c) => c())
  }
}
