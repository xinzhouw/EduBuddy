# Task 15: 修改登录 API 返回 language 字段和国际化错误消息

## 文件修改

**Files:**
- Modify: `backend/routes/auth.py`

## Interfaces

**Consumes:**
- `get_language(accept_language)` 依赖（Task 12）
- `get_message(key, language)` 函数（Task 11）

**Produces:** 
- 登录端点在响应中包含 language 字段
- 错误消息根据语言返回

## 任务描述

改造登录 API 端点，使其支持多语言。

### 实现代码示例

```python
from api.dependencies import get_language
from services.i18n import get_message

@app.post("/api/auth/login")
async def login(
    credentials: LoginSchema,
    db: Session = Depends(get_db),
    language: str = Depends(get_language)
) -> dict:
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        error_msg = get_message('INVALID_CREDENTIALS', language)
        raise HTTPException(status_code=401, detail=error_msg)
    
    token = generate_jwt_token(user.id)
    
    return {
        'token': token,
        'user': UserResponse.from_orm(user),  # 包含 language 字段
        'message': get_message('LOGIN_SUCCESS', language)
    }
```

## 报告位置

完成后报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-15-i18n-report.md`
