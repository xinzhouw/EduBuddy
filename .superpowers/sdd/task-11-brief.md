# Task 11: 创建国际化消息服务

## 文件修改

**Files:**
- Create: `backend/services/i18n.py`

## Interfaces

**Produces:**
- `MESSAGES: dict[str, dict[str, str]]` - 多语言消息映射
- `get_message(key: str, language: str) -> str` - 根据 key 和语言获取消息

## 任务描述

创建后端的国际化消息服务，定义所有错误和系统消息的多语言版本。

### 实现代码示例

```python
MESSAGES = {
    'zh': {
        'INVALID_CREDENTIALS': '邮箱或密码错误',
        'EMAIL_NOT_FOUND': '邮箱不存在',
        # ... 更多消息
    },
    'en': {
        'INVALID_CREDENTIALS': 'Invalid email or password',
        'EMAIL_NOT_FOUND': 'Email not found',
        # ... 更多消息
    }
}

def get_message(key: str, language: str = 'zh') -> str:
    return MESSAGES.get(language, {}).get(key, MESSAGES.get('zh', {}).get(key, key))
```

## 报告位置

完成后报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-11-i18n-report.md`
