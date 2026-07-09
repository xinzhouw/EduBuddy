# Task 19: 后端 API 多语言支持测试报告

**日期**: 2026-07-09  
**测试环境**: 本地后端 http://127.0.0.1:8002 (app.main:app)  
**总体结论**: **全部测试通过 ✅**

---

## 测试结果汇总

| # | 测试项 | 预期 | 实际 | 状态 |
|---|--------|------|------|------|
| 1 | 登录 API 中文错误 (Accept-Language: zh) | 返回中文错误消息 | "邮箱或密码错误" | PASS |
| 2 | 登录 API 英文错误 (Accept-Language: en) | 返回英文错误消息 | "Invalid email or password" | PASS |
| 3 | 登录成功 language 字段 | user 对象包含 language 字段 | language: "zh" | PASS |
| 4 | PATCH /api/users/preferences (en) | 成功更新语言偏好 | 200, "Language preference updated" | PASS |
| 5 | PATCH /api/users/preferences (无效值) | 400 错误 | "Unsupported language code, please use zh or en" | PASS |
| 6 | PATCH /api/users/preferences (回退到 zh) | 成功更新语言偏好 | 200, "语言偏好已更新" | PASS |
| 7 | 数据库 language 字段持久化 | language 字段正确保存 | zh/en 均可持久化 | PASS |
| 8 | 英文登录成功消息 | 返回英文成功消息 | "Login successful" | PASS |
| 9 | 未支持语言 fallback (Accept-Language: fr) | fallback 到中文 | "邮箱或密码错误" | PASS |

---

## 实现架构

### 核心文件

- `/home/xinzhouw/src/EduBuddy/backend/app/services/i18n.py` — 消息字典，支持 `zh` / `en`，缺失 key 自动 fallback 到 zh
- `/home/xinzhouw/src/EduBuddy/backend/app/dependencies.py` — `get_language()` 函数，解析 `Accept-Language` header，返回 `zh` 或 `en`
- `/home/xinzhouw/src/EduBuddy/backend/app/routers/auth.py` — 登录端点使用 `Depends(get_language)` 和 `get_message(key, language)`
- `/home/xinzhouw/src/EduBuddy/backend/app/routers/users.py` — `PATCH /api/users/preferences` 端点
- `/home/xinzhouw/src/EduBuddy/backend/app/models/user.py` — `language = Column(String(10), default='zh')`
- `/home/xinzhouw/src/EduBuddy/backend/app/schemas/auth.py` — `UserOut.language: str = 'zh'`

### i18n 工作流程

```
请求 Accept-Language: en
       ↓
get_language() → 返回 "en"
       ↓
login() 中 language = "en"
       ↓
get_message("INVALID_CREDENTIALS", "en") → "Invalid email or password"
```

### get_language 实现

```python
def get_language(accept_language: str = Header(default='zh')) -> str:
    if accept_language == 'en':
        return 'en'
    return 'zh'  # 默认中文，所有未知值都 fallback 到 zh
```

---

## 测试用 curl 命令

```bash
# 测试中文错误消息
curl -X POST http://127.0.0.1:8002/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Accept-Language: zh" \
  -d '{"email":"wrong@test.com","password":"wrong123"}'
# 返回: {"detail": {"message": "邮箱或密码错误", ...}}

# 测试英文错误消息
curl -X POST http://127.0.0.1:8002/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Accept-Language: en" \
  -d '{"email":"wrong@test.com","password":"wrong123"}'
# 返回: {"detail": {"message": "Invalid email or password", ...}}

# 更新语言偏好（需要 Bearer token）
curl -X PATCH http://127.0.0.1:8002/api/users/preferences \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"language":"en"}'
# 返回: {"code": 200, "message": "Language preference updated", "data": {"user": {..., "language": "en"}}}
```

---

## 注意事项

### Docker 容器 vs 本地后端

- **端口 8001**: Docker 容器内旧版本，`UserOut` 响应缺少 `language` 字段（容器代码未更新）
- **端口 8002**: 本地 `/home/xinzhouw/src/EduBuddy/backend`，含完整 i18n 实现，所有测试通过

**建议**: 重新构建 Docker 镜像以同步最新代码。

### 语言切换逻辑

- `PATCH /api/users/preferences` 错误消息语言由 `current_user.language` 决定（非 `Accept-Language` header）
- 这意味着：用户已将语言设置为 `en` 后，无效语言请求会返回英文错误消息 — 行为符合设计预期

---

## 结论

Task 19 后端 API 多语言支持已完整实现并通过全部测试：
1. `Accept-Language` header 正确控制错误消息语言
2. 登录成功响应包含 `language` 字段
3. `PATCH /api/users/preferences` 端点正常工作
4. 数据库 `language` 字段正确持久化
5. 不支持的语言代码自动 fallback 到中文
