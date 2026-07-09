# Task 10 完成报告：创建数据库迁移脚本

## 状态：完成

## 完成时间
2026-07-09

## 变更文件

| 文件 | 操作 |
|------|------|
| `backend/migrations/002_add_language_to_users.py` | 新建 - 幂等迁移脚本 |
| `backend/app/database.py` | 修改 - 注册 language 列到自动迁移列表 |

## 实现说明

### 迁移脚本（002_add_language_to_users.py）
- 遵循项目已有的迁移模式（参考 `001_add_chat_images_table.py`）
- 提供 `migrate_up(engine)` 和 `migrate_down(engine)` 两个函数
- `migrate_up` 是幂等的：先检查列是否存在，避免重复执行报错
- 列定义：`VARCHAR(10) NOT NULL DEFAULT 'zh'`
- `migrate_down` 因 SQLite 兼容性不支持 DROP COLUMN，打印提示信息

### database.py 更新
在 `_apply_lightweight_migrations()` 的 `column_additions` 列表中增加：
```python
("users", "language", "VARCHAR(10) NOT NULL DEFAULT 'zh'"),
```
这确保应用重启时自动为现有数据库补充 `language` 列，无需手动执行迁移。

### 迁移执行结果
```
✓ Added column 'language' to users table
```
验证：`PRAGMA table_info(users)` 确认列已存在：
```
(20, 'language', 'VARCHAR(10)', 1, "'zh'", 0)
```

## Git 提交
Commit: `6b6199c`
`feat: add language column migration for users table (i18n task 10)`

## 注意事项

- 项目未使用 Alembic，而是自定义的迁移系统（`migrations/` 目录 + `database.py` 内的轻量自动迁移）
- 本任务 brief 提到的 `alembic revision` 命令实际对应项目中的手动迁移文件创建
- `language` 列已在 User 模型（`app/models/user.py`）中定义，本迁移确保现有数据库同步
