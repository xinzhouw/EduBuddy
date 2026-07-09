# Task 12: 创建 get_language 依赖注入函数

## 文件修改

**Files:**
- Create or Modify: `backend/api/dependencies.py`

## Interfaces

**Produces:**
- `get_language(accept_language: str = Header(...)) -> str` - FastAPI 依赖，从 header 提取语言

## 任务描述

创建 FastAPI 依赖注入函数，从 Accept-Language header 提取语言代码。

### 实现代码

```python
from fastapi import Header

def get_language(accept_language: str = Header(default='zh')) -> str:
    """
    从 Accept-Language header 提取语言代码。
    返回 'zh' 或 'en'，默认 'zh'
    """
    if accept_language == 'en':
        return 'en'
    return 'zh'
```

## 报告位置

完成后报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-12-i18n-report.md`
