# Task 14: 更新 UserResponse Schema 添加 language 字段

## 文件修改

**Files:**
- Modify: `backend/schemas/user.py`

## Interfaces

**Produces:** 
- UserResponse 包含 language 字段

## 任务描述

在 UserResponse Pydantic schema 中添加 language 字段。

### 实现代码

```python
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    # ... 现有字段 ...
    language: str = 'zh'  # 新增
    
    class Config:
        from_attributes = True
```

## 报告位置

完成后报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-14-i18n-report.md`
