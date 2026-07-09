# Task 2 Report: 创建 i18n 配置文件

## 状态: DONE

## 创建的文件

| 文件 | 说明 |
|------|------|
| `frontend/src/i18n/index.ts` | vue-i18n 配置，`legacy: false`，默认语言 `zh` |
| `frontend/src/i18n/locales/zh.json` | 中文翻译，87 个 key（4 类） |
| `frontend/src/i18n/locales/en.json` | 英文翻译，87 个 key（4 类，结构相同） |

## 翻译内容概览

| 类别 | Keys 数量 | 内容 |
|------|-----------|------|
| common | 27 | yes/no/confirm/cancel/save/delete 等通用文本 |
| auth | 31 | login/logout/register/email/password 等认证相关 |
| navigation | 14 | dashboard/ai_chat/notes/homework 等导航菜单 |
| error | 15 | network_error/server_error/unauthorized 等错误消息 |

## 验证结果

```
zh top-level keys: auth,common,error,navigation
en top-level keys: auth,common,error,navigation
Keys match: true
common: zh=27, en=27 OK
auth: zh=31, en=31 OK
navigation: zh=14, en=14 OK
error: zh=15, en=15 OK
```

JSON 格式正确，无解析错误，zh/en 结构完全一致。

## Commit ID

`fd9cdab` — feat(i18n): create i18n config and translation files (Task 2)

## 观察与注意

- `index.ts` 使用 `legacy: false` 确保 Composition API 兼容
- `fallbackLocale: 'zh'` 确保找不到 key 时回退到中文
- 翻译 key 均采用英文小写下划线命名（符合全局约束）
- navigation 的 key 与 router 路由名称对应（dashboard/ai_chat/notes 等）
- main.ts 尚未注册 i18n 实例（由 Task 后续步骤处理）
