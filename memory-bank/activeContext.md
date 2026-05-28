# EduBuddy 活跃上下文

## 当前工作焦点
**日期**：2026-05-28  
**阶段**：Memory Bank 初始化完成，项目处于 V1.0 初期开发阶段

## 最近完成的工作
- 初始化 Memory Bank，创建所有 6 个核心文档文件
- 全面梳理了项目文档（PRD、架构、数据库设计）
- 确认了项目基础架构已搭建完成（前后端脚手架、所有文件骨架）

## 项目当前状态摘要

项目已完成**架构设计和文件骨架搭建**，但各模块的**具体业务逻辑实现**程度未知，需要逐一核查。

已确认存在的文件（骨架/占位）：
- 后端：所有路由文件、服务文件、ORM 模型、Schema 已创建
- 前端：所有视图页面、API 封装、路由配置、auth store 已创建
- 数据库文件：`backend/data/edubuddy.db` 已存在（说明后端曾启动过）

## 下一步建议

### 优先级 1：核查后端实现
1. 查看 `backend/app/routers/auth.py` — 确认注册/登录接口是否完整
2. 查看 `backend/app/services/ai_service.py` — 确认 OpenAI 调用是否实现
3. 查看 `backend/app/routers/ai.py` — 确认 SSE 流式接口是否实现

### 优先级 2：核查前端实现
1. 查看 `frontend/src/views/auth/LoginView.vue` — 登录页面 UI 是否完整
2. 查看 `frontend/src/views/ai/AIChatView.vue` — AI 问答页面是否实现
3. 查看 `frontend/vite.config.ts` — 确认 API 代理是否配置

### 优先级 3：启动验证
- 尝试启动 Docker Compose 或本地开发环境，验证项目可运行

## 重要模式与偏好

### 代码约定
- 后端 Python 异步优先（`async def`）
- 前端使用 `<script setup lang="ts">` Composition API 语法
- API 统一前缀 `/api/`
- 错误响应统一格式：`{ "code": 400, "message": "...", "data": null }`

### 关键路径
- AI 流式输出：后端 `StreamingResponse` → 前端 `fetch + ReadableStream`
- 用户认证：登录 → JWT Token → localStorage → Axios 请求头
- 错题复习：答题答错 → `wrong_items` 表 → `review_service` 计算下次复习时间

## 活跃决策与注意事项

1. **数据库 `init_db()` vs Alembic**：当前 `main.py` 在 startup 事件调用 `init_db()`，可能是直接 `create_all()` 建表，不需要 Alembic 也能运行
2. **Tailwind CSS v4**：`tailwind.config.js` 存在但 v4 的配置方式可能有变化，样式问题时优先检查此处
3. **后端端口**：Docker 生产环境后端映射到 8001，本地开发是 8000，前端代理配置需要注意区分
4. **SQLite 数据库路径**：Docker 中是 `sqlite:///./data/edubuddy.db`，本地开发路径由 `.env` 决定

## 学到的项目洞察

- 项目文档非常完整和详细，是理解业务逻辑的最佳参考
- 数据库文件 `edubuddy.db` 已存在，说明数据库初始化逻辑可用
- 所有前端视图文件都已存在，需要进一步核查每个文件的完成度
