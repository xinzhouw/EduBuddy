/**
 * 移动端性能优化工具
 */

/**
 * 按需加载 ECharts（只在需要时导入）
 */
export async function loadEChartsOnDemand() {
  return import('echarts')
}

/**
 * 延迟加载模块（使用 requestIdleCallback 或 setTimeout 的降级）
 */
export function lazyLoadModule(
  callback: () => Promise<any>,
  delay: number = 2000
): Promise<void> {
  return new Promise((resolve) => {
    if ('requestIdleCallback' in window) {
      ;(window as any).requestIdleCallback(() => {
        callback().then(() => resolve())
      })
    } else {
      setTimeout(() => {
        callback().then(() => resolve())
      }, delay)
    }
  })
}

/**
 * 图片懒加载优化
 */
export function setupImageLazyLoading(): void {
  // 使用浏览器原生 loading="lazy" 属性
  // 这里可以添加降级方案
  if ('IntersectionObserver' in window) {
    const images = document.querySelectorAll('img[data-src]')
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target as HTMLImageElement
          img.src = img.getAttribute('data-src') || ''
          img.removeAttribute('data-src')
          observer.unobserve(img)
        }
      })
    })

    images.forEach((img) => imageObserver.observe(img))
  }
}

/**
 * 防止 CLS（Cumulative Layout Shift）
 * 为图片和动态内容添加 aspect-ratio
 */
export function preventCLS(): void {
  const style = document.createElement('style')
  style.innerHTML = `
    /* 防止 CLS */
    img {
      aspect-ratio: auto;
    }

    .chart-container {
      min-height: 300px;
    }

    /* 移动端优化 */
    @media (max-width: 767px) {
      body {
        -webkit-tap-highlight-color: rgba(0, 0, 0, 0.1);
      }

      input, button, select, textarea {
        font-size: 16px; /* 防止 iOS 自动缩放 */
      }
    }
  `
  document.head.appendChild(style)
}

/**
 * 优化首屏加载
 * 隐藏非关键内容，优先加载关键路径
 */
export function optimizeCriticalPath(): void {
  // 延迟加载非关键内容
  const nonCriticalElements = document.querySelectorAll('[data-lazy-load="true"]')
  nonCriticalElements.forEach((el) => {
    el.classList.add('opacity-0')
  })

  // 页面完全加载后显示
  window.addEventListener('load', () => {
    nonCriticalElements.forEach((el) => {
      el.classList.remove('opacity-0')
      el.classList.add('transition-opacity', 'duration-300')
    })
  })
}

/**
 * 针对移动网络的优化
 */
export function optimizeForMobileNetwork(): void {
  // 检测网络状态
  if ('connection' in navigator) {
    const connection = (navigator as any).connection
    const effectiveType = connection?.effectiveType

    if (effectiveType === '4g') {
      // 4G 网络：可以加载更多资源
      document.documentElement.setAttribute('data-network', '4g')
    } else if (effectiveType === '3g' || effectiveType === '2g') {
      // 3G/2G 网络：减少资源加载
      document.documentElement.setAttribute('data-network', 'slow')
      // 可以根据需要动态调整策略
    }

    // 监听网络变化
    connection?.addEventListener('change', () => {
      const newType = connection.effectiveType
      document.documentElement.setAttribute('data-network', newType)
    })
  }
}

/**
 * Web 字体优化（使用 font-display）
 */
export function optimizeWebFonts(): void {
  const style = document.createElement('style')
  style.innerHTML = `
    @font-face {
      font-display: swap; /* 使用系统字体显示，然后替换为 Web 字体 */
    }
  `
  document.head.appendChild(style)
}

/**
 * 初始化所有性能优化
 */
export function initializePerformanceOptimizations(): void {
  preventCLS()
  optimizeCriticalPath()
  optimizeForMobileNetwork()
  optimizeWebFonts()
  setupImageLazyLoading()

  // 按需加载 ECharts
  lazyLoadModule(() => loadEChartsOnDemand(), 3000)
}

/**
 * 性能监控和报告
 */
export function reportPerformanceMetrics(): void {
  if ('PerformanceObserver' in window) {
    // 监控 LCP (Largest Contentful Paint)
    const lcpObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        console.log('LCP:', entry.startTime)
      }
    })
    lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] })

    // 监控 CLS (Cumulative Layout Shift)
    const clsObserver = new PerformanceObserver((list) => {
      let cls = 0
      for (const entry of list.getEntries()) {
        if (!(entry as any).hadRecentInput) {
          cls += (entry as any).value
        }
      }
      console.log('CLS:', cls)
    })
    clsObserver.observe({ entryTypes: ['layout-shift'] })

    // 监控 FID (First Input Delay)
    const fidObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        console.log('FID:', (entry as any).processingDuration)
      }
    })
    fidObserver.observe({ entryTypes: ['first-input'] })
  }
}
