# EduBuddy 技术架构文档

**版本**：V1.0  
**日期**：2026-05-28  

---

## 1. 整体架构概览

EduBuddy 采用前后端分离架构，前端为 Vue 3 SPA，后端为 Python FastAPI RESTful 服务。

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                             │
│                  Vue 3 SPA (前端应用)                         │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/HTTPS (REST API + SSE)
┌───────────────────────────▼─────────────────────────────────┐
│                   FastAPI 后端服务                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Auth    │  │   AI     │  │  Notes   │  │  Quiz    │   │
│  │  Router  │  │  Router  │  │  Router  │  │  Router  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Wrong   │  │  Plan    │  │  Docs    │  │  Stats   │   │
│  │  Router  │  │  Router  │  │  Router  │  │  Router  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                    Service Layer (业务逻辑)                   │
└──────────┬────────────────┬────────────────┬────────────────┘
           │                │                │
    ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │   SQLite    │  │  OpenAI API │  │  本地文件存储 │
    │  (数据库)   │  │  (AI服务)   │  │  (上传文件)  │
    └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 2. 前端架构

### 2.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.4 | 核心框架（Composition API） |
| TypeScript | ^5.x | 类型安全 |
| Vite | ^5.x | 构建工具 |
| Vue Router | ^4.x | 前端路由 |
| Pinia | ^2.x | 状态管理 |
| Axios | ^1.x | HTTP 请求 |
| Element Plus | ^2.x | UI 组件库 |
| Tailwind CSS | ^3.x | 样式框架 |
| KaTeX | ^0.16 | LaTeX 数学公式渲染 |
| marked | ^11.x | Markdown 渲染 |
| ECharts | ^5.x | 数据可视化图表 |

### 2.2 目录结构

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── main.ts                 # 应用入口
│   ├── App.vue                 # 根组件
│   ├── router/
│   │   └── index.ts            # 路由配置
│   ├── stores/                 # Pinia 状态管理
│   │   ├── auth.ts             # 用户认证状态
│   │   ├── notes.ts            # 笔记状态
│   │   ├── quiz.ts             # 练习题状态
│   │   └── wrongBook.ts        # 错题本状态
│   ├── api/                    # API 请求封装
│   │   ├── index.ts            # Axios 实例配置
│   │   ├── auth.ts
│   │   ├── ai.ts
│   │   ├── notes.ts
│   │   ├── quiz.ts
│   │   ├── wrongBook.ts
│   │   ├── plan.ts
│   │   └── docs.ts
│   ├── views/                  # 页面视图
│   │   ├── auth/
│   │   │   ├── LoginView.vue
│   │   │   └── RegisterView.vue
│   │   ├── DashboardView.vue   # 首页/仪表板
│   │   ├── ai/
│   │   │   └── AIChatView.vue  # AI 问答
│   │   ├── notes/
│   │   │   ├── NotesListView.vue
│   │   │   └── NoteEditView.vue
│   │   ├── quiz/
│   │   │   ├── QuizSetupView.vue
│   │   │   └── QuizSessionView.vue
│   │   ├── wrongBook/
│   │   │   ├── WrongBookView.vue
│   │   │   └── WrongDetailView.vue
│   │   ├── plan/
│   │   │   └── StudyPlanView.vue
│   │   ├── docs/
│   │   │   └── DocsView.vue
│   │   └── stats/
│   │       └── StatsView.vue
│   ├── components/             # 公共组件
│   │   ├── layout/
│   │   │   ├── AppSidebar.vue  # 侧边栏导航
│   │   │   └── AppHeader.vue   # 顶部导航
│   │   ├── common/
│   │   │   ├── LatexRenderer.vue    # 公式渲染
│   │   │   ├── MarkdownRenderer.vue # Markdown渲染
│   │   │   ├── LoadingSpinner.vue
│   │   │   └── SubjectTag.vue  # 学科标签
│   │   ├── ai/
│   │   │   ├── ChatMessage.vue
│   │   │   └── FeedbackButtons.vue  # 👍/👎
│   │   └── quiz/
│   │       ├── QuestionCard.vue
│   │       └── DifficultySelector.vue
│   ├── types/                  # TypeScript 类型定义
│   │   ├── user.ts
│   │   ├── note.ts
│   │   ├── quiz.ts
│   │   └── wrong.ts
│   └── utils/                  # 工具函数
│       ├── format.ts           # 日期格式化等
│       └── subjects.ts         # 学科常量
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
└── package.json
```

### 2.3 路由设计

| 路径 | 组件 | 说明 |
|------|------|------|
| `/login` | LoginView | 登录页（无需认证） |
| `/register` | RegisterView | 注册页（无需认证） |
| `/` | DashboardView | 首页/仪表板（需认证） |
| `/ai` | AIChatView | AI 问答（需认证） |
| `/notes` | NotesListView | 笔记列表（需认证） |
| `/notes/:id/edit` | NoteEditView | 笔记编辑（需认证） |
| `/quiz` | QuizSetupView | 练习题设置（需认证） |
| `/quiz/session` | QuizSessionView | 答题页面（需认证） |
| `/wrong-book` | WrongBookView | 错题本（需认证） |
| `/wrong-book/:id` | WrongDetailView | 错题详情（需认证） |
| `/plan` | StudyPlanView | 学习计划（需认证） |
| `/docs` | DocsView | 文档上传（需认证） |
| `/stats` | StatsView | 学习统计（需认证） |

### 2.4 状态管理（Pinia）

```typescript
// stores/auth.ts
interface AuthStore {
  token: string | null
  user: User | null
  isAuthenticated: boolean
}

// stores/wrongBook.ts
interface WrongBookStore {
  items: WrongItem[]
  todayReview: WrongItem[]  // 今日待复习
  loading: boolean
}
```

### 2.5 AI 流式输出处理

AI 问答使用 Server-Sent Events (SSE) 实现流式输出：

```typescript
// 前端接收流式数据
const response = await fetch('/api/ai/chat', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({ question, subject })
})
const reader = response.body?.getReader()
// 逐字符更新 UI，实现打字机效果
```

---

## 3. 后端架构

### 3.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | ^3.11 | 运行环境 |
| FastAPI | ^0.110 | Web 框架 |
| SQLAlchemy | ^2.0 | ORM |
| Alembic | ^1.13 | 数据库迁移 |
| SQLite | 内置 | 数据库（开发/生产） |
| Pydantic | ^2.x | 数据验证 |
| python-jose | ^3.3 | JWT 认证 |
| passlib[bcrypt] | ^1.7 | 密码加密 |
| openai | ^1.x | OpenAI SDK |
| PyMuPDF | ^1.24 | PDF 解析 |
| python-docx | ^1.x | Word 解析 |
| Pillow | ^10.x | 图片处理 |
| aiofiles | ^23.x | 异步文件操作 |
| uvicorn | ^0.27 | ASGI 服务器 |

### 3.2 目录结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 应用入口
│   ├── database.py             # 数据库连接配置
│   ├── config.py               # 环境变量配置
│   ├── dependencies.py         # 依赖注入（认证等）
│   ├── models/                 # SQLAlchemy 数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── note.py
│   │   ├── quiz.py
│   │   ├── wrong_item.py
│   │   ├── study_plan.py
│   │   └── document.py
│   ├── schemas/                # Pydantic 请求/响应模型
│   │   ├── auth.py
│   │   ├── note.py
│   │   ├── quiz.py
│   │   ├── wrong_item.py
│   │   ├── plan.py
│   │   └── document.py
│   ├── routers/                # API 路由
│   │   ├── auth.py             # 认证路由
│   │   ├── ai.py               # AI 问答路由
│   │   ├── notes.py            # 笔记路由
│   │   ├── quiz.py             # 练习题路由
│   │   ├── wrong_book.py       # 错题本路由
│   │   ├── plan.py             # 学习计划路由
│   │   ├── documents.py        # 文档上传路由
│   │   └── stats.py            # 统计路由
│   └── services/               # 业务逻辑服务
│       ├── ai_service.py       # AI 调用封装
│       ├── document_service.py # 文档解析
│       ├── quiz_service.py     # 练习题逻辑
│       ├── review_service.py   # 间隔复习调度
│       └── stats_service.py    # 统计计算
├── uploads/                    # 用户上传文件存储目录
├── alembic/                    # 数据库迁移文件
├── tests/                      # 单元测试
├── .env.example                # 环境变量示例
├── requirements.txt            # 依赖列表
└── run.py                      # 启动脚本
```

### 3.3 API 分层设计

```
HTTP Request
    ↓
Router (路由层)       - 处理 HTTP 请求/响应，参数验证（Pydantic Schema）
    ↓
Service (服务层)      - 业务逻辑，AI 调用，计算
    ↓
Model (数据层)        - SQLAlchemy ORM，数据库操作
    ↓
Database (SQLite)
```

### 3.4 AI 服务设计

```python
# services/ai_service.py

class AIService:
    SYSTEM_PROMPT = """
    你是 EduBuddy，一名专业的中学学科辅导老师。
    你只回答与中学数学、物理、化学、生物、语文、英语、
    历史、地理、政治相关的学习问题。
    解题方法必须在中学教学大纲范围内。
    对于非学习相关的问题，礼貌拒绝并引导学生回到学习。
    """
    
    async def chat_stream(self, question: str, subject: str, grade: str):
        """流式 AI 问答"""
        ...
    
    async def generate_quiz(self, subject: str, topic: str, 
                            difficulty: int, question_type: str, count: int):
        """生成练习题"""
        ...
    
    async def explain_wrong_answer(self, question: str, 
                                   wrong_answer: str, correct_answer: str):
        """错题 AI 讲解"""
        ...
    
    async def summarize_note(self, content: str):
        """笔记 AI 总结"""
        ...
    
    async def generate_study_plan(self, subjects: list, exam_date: str, 
                                  daily_hours: float, weak_subjects: list):
        """生成学习计划"""
        ...
    
    async def analyze_document(self, text: str, task: str):
        """文档 AI 分析（提取知识点/生成摘要/出题）"""
        ...
```

---

## 4. 数据库设计概览

使用 SQLite 作为数据库，通过 SQLAlchemy ORM 操作。详细设计见 `DATABASE_DESIGN.md`。

**核心数据表**：
- `users` — 用户信息
- `chat_sessions` — AI 问答会话
- `chat_messages` — 问答消息记录
- `notes` — 笔记
- `flashcards` — 知识卡片
- `quiz_sessions` — 练习题会话
- `questions` — 题目（AI生成后缓存）
- `wrong_items` — 错题
- `wrong_reviews` — 复习记录
- `study_plans` — 学习计划
- `plan_tasks` — 计划任务
- `documents` — 上传文档
- `study_logs` — 学习时长记录

---

## 5. 安全设计

### 5.1 认证流程

```
用户登录
  → 后端验证用户名密码
  → 生成 JWT Token（有效期 7天）
  → 前端存储到 localStorage
  → 每次请求在 Header 中携带 Authorization: Bearer <token>
  → 后端验证 Token 有效性
```

### 5.2 数据安全
- 密码使用 `bcrypt` 哈希存储（salt rounds = 12）
- JWT 使用 `HS256` 算法签名
- 所有数据库查询都通过 ORM，防止 SQL 注入
- 文件上传：校验文件类型和大小，存储在独立目录
- 用户数据隔离：所有查询强制加 `user_id` 过滤

---

## 6. 部署架构

### 6.1 开发环境

```bash
# 前端
cd frontend && npm run dev    # http://localhost:5173

# 后端
cd backend && uvicorn app.main:app --reload  # http://localhost:8000
```

### 6.2 生产环境（Docker Compose）

```yaml
# docker-compose.yml
services:
  frontend:
    build: ./frontend
    ports: ["80:80"]
    
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/data:/app/data  # SQLite 文件
    env_file: .env
```

### 6.3 环境变量

```env
# .env
OPENAI_API_KEY=sk-...
SECRET_KEY=your-jwt-secret-key
DATABASE_URL=sqlite:///./data/edubuddy.db
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=20
```

---

## 7. 前后端交互规范

### 7.1 统一响应格式

```json
// 成功
{
  "code": 200,
  "message": "success",
  "data": { ... }
}

// 失败
{
  "code": 400,
  "message": "错误描述",
  "data": null
}
```

### 7.2 错误码规范

| 错误码 | 说明 |
|-------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证（Token 失效或缺失） |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

### 7.3 分页规范

```json
// 请求参数
?page=1&size=20

// 响应
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```
