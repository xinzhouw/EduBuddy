# EduBuddy 代码整理与功能测试报告

**测试日期**：2026-06-04
**测试范围**：代码清理、后端 API 全功能、前端构建
**测试环境**：Python 3.12 / FastAPI 0.110 / Vue 3 + Vite / SQLite

---

## 一、代码整理（清理冗余）

### 1.1 删除的冗余文件

| 文件 | 原因 |
|------|------|
| `frontend/src/components/HelloWorld.vue` | Vite 脚手架残留组件，无任何引用 |
| `frontend/src/assets/hero.png` / `vue.svg` / `vite.svg` | 仅被 HelloWorld 使用 |
| `frontend/public/icons.svg` | 脚手架残留 |
| `backend/app/services/image_search_service.py` | 后端图片搜索服务，已被前端 `utils/imageSearch.ts`（浏览器直连 Wikimedia）取代，无前端调用 |
| `agents/textbook_crawler/download_pdfs.py` | README 标注的旧版下载脚本，已被 `download_all_hs.py` 取代 |
| `agents/textbook_crawler/parse_local_pdfs.py` | 旧版解析脚本，已被 `build_knowledge_base.py` 取代 |
| `agents/textbook_crawler/config.py` / `fetch_cdn.py` | 旧版配置/抓取脚本，不再使用 |
| `agents/textbook_crawler/crawler.log` / `cookies.json` | 运行时产物/无用凭证 |
| `agents/textbook_crawler/__pycache__/` | Python 缓存 |
| `backend/.venv/`（空虚拟环境） | 与有效的 `backend/venv/` 重复，无依赖 |

### 1.2 删除的冗余代码逻辑

| 位置 | 内容 | 原因 |
|------|------|------|
| `backend/app/routers/ai.py` | `GET /api/ai/search-images` 端点 | 无前端调用，前端改用浏览器直连 |
| `backend/app/routers/wrong_book.py` | `POST /api/wrong-book/ocr` 占位端点 | 返回假提示文字，已被 `quiz/extract-answer`（真实 Vision OCR）取代 |
| `frontend/src/api/ai.ts` | `searchImages()` 方法、空函数 `createChatStream()` | 无调用/返回 null 的死代码 |

### 1.3 代码现代化重构

| 文件 | 改动 |
|------|------|
| `backend/app/main.py` | 将已弃用的 `@app.on_event("startup")` 升级为 FastAPI 推荐的 `lifespan` 上下文管理器 |
| `backend/requirements.txt` | 移除未使用的 `alembic`（项目用 `init_db()` 建表）、移除已停止维护且有 bug 的 `passlib`，更新 `bcrypt>=4.0.1` |
| `agents/textbook_crawler/README.md` | 同步移除已删除脚本的目录说明 |

---

## 二、缺陷修复

### 🔴 严重 Bug：注册/登录全部 500 失败（已修复）

- **现象**：`POST /api/auth/register`、`/login` 返回 500 Internal Server Error，无法注册或登录。
- **根因**：实际安装的 `bcrypt 5.0.0` 与 `passlib 1.7.4` 不兼容。passlib 初始化 bcrypt 后端时执行 `detect_wrap_bug` 检测，传入超长密码触发 `ValueError: password cannot be longer than 72 bytes`。passlib 已停止维护，无法兼容 bcrypt 4.x/5.x。
- **修复**：新增 `backend/app/security.py`，直接使用 `bcrypt` 库实现 `hash_password()` / `verify_password()`（含 72 字节截断保护），`auth.py` 改用该模块，彻底移除 passlib 依赖。
- **验证**：注册/登录/改密/新密码登录全部通过（见 3.1）。

### 🟡 兼容性增强：temperature 参数导致部分模型网关 400（已修复）

- **现象**：当 `OPENAI_MODEL` 配置为 Claude/Bedrock 类模型（经 litellm 网关）时，所有 AI 调用返回 400 `temperature is deprecated for this model`。
- **根因**：`ai_service.py` 硬编码 `temperature` 参数，部分模型网关不接受。
- **修复**：新增配置项 `OPENAI_USE_TEMPERATURE`（默认 `true`，兼容标准 OpenAI）；`AIService` 新增 `_temp()` 辅助方法，按配置决定是否携带 temperature；13 处 AI 调用全部改用 `**self._temp(x)`。
- **验证**：设为 `false` 后，AI 问答/出题/总结/计划/批改全部正常（见 3.2）。

---

## 三、功能测试结果

后端在测试端口启动，逐接口验证。✅ 通过 / ❌ 失败

### 3.1 用户认证模块（无需 AI）

| 用例 | 预期 | 结果 |
|------|------|------|
| 注册新用户 | 200 + 用户信息 | ✅ |
| 重复邮箱注册 | 400 | ✅ |
| 错误密码登录 | 401 | ✅ |
| 正确登录获取 Token | 200 + JWT | ✅ |
| 携带 Token 获取个人信息 | 200 | ✅ |
| 无 Token 访问受保护接口 | 403 | ✅ |
| 更新昵称/年级 | 200 | ✅ |
| 修改密码 | 200 | ✅ |
| 新密码登录 | 200 | ✅ |

### 3.2 业务 CRUD 模块（无需 AI）

| 模块 | 用例 | 结果 |
|------|------|------|
| 笔记 | 创建/列表/详情/更新 | ✅ |
| 知识卡片 | 手动创建/列表 | ✅ |
| 错题本 | 手动录入/列表（含 today_due 统计） | ✅ |
| 错题本 | 复习算法（答对：1→3 天间隔，mastery=fuzzy） | ✅ |
| 错题本 | 复习算法（答错：重置回明天，review_count=0） | ✅ |
| 错题本 | 更新掌握度/删除 | ✅ |
| 学习统计 | overview/study-log/study-time 趋势/正确率/错题分布 | ✅ |
| 学习计划 | today/current（无计划返回空）/番茄钟记录 | ✅ |
| RAG 知识库 | 状态查询（未构建时优雅降级 available=false，不影响其他功能） | ✅ |

### 3.3 AI 功能模块（需 OpenAI 兼容接口）

| 模块 | 用例 | 结果 |
|------|------|------|
| AI 问答 | SSE 流式输出（content/done 事件）+ 会话消息持久化 | ✅ |
| AI 问答 | 消息点赞/点踩反馈、删除会话 | ✅ |
| 练习题生成 | AI 生成带 LaTeX 的单选题（JSON 格式） | ✅ |
| 练习题答题 | 提交判分（accuracy 计算）+ 错题自动录入错题本 | ✅ |
| 练习题 | 自适应推荐难度（0% 正确率 → 推荐基础难度） | ✅ |
| 笔记 | AI 总结（summary + key_points） | ✅ |
| 学习计划 | AI 生成按天任务（6 天计划生成 6 天任务） | ✅ |
| AI 批改作业 | 文本作业 SSE 流式批改 + 分数正则提取（错误答案得 13 分）+ 历史保存 | ✅ |

### 3.4 前端构建与类型检查

| 用例 | 结果 |
|------|------|
| `vue-tsc --noEmit` 类型检查 | ✅ 退出码 0，无错误 |
| `npm run build` 生产构建 | ✅ `built in 4.82s`，退出码 0 |

> 构建中出现的 `@vueuse/core` `/* #__PURE__ */` 注解警告为第三方库的无害提示，不影响产物。

---

## 四、路由完整性核对

清理后后端共注册 **52 个 API 路径**，确认 `/api/ai/search-images` 和 `/api/wrong-book/ocr` 已移除，其余功能路由（auth/ai/notes/quiz/wrong-book/plan/documents/stats/homework/flashcards）齐全。

---

## 五、结论

- **代码整理**：删除 11 个冗余文件 + 3 处死代码，代码库更精简清晰；完成 1 项现代化重构。
- **缺陷修复**：修复 1 个阻断性 Bug（认证 500）+ 1 个跨模型兼容性问题（temperature）。
- **功能测试**：认证、所有业务 CRUD、全部 AI 功能、前端构建 **全部通过**。
- **当前状态**：项目可正常启动、前后端可联调、生产可构建，处于健康可用状态。

### 遗留建议（非阻断）

1. `document_service._extract_image()` 仍返回占位文字，图片文档的 OCR 实际由各业务的 Vision API 完成，建议后续统一。
2. `HomeworkGrading` 模型有未使用字段（`score_breakdown`/`overall_comment` 等），可在确认无需后清理。
3. 前端打包产物单 chunk > 500KB，建议后续按路由做代码分割（dynamic import）。
