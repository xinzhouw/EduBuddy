# Task 10: 创建数据库迁移脚本

## 文件修改

**Files:**
- Create: `backend/alembic/versions/<timestamp>_add_language_to_users.py`

## Interfaces

**Produces:** 
- 数据库迁移脚本，向 users 表添加 language 列

## 任务描述

使用 Alembic 创建迁移脚本，向 users 表添加 language 字段。

### 实现步骤

1. 运行 `alembic revision -m "add_language_to_users"` 生成新迁移文件
2. 编辑迁移文件，在 upgrade() 中添加 language 列：
   ```python
   op.add_column('users', sa.Column('language', sa.String(10), nullable=False, server_default='zh'))
   ```
3. 在 downgrade() 中添加回滚：
   ```python
   op.drop_column('users', 'language')
   ```
4. 运行迁移：`alembic upgrade head`
5. 提交迁移脚本

## 报告位置

完成后报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-10-i18n-report.md`
