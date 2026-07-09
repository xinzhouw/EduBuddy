# Task 16 完成报告：创建更新用户语言偏好 API 端点

## 状态
已完成 ✅

## 修改文件

1. **新建** `/home/xinzhouw/src/EduBuddy/backend/app/routers/users.py`
2. **修改** `/home/xinzhouw/src/EduBuddy/backend/app/services/i18n.py`（添加 `LANGUAGE_UPDATED` / `INVALID_LANGUAGE` 消息键）
3. **修改** `/home/xinzhouw/src/EduBuddy/backend/app/main.py`（注册 users router）

## 端点规格

**路径**：`PATCH /api/users/preferences`  
**认证**：Bearer token（`get_current_user` 依赖）  
**请求体**（JSON）：
```json
{ "language": "zh" }
```
或
```json
{ "language": "en" }
```

**成功响应（200）**：
```json
{
  "code": 200,
  "message": "语言偏好已更新",
  "data": {
    "user": { ...UserOut fields including language... }
  }
}
```

**错误响应（400）**：
```json
{ "detail": "不支持的语言代码，请使用 zh 或 en" }
```

## 实现细节

- 使用 `UpdateLanguageRequest(BaseModel)` 接收 JSON 请求体中的 `language` 字段（与前端 axios `patch(url, { language })` 调用保持一致）
- 验证语言值为 `'zh'` 或 `'en'`，否则返回 400；错误消息通过 `get_message('INVALID_LANGUAGE', current_user.language)` 本地化
- 更新 `current_user.language` 后 `db.commit()` + `db.refresh()`
- 成功消息通过 `get_message('LANGUAGE_UPDATED', data.language)` 返回新语言版本
- `UserOut` 模式（已包含 `language` 字段）序列化完整用户数据

## 依赖说明

- `app.services.i18n.get_message`：i18n 服务已存在，本次添加 `LANGUAGE_UPDATED` 和 `INVALID_LANGUAGE` 两个消息键（中/英文）
- `app.schemas.auth.UserOut`：已包含 `language: str = 'zh'` 字段（由先前任务完成）
- `app.models.user.User`：已包含 `language` 列（由 Task 13 完成）
