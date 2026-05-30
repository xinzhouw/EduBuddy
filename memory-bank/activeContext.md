# EduBuddy 活跃上下文

## 当前工作焦点
**日期**：2026-05-30  
**阶段**：V1.0 开发阶段 — 新增 PDF 导出 & Undo/Redo 功能

## 最近完成的工作
- **新增题目练习扫描图片/文档输入功能**：
  - **背景**：当题目中含有复杂公式时，手动输入知识点非常困难
  - **后端 `backend/app/services/ai_service.py`**：
    - 新增 `extract_quiz_topic_from_image(image_base64, mime_type)` 方法：将图片 base64 传给 OpenAI Vision API，返回学科、知识点、识别文字、题目数量（JSON）
    - 新增 `extract_quiz_topic_from_pdf(text)` 方法：对 PDF/DOCX 提取的文字调用 AI 分析，返回相同结构
  - **后端 `backend/app/routers/quiz.py`**：
    - 新增 `POST /api/quiz/extract-topic` 接口（`UploadFile`），接受 JPG/PNG/GIF/WebP/PDF/DOCX
    - 图片直接 base64 编码调用 Vision API；PDF/DOCX 先用 `extract_text()` 提取文字再调用 AI
    - 返回 `{ subject, topic, recognized_text, question_count }`
  - **前端 `frontend/src/api/quiz.ts`**：新增 `extractTopicFromFile(file)` 方法（multipart/form-data）
  - **前端 `frontend/src/views/quiz/QuizSetupView.vue`**：
    - 在表单顶部增加「扫描图片/文档」拖拽上传区域
    - 支持点击选择文件和拖拽放入，有识别中动画
    - 识别成功后展示识别到的题目文字、学科、知识点，并自动填入下方表单
    - 支持「重新上传」和「应用到表单」操作

- **修复练习题评判错误 + 新增数学符号输入工具栏**（`frontend/src/views/quiz/QuizSessionView.vue`）：
  - **Bug1 根因**：`selectAnswer()` 原来将完整选项文本（如 `"B. π"`）存入 `answers`，但后端 `correct_answer` 只存字母 `"B"`，导致字符串比较永远不等而判错。
  - **修复**：新增 `extractOptionKey(opt)` 函数，用正则从 `"A. xxx"` / `"A、xxx"` 格式中提取字母；`selectAnswer`、`toggleMultiAnswer`、`isMultiSelected` 及选项高亮 `:class` 均改用此函数，保证前后端答案格式一致。
  - **Bug2 根因**：填空/简答题只有普通 textarea，无法输入数学符号（π、√、²、≥ 等）。
  - **修复**：在 textarea 上方增加「数学符号快捷输入工具栏」，包含 20 个常用符号按钮；点击时通过 `selectionStart/End` 将符号插入光标处，并恢复光标位置。

- **新增 AI 批改作业功能**：
  - 新增数据模型 `backend/app/models/homework.py`（`HomeworkGrading` 表）
  - 在 `backend/app/services/ai_service.py` 新增 `grade_homework()`（流式批改）和 `extract_score_from_report()`（正则提取分数）方法
  - 新增后端路由 `backend/app/routers/homework.py`：
    - `POST /api/homework/grade/text`：文本作业批改（SSE 流式）
    - `POST /api/homework/grade/file`：文件上传批改（PDF/DOCX/图片，SSE 流式）
    - `GET /api/homework/history`：批改历史列表
    - `GET /api/homework/history/{id}`：批改详情
    - `DELETE /api/homework/history/{id}`：删除记录
  - 注册路由到 `backend/app/main.py`，更新 `backend/app/database.py` init_db
  - 前端新增 `frontend/src/api/homework.ts`（REST API + SSE 流式工具函数）
  - 前端新增 `frontend/src/views/homework/HomeworkGradingView.vue`（完整提交+批改报告UI）
  - 前端路由 `/homework` 已注册，侧边栏已添加「✍️ AI 批改作业」入口

- **修复 AI 聊天界面题目显示与 AI 回答格式问题**：
  - 前端安装 `markdown-it`、`@types/markdown-it`、`katex`、`@vscode/markdown-it-katex` 依赖
  - 新建 `frontend/src/utils/markdown.ts`：封装 `renderMessage()` 函数，支持 Markdown + LaTeX（行内 `$...$`、独立块 `$$...$$`）渲染
  - 修改 `frontend/src/views/ai/AIChatView.vue`：
    - AI 回复消息改用 `v-html="renderMessage(msg.content)"` 富文本渲染（原为纯文本 `{{ msg.content }}`）
    - 添加完整的 `.markdown-body` CSS 样式（段落、标题、列表、代码块、引用、KaTeX 公式等）
    - 用户消息保持纯文本 `whitespace-pre-wrap` 显示
  - 修改 `backend/app/services/ai_service.py` 的 `SYSTEM_PROMPT`：
    - 要求 AI 使用 Markdown 格式输出（标题 `##`、加粗、列表）
    - 要求所有数学公式使用 LaTeX 语法（行内 `$...$`、块级 `$$...$$`）
    - 将原【】括号式纯文本结构改为 Markdown 标题结构

## 最近完成的工作（历史）
- 初始化 Memory Bank，创建所有 6 个核心文档文件
- 全面梳理了项目文档（PRD、架构、数据库设计）
- 确认了项目基础架构已搭建完成（前后端脚手架、所有文件骨架）
- **新增 OpenAI 兼容模式支持**：
  - `backend/app/config.py` 新增 `openai_base_url`、`openai_model` 两个配置项
  - `backend/app/services/ai_service.py` 初始化时按需传入 `base_url`，所有 API 调用改用 `self.model`（不再硬编码 `gpt-4o`）
  - `.env` 与 `backend/.env.example` 增加 `OPENAI_BASE_URL`、`OPENAI_MODEL` 示例配置
- **修复 Tailwind CSS v4 样式不生效问题**：
  - 安装 `@tailwindcss/vite` 插件并配置到 `vite.config.ts`
  - 将 `src/style.css` 从 v3 语法（`@tailwind base/components/utilities`）改为 v4 语法（`@import "tailwindcss"`）
  - 将 `tailwind.config.js` 的自定义主题迁移为 `@theme {}` 块写入 CSS
  - 在 `AppSidebar.vue` 和 `DashboardView.vue` 的 `<style scoped>` 块开头加 `@reference` 指令
- **修复 AI 聊天接口 DetachedInstanceError**：
  - `backend/app/routers/ai.py` 的 `chat()` 中，`StreamingResponse` 返回后 SQLAlchemy Session 已关闭
  - 在 `generate()` 调用前提前读取 `user_id = current_user.id` 和 `user_grade = current_user.grade`
  - `generate()` 内部改用这两个局部变量，不再访问 `current_user` 对象
- **修复 docker-compose 找不到根目录 .env 的问题**：
  - `docker-compose.yml` 的 `env_file` 引用了根目录 `.env`，但配置实际在 `backend/.env`
  - 将 `backend/.env` 复制到项目根目录 `.env`

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
