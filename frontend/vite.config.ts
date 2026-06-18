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
    rollupOptions: {
      output: {
        // 代码分割：改用 Rolldown 支持的函数形式
        manualChunks(id) {
          // 检查是否来自 node_modules
          if (id.includes('node_modules')) {
            // 将 ECharts 单独打包成一个 chunk
            if (id.includes('echarts')) {
              return 'echarts';
            }
            // 将 Vue + Element Plus 打包成 vue-vendor chunk
            if (id.includes('vue') || id.includes('element-plus')) {
              return 'vue-vendor';
            }
          }
        },
      },
    },
    // 使用性能极高的 oxc 压缩混淆器，不需要在外部独立安装
    minify: 'oxc',
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
