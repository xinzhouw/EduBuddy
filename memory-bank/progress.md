# EduBuddy 项目进展

## 当前状态
**项目阶段**：V1.0 初期开发阶段  
**最后更新**：2026-05-28

---

## 已完成的工作

### 项目基础架构 ✅
- [x] 项目整体文档撰写完成（PRD、架构设计、数据库设计、API设计、UI设计）
- [x] 前后端项目脚手架搭建完成
- [x] Docker Compose 部署配置完成
- [x] FastAPI 后端应用入口（main.py）完成，所有路由已注册
- [x] 数据库配置（database.py）完成
- [x] 环境变量配置（config.py）完成
- [x] JWT 认证依赖注入（dependencies.py）完成
- [x] SQLAlchemy ORM 模型文件已创建（user/note/quiz/document/study_plan/wrong_item）
- [x] Pydantic Schema 文件已创建（auth/note/quiz/document/plan/wrong_item）
- [x] 所有后端路由文件已创建（auth/ai/notes/quiz/wrong_book/plan/documents/stats）
- [x] 所有后端服务文件已创建（ai_service/document_service/review_service/stats_service）
- [x] Vue 3 前端项目搭建完成，所有依赖包已配置
- [x] 前端路由配置完成（含路由守卫）
- [x] 前端 Pinia auth store 已创建
- [x] 所有前端 API 封装文件已创建（auth/ai/notes/quiz/wrongBook/plan/docs）
- [x] 前端所有页面视图组件已创建（占位/骨架）
- [x] 布局组件已创建（AppSidebar.vue + AppHeader.vue）

---

## 待完成的工作

### 后端实现
- [ ] 验证各路由接口的具体业务逻辑是否完整实现
- [ ] Alembic 数据库迁移初始化（`alembic init alembic`）
- [ ] 验证 ORM 模型是否与数据库设计文档完全对应（quiz、flashcard 等表）
- [ ] AI 服务（ai_service.py）的具体实现验证
- [ ] 文档解析服务（document_service.py）的完整实现
- [ ] 间隔复习服务（review_service.py）的完整实现
- [ ] 学习统计服务（stats_service.py）的完整实现
- [ ] 单元测试编写

### 前端实现
- [ ] 各页面视图的 UI 和交互逻辑完整实现
  - [ ] DashboardView.vue（首页/仪表板）
  - [ ] AIChatView.vue（AI 问答，含 SSE 流式输出）
  - [ ] NotesListView.vue + NoteEditView.vue（笔记管理）
  - [ ] QuizSetupView.vue + QuizSessionView.vue（练习题）
  - [ ] WrongBookView.vue + WrongDetailView.vue（错题本）
  - [ ] StudyPlanView.vue（学习计划，含番茄钟）
  - [ ] DocsView.vue（文档上传）
  - [ ] StatsView.vue（学习统计，ECharts 图表）
  - [ ] LoginView.vue + RegisterView.vue（认证页面）
- [ ] AppSidebar.vue 侧边导航完整实现
- [ ] AppHeader.vue 顶部导航完整实现
- [ ] LaTeX 公式渲染（KaTeX 集成）
- [ ] Markdown 渲染（marked 集成）
- [ ] AI 问答 SSE 流式接收实现
- [ ] ECharts 图表集成（统计页面）
- [ ] 响应式设计适配（桌面/平板）

### 集成与测试
- [ ] 前后端联调测试
- [ ] Docker Compose 完整启动测试
- [ ] API 接口测试

---

## 已知问题

1. **数据库迁移**：Alembic 尚未初始化，当前数据库可能通过 `init_db()` 直接建表
2. **Tailwind CSS v4**：项目使用 Tailwind v4（前沿版本），配置方式与 v3 不同，需注意兼容性
3. **前端 vite.config.ts**：未确认是否配置了 `/api` 代理到后端 `:8000`（本地开发需要）

---

## 项目决策记录

| 日期 | 决策 | 原因 |
|------|------|------|
| 2026-05-28 | 使用 SQLite 而非 PostgreSQL | 简化部署，单机性能已满足需求 |
| 2026-05-28 | AI 流式输出使用 SSE + fetch ReadableStream | 避免 WebSocket 复杂性，SSE 更简单 |
| 2026-05-28 | JWT 存储在 localStorage | 简化实现，对中学生用户场景安全性足够 |
| 2026-05-28 | 生产后端端口映射为 8001 | 避免与本地开发 8000 端口冲突 |
