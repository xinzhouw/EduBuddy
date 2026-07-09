# Task 13: 更新 User 模型添加 language 字段

## 文件修改

**Files:**
- Modify: `backend/models/user.py`

## Interfaces

**Produces:** 
- User 模型包含 language 列

## 任务描述

在 User SQLAlchemy 模型中添加 language 字段。

### 实现代码

在 User 类中添加：

```python
from sqlalchemy import Column, String

class User(Base):
    __tablename__ = 'users'
    
    # ... 现有列 ...
    
    language = Column(String(10), nullable=False, default='zh')
```

## 报告位置

完成后报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-13-i18n-report.md`
