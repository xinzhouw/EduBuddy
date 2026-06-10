<div align="center">

# 📚 EduBuddy

**AI 驱动的中学生个性化学习助手**

[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?style=flat-square&logo=vue.js)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

一站式解决中学生学习痛点 —— AI 解题、错题管理、学习计划、练习题生成、作业批改，全部在一个平台完成。

[功能介绍](#-核心功能) · [快速开始](#-快速开始) · [技术架构](#️-技术架构) · [项目文档](#-项目文档) · [部署指南](#-部署指南)

</div>

---

## ✨ 核心功能

| 功能模块 | 描述 |
|---------|------|
| 🤖 **AI 问答解题** | 支持全部中学学科，结构化分步解析，流式打字机输出（SSE），多轮追问，👍/👎 反馈 |
| 📝 **笔记管理** | 富文本编辑器，支持 LaTeX 公式，AI 一键总结，自动生成知识卡片（Flashcard） |
| 📚 **练习题生成** | 按学科 / 知识点 / 题型 / 难度 AI 生成练习题，自动判题，自适应难度推荐 |
| ❌ **错题本** | 自动 / 手动录入，间隔复习（艾宾浩斯遗忘曲线），AI 逐步讲解，掌握度标记 |
| 📅 **学习计划** | 根据考试日期 AI 生成每日任务，番茄钟计时器，任务进度追踪 |
| ✍️ **AI 批改作业** | 上传文本 / 图片 / PDF 作业，AI 流式批改并给出评分与建议 |
| 📄 **文档上传解析** | 上传 PDF / Word / 图片，AI 提取知识点 / 生成摘要 / 基于文档出题 |
| 📊 **学习统计** | 学习时长趋势折线图、学科分布柱状图、掌握度雷达图、打卡热力图 |
| 🔊 **语音朗读** | 语文 / 英语学科的 AI 回答和作业批改报告支持语音朗读（Web Speech API） |
| 🧑‍🏫 **家长 / 教师监控** | 关联绑定学生账号，查看学习数据与进度 |

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

**前提条件**：安装 [Docker](https://docs.docker.com/get-docker/) 和 [Docker Compose](https://docs.docker.com/compose/install/)

```bash
# 1. 克隆项目
git clone https://github.com/xinzhouw/EduBuddy.git
cd EduBuddy

# 2. 配置环境变量
cp backend/.env.example .env
# 编辑 .env，填入必要的配置项（见下方环境变量说明）

# 3. 启动服务
docker compose up -d

# 4. 访问
# 前端：http://localhost:80
# 后端 API 文档：http://localhost:8001/docs
```

### 方式二：本地开发模式

**前提条件**：Python 3.11+，Node.js 18+

```bash
# ── 启动后端 ──────────────────────────────────
cd backend
pip install -r requirements.txt
cp .env.example .env          # 填写 OPENAI_API_KEY 等配置
uvicorn app.main:app --reload --port 8000
# API 文档：http://localhost:8000/docs

# ── 启动前端（新终端）────────────────────────
cd frontend
npm install
npm run dev
# 访问：http://localhost:5173
```

### 环境变量说明

编辑根目录 `.env` 文件（基于 `backend/.env.example`）：

```env
# AI 服务（必填）
OPENAI_API_KEY=sk-...                      # OpenAI API Key（或兼容服务的 Key）
OPENAI_BASE_URL=https://api.openai.com/v1  # 可替换为其他兼容 OpenAI 的 API 地址
OPENAI_MODEL=gpt-4o                        # 使用的模型名称
OPENAI_USE_TEMPERATURE=true                # 部分模型网关不支持 temperature 时设为 false

# 安全（必填）
SECRET_KEY=your-jwt-secret-key-change-this

# 数据库（可选，默认 SQLite）
DATABASE_URL=sqlite:///./data/edubuddy.db

# 文件上传
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=20

# 跨域
CORS_ORIGINS=http://localhost:5173,http://localhost:80
```

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────┐
│                   用户浏览器                          │
│              Vue 3 SPA（TypeScript）                  │
└──────────────────────┬──────────────────────────────┘
                       │  REST API + SSE（流式输出）
┌──────────────────────▼──────────────────────────────┐
│              FastAPI 后端服务                         │
│         Router → Service → Model → DB                │
└──────┬──────────────┬───────────────┬───────────────┘
       │              │               │
  SQLite DB      OpenAI API     本地文件存储
  (edubuddy.db)  (GPT-4o)       (uploads/)
```

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | ^3.5 | 核心框架（Composition API） |
| TypeScript | ~6.0 | 类型安全 |
| Vite | ^8.0 | 构建工具 |
| Vue Router | ^4.6 | 前端路由（含路由守卫） |
| Pinia | ^3.0 | 状态管理 |
| Element Plus | ^2.14 | UI 组件库 |
| Tailwind CSS | ^4.3 | 样式框架 |
| ECharts | ^6.1 | 数据可视化 |
| KaTeX | ^0.17 | LaTeX 数学公式渲染 |
| marked | ^18.0 | Markdown 渲染 |
| Axios | ^1.16 | HTTP 请求封装 |

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | ^3.11 | 运行环境 |
| FastAPI | 0.110 | Web 框架 |
| SQLAlchemy | 2.0 | ORM |
| SQLite | 内置 | 数据库（可迁移 PostgreSQL） |
| Pydantic | 2.6 | 数据验证 |
| OpenAI SDK | 1.14 | AI 服务调用 |
| PyMuPDF | 1.24 | PDF 解析 |
| python-docx | 1.1 | Word 解析 |
| ChromaDB | ^0.5 | 向量数据库（RAG） |
| bcrypt | 4.x | 密码加密 |
| python-jose | 3.3 | JWT 认证 |

---

## 📁 项目结构

```
EduBuddy/
├── .env                        # 环境变量（不提交 Git）
├── docker-compose.yml          # Docker Compose 配置
├── docs/                       # 项目设计文档
│   ├── PRD.md                  # 产品需求文档
│   ├── ARCHITECTURE.md         # 技术架构文档
│   ├── API_DESIGN.md           # API 接口设计
│   ├── DATABASE_DESIGN.md      # 数据库设计
│   ├── UI_DESIGN.md            # UI 设计规范
│   ├── DEPLOYMENT_GUIDE.md     # 部署指南
│   └── TEST_REPORT.md          # 测试报告
├── agents/                     # 工具脚本
│   └── textbook_crawler/       # 高中教材 PDF 下载 & RAG 知识库构建
├── backend/                    # FastAPI 后端
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py             # 应用入口，注册路由
│   │   ├── config.py           # 环境变量配置（Pydantic Settings）
│   │   ├── database.py         # SQLAlchemy 引擎 & Session
│   │   ├── dependencies.py     # 依赖注入（JWT 认证）
│   │   ├── security.py         # 密码加密（bcrypt）
│   │   ├── models/             # ORM 数据模型
│   │   ├── schemas/            # Pydantic 请求/响应 Schema
│   │   ├── routers/            # API 路由（每模块一文件）
│   │   └── services/           # 业务逻辑服务
│   ├── data/                   # SQLite 数据库 & 知识库
│   └── uploads/                # 用户上传文件
└── frontend/                   # Vue 3 前端
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── nginx.conf
    └── src/
        ├── api/                # API 封装（Axios）
        ├── views/              # 页面视图组件
        ├── components/         # 公共组件（Sidebar / Header）
        ├── stores/             # Pinia 状态管理
        ├── router/             # 路由配置
        └── utils/              # 工具函数（markdown / LaTeX 渲染等）
```

---

## 🗺️ 页面路由

| 路径 | 页面 | 认证 |
|------|------|------|
| `/login` | 登录 | 公开 |
| `/register` | 注册 | 公开 |
| `/` | 仪表盘 | ✅ |
| `/ai` | AI 问答解题 | ✅ |
| `/notes` | 笔记列表 | ✅ |
| `/notes/:id/edit` | 笔记编辑 | ✅ |
| `/quiz` | 练习题设置 | ✅ |
| `/quiz/session` | 练习题作答 | ✅ |
| `/wrong-book` | 错题本 | ✅ |
| `/wrong-book/:id` | 错题详情 | ✅ |
| `/plan` | 学习计划 | ✅ |
| `/homework` | AI 批改作业 | ✅ |
| `/docs` | 文档上传 | ✅ |
| `/stats` | 学习统计 | ✅ |
| `/profile` | 个人资料 | ✅ |
| `/monitor` | 监控（教师/家长） | ✅ |

---

## 🧠 RAG 知识库（可选）

EduBuddy 内置高中教材 RAG（检索增强生成）支持，可从国家智慧教育平台下载教材 PDF，构建本地向量知识库，大幅提升 AI 回答的准确性。

```bash
# 1. 安装依赖
cd agents/textbook_crawler
pip install -r requirements.txt

# 2. 下载教材（约 814MB，支持 --subject 单科下载）
python download_all_hs.py

# 3. 构建向量知识库
python build_knowledge_base.py
# 成果：14933 条向量记录，存于 backend/data/knowledge_base/chroma/
```

详细说明见 [agents/textbook_crawler/README.md](agents/textbook_crawler/README.md)

---

## 🔌 API 接口概览

| 路由前缀 | 功能 |
|---------|------|
| `POST /api/auth/register` | 用户注册 |
| `POST /api/auth/login` | 用户登录（返回 JWT） |
| `POST /api/ai/chat` | AI 问答（SSE 流式） |
| `GET /api/ai/knowledge-base/stats` | 知识库状态 |
| `GET/POST /api/notes` | 笔记 CRUD |
| `GET/POST /api/flashcards` | 知识卡片 CRUD |
| `POST /api/quiz/generate` | 生成练习题 |
| `POST /api/quiz/submit` | 提交答案（自动判题） |
| `POST /api/quiz/extract-topic` | 扫描图片/文档识别知识点 |
| `GET/POST /api/wrong-book` | 错题本 CRUD |
| `GET/POST /api/plan` | 学习计划 CRUD |
| `POST /api/homework/grade/text` | 文本作业批改（SSE） |
| `POST /api/homework/grade/file` | 文件作业批改（SSE） |
| `GET/POST /api/docs` | 文档上传 & 解析 |
| `GET /api/stats/overview` | 学习统计概览 |

完整接口文档：启动后访问 `http://localhost:8001/docs`（Swagger UI）

---

## 🚢 部署指南

### Docker Compose 生产部署

```bash
docker compose up -d --build

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

**端口映射**：
- 前端：`:80` → Nginx 静态服务
- 后端：`:8001` → Uvicorn（内部 :8000）

**持久化卷**：
- `./backend/uploads` → 用户上传文件
- `./backend/data` → SQLite 数据库

### 热更新部署（不重建镜像）

```bash
# 更新前端
docker cp frontend/dist/. edubuddy-frontend-1:/usr/share/nginx/html/

# 更新后端（单文件）
docker cp backend/app/routers/xxx.py edubuddy-backend-1:/app/app/routers/xxx.py
docker restart edubuddy-backend-1
```

更多部署细节见 [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)

---

## 🧪 测试

```bash
# 后端语法检查
python -m py_compile backend/app/**/*.py

# 前端 TypeScript 类型检查
cd frontend && npx vue-tsc --noEmit

# 前端构建验证
cd frontend && npm run build
```

---

## 📖 项目文档

| 文档 | 说明 |
|------|------|
| [docs/PRD.md](docs/PRD.md) | 产品需求文档 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 技术架构设计 |
| [docs/API_DESIGN.md](docs/API_DESIGN.md) | 完整 API 接口设计 |
| [docs/DATABASE_DESIGN.md](docs/DATABASE_DESIGN.md) | 数据库表结构设计 |
| [docs/UI_DESIGN.md](docs/UI_DESIGN.md) | UI 视觉与交互规范 |
| [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | 部署与运维指南 |
| [docs/TEST_REPORT.md](docs/TEST_REPORT.md) | 功能测试报告（19/19 ✅） |

---

## 🗺️ 版本规划

| 版本 | 状态 | 功能范围 |
|------|------|---------|
| MVP | ✅ 完成 | AI 问答 + 笔记管理 + 练习题生成 |
| V1.0 | 🚧 开发中 | MVP + 错题本 + 学习计划 + 文档上传 + 统计 + 作业批改 + RAG 知识库 |
| V2.0 | 📋 规划中 | 成就系统 + 社交功能（班级排行）+ 移动端 App |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/xxx`
3. 提交变更：`git commit -m 'feat: add xxx'`
4. 推送分支：`git push origin feature/xxx`
5. 提交 Pull Request

---

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">
Made with ❤️ for 中学生
</div>
