import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // 告知 Vue 编译器 math-field 是自定义元素（Web Component），不作为 Vue 组件处理
          isCustomElement: (tag: string) => tag === 'math-field',
        },
      },
    }),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    // 移动端性能优化配置
    cssMinify: true,
    reportCompressedSize: false, // 减少构建输出
    sourcemap: false, // 生产环境不生成 sourcemap
    rollupOptions: {
      output: {
        // 代码分割：改用 Rolldown 支持的函数形式
        manualChunks(id) {
          // 检查是否来自 node_modules
          if (id.includes('node_modules')) {
            // 将 ECharts 单独打包成一个 chunk（移动端可能不需要立即加载）
            if (id.includes('echarts')) {
              return 'echarts';
            }
            // 将 Vue + Element Plus 打包成 vue-vendor chunk
            if (id.includes('vue') || id.includes('element-plus')) {
              return 'vue-vendor';
            }
            // 将 markdown 相关库分离
            if (id.includes('markdown') || id.includes('katex')) {
              return 'markdown';
            }
          }
        },
      },
    },
    // 使用性能极高的 oxc 压缩混淆器，不需要在外部独立安装
    minify: 'oxc',
    // 性能优化：提高分块大小阈值
    chunkSizeWarningLimit: 600,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
