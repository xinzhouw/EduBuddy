# EduBuddy 详尽测试计划书

**文档版本**：V1.0  
**创建日期**：2026-05-30  
**产品版本**：EduBuddy V1.0  
**测试类型**：功能测试 / 接口测试 / 安全测试 / 性能测试 / 兼容性测试  

---

## 一、测试目标与范围

### 1.1 测试目标

1. 验证所有功能模块符合 PRD 需求规格
2. 确保前后端接口数据契约正确
3. 识别潜在的安全漏洞并验证修复效果
4. 验证代码检查报告中发现的缺陷
5. 保证系统在正常与异常场景下的稳定性

### 1.2 测试范围

| 模块 | 范围 | 优先级 |
|------|------|--------|
| 用户认证（注册/登录/Token） | 全部接口 + 前端交互 | P0（最高） |
| AI 问答（SSE 流式） | 核心流程 + 异常 | P0 |
| 练习题生成与评判 | 全部题型 + 多选题排序Bug | P0 |
| 错题本（增删查/复习算法） | 复习逻辑重点验证 | P0 |
| AI 批改作业 | 文本+文件+图片 | P1 |
| 笔记管理 + 知识卡片 | CRUD + AI总结 | P1 |
| 学习计划 + 番茄钟 | 生成+任务完成 | P1 |
| 文档上传与分析 | 上传+AI分析+删除 | P1 |
| 学习统计 | 各维度数据正确性 | P2 |
| 配置与部署 | Docker 环境验证 | P2 |

### 1.3 不在测试范围内
- V2.0 功能（成就系统、社交功能、移动端）
- 第三方 AI 服务（OpenAI API）的稳定性
- 大规模并发（>100 并发用户）

---

## 二、测试环境要求

### 2.1 后端测试环境
```
操作系统：Ubuntu 22.04 / macOS 14
Python：3.10+
依赖：按 requirements.txt 安装
数据库：SQLite（测试专用库 test_edubuddy.db）
AI 服务：OpenAI API（需配置有效 Key）或 Mock
测试框架：pytest + pytest-asyncio + httpx
```

### 2.2 前端测试环境
```
Node.js：18+
浏览器：Chrome 120+ / Firefox 120+ / Safari 17+
移动端：iOS Safari 16+ / Chrome Android
屏幕分辨率：1280x800 / 1920x1080 / 375x812（移动端）
```

### 2.3 集成测试环境
```
Docker Compose 部署（模拟生产）
前端地址：http://localhost:80
后端地址：http://localhost:8001
数据库：SQLite volume 挂载
```

### 2.4 测试数据准备
- 测试用户账号：至少 3 个（普通用户 × 2、边界测试用户 × 1）
- 测试文件：PDF（含中文/公式）、DOCX（含表格）、JPG（手写数学题）、PNG（打印题目）
- 测试作业内容：含 LaTeX 公式的数学作业文本

---

## 三、功能测试用例

### 模块 1：用户认证

#### TC-AUTH-001：正常注册
- **前置条件**：邮箱未注册
- **输入**：`email=test@edubuddy.com, password=Test123456, nickname=测试用户, grade=高一`
- **操作步骤**：
  1. POST `/api/auth/register` 发送注册请求
  2. 检查响应
- **预期结果**：`HTTP 200, {"code": 200, "message": "注册成功", "data": {"id": ..., "email": "test@edubuddy.com", "nickname": "测试用户", "grade": "高一"}}`
- **验证点**：数据库中用户记录已创建，密码为 bcrypt 哈希值（非明文）

#### TC-AUTH-002：重复邮箱注册
- **输入**：已注册的邮箱
- **预期结果**：`HTTP 400, {"detail": "该邮箱已被注册"}`

#### TC-AUTH-003：正常登录
- **前置条件**：TC-AUTH-001 注册成功
- **输入**：`email=test@edubuddy.com, password=Test123456`
- **预期结果**：
  ```json
  {
    "code": 200,
    "data": {
      "access_token": "eyJ...",
      "token_type": "bearer",
      "expires_in": 604800,
      "user": {"id": 1, ...}
    }
  }
  ```
- **验证点**：JWT Token 有效、`expires_in = 7 * 86400 = 604800`

#### TC-AUTH-004：密码错误登录
- **输入**：正确邮箱 + 错误密码
- **预期结果**：`HTTP 401, {"detail": "邮箱或密码错误"}`

#### TC-AUTH-005：过期/无效 Token 访问受保护接口
- **输入**：伪造 Token `Authorization: Bearer invalid_token`
- **预期结果**：`HTTP 401, {"detail": "Token无效或已过期"}`

#### TC-AUTH-006：Token 中 user_id 为非数字字符串（安全测试）
- **目标**：验证代码检查报告中发现的 `int(user_id)` ValueError 问题
- **操作**：构造 JWT payload `{"sub": "not-a-number", "exp": ...}` 并发送
- **预期结果**：返回 `HTTP 401`，而非 `HTTP 500`

#### TC-AUTH-007：修改密码
- **输入**：`old_password=Test123456, new_password=NewPass789`
- **预期结果**：`HTTP 200, {"code": 200, "message": "密码修改成功"}`
- **后置验证**：使用新密码可以正常登录

#### TC-AUTH-008：更新用户信息（空字段测试）
- **输入**：`nickname=""` （空字符串）
- **预期结果**：应不更新 nickname（当前版本会更新为空，记录为已知 Bug）

#### TC-AUTH-009：前端登录交互
- **操作**：打开 `/login`，输入正确用户名密码，点击登录
- **预期结果**：跳转到 `/`（Dashboard），侧边栏显示用户 nickname 和 grade
- **验证点**：`localStorage` 中存在 `token` 和 `user` 键

#### TC-AUTH-010：前端登出
- **操作**：侧边栏底部悬浮退出按钮，点击退出
- **预期结果**：跳转到 `/login`，`localStorage` 中 `token` 和 `user` 被清除

---

### 模块 2：AI 问答

#### TC-AI-001：新建会话并发送问题（SSE 流式）
- **前置条件**：已登录，未指定 session_id
- **输入**：`question=求解方程 x²-5x+6=0, subject=数学`
- **操作**：POST `/api/ai/chat`，监听 SSE 流
- **预期结果**：
  - 返回 `Content-Type: text/event-stream`
  - 逐块接收 `data: {"type": "content", "delta": "..."}`
  - 最终接收 `data: {"type": "done", "message_id": ..., "session_id": "uuid"}`
  - 数据库中 `chat_sessions` 新增记录，`chat_messages` 新增用户消息和 AI 消息

#### TC-AI-002：在已有会话中追问
- **前置条件**：TC-AI-001 已执行，获得 `session_id`
- **输入**：`session_id=已有id, question=请详细解释第一步`
- **预期结果**：同 TC-AI-001，AI 能理解上下文

#### TC-AI-003：获取会话列表
- **操作**：GET `/api/ai/sessions?page=1&size=20`
- **预期结果**：返回当前用户的会话列表，包含 `title`、`subject`、`message_count`

#### TC-AI-004：获取指定会话消息
- **操作**：GET `/api/ai/sessions/{session_id}/messages`
- **预期结果**：返回该会话的所有消息，按创建时间升序排列

#### TC-AI-005：消息点赞/点踩反馈
- **操作**：POST `/api/ai/messages/{message_id}/feedback` with `{"rating": "thumbs_up"}`
- **预期结果**：`HTTP 200`，数据库 `chat_messages.feedback` 更新

#### TC-AI-006：从聊天消息加入错题本
- **操作**：POST `/api/ai/messages/{message_id}/add-to-wrong-book` with `{"subject": "数学", "tags": ["方程"]}`
- **前置条件**：`message_id` 为用户消息
- **预期结果**：`HTTP 200`，`wrong_items` 表新增记录，`source="ai_chat"`

#### TC-AI-007：删除会话
- **操作**：DELETE `/api/ai/sessions/{session_id}`
- **预期结果**：`HTTP 200`，`chat_sessions` 和 `chat_messages` 对应记录均被删除

#### TC-AI-008：前端 AI 问答界面流式显示
- **操作**：打开 `/ai`，输入数学问题，点击发送
- **预期结果**：
  - AI 回答逐字显示（流式效果）
  - 包含 Markdown 格式（标题、列表、代码块）
  - LaTeX 公式正确渲染（如 $x^2$ 显示为上标）
  - 非学科问题被礼貌拒绝

#### TC-AI-009：访问他人会话（越权测试）
- **前置条件**：用户 A 创建的 session_id
- **操作**：用户 B 的 Token 访问该 session_id
- **预期结果**：`HTTP 404, {"detail": "会话不存在"}`

---

### 模块 3：练习题生成与评判

#### TC-QUIZ-001：生成单选题
- **输入**：
  ```json
  {
    "subject": "数学",
    "topic": "一元二次方程",
    "difficulty": 2,
    "question_types": ["single_choice"],
    "count": 5
  }
  ```
- **预期结果**：
  - `HTTP 200`，返回 `session_id` 和 5 道题
  - 每道题包含 `type`, `content`, `options`（4个选项 A/B/C/D 格式），无 `correct_answer`（不暴露）
  - LaTeX 公式用 `$...$` 包裹

#### TC-QUIZ-002：生成多选题
- **输入**：`question_types: ["multiple_choice"]`
- **预期结果**：选项格式正确，每道题有 4 个选项

#### TC-QUIZ-003：生成填空题
- **输入**：`question_types: ["fill_blank"]`
- **预期结果**：`options` 字段为 `null`

#### TC-QUIZ-004：生成判断题
- **输入**：`question_types: ["true_false"]`
- **预期结果**：`options` 为 `["正确", "错误"]`

#### TC-QUIZ-005：单选题答案提交（正确）
- **前置条件**：TC-QUIZ-001 生成的会话
- **输入**：提交正确答案（如 `answer: "A"`）
- **预期结果**：`is_correct: true`，`correct_count` 增加

#### TC-QUIZ-006：单选题答案提交（错误）
- **输入**：提交错误答案
- **预期结果**：
  - `is_correct: false`
  - `wrong_items` 表自动新增记录
  - 返回 `explanation`（AI 解析）

#### TC-QUIZ-007：多选题答案排序验证（关键Bug修复验证）
- **目标**：验证代码检查报告中多选题 "AB" vs "BA" 判断问题
- **前置条件**：生成一道多选题，正确答案为 `"AB"`
- **输入 1**：`answer: "AB"` → 预期 `is_correct: true`
- **输入 2**：`answer: "BA"` → 当前代码预期 `is_correct: false`（**已知 Bug**）
- **记录**：此 Bug 已在代码检查报告中标注，修复后重测应均返回 `true`

#### TC-QUIZ-008：扫描图片识别题目（`/extract-topic`）
- **输入**：上传一张包含数学方程的 JPG 图片
- **预期结果**：
  ```json
  {
    "code": 200,
    "data": {
      "subject": "数学",
      "topic": "...",
      "recognized_text": "...",
      "question_count": 1
    }
  }
  ```

#### TC-QUIZ-009：扫描图片识别答案（`/extract-answer`）
- **输入**：上传手写答案图片，传入题目内容
- **预期结果**：返回 `answer`（识别文字）和 `confidence`（high/medium/low）

#### TC-QUIZ-010：题目数量超限测试
- **输入**：`count: 100`
- **预期结果**：当前代码无限制，AI 会尝试生成 100 道（已知 Bug），理想应返回 `422` 或截断到 20

#### TC-QUIZ-011：练习历史列表
- **操作**：GET `/api/quiz/sessions?page=1&size=20`
- **预期结果**：只返回 `status="completed"` 的会话

#### TC-QUIZ-012：推荐难度接口
- **操作**：GET `/api/quiz/recommended-difficulty?subject=数学&topic=方程`
- **预期结果**：根据历史正确率返回 1/2/3 难度等级和原因

#### TC-QUIZ-013：前端练习题生成流程
- **操作**：
  1. 打开 `/quiz`
  2. 选择学科/知识点/难度/题型
  3. 点击"开始练习"
  4. 在 `/quiz/session` 答题
  5. 点击"提交答案"
- **预期结果**：
  - 自动跳转到答题界面
  - 单选题选项高亮显示已选
  - 提交后显示正确/错误标识和得分
  - 错题提示"已加入错题本"

---

### 模块 4：错题本

#### TC-WRONG-001：手动添加错题
- **输入**：
  ```json
  {
    "question": "设 α∈(0,π)，已知 sin α=3/5，求 cos α",
    "correct_answer": "-4/5",
    "user_wrong_answer": "4/5",
    "subject": "数学",
    "tags": ["三角函数", "辅助角公式"]
  }
  ```
- **预期结果**：`HTTP 200`，`next_review_at = tomorrow（明天）`，`mastery="unmastered"`

#### TC-WRONG-002：查看错题列表（带筛选）
- **操作**：GET `/api/wrong-book?subject=数学&mastery=unmastered&page=1&size=20`
- **预期结果**：只返回数学科目、未掌握状态的错题

#### TC-WRONG-003：查看今日待复习错题
- **操作**：GET `/api/wrong-book?due_review=true`
- **预期结果**：`next_review_at <= today AND mastery != "mastered"` 的错题

#### TC-WRONG-004：AI 解析错题（SSE 流式）
- **操作**：POST `/api/wrong-book/{item_id}/ai-explain`
- **预期结果**：流式返回 AI 解析，完成后 `ai_explanation` 字段被保存

#### TC-WRONG-005：复习答对（艾宾浩斯进阶）
- **前置条件**：`review_count=0`（新错题）
- **操作**：POST `/api/wrong-book/{item_id}/review` with `{"answer": "正确答案", "is_correct": true}`
- **预期结果**：
  - `review_count = 1`
  - `next_review_at = today + 1天`（interval[0] = 1）
  - `mastery = "unmastered"`（review_count=1 < 2，应为 unmastered）

#### TC-WRONG-006：复习连续答对（掌握程度进阶）
- **测试艾宾浩斯算法完整流程**：

| 操作 | review_count（前） | is_correct | 预期 next_review_at | 预期 mastery |
|------|------------------|------------|---------------------|-------------|
| 第1次复习 | 0 | true | today+1 | unmastered |
| 第2次复习 | 1 | true | today+3 | fuzzy（review_count>=2） |
| 第3次复习 | 2 | true | today+7 | **待验证**（代码检查发现 Bug） |
| 第4次复习 | 3 | true | today+14 | mastered（应为 mastered） |
| 第5次复习 | 4 | true | today+30 | mastered |

> **注**：TC-WRONG-006 专门验证 `review_service.py:30` 中 mastery 逻辑 Bug。当 `review_count=2 → new_count=3`，当前代码返回 `mastery="mastered"`（Bug），修复后应返回 `mastery="fuzzy"`。

#### TC-WRONG-007：复习答错（重置）
- **前置条件**：`review_count=3`（已复习多次）
- **操作**：`is_correct: false`
- **预期结果**：`review_count=0`，`mastery="unmastered"`，`next_review_at = today+1`

#### TC-WRONG-008：更新掌握程度
- **操作**：PUT `/api/wrong-book/{item_id}/mastery` with `{"mastery": "mastered"}`
- **预期结果**：`HTTP 200`
- **边界测试**：`mastery: "invalid_value"` → 当前代码无枚举限制会写入（已知 Bug）

#### TC-WRONG-009：生成相似题目
- **操作**：POST `/api/wrong-book/{item_id}/similar-quiz` with `{"count": 3}`
- **预期结果**：返回 3 道相似题目

#### TC-WRONG-010：删除错题
- **操作**：DELETE `/api/wrong-book/{item_id}`
- **预期结果**：`HTTP 200`，数据库记录被删除

#### TC-WRONG-011：越权访问他人错题
- **操作**：用户 B 的 Token 访问用户 A 的错题 ID
- **预期结果**：`HTTP 404`

---

### 模块 5：AI 批改作业

#### TC-HW-001：文本作业批改（SSE 流式）
- **输入**：
  ```json
  {
    "title": "数学作业第一章",
    "subject": "数学",
    "content": "1. 已知 x²-5x+6=0，求 x 的值。\n答：x=2 或 x=3"
  }
  ```
- **操作**：POST `/api/homework/grade/text`，监听 SSE 流
- **预期结果**：
  - 逐块接收批改报告
  - 最终 `done` 事件包含 `grading_id` 和 `score`
  - 数据库 `homework_gradings` 记录状态变为 `"done"`
  - `score` 字段为 0-100 之间的浮点数

#### TC-HW-002：文件作业批改（PDF）
- **操作**：POST `/api/homework/grade/file`（multipart/form-data）上传 PDF 文件
- **预期结果**：提取 PDF 文字后进行批改，返回格式同 TC-HW-001

#### TC-HW-003：图片作业批改
- **操作**：上传包含手写作业的 JPG 图片
- **预期结果**：使用 Vision API 识别图片内容并批改

#### TC-HW-004：图片识别预览（`/recognize`）
- **操作**：POST `/api/homework/recognize` 上传图片
- **预期结果**：返回 `recognized_text` 和 `confidence`，不保存到数据库

#### TC-HW-005：不支持的学科
- **输入**：`subject: "体育"`
- **预期结果**：`HTTP 400, {"detail": "不支持的学科，请选择：..."}`

#### TC-HW-006：作业内容超长
- **输入**：`content` 超过 10000 字符
- **预期结果**：`HTTP 400, {"detail": "作业内容过长..."}`

#### TC-HW-007：批改历史列表
- **操作**：GET `/api/homework/history?page=1&size=20`
- **预期结果**：返回当前用户的批改历史，按时间倒序

#### TC-HW-008：批改详情
- **操作**：GET `/api/homework/history/{grading_id}`
- **预期结果**：返回完整批改报告（`detailed_feedback`）

#### TC-HW-009：删除批改记录
- **操作**：DELETE `/api/homework/history/{grading_id}`
- **预期结果**：`HTTP 200`，记录被删除；若有关联文件，验证磁盘文件是否同步删除（当前版本为已知 Bug：文件不会删除）

#### TC-HW-010：前端批改完整流程
- **操作**：
  1. 打开 `/homework`
  2. 选择"文本输入"模式，输入数学作业内容
  3. 点击"提交批改"
  4. 观察流式输出，等待批改完成
  5. 查看分数和批改报告
  6. 点击"导出 PDF"
- **预期结果**：
  - 批改过程中显示"AI 正在批改中"和实时流式内容
  - 完成后显示圆形分数计，Markdown 报告正确渲染（含 LaTeX）
  - 点击"导出 PDF"打开新窗口，自动弹出打印对话框

#### TC-HW-011：前端 Undo/Redo 功能
- **操作**：在图片识别编辑模式下编辑文字，测试 Ctrl+Z 和 Ctrl+Y
- **预期结果**：
  - Ctrl+Z 还原到上一个状态
  - Ctrl+Y 重做
  - Undo 按钮在无历史时为 disabled 状态

#### TC-HW-012：上传不支持的文件格式
- **输入**：上传 `.txt` 或 `.xlsx` 文件
- **预期结果**：`HTTP 400, {"detail": "不支持的文件类型..."}`

---

### 模块 6：笔记管理

#### TC-NOTE-001：创建笔记
- **输入**：`{"title": "等差数列", "subject": "数学", "content": "等差数列的通项公式..."}`
- **预期结果**：`HTTP 200`，返回创建的笔记对象

#### TC-NOTE-002：查看笔记列表（带学科筛选）
- **操作**：GET `/api/notes?subject=数学&page=1&size=20`
- **预期结果**：只返回数学学科的笔记

#### TC-NOTE-003：更新笔记
- **操作**：PUT `/api/notes/{note_id}` with 新标题/内容
- **预期结果**：`HTTP 200`，`updated_at` 字段更新

#### TC-NOTE-004：AI 总结笔记
- **操作**：POST `/api/notes/{note_id}/ai-summarize`
- **预期结果**：返回 `summary` 和 `key_points`，笔记 `ai_summary` 和 `key_points` 字段被更新

#### TC-NOTE-005：生成知识卡片（Flashcard）
- **操作**：POST `/api/notes/{note_id}/generate-flashcards`
- **预期结果**：返回 5-10 张知识卡片，`flashcards` 表新增记录

#### TC-NOTE-006：查看知识卡片
- **操作**：GET `/api/flashcards?subject=数学`
- **预期结果**：返回当前用户的知识卡片列表

#### TC-NOTE-007：对空内容笔记 AI 总结
- **前置条件**：笔记 `content` 为空
- **预期结果**：`HTTP 400, {"detail": "笔记内容为空"}`

#### TC-NOTE-008：删除笔记
- **操作**：DELETE `/api/notes/{note_id}`
- **预期结果**：`HTTP 200`，记录删除

---

### 模块 7：学习计划

#### TC-PLAN-001：生成学习计划
- **输入**：
  ```json
  {
    "subjects": ["数学", "物理", "化学"],
    "exam_date": "2026-06-15",
    "daily_hours": 4.0,
    "weak_subjects": ["化学"]
  }
  ```
- **预期结果**：返回按日期分组的任务列表，总天数 = exam_date - today + 1，化学任务多于其他学科

#### TC-PLAN-002：获取当前计划
- **操作**：GET `/api/plan/current`
- **预期结果**：返回最新激活的计划及所有任务

#### TC-PLAN-003：获取今日任务
- **操作**：GET `/api/plan/today`
- **预期结果**：只返回今天的任务

#### TC-PLAN-004：标记任务完成
- **操作**：PUT `/api/plan/tasks/{task_id}/done` with `{"is_done": true}`
- **预期结果**：`HTTP 200`，`done_at` 更新为当前时间

#### TC-PLAN-005：重新生成计划（停用旧计划）
- **操作**：调用 TC-PLAN-001 再次生成计划
- **预期结果**：旧计划 `is_active` 变为 `false`，新计划创建

#### TC-PLAN-006：记录番茄钟
- **操作**：POST `/api/plan/pomodoro` with `{"subject": "数学", "duration_minutes": 25, "completed": true}`
- **预期结果**：`HTTP 200`，`pomodoros` 表新增记录

---

### 模块 8：文档上传与分析

#### TC-DOC-001：上传 PDF 文档
- **操作**：POST `/api/documents/upload`（multipart/form-data），上传 PDF
- **预期结果**：
  - `HTTP 200`，返回文档信息
  - `status = "done"`（同步提取文字）
  - `content_text` 包含提取的文字内容

#### TC-DOC-002：上传 DOCX 文档
- **操作**：上传 Word 文档
- **预期结果**：同 TC-DOC-001

#### TC-DOC-003：上传图片文档
- **操作**：上传 JPG/PNG 图片
- **预期结果**：
  - `status = "done"` 或 `"error"`（因图片 OCR 未实现）
  - `content_text` 为提示字符串（已知 Bug：应标记为 error）

#### TC-DOC-004：AI 分析文档（提取知识点）
- **操作**：POST `/api/documents/{doc_id}/analyze` with `{"task": "extract_key_points"}`
- **预期结果**：流式返回知识点列表，文档 `key_points` 字段更新

#### TC-DOC-005：AI 分析文档（生成摘要）
- **操作**：`{"task": "summarize"}`
- **预期结果**：流式返回摘要，文档 `ai_summary` 字段更新

#### TC-DOC-006：AI 分析文档（出题）
- **操作**：`{"task": "generate_quiz"}`
- **预期结果**：流式返回 5 道练习题

#### TC-DOC-007：上传超大文件
- **输入**：大于 `MAX_FILE_SIZE_MB=20` 的文件（如 25MB PDF）
- **预期结果**：`HTTP 400, {"detail": "文件大小超过限制（最大 20MB）"}`

#### TC-DOC-008：删除文档
- **操作**：DELETE `/api/documents/{doc_id}`
- **预期结果**：`HTTP 200`，数据库记录和磁盘文件均被删除

---

### 模块 9：学习统计

#### TC-STATS-001：统计概览
- **操作**：GET `/api/stats/overview`
- **预期结果**：返回以下字段，数值非负：
  - `today_study_minutes`: 今日学习分钟数
  - `streak_days`: 连续学习天数
  - `total_study_days`: 总学习天数
  - `total_questions_done`: 总做题数
  - `average_accuracy`: 平均正确率（0-1 之间）
  - `wrong_book_count`: 错题总数
  - `mastered_count`: 已掌握错题数

#### TC-STATS-002：学习时间趋势（周）
- **操作**：GET `/api/stats/study-time?period=week`
- **预期结果**：返回 7 天的 `labels` 和 `values` 数组

#### TC-STATS-003：学习时间趋势（月）
- **操作**：GET `/api/stats/study-time?period=month`
- **预期结果**：返回 30 天数据

#### TC-STATS-004：各科正确率
- **操作**：GET `/api/stats/accuracy-by-subject`
- **预期结果**：返回各学科的 `accuracy` 和 `question_count`

#### TC-STATS-005：错题分布
- **操作**：GET `/api/stats/wrong-book-distribution`
- **预期结果**：按学科返回未掌握错题数量

#### TC-STATS-006：记录学习时长
- **操作**：POST `/api/stats/study-log` with `{"subject": "数学", "duration_minutes": 30, "activity_type": "quiz"}`
- **预期结果**：`HTTP 200`，`study_logs` 新增记录

---

## 四、接口层专项测试

### 4.1 认证边界测试

| 测试ID | 请求 | 预期 |
|--------|------|------|
| SEC-001 | 无 Authorization 头访问受保护接口 | HTTP 403（FastAPI HTTPBearer 默认） |
| SEC-002 | `Authorization: Bearer ` 空 Token | HTTP 403 |
| SEC-003 | `Authorization: Basic xxx` 非 Bearer | HTTP 403 |
| SEC-004 | 已注销用户的 Token | HTTP 401（token 仍有效，无法撤销，这是已知限制） |

### 4.2 数据隔离测试（越权防护）

| 测试ID | 场景 | 预期 |
|--------|------|------|
| ISO-001 | 用户 B 访问用户 A 的笔记 `/notes/{A的笔记ID}` | HTTP 404 |
| ISO-002 | 用户 B 访问用户 A 的错题 | HTTP 404 |
| ISO-003 | 用户 B 修改用户 A 的学习计划任务 | HTTP 404 |
| ISO-004 | 用户 B 获取用户 A 的统计数据 | 返回用户 B 自己的数据（各接口均过滤 user_id） |

### 4.3 输入验证测试

| 测试ID | 输入 | 预期 |
|--------|------|------|
| VAL-001 | 邮箱格式错误（`not-an-email`） | HTTP 422 Pydantic 验证错误 |
| VAL-002 | `difficulty` 超范围（如 `difficulty: 5`） | 当前代码无限制（已知 Bug） |
| VAL-003 | `mastery` 非法值（`mastery: "xyz"`） | 当前代码直接写入（已知 Bug） |
| VAL-004 | `page: 0`（页码从0开始） | 实际返回第1页，边界处理 |
| VAL-005 | SQL 注入尝试（在 `topic` 字段注入） | SQLAlchemy ORM 自动防护，返回正常 |
| VAL-006 | XSS 尝试（在 `content` 字段注入 `<script>` 标签） | 后端存储原始内容，前端 markdown.ts 已关闭 html 渲染（`html: false`），安全 |

---

## 五、前端 E2E 测试场景

### 5.1 完整学习流程

**场景 1：新用户注册并完成第一次 AI 问答**
1. 访问 `/register`，填写信息注册
2. 跳转到 `/login`，使用新账号登录
3. 跳转到 `/`（Dashboard）
4. 点击侧边栏"AI 问答"
5. 输入数学问题，发送
6. 等待 AI 流式回答完成
7. 对 AI 回答点击👍

**验证点**：全程无 JS 报错，数学公式正确渲染，流式效果正常

**场景 2：完整做题并查看错题**
1. 进入 `/quiz`，配置一套数学选择题
2. 在 `/quiz/session` 答题（故意答错至少1题）
3. 提交后查看结果
4. 跳转到 `/wrong-book`，确认错题已录入
5. 点击错题，触发 AI 解析

**验证点**：错题自动入库，AI 解析正确渲染

**场景 3：上传作业并导出 PDF**
1. 进入 `/homework`
2. 粘贴含 LaTeX 公式的数学作业文本
3. 提交批改
4. 等待批改完成，查看报告
5. 点击"导出 PDF"，验证新窗口和打印对话框

---

## 六、性能测试要求

### 6.1 接口响应时间要求

| 接口 | 正常响应时间 | 最大可接受时间 |
|------|------------|--------------|
| `POST /api/auth/login` | < 500ms | < 2s |
| `GET /api/notes` | < 200ms | < 1s |
| `POST /api/quiz/generate` | < 10s（AI 调用） | < 30s |
| `POST /api/ai/chat`（首字符） | < 3s | < 10s |
| `POST /api/homework/grade/text`（首字符） | < 5s | < 15s |
| `GET /api/stats/overview` | < 500ms | < 2s |

### 6.2 统计性能专项（N+1 问题验证）

**TC-PERF-001：`get_streak_days` 性能测试**

- **背景**：代码检查报告发现 `get_streak_days` 存在 N+1 查询问题（每天一次 DB 查询）
- **测试方法**：
  1. 为测试用户插入 100 天连续 `study_logs` 记录
  2. 调用 `GET /api/stats/overview`，测量响应时间
  3. 用 SQLite 慢查询日志记录查询次数
- **预期当前**：响应时间 > 1s（100 次 DB 查询）
- **预期修复后**：响应时间 < 100ms（单次查询）

### 6.3 并发测试

| 场景 | 并发数 | 目标 |
|------|--------|------|
| 同时 10 个用户 GET /api/stats/overview | 10 | 全部 < 2s，无报错 |
| 同时 5 个用户 POST /api/ai/chat | 5 | 全部收到 SSE 流，无超时 |
| 同时 3 个用户上传文件 | 3 | 全部上传成功，文件不混淆 |

---

## 七、安全测试

### 7.1 高危问题修复验证

| 测试ID | 验证目标 | 测试方法 |
|--------|---------|---------|
| SEC-FIX-001 | `secret_key` 默认弱密钥风险 | 部署时不配置 `.env`，检查是否使用默认 key 签发 Token |
| SEC-FIX-002 | JWT ValueError 崩溃（代码检查报告 TC-AUTH-006） | 构造非数字 `sub` 字段的 JWT，验证返回 401 而非 500 |
| SEC-FIX-003 | 密码强度 | 尝试注册 `password=123` 短密码，验证是否被拒绝（当前无限制，为已知 Bug） |

### 7.2 XSS 防护验证

| 测试ID | 输入 | 预期 |
|--------|------|------|
| XSS-001 | 笔记内容：`<script>alert(1)</script>` | 前端 `markdown-it` 的 `html: false` 阻止执行 |
| XSS-002 | AI 问答内容包含 HTML 标签 | AI 回答使用 `v-html` 渲染，但 `html: false` 阻止原始 HTML |
| XSS-003 | 作业标题包含 `"` 引号 | `escapeHtml` 函数转义，PDF 导出中不会破坏 HTML 结构 |

### 7.3 文件上传安全

| 测试ID | 输入 | 预期 |
|--------|------|------|
| FILE-SEC-001 | 上传 `.php` / `.sh` 可执行文件 | HTTP 400（MIME type 校验） |
| FILE-SEC-002 | 伪造 Content-Type 为 `image/jpeg` 的实际可执行文件 | 文件以 UUID 命名存储，不可被 Web Server 执行 |
| FILE-SEC-003 | 路径遍历（`filename: ../../etc/passwd`） | 文件保存使用 `uuid.uuid4().hex + ext`，原始文件名不影响存储路径 |

---

## 八、兼容性测试

### 8.1 浏览器兼容性

| 浏览器 | 版本 | 测试重点 |
|--------|------|---------|
| Chrome | 120+ | 全功能测试 |
| Firefox | 120+ | SSE 流式、PDF 打印 |
| Safari | 17+ | LaTeX 渲染、文件上传 |
| Edge | 120+ | MathLive 公式编辑器 |

### 8.2 前端特殊功能兼容性

| 功能 | 测试场景 |
|------|---------|
| SSE 流式输出 | 各浏览器的 `fetch + ReadableStream` 支持 |
| MathLive 公式编辑器 | Web Component 在各浏览器的 Virtual Keyboard |
| 拖拽文件上传 | 各浏览器 `DragEvent` 支持 |
| `window.print()` PDF 导出 | 各浏览器打印对话框兼容性 |

---

## 九、回归测试清单（修复后验证）

针对代码检查报告中已知 Bug，修复后需运行以下回归测试：

| Bug 编号 | 测试用例 | 优先级 |
|----------|---------|--------|
| Bug-01（多选题排序） | TC-QUIZ-007 | P0 |
| Bug-02（JWT ValueError） | TC-AUTH-006 | P0 |
| Bug-03（review_service mastery 逻辑） | TC-WRONG-006（step 3） | P0 |
| Bug-04（SSE 中 Session 关闭） | TC-AI-001（长时间流式，验证 AI 消息保存）| P0 |
| Bug-05（document_service ALLOWED_TYPES 缺 gif/webp） | TC-HW-003（上传 WebP 图片） | P1 |
| Bug-06（_extract_image 返回提示字符串存 content_text） | TC-DOC-003 | P1 |
| Bug-07（删除作业记录不清除文件） | TC-HW-009 | P1 |
| Bug-08（OCR 接口返回 200 但未实现） | 调用 `POST /api/wrong-book/ocr`，验证返回 501 | P2 |

---

## 十、测试执行计划

### 10.1 测试阶段

| 阶段 | 内容 | 工期 | 负责 |
|------|------|------|------|
| 阶段一 | 搭建测试环境，准备测试数据 | 0.5 天 | 开发/测试 |
| 阶段二 | 后端接口自动化测试（pytest） | 2 天 | 测试 |
| 阶段三 | 前端功能测试（手动） | 2 天 | 测试 |
| 阶段四 | 安全测试 & 性能测试 | 1 天 | 测试 |
| 阶段五 | Bug 修复 & 回归测试 | 1 天 | 开发+测试 |
| 阶段六 | 最终报告 & 上线审查 | 0.5 天 | PM+测试 |

### 10.2 自动化测试框架建议（pytest）

```python
# 推荐的测试文件结构
backend/tests/
├── conftest.py          # pytest fixtures（test db, test client, auth headers）
├── test_auth.py         # TC-AUTH-001 ~ TC-AUTH-010
├── test_ai.py           # TC-AI-001 ~ TC-AI-009
├── test_quiz.py         # TC-QUIZ-001 ~ TC-QUIZ-013
├── test_wrong_book.py   # TC-WRONG-001 ~ TC-WRONG-011
├── test_homework.py     # TC-HW-001 ~ TC-HW-012
├── test_notes.py        # TC-NOTE-001 ~ TC-NOTE-008
├── test_plan.py         # TC-PLAN-001 ~ TC-PLAN-006
├── test_docs.py         # TC-DOC-001 ~ TC-DOC-008
├── test_stats.py        # TC-STATS-001 ~ TC-STATS-006
└── test_security.py     # SEC-*, XSS-*, FILE-SEC-*
```

**conftest.py 关键 Fixtures 示例**：
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# 使用内存 SQLite 数据库
TEST_DATABASE_URL = "sqlite:///./test_edubuddy.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(client):
    """创建并登录测试用户，返回 auth headers"""
    client.post("/api/auth/register", json={
        "email": "test@test.com",
        "password": "Test123456",
        "nickname": "测试用户",
        "grade": "高一"
    })
    res = client.post("/api/auth/login", json={
        "email": "test@test.com",
        "password": "Test123456"
    })
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

---

## 十一、测试通过标准

### 11.1 发布前必须通过（P0）

- [ ] 所有 P0 测试用例通过率 100%
- [ ] 无高危（🔴）安全问题遗留
- [ ] 用户认证流程完整无误
- [ ] 多选题答案评判逻辑正确（TC-QUIZ-007 Bug 修复）
- [ ] 艾宾浩斯复习算法 mastery 逻辑正确（TC-WRONG-006 Bug 修复）
- [ ] SSE 流式输出稳定（TC-AI-001、TC-HW-001 无超时/报错）

### 11.2 发布前建议通过（P1）

- [ ] 所有 P1 测试用例通过率 ≥ 95%
- [ ] 无已知功能性中危 Bug 遗留
- [ ] 性能测试达标（接口响应时间符合第六章要求）

### 11.3 可规划修复（P2）

- [ ] 所有 P2 测试用例通过率 ≥ 80%（允许已知低危 Bug 遗留，记录在 backlog）

---

## 十二、测试交付物

| 交付物 | 说明 |
|--------|------|
| 测试用例执行记录 | 按本计划书逐条标注 Pass/Fail/Blocked |
| Bug 报告 | 问题描述、复现步骤、截图/日志、严重级别 |
| pytest 测试报告 | HTML 格式覆盖率报告（目标：后端核心逻辑覆盖率 ≥ 70%） |
| 性能测试报告 | 响应时间分布、P95/P99 数据 |
| 安全测试报告 | 漏洞列表及修复建议 |

---

*测试计划书版本：V1.0 | 生成时间：2026-05-30*
