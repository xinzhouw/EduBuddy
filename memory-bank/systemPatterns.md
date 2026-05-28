# EduBuddy 系统架构与设计模式

## 整体架构

前后端分离架构：
- **前端**：Vue 3 SPA（单页应用）
- **后端**：Python FastAPI RESTful 服务
- **通信**：REST API + SSE（流式输出）
- **部署**：Docker Compose（前端 Nginx + 后端 Uvicorn）

```
用户浏览器 (Vue 3 SPA)
      │ HTTP/HTTPS (REST API + SSE)
FastAPI 后端服务
      │              │              │
   SQLite DB    OpenAI API    本地文件存储
```

## 后端架构分层

```
HTTP Request
    ↓
Router (路由层)    — 处理 HTTP 请求/响应，Pydantic Schema 参数验证
    ↓
Service (服务层)   — 业务逻辑、AI 调用、复杂计算
    ↓
Model (数据层)     — SQLAlchemy ORM，数据库操作
    ↓
Database (SQLite)
```

### 后端核心文件结构
```
backend/app/
├── main.py            # FastAPI 应用入口，注册路由，挂载静态文件
├── config.py          # Pydantic Settings，读取环境变量
├── database.py        # SQLAlchemy 引擎和 Session 配置
├── dependencies.py    # 依赖注入（JWT 认证，获取当前用户）
├── models/            # SQLAlchemy ORM 模型
├── schemas/           # Pydantic 请求/响应模型
├── routers/           # API 路由（每个模块一个文件）
└── services/          # 业务逻辑服务
```

### 已注册路由
| 路由文件 | 路径前缀 | 功能 |
|---------|---------|------|
| auth.py | /api/auth | 用户注册/登录/信息 |
| ai.py | /api/ai | AI 问答（SSE 流式） |
| notes.py | /api/notes | 笔记 CRUD，AI 总结 |
| notes.py (flashcard_router) | /api/flashcards | 知识卡片 |
| quiz.py | /api/quiz | 练习题生成和答题 |
| wrong_book.py | /api/wrong-book | 错题本管理 |
| plan.py | /api/plan | 学习计划 |
| documents.py | /api/docs | 文档上传/解析 |
| stats.py | /api/stats | 学习统计 |

## 前端架构

### 核心技术
- **Vue 3 Composition API** + TypeScript
- **Vue Router 4** 路由管理（含路由守卫：未登录跳转 /login）
- **Pinia** 状态管理（auth store 已实现）
- **Element Plus** UI 组件库
- **Tailwind CSS** 样式框架
- **Axios** HTTP 请求封装（`/src/api/index.ts` 统一配置）

### 前端目录结构
```
frontend/src/
├── main.ts           # 应用入口
├── App.vue           # 根组件
├── router/index.ts   # 路由配置（含 beforeEach 守卫）
├── stores/auth.ts    # Pinia 用户认证 store
├── api/              # API 封装（auth/ai/notes/quiz/wrongBook/plan/docs）
├── views/            # 页面视图（按功能模块分目录）
├── components/layout/ # AppSidebar.vue + AppHeader.vue
└── assets/
```

### 路由结构
| 路径 | 视图组件 | 认证要求 |
|------|---------|---------|
| /login | LoginView | 公开 |
| /register | RegisterView | 公开 |
| / | DashboardView | 需认证 |
| /ai | AIChatView | 需认证 |
| /notes | NotesListView | 需认证 |
| /notes/:id/edit | NoteEditView | 需认证 |
| /quiz | QuizSetupView | 需认证 |
| /quiz/session | QuizSessionView | 需认证 |
| /wrong-book | WrongBookView | 需认证 |
| /wrong-book/:id | WrongDetailView | 需认证 |
| /plan | StudyPlanView | 需认证 |
| /docs | DocsView | 需认证 |
| /stats | StatsView | 需认证 |

## AI 服务设计（ai_service.py）

AIService 类封装所有 OpenAI 调用：
- `chat_stream()` — 流式问答（SSE）
- `generate_quiz()` — 生成练习题
- `explain_wrong_answer()` — 错题 AI 讲解
- `summarize_note()` — 笔记 AI 总结
- `generate_study_plan()` — 生成学习计划
- `analyze_document()` — 文档分析（提取知识点/摘要/出题）

System Prompt 约束 AI 只回答中学学科问题。

## AI 流式输出实现（SSE）

```
后端：FastAPI StreamingResponse + yield
前端：fetch() + ReadableStream reader 逐字符更新 UI
```

## 安全设计

- **认证**：JWT Token（HS256，有效期 7 天），存储于 localStorage
- **密码**：bcrypt 哈希（salt rounds = 12）
- **数据隔离**：所有数据库查询强制加 `user_id` 过滤
- **文件上传**：校验文件类型和大小，独立存储目录 `./uploads/`
- **SQL 注入防护**：全部通过 SQLAlchemy ORM 操作

## 数据库设计要点

- **数据库**：SQLite（文件路径：`backend/data/edubuddy.db`）
- **ORM**：SQLAlchemy 2.0
- **迁移**：Alembic（待配置）

### 核心表关系
```
users (1)
  ├─ (1:N) chat_sessions → (1:N) chat_messages
  ├─ (1:N) notes → (1:N) flashcards
  ├─ (1:N) quiz_sessions → (1:N) questions → (1:N) quiz_answers
  ├─ (1:N) wrong_items → (1:N) wrong_reviews
  ├─ (1:N) study_plans → (1:N) plan_tasks
  ├─ (1:N) pomodoros
  ├─ (1:N) documents
  └─ (1:N) study_logs
```

### 间隔复习算法（review_service.py）
基于艾宾浩斯遗忘曲线，`wrong_items.review_count` 决定下次复习间隔：
| review_count | 间隔 |
|-------------|------|
| 0（新增） | 1 天 |
| 1 | 3 天 |
| 2 | 7 天 |
| 3 | 14 天 |
| 4 | 30 天（标记 mastered） |

## API 响应规范

```json
// 成功
{ "code": 200, "message": "success", "data": { ... } }

// 失败
{ "code": 400, "message": "错误描述", "data": null }
```

分页：`?page=1&size=20`，响应含 `items/total/page/size/pages`

## 部署

- **开发**：前端 `npm run dev`（:5173），后端 `uvicorn`（:8000）
- **生产**：Docker Compose，前端容器（:80），后端容器（:8001→8000）
- **环境变量**：根目录 `.env` 文件（OPENAI_API_KEY、SECRET_KEY 等）
