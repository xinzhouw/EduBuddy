# Task 16: 创建更新用户语言偏好 API 端点

## 文件修改

**Files:**
- Create or Modify: `backend/api/routes/users.py`

## Interfaces

**Consumes:**
- `get_current_user` 依赖
- `get_message()` 函数

**Produces:** 
- PATCH `/api/users/preferences` 端点

## 任务描述

创建新的 API 端点用于更新用户语言偏好。

### 实现代码

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.dependencies import get_db, get_current_user
from services.i18n import get_message
from schemas.user import UserResponse
from models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])

@router.patch("/preferences")
async def update_language_preference(
    language: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    if language not in ['zh', 'en']:
        raise HTTPException(status_code=400, detail="Invalid language code")
    
    current_user.language = language
    db.commit()
    db.refresh(current_user)
    
    return {
        'user': UserResponse.from_orm(current_user),
        'message': get_message('LANGUAGE_UPDATED', language)
    }
```

在主应用中注册此路由。

## 报告位置

完成后报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-16-i18n-report.md`
