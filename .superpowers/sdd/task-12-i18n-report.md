# Task 12 完成报告：get_language 依赖注入函数

## 状态：已完成

## 修改文件

- `backend/app/dependencies.py`（注意：实际路径为 `backend/app/`，而非 brief 中的 `backend/api/`）

## 变更内容

1. 在 import 行添加了 `Header` 到 fastapi 导入中
2. 在 `require_rate_limit` 函数前新增 `get_language` 函数

## 实现代码

```python
def get_language(accept_language: str = Header(default='zh')) -> str:
    """
    从 Accept-Language header 提取语言代码。
    返回 'zh' 或 'en'，默认 'zh'
    """
    if accept_language == 'en':
        return 'en'
    return 'zh'
```

## 接口说明

- **函数签名**：`get_language(accept_language: str = Header(default='zh')) -> str`
- **Header 名称**：`Accept-Language`（FastAPI 自动将参数名 `accept_language` 映射为 `accept-language` header）
- **返回值**：`'en'` 或 `'zh'`（默认 `'zh'`）
- **用法示例**：
  ```python
  from app.dependencies import get_language

  @router.get("/some-endpoint")
  def handler(lang: str = Depends(get_language)):
      ...
  ```
