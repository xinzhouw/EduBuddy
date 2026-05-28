# EduBuddy 技术上下文

## 技术栈总览

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | ^3.11 | 运行环境 |
| FastAPI | 0.110.0 | Web 框架 |
| SQLAlchemy | 2.0.28 | ORM |
| Alembic | 1.13.1 | 数据库迁移 |
| SQLite | 内置 | 数据库 |
| Pydantic | 2.6.3 | 数据验证 |
| pydantic-settings | 2.2.1 | 环境变量配置 |
| python-jose | 3.3.0 | JWT 认证 |
| passlib[bcrypt] | 1.7.4 | 密码加密 |
| openai | 1.14.0 | OpenAI SDK |
| PyMuPDF | 1.24.0 | PDF 解析 |
| python-docx | 1.1.0 | Word 文档解析 |
| Pillow | 10.2.0 | 图片处理 |
| aiofiles | 23.2.1 | 异步文件操作 |
| uvicorn[standard] | 0.27.1 | ASGI 服务器 |
| python-multipart | 0.0.9 | 文件上传支持 |
| httpx | 0.27.0 | 异步 HTTP 客户端 |
| python-dotenv | 1.0.1 | .env 文件加载 |

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | ^3.5.34 | 核心框架（Composition API） |
| TypeScript | ~6.0.2 | 类型安全 |
| Vite | ^8.0.12 | 构建工具 |
| Vue Router | ^4.6.4 | 前端路由 |
| Pinia | ^3.0.4 | 状态管理 |
| Axios | ^1.16.1 | HTTP 请求 |
| Element Plus | ^2.14.0 | UI 组件库 |
| @element-plus/icons-vue | ^2.3.2 | 图标库 |
| Tailwind CSS | ^4.3.0 | 样式框架 |
| KaTeX | ^0.17.0 | LaTeX 数学公式渲染 |
| marked | ^18.0.4 | Markdown 渲染 |
| ECharts | ^6.1.0 | 数据可视化图表 |
| @vueuse/core | ^14.3.0 | Vue 组合式工具库 |

## 开发环境配置

### 本地开发启动

```bash
# 后端（需在 backend/ 目录下）
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# 访问：http://localhost:8000
# API 文档：http://localhost:8000/docs

# 前端（需在 frontend/ 目录下）
npm install
npm run dev
# 访问：http://localhost:5173
```

### 环境变量（根目录 .env）
```
OPENAI_API_KEY=sk-...
SECRET_KEY=your-jwt-secret-key
DATABASE_URL=sqlite:///./data/edubuddy.db
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=20
CORS_ORIGINS=http://localhost:5173,http://localhost:80
```

### Docker Compose 生产部署
```bash
docker compose up -d
# 前端：http://localhost:80
# 后端：http://localhost:8001
```

Docker 端口映射：
- 前端容器：`:80:80`（Nginx 静态服务）
- 后端容器：`:8001:8000`（Uvicorn）

持久化卷：
- `./backend/uploads:/app/uploads`（用户上传文件）
- `./backend/data:/app/data`（SQLite 数据库文件）

## 项目文件结构

```
EduBuddy/
├── .env                  # 环境变量（不提交 Git）
├── docker-compose.yml    # Docker Compose 配置
├── docs/                 # 项目文档
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE_DESIGN.md
│   ├── API_DESIGN.md
│   ├── UI_DESIGN.md
│   └── README.md
├── memory-bank/          # Cline Memory Bank
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run.py
│   ├── .env.example
│   ├── app/              # FastAPI 应用
│   ├── data/             # SQLite 数据库文件
│   └── uploads/          # 用户上传文件
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── index.html
    └── src/              # Vue 应用源码
```

## 关键技术约束与注意事项

1. **SQLite 并发**：SQLite 在高并发写入时有限制，生产环境高流量时可考虑迁移到 PostgreSQL（架构已预留，修改 DATABASE_URL 即可）
2. **OpenAI API 依赖**：需要有效的 `OPENAI_API_KEY`，流式接口使用 SSE
3. **文件存储**：当前使用本地文件系统，扩展时可替换为 OSS/S3
4. **数据库迁移**：Alembic 已在依赖中，但迁移文件尚未初始化（`alembic init alembic` 待执行）
5. **Tailwind CSS 版本**：当前使用 Tailwind v4（与 v3 配置方式不同）
6. **前端 API 代理**：Vite 开发模式下需配置 proxy 将 `/api` 请求代理到后端 `:8000`

## 代码风格约定

- 后端：Python，遵循 FastAPI 惯用模式，异步函数使用 `async/await`
- 前端：TypeScript，Vue 3 Composition API（`<script setup>` 语法糖）
- API 路径统一以 `/api/` 为前缀
- 数据模型命名：ORM 用 `snake_case`，Pydantic Schema 用 `camelCase`（JSON 输出）
