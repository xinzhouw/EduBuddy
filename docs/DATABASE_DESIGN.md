# EduBuddy 数据库设计文档

**版本**：V1.0  
**日期**：2026-05-28  
**数据库**：SQLite（开发/生产）  
**ORM**：SQLAlchemy 2.0  

---

## 1. 数据表总览

| 表名 | 说明 |
|------|------|
| `users` | 用户信息 |
| `chat_sessions` | AI 问答会话 |
| `chat_messages` | 问答消息记录 |
| `notes` | 笔记 |
| `flashcards` | 知识卡片 |
| `quiz_sessions` | 练习题会话 |
| `questions` | 题目缓存 |
| `quiz_answers` | 答题记录 |
| `wrong_items` | 错题本 |
| `wrong_reviews` | 错题复习记录 |
| `study_plans` | 学习计划 |
| `plan_tasks` | 计划任务 |
| `pomodoros` | 番茄钟记录 |
| `documents` | 上传文档 |
| `study_logs` | 学习时长记录 |

---

## 2. 详细表结构

### 2.1 users（用户表）

```sql
CREATE TABLE users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       VARCHAR(255) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,         -- bcrypt 哈希
    nickname    VARCHAR(50)  NOT NULL,
    grade       VARCHAR(10)  NOT NULL,         -- 初一~高三
    avatar_url  VARCHAR(500),                  -- 头像文件路径
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| email | VARCHAR(255) | 邮箱，唯一索引 |
| password | VARCHAR(255) | bcrypt 哈希密码 |
| nickname | VARCHAR(50) | 显示昵称 |
| grade | VARCHAR(10) | 年级：初一/初二/初三/高一/高二/高三 |
| avatar_url | VARCHAR(500) | 头像图片路径（可空） |
| is_active | BOOLEAN | 是否激活 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

---

### 2.2 chat_sessions（AI 问答会话表）

```sql
CREATE TABLE chat_sessions (
    id          VARCHAR(36)  PRIMARY KEY,      -- UUID
    user_id     INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200),                  -- 会话标题（取第一条提问自动截取）
    subject     VARCHAR(20),                   -- 主要学科
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
```

---

### 2.3 chat_messages（问答消息表）

```sql
CREATE TABLE chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  VARCHAR(36)  NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id     INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        VARCHAR(10)  NOT NULL,         -- 'user' 或 'assistant'
    content     TEXT         NOT NULL,         -- 消息内容（Markdown格式）
    feedback    VARCHAR(20),                   -- 'thumbs_up' / 'thumbs_down'
    feedback_reason VARCHAR(50),              -- 差评原因
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
```

---

### 2.4 notes（笔记表）

```sql
CREATE TABLE notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    subject     VARCHAR(20)  NOT NULL,
    content     TEXT         NOT NULL DEFAULT '',  -- Markdown 格式
    ai_summary  TEXT,                             -- AI 生成的摘要
    key_points  TEXT,                             -- JSON 数组，知识点列表
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notes_user_id ON notes(user_id);
CREATE INDEX idx_notes_subject ON notes(subject);
```

**`key_points` 字段示例**：
```json
["配方法", "顶点坐标", "对称轴", "最值问题"]
```

---

### 2.5 flashcards（知识卡片表）

```sql
CREATE TABLE flashcards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    note_id     INTEGER      REFERENCES notes(id) ON DELETE SET NULL,  -- 来源笔记（可空）
    front       TEXT         NOT NULL,   -- 正面（问题/概念）
    back        TEXT         NOT NULL,   -- 背面（答案/解释）
    subject     VARCHAR(20)  NOT NULL,
    tags        TEXT         NOT NULL DEFAULT '[]',  -- JSON 数组
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_flashcards_user_id ON flashcards(user_id);
```

---

### 2.6 quiz_sessions（练习会话表）

```sql
CREATE TABLE quiz_sessions (
    id              VARCHAR(36)  PRIMARY KEY,  -- UUID
    user_id         INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject         VARCHAR(20)  NOT NULL,
    topic           VARCHAR(100) NOT NULL,
    difficulty      INTEGER      NOT NULL,     -- 1~4
    question_types  TEXT         NOT NULL,     -- JSON 数组
    total_count     INTEGER      NOT NULL,
    correct_count   INTEGER      NOT NULL DEFAULT 0,
    time_spent      INTEGER      NOT NULL DEFAULT 0,  -- 秒
    status          VARCHAR(20)  NOT NULL DEFAULT 'in_progress',  -- 'in_progress'/'completed'
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME
);

CREATE INDEX idx_quiz_sessions_user_id ON quiz_sessions(user_id);
```

---

### 2.7 questions（题目缓存表）

```sql
CREATE TABLE questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      VARCHAR(36)  NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    question_type   VARCHAR(20)  NOT NULL,    -- 'single_choice'/'multiple_choice'/'fill_blank'/'true_false'/'subjective'
    content         TEXT         NOT NULL,    -- 题目内容（支持 LaTeX）
    options         TEXT,                     -- JSON 数组（选择题用）
    correct_answer  TEXT         NOT NULL,    -- 正确答案
    explanation     TEXT,                     -- AI 解析（答题后生成）
    difficulty      INTEGER      NOT NULL,
    subject         VARCHAR(20)  NOT NULL,
    topic           VARCHAR(100) NOT NULL,
    order_num       INTEGER      NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

### 2.8 quiz_answers（答题记录表）

```sql
CREATE TABLE quiz_answers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      VARCHAR(36)  NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    question_id     INTEGER      NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    user_id         INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_answer     TEXT         NOT NULL,
    is_correct      BOOLEAN      NOT NULL,
    time_spent      INTEGER      NOT NULL DEFAULT 0,  -- 秒
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

### 2.9 wrong_items（错题本表）

```sql
CREATE TABLE wrong_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question            TEXT         NOT NULL,          -- 题目内容
    correct_answer      TEXT         NOT NULL,          -- 正确答案
    user_wrong_answer   TEXT,                           -- 学生的错误答案（可空）
    subject             VARCHAR(20)  NOT NULL,
    tags                TEXT         NOT NULL DEFAULT '[]',  -- JSON 数组
    source              VARCHAR(20)  NOT NULL DEFAULT 'manual',  -- 'quiz'/'manual'/'ai_chat'
    source_id           VARCHAR(100),                   -- 来源ID（如 quiz question_id）
    mastery             VARCHAR(20)  NOT NULL DEFAULT 'unmastered',  -- 'unmastered'/'fuzzy'/'mastered'
    review_count        INTEGER      NOT NULL DEFAULT 0,
    next_review_at      DATE,                           -- 下次复习日期
    ai_explanation      TEXT,                           -- AI 讲解缓存
    created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_wrong_items_user_id ON wrong_items(user_id);
CREATE INDEX idx_wrong_items_subject ON wrong_items(subject);
CREATE INDEX idx_wrong_items_next_review ON wrong_items(next_review_at);
CREATE INDEX idx_wrong_items_mastery ON wrong_items(mastery);
```

---

### 2.10 wrong_reviews（错题复习记录表）

```sql
CREATE TABLE wrong_reviews (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    wrong_item_id   INTEGER      NOT NULL REFERENCES wrong_items(id) ON DELETE CASCADE,
    user_id         INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_answer     TEXT,
    is_correct      BOOLEAN      NOT NULL,
    reviewed_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_wrong_reviews_wrong_item_id ON wrong_reviews(wrong_item_id);
```

**间隔复习逻辑**（在 `review_service.py` 中实现）：
```
复习次数 → 下次复习间隔
0（新增）→ 第二天（1天后）
1        → 3 天后
2        → 7 天后
3        → 14 天后
4        → 30 天后（标记为已掌握）
```

---

### 2.11 study_plans（学习计划表）

```sql
CREATE TABLE study_plans (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subjects        TEXT         NOT NULL,   -- JSON 数组，备考学科
    exam_date       DATE         NOT NULL,
    daily_hours     REAL         NOT NULL,
    weak_subjects   TEXT         NOT NULL DEFAULT '[]',  -- JSON 数组
    start_date      DATE         NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_study_plans_user_id ON study_plans(user_id);
```

---

### 2.12 plan_tasks（计划任务表）

```sql
CREATE TABLE plan_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id         INTEGER      NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
    user_id         INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date            DATE         NOT NULL,
    subject         VARCHAR(20)  NOT NULL,
    topic           VARCHAR(100) NOT NULL,
    task_type       VARCHAR(20)  NOT NULL,   -- 'study'/'practice'/'review'
    duration_minutes INTEGER     NOT NULL,
    is_done         BOOLEAN      NOT NULL DEFAULT FALSE,
    done_at         DATETIME,
    order_num       INTEGER      NOT NULL DEFAULT 1
);

CREATE INDEX idx_plan_tasks_plan_id ON plan_tasks(plan_id);
CREATE INDEX idx_plan_tasks_date ON plan_tasks(date);
CREATE INDEX idx_plan_tasks_user_date ON plan_tasks(user_id, date);
```

---

### 2.13 pomodoros（番茄钟记录表）

```sql
CREATE TABLE pomodoros (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject         VARCHAR(20),
    duration_minutes INTEGER     NOT NULL DEFAULT 25,
    completed       BOOLEAN      NOT NULL DEFAULT TRUE,
    started_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pomodoros_user_id ON pomodoros(user_id);
```

---

### 2.14 documents（文档表）

```sql
CREATE TABLE documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(300) NOT NULL,
    subject         VARCHAR(20),
    file_type       VARCHAR(10)  NOT NULL,   -- 'pdf'/'docx'/'jpg'/'png'
    file_path       VARCHAR(500) NOT NULL,   -- 服务器存储路径
    file_size       INTEGER      NOT NULL,   -- 字节数
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending',  -- 'pending'/'processing'/'done'/'error'
    content_text    TEXT,                    -- 提取的文本内容
    key_points      TEXT,                    -- JSON 数组，AI 提取的知识点
    ai_summary      TEXT,                    -- AI 摘要
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at    DATETIME
);

CREATE INDEX idx_documents_user_id ON documents(user_id);
```

---

### 2.15 study_logs（学习时长记录表）

```sql
CREATE TABLE study_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date            DATE         NOT NULL,
    subject         VARCHAR(20),
    duration_minutes INTEGER     NOT NULL,
    activity_type   VARCHAR(20)  NOT NULL,   -- 'ai_chat'/'notes'/'quiz'/'review'/'plan'/'docs'
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_study_logs_user_id ON study_logs(user_id);
CREATE INDEX idx_study_logs_date ON study_logs(date);
CREATE INDEX idx_study_logs_user_date ON study_logs(user_id, date);
```

---

## 3. 实体关系图（ER Diagram）

```
users (1) ─────────────────────────────────────────────────────────────
  │                                                                     │
  ├─ (1:N) ── chat_sessions (1) ── (1:N) ── chat_messages             │
  │                                                                     │
  ├─ (1:N) ── notes (1) ── (1:N) ── flashcards                        │
  │                                                                     │
  ├─ (1:N) ── quiz_sessions (1) ── (1:N) ── questions                 │
  │                                  └── (1:N) ── quiz_answers         │
  │                                                                     │
  ├─ (1:N) ── wrong_items (1) ── (1:N) ── wrong_reviews               │
  │                                                                     │
  ├─ (1:N) ── study_plans (1) ── (1:N) ── plan_tasks                  │
  │                                                                     │
  ├─ (1:N) ── pomodoros                                                │
  │                                                                     │
  ├─ (1:N) ── documents                                                │
  │                                                                     │
  └─ (1:N) ── study_logs ──────────────────────────────────────────────
```

---

## 4. 数据库初始化与迁移

### 4.1 使用 Alembic 管理迁移

```bash
# 初始化 Alembic
cd backend
alembic init alembic

# 生成迁移文件
alembic revision --autogenerate -m "initial tables"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

### 4.2 常用查询示例

**查询今日待复习的错题**：
```sql
SELECT * FROM wrong_items
WHERE user_id = :user_id
  AND mastery != 'mastered'
  AND next_review_at <= DATE('now')
ORDER BY next_review_at ASC;
```

**查询某学科的答题正确率**：
```sql
SELECT
    q.subject,
    COUNT(*) AS total,
    SUM(CASE WHEN qa.is_correct THEN 1 ELSE 0 END) AS correct,
    ROUND(AVG(CASE WHEN qa.is_correct THEN 1.0 ELSE 0.0 END), 2) AS accuracy
FROM quiz_answers qa
JOIN questions q ON qa.question_id = q.id
WHERE qa.user_id = :user_id
GROUP BY q.subject;
```

**查询用户连续学习天数（streak）**：
```sql
WITH RECURSIVE dates AS (
    SELECT DATE('now') AS d
    UNION ALL
    SELECT DATE(d, '-1 day') FROM dates
    WHERE EXISTS (
        SELECT 1 FROM study_logs
        WHERE user_id = :user_id AND date = DATE(d, '-1 day')
    )
)
SELECT COUNT(*) - 1 AS streak_days FROM dates;
```
