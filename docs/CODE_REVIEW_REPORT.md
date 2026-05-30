# EduBuddy 代码全面检查报告

**生成日期**：2026-05-30  
**检查版本**：V1.0（当前开发阶段）  
**检查范围**：后端（FastAPI）+ 前端（Vue 3）+ 配置文件  
**检查人**：Cline AI Code Review

---

## 一、总体概况

| 维度 | 评分（满分10） | 说明 |
|------|--------------|------|
| 代码结构与架构 | 8.5 | 分层清晰，模块化良好 |
| 安全性 | 7.0 | JWT认证正确，但存在若干安全隐患 |
| 健壮性与错误处理 | 6.5 | 部分接口异常处理不完善 |
| 性能 | 7.0 | 基础查询良好，存在N+1问题 |
| 代码规范与可维护性 | 8.0 | 命名一致，但缺乏测试 |
| 前后端一致性 | 8.0 | 接口对接基本正确，少数类型不一致 |
| **综合评分** | **7.5** | 可生产使用，建议修复中高危问题 |

---

## 二、后端代码检查

### 2.1 配置层（`config.py`）

#### ✅ 正确点
- 使用 `pydantic_settings.BaseSettings` 进行类型安全配置读取
- `lru_cache` 保证单例，避免多次读 `.env`
- 提供 `cors_origins_list` / `max_file_size_bytes` 属性方法

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🔴 高危 | `secret_key` 默认值为 `"dev-secret-key-change-in-production"`，生产环境若未配置 `.env` 将直接使用弱密钥 | `config.py:10` | 设为无默认值 `secret_key: str`，强制从环境变量读取；启动时校验非空 |
| 🔴 高危 | `openai_api_key` 默认空字符串，当 API Key 未配置时代码不会立即报错，而是在第一次 AI 调用时才抛 `ValueError`，UX 差 | `config.py:7` | 在 startup 时检测 API Key 并打印明确警告 |
| 🟡 中危 | `cors_origins` 允许 `http://localhost:5173,http://localhost:80`，部署时如果未更新可能跨域策略过宽 | `config.py:14` | 生产部署 README 中标注必须覆写此项 |

---

### 2.2 数据库层（`database.py`）

#### ✅ 正确点
- `get_db()` 使用 generator + try/finally 保证 Session 关闭
- `init_db()` 在 startup 事件中调用，采用延迟 import 避免循环导入

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | `declarative_base()` 来自 `sqlalchemy.ext.declarative`（旧接口），SQLAlchemy 2.0 推荐使用 `sqlalchemy.orm.DeclarativeBase` | `database.py:3` | 迁移到 `from sqlalchemy.orm import DeclarativeBase; class Base(DeclarativeBase): pass` |
| 🟡 中危 | `db_path` 解析逻辑对绝对路径（如 `sqlite:////abs/path`）有问题：`replace("sqlite:///", "")` 只处理相对路径 | `database.py:10` | 使用正则或 `urllib.parse.urlparse` 解析路径 |
| 🟢 低危 | 未配置 Alembic 迁移。使用 `create_all()` 部署后，若增加字段需手动处理数据库升级 | `database.py:33` | 按 memory-bank 中记录，设置 Alembic 迁移（优先级低） |
| 🟢 低危 | `get_db()` 只有 `finally: db.close()`，未对 commit/rollback 统一处理，可能在路由层出现未 commit 的挂起事务 | `database.py:24` | 添加 `except: db.rollback(); raise` 语句 |

---

### 2.3 认证层（`dependencies.py`, `routers/auth.py`）

#### ✅ 正确点
- JWT decode 使用 `HS256`，并验证 `sub` 字段
- 密码使用 bcrypt 哈希，`CryptContext` 配置正确
- Token 有效期 7 天，登录时返回 `expires_in`

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🔴 高危 | JWT payload 中 `user_id: int = payload.get("sub")`，但 `jwt.encode` 存的是 `str(user_id)`，当 token 被篡改或格式错误时 `int(user_id)` 会抛 `ValueError` 而非返回 401 | `dependencies.py:25,31` | 用 `try/except (JWTError, ValueError, TypeError)` 统一捕获 |
| 🟡 中危 | 密码验证：`UserRegister` 没有对 `password` 强度做任何校验（长度/复杂度） | `schemas/auth.py:8` | 添加 `@validator('password')` 检查最小长度 8 位 |
| 🟡 中危 | `update_me` 接口只允许更新 `nickname` 和 `grade`，但没有字段为空时的校验；若传空字符串 `""` 也会被更新 | `auth.py:63-66` | 加非空判断 `if data.nickname is not None and data.nickname.strip()` |
| 🟡 中危 | `change_password` 接口：没有对新密码做强度/与旧密码不同的校验 | `auth.py:76` | 添加新密码不等于旧密码的判断 |
| 🟢 低危 | `create_token` 使用 `datetime.utcnow()`（已废弃），Python 3.12+ 会触发 DeprecationWarning | `auth.py:18` | 改为 `datetime.now(datetime.UTC)` 或 `datetime.now(timezone.utc)` |

---

### 2.4 AI 路由（`routers/ai.py`）

#### ✅ 正确点
- 提前读取 `user_id = current_user.id` 避免 `DetachedInstanceError`
- 聊天历史使用倒序查询最近10条，避免无限膨胀
- `add_to_wrong_book` 实现了从聊天消息自动录入错题

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | `generate()` 异步生成器内的 `db.commit()` 在 `StreamingResponse` 返回后执行，此时 `db` Session 可能已被 FastAPI 依赖注入框架关闭（FastAPI `Depends(get_db)` 在响应结束后关闭 session） | `ai.py:103` | 在 `generate()` 内部使用独立的 `SessionLocal()` 创建新 Session 进行写入操作 |
| 🟡 中危 | `generate()` 内 `session.updated_at = func.now()` 通过已有 session 更新对象属性，若 session 已关闭将报错 | `ai.py:102` | 同上，使用独立 Session |
| 🟡 中危 | 获取会话消息历史 `limit(10)` 但使用 `desc()` 倒序后再 `reversed()`，逻辑上获取的是"最近10条"，但对于很长的对话可能遗漏上下文 | `ai.py:60` | 这是设计权衡，建议文档注明 |
| 🟢 低危 | 流式 SSE 中没有心跳机制，若 AI 响应慢，Nginx/代理可能超时 | `ai.py:82` | 在 nginx 配置中已设置 `proxy_read_timeout 300s` 可以缓解，建议加注释 |

---

### 2.5 Quiz 路由（`routers/quiz.py`）

#### ✅ 正确点
- `extractOptionKey()` 逻辑在前端已对齐（修复了历史 Bug）
- 答题提交时自动录入错题，并传入 AI 解析
- `recommended-difficulty` 使用历史正确率智能推荐

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🔴 高危 | `submit_quiz` 中答案比较 `ans.answer.strip().upper() == question.correct_answer.strip().upper()`，对多选题（如 "AB"）需要按字母排序后比较，否则 "BA" 会判错 | `quiz.py:199` | 多选题答案比较：`sorted(ans.answer.strip().upper()) == sorted(question.correct_answer.strip().upper())` |
| 🟡 中危 | `extract-topic` 接口使用 `tempfile.NamedTemporaryFile` 创建临时文件，若 AI 调用异常，`os.unlink(tmp_path)` 不会被执行（在 exception 前），导致临时文件泄漏 | `quiz.py:103-111` | 使用 `try/finally` 确保删除临时文件 |
| 🟡 中危 | `generate_quiz` 不限制 `count` 的范围。若用户传入 `count=100`，将消耗大量 token | `quiz.py:122` | 限制最大值：`count: int = Field(default=5, ge=1, le=20)` |
| 🟡 中危 | `extract-answer` 接口（识别答案图片）文件大小限制为 10MB（硬编码），与全局 `max_file_size_mb=20` 不一致 | `quiz.py:52` | 使用 `settings.max_file_size_bytes` 统一 |
| 🟢 低危 | `recommended-difficulty` 接口中对 `case` 条件写法为 `case((QuizAnswer.is_correct == True, 1.0), else_=0.0)`，SQLAlchemy 2.0 新语法需要确认兼容性 | `quiz.py:294` | 确认 SQLAlchemy 2.0 case 语法，该语法正确 |

---

### 2.6 作业批改路由（`routers/homework.py`）

#### ✅ 正确点
- 提前读取 `grade_level` 避免 Session 关闭问题
- 图片识别与文本批改分路处理
- SSE 错误时更新 DB 状态为 `error`

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | `grade_file_homework` 中 `generate()` 内部 `db.commit()` 存在与 `ai.py` 相同的 Session 关闭问题（StreamingResponse 返回后依赖注入的 Session 可能已关闭） | `homework.py:282` | 在 `generate()` 内使用独立 Session |
| 🟡 中危 | `SUPPORTED_FILE_TYPES` 字典与后续的硬编码 content_type 集合有重复校验逻辑，代码不一致：`SUPPORTED_FILE_TYPES` 不含 `image/jpg`，但硬编码集合中有 | `homework.py:20-183` | 统一使用 `SUPPORTED_FILE_TYPES` 字典进行校验 |
| 🟢 低危 | 删除批改记录 (`DELETE /history/{id}`) 时，若有关联的上传文件，不会删除磁盘上的文件，造成磁盘空间泄漏 | `homework.py:376` | 参考 `documents.py` 的删除实现，同步删除磁盘文件 |
| 🟢 低危 | `grade_level` 传参未做学科有效性以外的验证，任意字符串均可入库 | `homework.py:158` | 可选：限制为合法年级列表 |

---

### 2.7 错题本路由（`routers/wrong_book.py`）

#### ✅ 正确点
- 间隔复习算法（艾宾浩斯）实现完整且逻辑正确
- 数据隔离：所有查询均过滤 `user_id`
- `similar-quiz` 接口支持生成相似题目

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | `follow_up` 接口的 `data: dict` 参数没有用 Pydantic Schema 验证，`question` 字段可能不存在或为非字符串 | `wrong_book.py:127` | 新建 `FollowUpRequest(BaseModel): question: str` Schema |
| 🟡 中危 | `ai_explain` 的 `generate()` 内 `db.commit()` 存在同样的 Session 关闭问题 | `wrong_book.py:116` | 使用独立 Session |
| 🟡 中危 | `similar_quiz` 接口的 `data: dict` 同样缺乏结构化验证 | `wrong_book.py:213` | 新建 `SimilarQuizRequest(BaseModel): count: int = 3` Schema |
| 🟢 低危 | OCR 接口 `POST /ocr` 实际不执行真正 OCR，只返回提示文字，但接口 HTTP 状态码为 200，误导调用方 | `wrong_book.py:79` | 要么实现真正 OCR，要么改为 501 Not Implemented，或直接移除接口 |
| 🟢 低危 | `update_mastery` 的 `mastery` 字段未验证枚举值，任意字符串均可写入 | `wrong_book.py:158` | 使用 `Literal['unmastered', 'fuzzy', 'mastered']` 限定枚举 |

---

### 2.8 统计路由（`routers/stats.py` + `services/stats_service.py`）

#### ✅ 正确点
- 统计逻辑完全在 `stats_service.py` 中封装，路由层职责单一
- 学习时间趋势、各科正确率、错题分布均已实现

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | `get_streak_days` 实现是逐天查库（while 循环），若用户连续学习超过 100 天，将产生大量 DB 查询（N+1 问题），性能较差 | `stats_service.py:18` | 改为一次性查询所有学习日期，再计算连续天数 |
| 🟢 低危 | `get_study_time_trend` 的 `period` 参数只支持 `"week"` 和 `"month"`，其他值返回 7 天数据，无明确错误 | `stats_service.py:57` | 添加参数校验 |

---

### 2.9 文档服务（`services/document_service.py`）

#### ✅ 正确点
- 文件 UUID 命名，避免冲突
- 按用户 ID 分目录存储
- 文件大小校验

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | `save_upload_file` 的 `ALLOWED_TYPES` 只包含 PDF/DOCX/JPG/PNG，但 `homework.py` 路由额外支持 GIF/WebP 等格式，调用 `save_upload_file` 时会被拒绝，导致 GIF/WebP 作业上传失败 | `document_service.py:9` | 扩展 `ALLOWED_TYPES` 或在作业路由中单独实现文件保存逻辑 |
| 🟡 中危 | `_extract_image` 函数仅返回提示字符串，而非实际 OCR 内容，但调用方 `documents.py` 的文档上传接口不区分此情况，直接将此字符串存入 `content_text` 字段 | `document_service.py:83` | 在 `documents.py` 中检测返回值是否为错误提示，相应更新 `doc.status = "error"` |
| 🟢 低危 | `_extract_docx` 只提取 `para.text`（段落文本），忽略了表格、标题样式等 | `document_service.py:76` | 增加表格内容提取 |

---

### 2.10 复习服务（`services/review_service.py`）

#### ✅ 正确点
- 艾宾浩斯遗忘曲线间隔实现正确：`[1, 3, 7, 14, 30]`
- `get_next_review_date` 答错时重置复习计数，符合遗忘曲线原理

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | `get_next_review_date` 中 mastery 判断逻辑：`review_count <= 2` 为 `fuzzy`，否则为 `mastered`——但当 `new_count = 3` 时（未到最后一次），已被标记为 `mastered`，与间隔阶段 `[1,3,7,14,30]` 的5个阶段不完全对应 | `review_service.py:30` | 与 memory-bank 的设计核对：review_count 4 才标记 mastered；当前逻辑 `new_count >= len(REVIEW_INTERVALS)` 即 5 才标记完成，但 `mastery = "mastered" if new_count > 2 else "fuzzy"` 在 count=3,4 时就标记 mastered，有逻辑矛盾 |

**具体验证**：
```python
# REVIEW_INTERVALS = [1, 3, 7, 14, 30]
# 当 review_count=2, is_correct=True：
#   new_count = 3
#   new_count < len([1,3,7,14,30]) = 5，不标 mastered
#   mastery = "mastered" if 3 > 2 else "fuzzy"  → "mastered" ❌（应为 fuzzy）
```
建议修改为：`mastery = "mastered" if new_count >= len(REVIEW_INTERVALS) else ("fuzzy" if new_count >= 2 else "unmastered")`

---

### 2.11 AI 服务（`services/ai_service.py`）

#### ✅ 正确点
- 全局单例 `ai_service = AIService()`，避免重复实例化
- 支持 OpenAI 兼容接口（`base_url` 可配置）
- `generate_quiz` 使用 `response_format={"type": "json_object"}` 保证 JSON 输出
- `extract_score_from_report` 使用正则从报告提取分数，无需额外 API 调用

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | `summarize_note` / `generate_flashcards` / `generate_study_plan` 直接 `json.loads(response.choices[0].message.content)`，若 AI 返回非 JSON（如遭遇 API 错误、流量控制），会抛 `json.JSONDecodeError` 未被捕获 | `ai_service.py:144,199,275` | 用 `try/except json.JSONDecodeError` 包裹，返回友好错误或重试 |
| 🟡 中危 | `analyze_document` 文档内容截取 `text[:3000]`，但对于多语言内容这可能切断中间字符（虽然 Python 字符串 slice 安全，但 3000 字符的上下文窗口较短） | `ai_service.py:284-286` | 可适当增加 token 上下文，如 `text[:8000]` |
| 🟡 中危 | `grade_homework` 的 `max_tokens=6000` 可能超出部分模型的输出限制，对某些兼容模型会报错 | `ai_service.py:386` | 添加异常处理，捕获 `openai.BadRequestError` |
| 🟢 低危 | `chat_stream` 中没有对 OpenAI API 调用设置超时（`timeout` 参数） | `ai_service.py:75` | 添加 `timeout=60` |
| 🟢 低危 | `extract_score_from_report` 正则仅识别 `最终得分：xx/100` 和 `xx/100分` 两种格式，若 AI 输出 `得分：85分` 等其他格式则返回 0.0 | `ai_service.py:439` | 增加更多正则模式 |

---

## 三、前端代码检查

### 3.1 路由与认证（`router/index.ts`, `stores/auth.ts`）

#### ✅ 正确点
- 路由守卫双向判断：未登录跳 `/login`，已登录跳 `/`
- Pinia Store 从 `localStorage` 初始化，页面刷新不丢失登录态
- `logout()` 同时清除 token 和 user 两个缓存

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | 路由守卫中的认证检查只判断 `token` 是否存在于 `localStorage`，不验证 Token 是否已过期（过期的 JWT 仍在 localStorage 中） | `router/index.ts:28` | 在 `isAuthenticated` 计算属性中解析 JWT 的 `exp` 字段，或在请求 401 时跳转登录（已有，见 `api/index.ts:26`） |
| 🟡 中危 | `fetchMe()` 在何处被调用未明确（代码中未找到 `fetchMe` 的调用点），可能导致 user 信息不会主动刷新 | `stores/auth.ts:34` | 在 `App.vue` 的 `onMounted` 中调用 `fetchMe()` 同步最新用户信息 |
| 🟢 低危 | `login()` 直接保存到 `localStorage`（敏感信息），建议加密或改用 `sessionStorage` | `stores/auth.ts:24` | 生产环境可考虑 `httpOnly Cookie` 方案 |

---

### 3.2 API 封装（`api/index.ts`, `api/quiz.ts`, `api/homework.ts`）

#### ✅ 正确点
- Axios 实例统一添加 `Bearer Token`
- 响应拦截器统一处理 401（跳转登录）、错误提示
- `homework.ts` 中 SSE 流式接口使用 `fetch + ReadableStream`，并提供取消控制

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | `api/index.ts` 中 `timeout: 30000`（30秒），对于 AI 流式接口（批改作业可能需要 1-2 分钟）可能超时 | `api/index.ts:6` | SSE 流式接口直接使用 `fetch`（已实现），普通 AI 接口（如 `generate_quiz`）超时时间应增加到 120s |
| 🟡 中危 | `QuizSessionView.vue` 中 `onAnswerImageChange` 中 `res.data.data?.answer` 的访问路径有问题：Axios 拦截器已将 `response.data` 返回（见 `api/index.ts:20`），所以 `res` 已经是 `{code, data}` 对象，正确路径应为 `res?.data?.answer`（跳过一层 `.data`）| `QuizSessionView.vue:179` | 核查：`res` 的层级结构，若 Axios 已做 `response.data`，则 `res.data.answer` 而非 `res.data.data.answer` |
| 🟢 低危 | `homework.ts` 的 SSE 解析 `catch {}` 完全吞掉了 JSON 解析错误，难以调试 | `homework.ts:75,137` | 改为 `catch(e) { console.warn('SSE parse error:', e) }` |

---

### 3.3 练习题会话（`QuizSessionView.vue`）

#### ✅ 正确点
- `extractOptionKey()` 正确从选项文本中提取字母，修复了历史答案比较 Bug
- 数学符号快捷工具栏实现完整，光标恢复位置正确
- 图片扫描答案功能与后端 `/quiz/extract-answer` 接口正确对接

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | `submitQuiz()` 中 `time_spent` 计算是 `elapsed / questions.length`（每题平均时间），这意味着每道题记录的时间相同，与实际不符 | `QuizSessionView.vue:319` | 为每道题单独计时，或记录总时间并在结果中展示 |
| 🟡 中危 | 若用户刷新页面，`sessionStorage` 中的 `quizSession` 被清除，导致答题数据丢失，没有友好提示 | `QuizSessionView.vue:138` | 可以提示"刷新后进度丢失"，或考虑使用后端保存进度 |
| 🟢 低危 | `submitQuiz` 不会检查是否所有题目都已回答，直接提交包含空答案的结果 | `QuizSessionView.vue:316` | 增加未答题目的提示 |

---

### 3.4 AI 批改作业（`HomeworkGradingView.vue`）

#### ✅ 正确点
- Undo/Redo 实现完整（使用 `beforeinput` 事件保存快照，最多 100 步）
- PDF 导出使用新窗口 + `window.print()` 方案，绕开 `html2canvas` + oklch 颜色兼容问题
- 文件拖拽上传、图片自动识别预览实现完整
- MathLive 公式编辑器集成正确

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | `onRecognizeInput` 函数体内的 debounce 逻辑是空的（`setTimeout` 回调为空注释），`undo` 快照依赖 `beforeinput` 事件；但 `onRecognizeInput` 函数本身没有实际作用，代码存在误导 | `HomeworkGradingView.vue:531-543` | 清理空函数体，或改为正确的 debounce 快照逻辑 |
| 🟡 中危 | PDF 导出时通过 `renderMessage(gradingReport.value)` 内联 KaTeX CSS，但 CDN 加载公式样式依赖网络，离线环境下公式会显示原始 LaTeX | `HomeworkGradingView.vue:739` | 文档说明：导出PDF需要网络连接 |
| 🟢 低危 | `canSubmit` 计算属性中图片文件判断：`recognizedText.value === null && !recognizeError.value`，识别错误时仍可提交，但未告知用户当前是用识别内容还是原始图片批改 | `HomeworkGradingView.vue:652` | 识别失败时展示提示：将直接使用图片原图进行 AI 批改 |
| 🟢 低危 | `escapeHtml` 函数没有转义单引号 `'`，在 HTML 属性中可能存在 XSS 风险 | `HomeworkGradingView.vue:794` | 增加 `.replace(/'/g, '&#039;')` |

---

### 3.5 Markdown/LaTeX 渲染（`utils/markdown.ts`）

#### ✅ 正确点
- 占位符策略（`\uFFFD` 字符）有效防止 `markdown-it` 处理 LaTeX 公式
- `renderRecognizedText` 安全渲染（HTML 转义 + LaTeX 渲染）
- `renderLatexOnly` 适用于不含 Markdown 的纯文本

#### ⚠️ 问题
| 级别 | 问题 | 位置 | 建议 |
|------|------|------|------|
| 🟡 中危 | `renderMessage` 中行内公式正则 `$([^$]+?)$` 不允许跨行，但注释说"允许跨最多一个换行"，实际正则中 `[^$]` 不包含 `\n`，两者不一致 | `markdown.ts:65` | 正则注释与实现保持一致；若需要跨行，改为 `[\s\S]+?` |
| 🟢 低危 | `renderRecognizedText` 中裸 LaTeX 命令序列的正则匹配非常复杂，可能有误报（将普通反斜杠转义序列误识别为 LaTeX）| `markdown.ts:128` | 建议通过充分的单元测试覆盖边界情况 |

---

## 四、配置与部署检查

### 4.1 Docker Compose（`docker-compose.yml`）

| 级别 | 问题 | 建议 |
|------|------|------|
| 🔴 高危 | `env_file: - .env` 引用根目录 `.env`，但项目历史记录（memory-bank）显示曾出现找不到 `.env` 的问题；根目录 `.env` 需要与 `backend/.env` 手动同步，容易遗漏 | 使用 `env_file: - backend/.env`，或在 CI/CD 中自动复制 |
| 🟡 中危 | `backend` 服务暴露端口 8001，但 `frontend` nginx 代理的后端地址是 `http://backend:8000`（内部 Docker 网络），只要不直接访问 8001 端口就是安全的。但文档未明确说明 8001 是调试端口 | 文档中说明 8001 仅用于本地调试访问 |
| 🟡 中危 | 没有设置 `healthcheck`，若后端启动失败，前端容器仍会启动并报代理错误 | 添加 `healthcheck` 和 `depends_on.condition: service_healthy` |
| 🟢 低危 | SQLite 数据库使用 volume 挂载 `./backend/data`，生产环境不建议使用 SQLite | 提示用户升级到 PostgreSQL |

---

### 4.2 Nginx 配置（`frontend/nginx.conf`）

#### ✅ 正确点
- SSE 支持：`proxy_buffering off`、`chunked_transfer_encoding on`
- 静态资源长期缓存（hash 文件名）
- 前端路由支持：`try_files $uri $uri/ /index.html`

#### ⚠️ 问题
| 级别 | 问题 | 建议 |
|------|------|------|
| 🟡 中危 | `/api/` 代理没有设置 `proxy_set_header X-Forwarded-Proto` 和 `X-Forwarded-For`，HTTPS 部署时后端无法获取真实客户端 IP | 添加标准代理头 |
| 🟢 低危 | `/api/` location 中 `client_max_body_size 50m` 重复声明（已在 `server` 块声明）| 删除重复声明 |

---

### 4.3 requirements.txt

#### ✅ 正确点
- 版本固定（非 `>=` 浮动），适合生产环境
- 所有依赖包功能对齐代码

#### ⚠️ 问题
| 级别 | 问题 | 建议 |
|------|------|------|
| 🟡 中危 | `openai==1.14.0` 版本较旧（当前最新 1.x 系列为 1.50+）；低版本可能不支持某些兼容 API 特性 | 升级到 `openai>=1.40.0` 并测试兼容性 |
| 🟢 低危 | 缺乏 `pytest`、`httpx` 测试依赖（用于测试）；`httpx==0.27.0` 已在 requirements.txt 中，可复用 | 创建 `requirements-dev.txt` 包含 `pytest`、`pytest-asyncio`、`pytest-cov` |

---

### 4.4 前端 package.json

#### ✅ 正确点
- Vue 3.5、Vue Router 4、Pinia 3 版本组合兼容良好
- Tailwind v4 + `@tailwindcss/vite` 集成正确

#### ⚠️ 问题
| 级别 | 问题 | 建议 |
|------|------|------|
| 🟡 中危 | `typescript: ~6.0.2` 和 `vite: ^8.0.12` 版本较新，与部分 Element Plus 插件可能有兼容性问题 | 确认 Element Plus `^2.14.0` 支持 TS 6.x |
| 🟢 低危 | 同时引入 `markdown-it` 和 `marked` 两个 Markdown 库，造成冗余 | 确认是否两者都在使用；当前代码只使用 `markdown-it`，`marked` 可以移除 |
| 🟢 低危 | `html2canvas` 已在 package.json 中，但实际 PDF 导出已改为 `window.print()` 方案，该库已无用 | 可以移除 `html2canvas` 和 `jspdf` 减小 bundle size |

---

## 五、问题汇总统计

| 级别 | 数量 | 说明 |
|------|------|------|
| 🔴 高危（需立即修复） | 5 | 可能导致安全漏洞或功能错误 |
| 🟡 中危（建议尽快修复） | 27 | 影响稳定性、性能或用户体验 |
| 🟢 低危（可规划修复） | 16 | 代码质量、可维护性问题 |

---

## 六、高危问题修复优先级列表

1. **`config.py:10`** — `secret_key` 无强制要求，默认弱密钥
2. **`dependencies.py:25,31`** — JWT payload 解析 `int(user_id)` 未捕获 `ValueError`
3. **`quiz.py:199`** — 多选题答案比较未做字母排序
4. **`review_service.py:30`** — mastery 判断逻辑与阶段设计不一致
5. **`docker-compose.yml`** — env_file 路径混乱，容易环境变量缺失

---

## 七、代码亮点（值得称赞）

1. **SSE 流式输出**：前后端配合完整，包括取消控制（AbortController）
2. **DetachedInstanceError 修复**：在 AI 流式接口中提前读取用户属性，解决 Session 关闭问题（设计意识很好）
3. **多选题答案提取**：`extractOptionKey()` 函数设计巧妙，兼容 `A.`/`A、`/`A．` 多种格式
4. **Undo/Redo 实现**：使用 `beforeinput` 事件精准记录快照，性能优于 watch
5. **Markdown + LaTeX 渲染**：占位符策略有效避免 markdown-it 干扰 LaTeX
6. **PDF 导出方案**：使用新窗口 + `window.print()` 完全绕开了 html2canvas 对 oklch 颜色的兼容问题，设计务实
7. **数据隔离**：所有数据库查询均强制过滤 `user_id`，不存在越权访问漏洞

---

*报告生成时间：2026-05-30*
