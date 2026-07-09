# Task 14 完成报告：UserResponse Schema 添加 language 字段

## 状态
已完成

## 变更内容

**修改文件：** `backend/app/schemas/auth.py`

**变更：** 在 `UserOut` 类中添加 `language: str = 'zh'` 字段

> 注：任务简报中称该类为 `UserResponse`，实际代码中对应类名为 `UserOut`，功能等同。

## 说明

- User 数据库模型（`backend/app/models/user.py`，第 24 行）已包含 `language` 列，默认值为 `'zh'`
- `UserOut` schema 新增 `language: str = 'zh'` 字段，与模型保持一致
- `from_attributes = True` 已存在，ORM 对象可直接序列化

## 受影响接口

所有返回 `UserOut` 的 API 响应（登录、注册、获取用户信息等）现在将包含 `language` 字段。
