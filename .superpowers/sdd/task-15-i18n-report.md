# Task 15 完成报告：修改登录 API 支持多语言

## 状态：已完成

## 修改文件

1. `backend/app/routers/auth.py` — 登录端点国际化改造
2. `backend/app/services/i18n.py` — 补充 `LOGIN_SUCCESS` 消息键

---

## 变更详情

### `backend/app/routers/auth.py`

**新增 import（第 10-11 行）：**
```python
from app.dependencies import ..., get_language
from app.services.i18n import get_message
```

**登录端点签名（第 157 行）：**
```python
def login(data: UserLogin, db: Session = Depends(get_db), request: Request = None, language: str = Depends(get_language)):
```

**错误消息改造（3 处）：**
| 位置 | 原文本（硬编码中文） | 改为 |
|------|---------------------|------|
| 速率限制 429 | `f"登录过于频繁，请在 {retry_after} 秒后重试"` | `get_message("RATE_LIMIT_EXCEEDED", language)` |
| 凭证错误 401 | `"邮箱或密码错误"` | `get_message("INVALID_CREDENTIALS", language)` |
| 账户禁用 401 | `"邮箱或密码错误"` | `get_message("INVALID_CREDENTIALS", language)`（保持防枚举一致性） |

**成功响应消息：**
```python
"message": get_message("LOGIN_SUCCESS", language)
```

**user 字段：** `UserOut.model_validate(user)` 序列化后已包含 `language` 字段（Task 13 已在 `UserOut` schema 和 `User` model 中添加）。

---

### `backend/app/services/i18n.py`

补充了 `LOGIN_SUCCESS` 键（原文件中缺失）：
```python
"zh": { "LOGIN_SUCCESS": "登录成功", ... }
"en": { "LOGIN_SUCCESS": "Login successful", ... }
```

（`i18n.py` 文件已在 Task 11 阶段由其他 agent 创建完成，包含所有其他认证相关键。）

---

## 依赖状态确认

| 依赖 | 来源 Task | 状态 |
|------|-----------|------|
| `get_language` in `app/dependencies.py` | Task 12 | 已存在（Line 117） |
| `get_message` in `app/services/i18n.py` | Task 11 | 已存在，已补充 `LOGIN_SUCCESS` |
| `language` field in `UserOut` / `User` model | Task 13 | 已存在 |

---

## 行为说明

- 客户端发送 `Accept-Language: en` header → 登录错误/成功消息返回英文
- 客户端不发送或发送其他值 → 默认返回中文
- `user` 对象包含 `language` 字段，前端可读取用户存储的语言偏好
