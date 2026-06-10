# EduBuddy — 学习计划与学习状况分析功能设计文档

**版本**：V1.1  
**日期**：2026-06-09  
**状态**：设计稿（待实现）

---

## 目录

1. [功能概述与目标](#1-功能概述与目标)
2. [理论基础](#2-理论基础)
3. [用户角色体系](#3-用户角色体系)
4. [功能模块详细设计](#4-功能模块详细设计)
   - 4.1 学习计划模块（增强版）
   - 4.2 学习状况分析模块（增强版）
   - 4.3 每日学习建议模块（新增）
   - 4.4 教师/家长监督视图（新增）
5. [数据模型设计](#5-数据模型设计)
6. [API 接口设计](#6-api-接口设计)
7. [前端页面设计](#7-前端页面设计)
8. [AI 服务设计](#8-ai-服务设计)
9. [实现路线图](#9-实现路线图)

---

## 1. 功能概述与目标

### 1.1 现状分析

当前 EduBuddy 已有基础的学习计划与统计功能：

| 模块 | 现有能力 | 缺失能力 |
|------|---------|---------|
| 学习计划 | AI 生成按天任务、番茄钟、任务打卡 | 计划调整建议、漏做延期、完成度预警 |
| 学习统计 | 今日时长、连续打卡、答题数、正确率趋势、错题分布 | 雷达图、热力图、学科深度分析、完成率对比 |
| 用户角色 | 单一学生角色 | 教师/家长角色及关联学生视图 |
| 学习建议 | 无 | 每日首次登录时的个性化建议 |

### 1.2 设计目标

- **学生端**：提供科学、个性化的学习计划生成与调整机制；通过多维统计图表直观反映学习状况；每日首次登录时推送有依据的学习建议。
- **教师/家长端**：提供被关联学生的学习状况全景视图，支持多维度查看，辅助教学或家庭辅导决策。
- **理论支撑**：所有分析算法和建议生成均基于教育心理学和认知科学的成熟理论（详见第 2 节）。

---

## 2. 理论基础

### 2.1 艾宾浩斯遗忘曲线（Ebbinghaus Forgetting Curve）

**来源**：德国心理学家赫尔曼·艾宾浩斯，1885 年《记忆》。

**核心原理**：遗忘呈幂函数规律，新学知识在 24 小时内遗忘约 70%。通过**间隔重复（Spaced Repetition）**在遗忘临界点前复习，可指数级提升记忆留存率。

**在本系统中的应用**：
- 错题本的复习间隔调度（已实现：1→3→7→14→30 天）
- **学习计划中的复习任务安排**：知识点学习后，系统在第 1、3、7 天自动插入复习任务
- **学习建议中**：若某知识点到达遗忘临界点但尚未复习，在当日建议中优先提示

### 2.2 间隔效应（Spacing Effect）

**来源**：认知心理学研究证实，分散学习（多次短时间学习）远优于集中学习（一次长时间学习）。

**在本系统中的应用**：
- 学习计划生成时，同一学科不安排连续超过 2 天，强制轮换
- 单次学习任务建议时长：20~45 分钟（符合人类专注力峰值区间）
- 番茄钟默认 25 分钟专注 + 5 分钟休息，契合间隔效应

### 2.3 测试效应（Testing Effect / Retrieval Practice）

**来源**：Roediger & Karpicke（2006）研究证实，主动回忆（测试）比被动重读学习效果高出 50% 以上。

**在本系统中的应用**：
- 学习计划中的任务类型权重：`practice`（练习）> `review`（复习）> `study`（新知识学习）
- 学习效果分析时，**练习题正确率趋势**作为掌握程度的核心指标，权重高于学习时长
- 建议生成时，若某学科学习时长充足但正确率未提升，主动建议"转为刷题模式"

### 2.4 认知负荷理论（Cognitive Load Theory）

**来源**：Sweller（1988）。人的工作记忆容量有限，过高的认知负荷会导致学习效率下降。

**在本系统中的应用**：
- 每日任务规划时，不同学科任务分布在不同时段，避免同一学科连续学习超过 90 分钟
- 统计分析 Dashboard 采用渐进式呈现：摘要卡片 → 趋势图表 → 详细分析，避免信息过载
- 每日建议条数限制在 3~5 条，条目精简有重点

### 2.5 动机与自我效能感理论（Bandura's Self-Efficacy）

**来源**：Albert Bandura（1977），自我效能感指个体对自己完成某任务的信心程度，直接影响学习坚持性。

**在本系统中的应用**：
- **进度可视化**：今日完成度、整体完成率以百分比+进度条呈现，强化"我做到了"的正反馈
- **连续打卡**（Streak）：利用行为心理学"损失厌恶"效应，维持学习惯性
- 建议措辞：正向激励为主（"你在 XX 方面已进步 XX%"），避免负向强调

### 2.6 布鲁姆教育目标分类（Bloom's Taxonomy）

**来源**：Benjamin Bloom（1956）。将学习目标分为 6 个层次：记忆→理解→应用→分析→评价→创造。

**在本系统中的应用**：
- 任务类型映射：`study`（记忆/理解层）→ `practice`（应用/分析层）→ `review`（巩固）
- 学习状况分析中的"掌握深度评分"：综合**答题正确率**（应用层）+ **错题复习次数**（分析层）+ **知识点覆盖率**（记忆层）三维评估

---

## 3. 用户角色体系

### 3.1 角色定义

系统新增 `role` 字段，支持三种用户角色：

| 角色 | 值 | 描述 |
|------|-----|------|
| 学生 | `student` | 默认角色，使用所有学习功能 |
| 教师 | `teacher` | 可查看绑定学生的学习状况 |
| 家长 | `parent` | 可查看绑定子女的学习状况 |

### 3.2 绑定关系

教师/家长与学生之间通过**关联关系表**（`user_relations`）绑定：

- **教师**：通过分享**班级邀请码**，学生加入后自动绑定
- **家长**：通过学生生成的**专属绑定码**（6 位数字，有效期 24 小时）绑定

### 3.3 权限矩阵

| 功能 | 学生 | 教师 | 家长 |
|------|------|------|------|
| 查看自己学习计划 | ✅ | ✅（自己） | ✅（自己） |
| 查看关联学生计划 | ❌ | ✅（只读） | ✅（只读） |
| 查看自己学习统计 | ✅ | ✅（自己） | ✅（自己） |
| 查看关联学生统计 | ❌ | ✅（只读） | ✅（只读） |
| 接收每日建议 | ✅ | ❌ | ❌ |
| 查看学生列表 | ❌ | ✅ | ✅ |
| 生成学生学习报告 | ❌ | ✅ | ✅ |

---

## 4. 功能模块详细设计

### 4.1 学习计划模块（增强版）

#### 4.1.1 计划生成（优化）

**输入参数**（在现有基础上增加）：

| 参数 | 类型 | 说明 |
|------|------|------|
| subjects | List[str] | 备考学科（多选） |
| exam_date | date | 考试日期 |
| daily_hours | float | 每天可学习时长（小时） |
| weak_subjects | List[str] | 薄弱学科（可选） |
| **study_style** | str（新增） | 学习风格：`balanced`（均衡）/ `intensive`（冲刺）/ `steady`（稳扎稳打） |
| **preferred_times** | List[str]（新增） | 偏好学习时段：`morning`/`afternoon`/`evening` |

**AI 生成逻辑优化**：
- 基于艾宾浩斯曲线，自动在学习日后的第 1、3、7 天插入复习任务
- 薄弱学科分配 40% 学习时间（较其他学科加权）
- 考试前 7 天自动切换为"综合复习模式"（仅 `review` 类型任务）
- 每天任务总时长误差控制在 ±15 分钟内

#### 4.1.2 计划调整（新增）

- **漏做任务延期**：未完成的任务在第二天自动标注 `🔴 逾期`，并在下一次生成建议时纳入优先级
- **任务拖拽排序**：前端支持同日任务的拖拽重排（`order_num` 更新）
- **单任务修改**：可修改某任务的时长、学科、知识点（不影响整体计划）

#### 4.1.3 计划完成度追踪（新增）

- **今日完成率** = 今日已完成任务时长 / 今日总任务时长 × 100%
- **整体完成率** = 截至今日已完成任务数 / 截至今日应完成任务总数 × 100%
- **学科完成率**：按学科分组统计，用于雷达图展示

#### 4.1.4 番茄钟（增强）

- **自定义时长**：专注时间可选 15/20/25/30 分钟，休息时间可选 5/10 分钟
- **休息小贴士**：休息时随机显示学习小知识（基于当前学习学科）
- **番茄统计**：当日已完成番茄数 + 最近 7 天趋势

---

### 4.2 学习状况分析模块（增强版）

#### 4.2.1 概览卡片（现有 + 增强）

| 指标 | 现有 | 增强内容 |
|------|------|---------|
| 今日学习时长 | ✅ | 增加与目标时长对比（环形进度） |
| 连续打卡天数 | ✅ | 增加历史最高连续天数对比 |
| 累计完成题数 | ✅ | 增加本周/本月趋势箭头 |
| 平均正确率 | ✅ | 增加与上周对比（↑↓）|
| **计划完成率** | ❌（新增） | 今日计划完成率，配合进度条 |
| **掌握深度评分** | ❌（新增） | 综合布鲁姆分类的综合评分（0~100） |

#### 4.2.2 图表模块

**① 学习时长趋势（折线图）**
- 时间维度：本周 / 本月
- 数据：每日学习分钟数
- 增强：叠加"计划目标线"（每日应学时长），直观显示超额/欠额

**② 各学科正确率（水平条形图）**
- 现有功能保留
- 增强：条形颜色编码（≥80% 绿色，60~80% 橙色，<60% 红色）

**③ 错题知识点分布（柱状图）**
- 现有功能保留
- 增强：鼠标悬浮显示具体错误知识点列表

**④ 各学科掌握雷达图（新增）**
- 轴：各学科（数学、物理、化学等）
- 数值：掌握深度评分（0~100）
- 计算公式：
  ```
  掌握深度 = 正确率(40%) × 100 
            + 复习完成率(30%) × 100 
            + 知识点覆盖率(30%) × 100
  ```

**⑤ 学习活跃度热力图（新增）**
- 类 GitHub Contribution 日历热力图
- 颜色深度代表当日学习分钟数（0/1~30/31~60/60+ 四级）
- 展示近 3 个月数据

**⑥ 学科学习时长占比（饼图/环形图，新增）**
- 最近 30 天各学科累计学习时长占比
- 与计划分配比例对比（双环形）

#### 4.2.3 深度分析报告（新增）

点击"生成分析报告"，AI 根据近 30 天数据生成结构化报告（非流式，约 500 字），包含：
1. **总体评价**：学习表现定性描述
2. **优势学科**：正确率 + 学习时长双高的学科
3. **薄弱环节**：错题集中知识点 + 改善建议
4. **行为模式分析**：高效学习时段、平均专注时长（基于番茄钟数据）
5. **下一阶段建议**：具体可行的 3 条学习建议

---

### 4.3 每日学习建议模块（新增）

#### 4.3.1 触发机制

- **触发条件**：学生用户每日**首次登录**时（根据 `last_login_date` 判断，UTC+8 日期变化触发）
- **显示形式**：登录后在 Dashboard 顶部以**轮播卡片**形式展示，可手动关闭
- **生成时机**：后台异步生成（登录时触发，5 秒内完成；若未完成则下次刷新时展示）

#### 4.3.2 建议内容结构

每日建议由 3~5 条独立建议组成，每条建议包含：

```json
{
  "id": "唯一ID",
  "type": "review_reminder | practice_suggestion | plan_adjustment | achievement | general",
  "priority": 1,
  "icon": "🔄",
  "title": "建议标题（10字以内）",
  "content": "具体建议内容（50字以内）",
  "action": {
    "label": "去复习",
    "route": "/wrong-book",
    "params": { "subject": "数学" }
  },
  "theory_basis": "艾宾浩斯遗忘曲线：该知识点距上次学习已7天，正处于遗忘临界期",
  "generated_date": "2026-06-09"
}
```

#### 4.3.3 建议类型与生成规则

| 类型 | 触发条件 | 理论依据 | 示例 |
|------|---------|---------|------|
| `review_reminder` | 错题本中有到达复习节点的条目 | 艾宾浩斯遗忘曲线 | "📚 有 3 道数学错题今日到达复习节点，趁热打铁！" |
| `practice_suggestion` | 某学科学习 >2 天但近 7 天正确率 <60% | 测试效应 | "💡 你的物理正确率已连续 3 天低于 60%，建议今天多做练习题" |
| `plan_adjustment` | 连续 2 天以上计划完成率 <50% | 认知负荷理论 | "⚠️ 近 2 天计划完成度不足 50%，建议调整今日任务量" |
| `achievement` | 连续打卡、正确率提升等正向事件 | 自我效能感理论 | "🎉 你已连续学习 7 天，英语正确率较上周提升 15%！" |
| `general` | 无特定触发条件时的通用建议 | 间隔效应 | "🕐 今日计划学习 3 小时，建议拆分为 4 个番茄钟，每钟后休息 5 分钟" |

#### 4.3.4 建议追踪机制

- 每条建议被展示时，自动记录 `shown_at`
- 用户点击建议附带的行动按钮，记录 `acted_at`
- 次日建议生成时，AI 读取近 7 天的建议执行情况，判断：
  - 若上日的 `practice_suggestion` 用户已执行（正确率有改善），在今日建议中给予正向强化
  - 若上日的 `review_reminder` 用户已完成复习，该条建议不再重复
  - 若 `plan_adjustment` 建议连续 3 天未被响应，升级为"计划重新生成"提示

---

### 4.4 教师/家长监督视图（新增）

#### 4.4.1 学生列表页

- 展示所有已绑定的学生
- 每个学生卡片显示：昵称、年级、今日学习时长、近 7 天连续打卡、整体计划完成率
- 支持按"完成率"或"学习时长"排序
- 点击进入学生详情

#### 4.4.2 学生详情页

与学生端的"学习状况分析"布局相同，但：
- 只读模式，无法操作任何功能
- 顶部显示学生姓名 + 年级 + 最后活跃时间
- 新增"生成学生报告"按钮（PDF 导出）

**可查看的数据**：
- 近 7/30 天学习时长趋势
- 各学科正确率（雷达图）
- 计划生成及完成情况
- 错题本摘要（学科分布，不展示具体题目内容）
- 活跃度热力图

#### 4.4.3 绑定管理

**学生侧**：
- 在"个人中心"生成 6 位绑定码（有效期 24 小时）
- 可查看已绑定的教师/家长列表
- 可解除绑定

**教师侧**：
- 创建"班级"（班级名称 + 邀请码）
- 学生输入邀请码加入班级
- 可批量查看班级学生统计

**家长侧**：
- 输入学生生成的绑定码完成关联

---

## 5. 数据模型设计

### 5.1 User 表（扩展）

```python
class User(Base):
    __tablename__ = "users"
    # ... 现有字段 ...
    role = Column(String(20), nullable=False, default="student")  # student/teacher/parent（新增）
    last_login_date = Column(Date, nullable=True)                 # 最后登录日期（新增）
```

### 5.2 UserRelation 表（新增）

```python
class UserRelation(Base):
    """教师/家长 与 学生 的关联关系"""
    __tablename__ = "user_relations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    observer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # 观察者（教师/家长）
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # 被观察学生
    relation_type = Column(String(20), nullable=False)  # teacher / parent
    class_name = Column(String(50), nullable=True)      # 班级名称（教师用）
    created_at = Column(DateTime, nullable=False, server_default=func.now())
```

### 5.3 BindCode 表（新增）

```python
class BindCode(Base):
    """学生生成供家长/教师绑定的临时码"""
    __tablename__ = "bind_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String(10), nullable=False, unique=True, index=True)
    relation_type = Column(String(20), nullable=False)  # teacher / parent
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
```

### 5.4 ClassGroup 表（新增）

```python
class ClassGroup(Base):
    """教师创建的班级"""
    __tablename__ = "class_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    invite_code = Column(String(10), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
```

### 5.5 DailyAdvice 表（新增）

```python
class DailyAdvice(Base):
    """每日学习建议记录"""
    __tablename__ = "daily_advices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    advices_json = Column(Text, nullable=False)    # JSON 数组，存储当日所有建议条目
    generated_at = Column(DateTime, nullable=False, server_default=func.now())
    shown_at = Column(DateTime, nullable=True)     # 用户首次看到时间
```

### 5.6 AdviceAction 表（新增）

```python
class AdviceAction(Base):
    """用户对建议的响应记录（用于追踪建议执行情况）"""
    __tablename__ = "advice_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    advice_id = Column(Integer, ForeignKey("daily_advices.id"), nullable=False)
    advice_item_id = Column(String(50), nullable=False)  # 建议条目的唯一 ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    acted_at = Column(DateTime, nullable=False, server_default=func.now())
    outcome = Column(String(50), nullable=True)  # 执行后的效果评估（后台计算填充）
```

### 5.7 StudyPlan 表（扩展）

```python
class StudyPlan(Base):
    # ... 现有字段 ...
    study_style = Column(String(20), nullable=True, default="balanced")  # 新增
    preferred_times = Column(Text, nullable=True, default="[]")           # JSON array，新增
```

### 5.8 PlanTask 表（扩展）

```python
class PlanTask(Base):
    # ... 现有字段 ...
    is_overdue = Column(Boolean, nullable=False, default=False)        # 是否逾期，新增
    review_count = Column(Integer, nullable=False, default=0)          # 该知识点复习次数，新增
    notes = Column(Text, nullable=True)                                # 任务备注，新增
```

---

## 6. API 接口设计

### 6.1 用户角色与绑定

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/auth/register` | 注册时新增 `role` 字段（默认 `student`） |
| POST | `/api/relations/bind-code` | 学生生成绑定码 |
| POST | `/api/relations/bind` | 教师/家长使用绑定码绑定学生 |
| GET | `/api/relations/students` | 获取关联学生列表（教师/家长） |
| GET | `/api/relations/observers` | 获取自己的关联教师/家长列表（学生） |
| DELETE | `/api/relations/{relation_id}` | 解除关联 |
| POST | `/api/classes` | 教师创建班级 |
| GET | `/api/classes` | 获取我的班级列表 |
| POST | `/api/classes/join` | 学生通过邀请码加入班级 |

### 6.2 每日学习建议

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/advice/today` | 获取今日建议（触发生成逻辑） |
| POST | `/api/advice/{advice_id}/action` | 记录建议执行行为 |
| GET | `/api/advice/history` | 获取近 7 天建议历史 |

**GET `/api/advice/today` 响应示例**：
```json
{
  "code": 200,
  "data": {
    "date": "2026-06-09",
    "is_new": true,
    "advices": [
      {
        "id": "adv-001",
        "type": "review_reminder",
        "priority": 1,
        "icon": "📚",
        "title": "错题复习提醒",
        "content": "有 3 道数学错题（三角函数）距上次学习已满 7 天，正处遗忘临界期，建议今日复习。",
        "action": { "label": "去复习", "route": "/wrong-book", "params": { "subject": "数学" } },
        "theory_basis": "艾宾浩斯遗忘曲线：知识点在第7天遗忘率约75%，此时复习效率最高。"
      },
      {
        "id": "adv-002",
        "type": "achievement",
        "priority": 2,
        "icon": "🎉",
        "title": "进步值得鼓励",
        "content": "你的英语正确率本周从 62% 提升到 78%，词汇量在持续增长！",
        "action": null,
        "theory_basis": "自我效能感：阶段性进步的可视化反馈有助于维持学习动机。"
      }
    ]
  }
}
```

### 6.3 学习计划（增强）

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/plan/generate` | 生成计划（增加新参数） |
| GET | `/api/plan/current` | 获取当前计划 |
| GET | `/api/plan/today` | 获取今日任务 |
| PUT | `/api/plan/tasks/{task_id}/done` | 标记任务完成 |
| PUT | `/api/plan/tasks/{task_id}` | 修改单个任务（新增） |
| PUT | `/api/plan/tasks/reorder` | 拖拽排序（新增） |
| GET | `/api/plan/completion-stats` | 获取完成率统计（新增） |
| POST | `/api/plan/pomodoro` | 记录番茄钟 |
| GET | `/api/plan/pomodoro/today` | 获取今日番茄钟统计（新增） |

### 6.4 学习统计（增强）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/stats/overview` | 概览数据（增加计划完成率、掌握深度评分） |
| GET | `/api/stats/study-time` | 学习时长趋势（增加目标线数据） |
| GET | `/api/stats/accuracy-by-subject` | 各学科正确率 |
| GET | `/api/stats/wrong-book-distribution` | 错题分布 |
| GET | `/api/stats/radar` | 各学科雷达图数据（新增） |
| GET | `/api/stats/heatmap` | 近3月活跃度热力图数据（新增） |
| GET | `/api/stats/subject-time-distribution` | 各学科学习时长占比（新增） |
| POST | `/api/stats/generate-report` | 触发 AI 分析报告生成（新增，非流式） |
| GET | `/api/stats/latest-report` | 获取最新分析报告（新增） |
| POST | `/api/stats/study-log` | 记录学习时长 |

### 6.5 监督视图（教师/家长）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/monitor/students` | 获取关联学生列表（含摘要数据） |
| GET | `/api/monitor/students/{student_id}/overview` | 学生学习概览 |
| GET | `/api/monitor/students/{student_id}/stats` | 学生详细统计（与 /api/stats/* 结构相同） |
| GET | `/api/monitor/students/{student_id}/plan` | 学生当前学习计划（只读） |
| POST | `/api/monitor/students/{student_id}/report` | 为学生生成学习报告（PDF） |

---

## 7. 前端页面设计

### 7.1 学习计划页（`/plan`）增强

**新增区域**：
- 创建表单增加"学习风格"选择（均衡/冲刺/稳扎稳打）
- 今日任务列表支持逾期标注（🔴）和任务拖拽排序
- 番茄钟组件增加自定义时长选项 + 休息小贴士弹窗
- 页面右侧新增"整体完成率"进度环形图

**布局结构**：
```
┌────────────────────────────────────────┐
│  考试倒计时 | 今日完成 X/X | 整体完成率  │
│  ───────── 进度条 ──────────           │
├──────────────────┬─────────────────────┤
│  📋 今日任务列表  │  🍅 番茄钟          │
│  [任务1] ✅      │  25:00              │
│  [任务2] 🔴逾期  │  [开始] [重置]      │
│  [任务3]         │  今日: 🍅🍅🍅        │
│  [+ 自定义任务]  │  休息贴士: ...      │
├──────────────────┴─────────────────────┤
│  📅 本周计划日历视图（7天任务预览）      │
└────────────────────────────────────────┘
```

### 7.2 学习统计页（`/stats`）增强

**布局结构**：
```
┌──────────────────────────────────────────┐
│  概览卡片 × 6（含计划完成率、掌握深度）   │
├─────────────────────┬────────────────────┤
│  📈 学习时长趋势图   │  🕸️ 学科掌握雷达图  │
│  （折线 + 目标线）   │                    │
├─────────────────────┴────────────────────┤
│  📅 学习活跃度热力图（近3个月）           │
├─────────────────────┬────────────────────┤
│  📊 各学科正确率     │  🥧 学科时长占比    │
├─────────────────────┴────────────────────┤
│  📋 学习总览数据                          │
│  [🤖 生成AI深度分析报告]  [查看历史报告]  │
└──────────────────────────────────────────┘
```

### 7.3 每日建议组件（Dashboard 首页）

- **位置**：Dashboard 页面顶部，在问候语下方
- **样式**：渐变背景卡片，支持左右滑动切换
- **关闭逻辑**：点击 × 关闭，记录 `dismissed_at`，当日不再展示
- **深色主题**：icon + 标题 + 正文 + 理论依据（可折叠）+ 行动按钮

```
┌─────────────────────────────────────────┐
│  📚 错题复习提醒                    [×] │
│  有 3 道数学错题（三角函数）处于遗忘      │
│  临界期（距上次学习已 7 天），建议今日    │
│  复习以巩固记忆。                        │
│  ──────────────────────────────         │
│  📖 理论依据 ▼（点击展开）              │
│  [去复习 →]                             │
│  ← 1/3 →                               │
└─────────────────────────────────────────┘
```

### 7.4 教师/家长视图（新增页面）

**路由**：
- `/monitor` — 学生列表（教师/家长专属，无角色时重定向）
- `/monitor/students/:id` — 学生详情

**学生列表卡片**：
```
┌─────────────────────────────────────────┐
│  👤 张小明  高一                         │
│  今日: 1.5h  |  连续: 5天  |  完成率: 80%│
│  最后活跃: 10分钟前                      │
│  [查看详情]                              │
└─────────────────────────────────────────┘
```

---

## 8. AI 服务设计

### 8.1 每日建议生成（新增方法 `generate_daily_advice`）

**输入数据**（由后端服务层汇总传入）：
```python
{
    "student_info": { "nickname": "张小明", "grade": "高一" },
    "recent_stats": {
        "streak_days": 5,
        "today_plan_completion": 0.7,
        "recent_accuracy_trend": [0.62, 0.71, 0.78],  # 近3天
        "weak_subjects": ["数学", "物理"]
    },
    "due_reviews": [
        { "subject": "数学", "topic": "三角函数", "days_since_last_review": 7 }
    ],
    "previous_advice_outcomes": [
        { "type": "review_reminder", "acted": True, "outcome": "accuracy_improved" }
    ]
}
```

**Prompt 设计**：AI 基于以上数据，结合教育心理学理论，生成 JSON 格式的建议数组（3~5 条）。每条建议必须注明 `theory_basis` 字段，引用具体的理论依据。

### 8.2 学习分析报告生成（新增方法 `generate_study_report`）

**触发方式**：学生/教师点击按钮，后台异步生成，完成后缓存 24 小时。

**输入数据**：近 30 天的全量统计数据（学习时长、答题记录、计划执行、错题变化）。

**输出格式**：结构化 Markdown，约 500~800 字，含：
- 总体评价 + 量化数据（"过去 30 天共学习 XX 小时，答对 XX 题"）
- 优势学科分析（理论依据：布鲁姆分类的知识掌握层次）
- 薄弱环节分析（理论依据：遗忘曲线 + 测试效应）
- 行为模式洞察（高效时段、专注度趋势）
- 未来 7 天行动建议（具体、可执行）

### 8.3 学习计划生成（优化现有 `generate_study_plan`）

优化 Prompt，增加以下约束：
- 明确应用间隔重复：学习日后第 1、3、7 天自动插入复习任务
- 明确应用认知负荷原理：同一天不安排超过 3 个学科，单学科连续学习 ≤ 90 分钟
- 明确应用测试效应：每 2 个 `study` 任务配套 1 个 `practice` 任务

---

## 9. 实现路线图

### Phase 1：基础增强（预计 3~5 天）

- [ ] `User` 模型新增 `role`、`last_login_date` 字段
- [ ] 新增 `DailyAdvice`、`AdviceAction` 数据模型
- [ ] 实现每日建议生成 API 及 AI 方法
- [ ] 前端 Dashboard 增加每日建议卡片组件
- [ ] 学习统计页增加雷达图、热力图

### Phase 2：计划增强（预计 2~3 天）

- [ ] 学习计划生成优化（间隔复习插入、认知负荷约束）
- [ ] 任务拖拽排序、单任务修改
- [ ] 逾期任务标注逻辑
- [ ] 番茄钟自定义时长 + 休息贴士

### Phase 3：角色体系（预计 4~6 天）

- [ ] 新增 `UserRelation`、`BindCode`、`ClassGroup` 数据模型
- [ ] 实现绑定/解绑 API
- [ ] 教师班级管理功能
- [ ] 监督视图前后端实现（`/monitor` 路由）

### Phase 4：深度分析（预计 2~3 天）

- [ ] AI 学习分析报告生成
- [ ] 报告前端展示（Markdown 渲染）
- [ ] 学科时长占比图表
- [ ] 建议追踪效果评估逻辑

---

## 附录：关键指标计算公式

### 掌握深度评分（Mastery Score）

```
掌握深度(学科X) = 
    正确率(学科X) × 0.4 × 100 
  + 复习完成率(学科X) × 0.3 × 100 
  + 知识点覆盖率(学科X) × 0.3 × 100

其中：
  复习完成率 = 已复习错题数 / 到期复习错题总数
  知识点覆盖率 = 已练习过的知识点数 / 该学科课纲知识点总数
```

### 今日计划完成率

```
今日计划完成率 = 
    Σ(已完成任务时长) / Σ(今日计划任务总时长) × 100%
```

### 整体计划完成率

```
整体计划完成率 = 
    Σ(截至今日已完成任务数) / Σ(截至今日应完成任务总数) × 100%
  （未来日期的任务不纳入分母）
```

### 建议优先级评分

```
建议优先级 =
    遗忘风险分(0~40) 
  + 正确率下滑分(0~30) 
  + 计划偏差分(0~20) 
  + 成就激励分(0~10)

最终取 priority 最高的 3~5 条展示
```
