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
        // 代码分割：将第三方库与业务代码分离，加快初始加载速度
        manualChunks: {
          // 将 ECharts 单独打包成一个 chunk
          echarts: ['echarts'],
          // 将 Vue + Element Plus 打包成 vendor chunk
          'vue-vendor': ['vue', 'element-plus'],
        },
      },
    },
    // 文件过小时不分割代码
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // 生产环境移除 console 日志
      },
    },
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
