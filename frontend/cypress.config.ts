import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    // 前端开发服务器地址（vite dev server 默认端口 5173）
    baseUrl: 'http://localhost:5173',

    // E2E 测试文件目录
    specPattern: 'tests/e2e/**/*.cy.{ts,js}',

    // 支持文件（可按需创建 tests/e2e/support/e2e.ts）
    supportFile: false,

    // 视口尺寸（桌面端）
    viewportWidth: 1280,
    viewportHeight: 800,

    // 默认超时（毫秒）
    defaultCommandTimeout: 8000,

    // 视频录制（CI 中建议关闭以加快速度）
    video: false,
  },
})
