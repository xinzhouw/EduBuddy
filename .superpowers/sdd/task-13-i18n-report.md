# Task 13 完成报告：User 模型添加 language 字段

## 状态
完成 ✓

## 修改文件
- `/home/xinzhouw/src/EduBuddy/backend/app/models/user.py`

## 变更内容

在 `User` 类的 `login_count` 列之后添加了 `language` 列：

```python
language = Column(String(10), nullable=False, default='zh')  # 界面语言：zh / en
```

## 字段规格
- 类型：`String(10)`
- 约束：`nullable=False`
- 默认值：`'zh'`（中文）
- 支持值：`zh`（中文）、`en`（英文）

## 说明
字段插入位置在 `login_count` 和 `created_at` 之间，与其他用户属性字段（gender、age 等）保持分组一致。数据库迁移将由 SQLAlchemy 的 `create_all` 或 Alembic 迁移脚本在服务重启时自动处理。
