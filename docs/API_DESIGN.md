# EduBuddy API 接口设计文档

**版本**：V1.0  
**日期**：2026-05-28  
**Base URL**：`http://localhost:8000/api`  
**认证方式**：JWT Bearer Token（除登录/注册外，所有接口需携带）

---

## 目录

1. [认证模块](#1-认证模块)
2. [AI 问答模块](#2-ai-问答模块)
3. [笔记模块](#3-笔记模块)
4. [练习题模块](#4-练习题模块)
5. [错题本模块](#5-错题本模块)
6. [学习计划模块](#6-学习计划模块)
7. [文档模块](#7-文档模块)
8. [学习统计模块](#8-学习统计模块)

---

## 1. 认证模块

### 1.1 用户注册

```
POST /api/auth/register
```

**请求体**：
```json
{
  "email": "student@example.com",
  "password": "password123",
  "nickname": "小明",
  "grade": "高一"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "id": 1,
    "email": "student@example.com",
    "nickname": "小明",
    "grade": "高一",
    "created_at": "2026-05-28T09:00:00"
  }
}
```

**错误**：
- `400` 邮箱已被注册
- `422` 参数格式错误

---

### 1.2 用户登录

```
POST /api/auth/login
```

**请求体**：
```json
{
  "email": "student@example.com",
  "password": "password123"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 604800,
    "user": {
      "id": 1,
      "email": "student@example.com",
      "nickname": "小明",
      "grade": "高一"
    }
  }
}
```

---

### 1.3 获取当前用户信息

```
GET /api/auth/me
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "email": "student@example.com",
    "nickname": "小明",
    "grade": "高一",
    "avatar_url": null,
    "created_at": "2026-05-28T09:00:00"
  }
}
```

---

### 1.4 更新用户信息

```
PUT /api/auth/me
```

**请求体**：
```json
{
  "nickname": "新昵称",
  "grade": "高二"
}
```

---

### 1.5 修改密码

```
PUT /api/auth/password
```

**请求体**：
```json
{
  "old_password": "oldpass123",
  "new_password": "newpass456"
}
```

---

## 2. AI 问答模块

### 2.1 发送问题（流式输出）

```
POST /api/ai/chat
Content-Type: application/json
Accept: text/event-stream
```

**请求体**：
```json
{
  "session_id": "optional-session-id",
  "question": "已知二次函数 f(x) = x² - 4x + 3，求其最小值",
  "subject": "数学",
  "images": []
}
```

**响应（SSE 流式）**：
```
data: {"type": "content", "delta": "【解题思路"}
data: {"type": "content", "delta": "】\n这是求"}
data: {"type": "content", "delta": "二次函数最值的问题"}
...
data: {"type": "done", "message_id": 42, "session_id": "abc123"}
```

**说明**：
- 若不传 `session_id`，后端自动创建新会话
- 返回 `session_id` 用于后续追问

---

### 2.2 获取问答会话列表

```
GET /api/ai/sessions?page=1&size=20
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "abc123",
        "title": "二次函数最小值问题",
        "subject": "数学",
        "last_message_at": "2026-05-28T10:00:00",
        "message_count": 4
      }
    ],
    "total": 15,
    "page": 1,
    "size": 20
  }
}
```

---

### 2.3 获取会话消息历史

```
GET /api/ai/sessions/{session_id}/messages
```

**响应**：
```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "role": "user",
      "content": "求二次函数最小值",
      "created_at": "2026-05-28T10:00:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "【解题思路】...",
      "feedback": null,
      "created_at": "2026-05-28T10:00:05"
    }
  ]
}
```

---

### 2.4 反馈 AI 回答质量

```
POST /api/ai/messages/{message_id}/feedback
```

**请求体**：
```json
{
  "rating": "thumbs_down",
  "reason": "答案错误"
}
```

**`rating`** 可选值：`thumbs_up` / `thumbs_down`  
**`reason`** 可选值：`答案错误` / `步骤不清楚` / `与问题无关` / `其他`

---

### 2.5 将问答加入错题本

```
POST /api/ai/messages/{message_id}/add-to-wrong-book
```

**请求体**：
```json
{
  "subject": "数学",
  "tags": ["二次函数", "配方法"]
}
```

---

## 3. 笔记模块

### 3.1 获取笔记列表

```
GET /api/notes?subject=数学&page=1&size=20
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "title": "二次函数笔记",
        "subject": "数学",
        "summary": "本笔记包含配方法、顶点公式...",
        "created_at": "2026-05-28T09:00:00",
        "updated_at": "2026-05-28T09:30:00"
      }
    ],
    "total": 5
  }
}
```

---

### 3.2 创建笔记

```
POST /api/notes
```

**请求体**：
```json
{
  "title": "二次函数笔记",
  "subject": "数学",
  "content": "## 配方法\n\n将 $f(x) = ax^2 + bx + c$ 配方..."
}
```

---

### 3.3 获取笔记详情

```
GET /api/notes/{note_id}
```

---

### 3.4 更新笔记

```
PUT /api/notes/{note_id}
```

**请求体**：
```json
{
  "title": "更新后的标题",
  "content": "更新后的内容"
}
```

---

### 3.5 删除笔记

```
DELETE /api/notes/{note_id}
```

---

### 3.6 AI 总结笔记

```
POST /api/notes/{note_id}/ai-summarize
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "summary": "本笔记核心知识点：\n1. 配方法：...\n2. 顶点公式：...",
    "key_points": ["配方法", "顶点坐标", "对称轴", "最值问题"]
  }
}
```

---

### 3.7 AI 生成知识卡片

```
POST /api/notes/{note_id}/generate-flashcards
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "flashcards": [
      {
        "front": "二次函数顶点公式是什么？",
        "back": "顶点坐标为 $(-\\frac{b}{2a}, \\frac{4ac-b^2}{4a})$",
        "subject": "数学",
        "tags": ["二次函数", "顶点公式"]
      }
    ],
    "count": 5
  }
}
```

---

### 3.8 获取知识卡片列表

```
GET /api/flashcards?subject=数学&page=1&size=20
```

---

### 3.9 创建知识卡片

```
POST /api/flashcards
```

**请求体**：
```json
{
  "front": "牛顿第二定律的公式？",
  "back": "$F = ma$，其中F为合外力，m为质量，a为加速度",
  "subject": "物理",
  "tags": ["牛顿定律", "力学"]
}
```

---

## 4. 练习题模块

### 4.1 生成练习题

```
POST /api/quiz/generate
```

**请求体**：
```json
{
  "subject": "数学",
  "topic": "二次函数",
  "difficulty": 2,
  "question_types": ["single_choice", "fill_blank"],
  "count": 5
}
```

**`difficulty`** 取值：1（基础）/ 2（中等）/ 3（困难）/ 4（挑战）  
**`question_types`** 取值：`single_choice` / `multiple_choice` / `fill_blank` / `true_false` / `subjective`

**响应**：
```json
{
  "code": 200,
  "data": {
    "session_id": "quiz-abc123",
    "questions": [
      {
        "id": 1,
        "type": "single_choice",
        "content": "已知 f(x) = x² - 4x + 3，则最小值为（  ）",
        "options": ["A. -1", "B. 0", "C. 1", "D. 3"],
        "difficulty": 2
      }
    ]
  }
}
```

---

### 4.2 提交答案

```
POST /api/quiz/sessions/{session_id}/submit
```

**请求体**：
```json
{
  "answers": [
    {
      "question_id": 1,
      "answer": "A",
      "time_spent": 45
    },
    {
      "question_id": 2,
      "answer": "3x+2",
      "time_spent": 60
    }
  ]
}
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "total": 5,
    "correct": 3,
    "accuracy": 0.6,
    "time_spent": 320,
    "results": [
      {
        "question_id": 1,
        "is_correct": true,
        "correct_answer": "A",
        "user_answer": "A",
        "explanation": "【解题思路】..."
      },
      {
        "question_id": 2,
        "is_correct": false,
        "correct_answer": "3x-2",
        "user_answer": "3x+2",
        "explanation": "【解题思路】..."
      }
    ],
    "wrong_items_added": [2]
  }
}
```

---

### 4.3 获取练习记录

```
GET /api/quiz/sessions?page=1&size=20
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "quiz-abc123",
        "subject": "数学",
        "topic": "二次函数",
        "total": 5,
        "correct": 3,
        "accuracy": 0.6,
        "created_at": "2026-05-28T10:00:00"
      }
    ],
    "total": 20
  }
}
```

---

### 4.4 获取自适应难度推荐

```
GET /api/quiz/recommended-difficulty?subject=数学&topic=二次函数
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "recommended_difficulty": 2,
    "reason": "您在该知识点的历史正确率为65%，推荐中等难度",
    "accuracy_history": 0.65
  }
}
```

---

## 5. 错题本模块

### 5.1 获取错题列表

```
GET /api/wrong-book?subject=数学&mastery=unmastered&page=1&size=20
```

**查询参数**：
- `subject`：学科筛选（可选）
- `mastery`：掌握程度 `unmastered` / `fuzzy` / `mastered`（可选）
- `due_review`：是否只看今日到期复习的题（`true`/`false`）

**响应**：
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "question": "已知 f(x) = x² - 4x + 3...",
        "correct_answer": "最小值为-1，在x=2时取得",
        "user_wrong_answer": "最小值为-1",
        "subject": "数学",
        "tags": ["二次函数", "最值"],
        "mastery": "unmastered",
        "review_count": 0,
        "next_review_at": "2026-05-28",
        "source": "quiz",
        "created_at": "2026-05-28T10:00:00"
      }
    ],
    "total": 15,
    "today_due_count": 3
  }
}
```

---

### 5.2 手动添加错题

```
POST /api/wrong-book
```

**请求体**：
```json
{
  "question": "题目内容",
  "correct_answer": "正确答案",
  "user_wrong_answer": "我的错误答案（可选）",
  "subject": "数学",
  "tags": ["二次函数"]
}
```

---

### 5.3 OCR 识别上传图片

```
POST /api/wrong-book/ocr
Content-Type: multipart/form-data
```

**表单字段**：
- `file`：图片文件（JPG/PNG，最大5MB）

**响应**：
```json
{
  "code": 200,
  "data": {
    "recognized_text": "已知二次函数 f(x) = x² - 4x + 3，求其最小值"
  }
}
```

---

### 5.4 获取错题详情

```
GET /api/wrong-book/{item_id}
```

---

### 5.5 AI 讲解错题

```
POST /api/wrong-book/{item_id}/ai-explain
```

**响应（SSE 流式）**：
```
data: {"type": "content", "delta": "【解题思路】\n"}
data: {"type": "content", "delta": "这道题考察配方法..."}
...
data: {"type": "done"}
```

---

### 5.6 追问 AI（错题对话）

```
POST /api/wrong-book/{item_id}/follow-up
```

**请求体**：
```json
{
  "question": "为什么要配方而不用求导？"
}
```

**响应（SSE 流式）**：同 5.5

---

### 5.7 更新掌握程度

```
PUT /api/wrong-book/{item_id}/mastery
```

**请求体**：
```json
{
  "mastery": "mastered"
}
```

**`mastery`** 取值：`unmastered` / `fuzzy` / `mastered`

---

### 5.8 复习错题（闯关模式答题）

```
POST /api/wrong-book/{item_id}/review
```

**请求体**：
```json
{
  "answer": "学生的回答",
  "is_correct": true
}
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "next_review_at": "2026-05-31",
    "review_count": 2,
    "mastery": "fuzzy",
    "message": "✅ 答对了！下次复习时间：3天后"
  }
}
```

---

### 5.9 删除错题

```
DELETE /api/wrong-book/{item_id}
```

---

### 5.10 生成同类练习题

```
POST /api/wrong-book/{item_id}/similar-quiz
```

**请求体**：
```json
{
  "count": 3
}
```

**响应**：同练习题生成接口

---

## 6. 学习计划模块

### 6.1 生成学习计划

```
POST /api/plan/generate
```

**请求体**：
```json
{
  "subjects": ["数学", "物理", "英语"],
  "exam_date": "2026-06-15",
  "daily_hours": 3.0,
  "weak_subjects": ["物理"]
}
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "plan_id": 1,
    "start_date": "2026-05-28",
    "end_date": "2026-06-15",
    "total_days": 18,
    "tasks_by_date": {
      "2026-05-28": [
        {
          "id": 1,
          "subject": "数学",
          "topic": "二次函数综合",
          "task_type": "study",
          "duration_minutes": 60,
          "is_done": false
        },
        {
          "id": 2,
          "subject": "物理",
          "topic": "牛顿第二定律",
          "task_type": "practice",
          "duration_minutes": 45,
          "is_done": false
        }
      ]
    }
  }
}
```

---

### 6.2 获取当前计划

```
GET /api/plan/current
```

---

### 6.3 获取今日任务

```
GET /api/plan/today
```

---

### 6.4 标记任务完成

```
PUT /api/plan/tasks/{task_id}/done
```

**请求体**：
```json
{
  "is_done": true
}
```

---

### 6.5 记录番茄钟

```
POST /api/plan/pomodoro
```

**请求体**：
```json
{
  "subject": "数学",
  "duration_minutes": 25,
  "completed": true
}
```

---

## 7. 文档模块

### 7.1 上传文档

```
POST /api/documents/upload
Content-Type: multipart/form-data
```

**表单字段**：
- `file`：文件（PDF/DOCX/JPG/PNG，最大20MB）
- `subject`：学科（可选）
- `title`：自定义标题（可选）

**响应**：
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "title": "高中数学讲义.pdf",
    "subject": "数学",
    "file_type": "pdf",
    "file_size": 1024000,
    "status": "processing",
    "created_at": "2026-05-28T10:00:00"
  }
}
```

---

### 7.2 获取文档列表

```
GET /api/documents?subject=数学&page=1&size=20
```

---

### 7.3 获取文档详情（含解析结果）

```
GET /api/documents/{doc_id}
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "title": "高中数学讲义.pdf",
    "subject": "数学",
    "status": "done",
    "content_text": "文档提取的文本内容...",
    "key_points": ["知识点1", "知识点2"],
    "summary": "本文档讲述了..."
  }
}
```

---

### 7.4 AI 分析文档

```
POST /api/documents/{doc_id}/analyze
```

**请求体**：
```json
{
  "task": "extract_key_points"
}
```

**`task`** 取值：
- `extract_key_points`：提取知识点
- `summarize`：生成摘要
- `generate_quiz`：基于文档出题

**响应（SSE 流式）**：同问答流式接口

---

### 7.5 删除文档

```
DELETE /api/documents/{doc_id}
```

---

## 8. 学习统计模块

### 8.1 获取学习概览

```
GET /api/stats/overview
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "today_study_minutes": 90,
    "streak_days": 5,
    "total_study_days": 30,
    "total_questions_done": 150,
    "average_accuracy": 0.72,
    "wrong_book_count": 23,
    "mastered_count": 8
  }
}
```

---

### 8.2 获取学习时长趋势

```
GET /api/stats/study-time?period=week
```

**`period`** 取值：`week` / `month`

**响应**：
```json
{
  "code": 200,
  "data": {
    "labels": ["5/22", "5/23", "5/24", "5/25", "5/26", "5/27", "5/28"],
    "values": [60, 90, 45, 120, 0, 75, 90]
  }
}
```

---

### 8.3 获取各学科正确率

```
GET /api/stats/accuracy-by-subject
```

**响应**：
```json
{
  "code": 200,
  "data": [
    { "subject": "数学", "accuracy": 0.68, "question_count": 50 },
    { "subject": "物理", "accuracy": 0.55, "question_count": 30 },
    { "subject": "英语", "accuracy": 0.82, "question_count": 40 }
  ]
}
```

---

### 8.4 获取错题知识点分布

```
GET /api/stats/wrong-book-distribution
```

**响应**：
```json
{
  "code": 200,
  "data": [
    { "subject": "数学", "count": 12 },
    { "subject": "物理", "count": 8 },
    { "subject": "化学", "count": 3 }
  ]
}
```

---

### 8.5 记录学习时长

```
POST /api/stats/study-log
```

**请求体**：
```json
{
  "subject": "数学",
  "duration_minutes": 30,
  "activity_type": "quiz"
}
```

**`activity_type`** 取值：`ai_chat` / `notes` / `quiz` / `review` / `plan` / `docs`
