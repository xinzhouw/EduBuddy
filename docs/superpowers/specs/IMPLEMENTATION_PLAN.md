# 实现计划：微信公众号 AI 问答集成

**关联文档：** [2026-06-18-wechat-integration-design.md](2026-06-18-wechat-integration-design.md)  
**计划日期：** 2026-06-18  
**预计工作量：** 2-3 天

---

## 概述

为 EduBuddy 平台集成微信公众号 AI 问答功能。用户通过微信绑定 EduBuddy 账户，即可在微信中直接与 AI 对话。设计采用异步处理 + 消息推送的方案，规避微信 5 秒超时限制。

---

## 架构决策

| 决策 | 理由 |
|------|------|
| 异步处理 + 客服推送 | 微信回调 5 秒超时，AI 生成往往需要 10-30 秒。立即返回成功，后台推送结果。 |
| 绑定码验证 | 不依赖第三方 OAuth，简单可靠。用户需要主动发送绑定码，防止冒充。 |
| 复用现有 AI 服务 | 不重复开发，使用现有的 `ai_service.chat_stream()` 和 `rag_service.retrieve()`。 |
| 无消息持久化 | 微信对话不保存到 `chat_sessions` 表，保持轻量级。用户可稍后在 web 重新提问。 |
| 手动实现微信接口 | 不依赖第三方 SDK，减少外部依赖。核心代码量少，易维护。 |

---

## 任务依赖图

```
数据库迁移（Task 1）
    ↓
环境变量配置（Task 2）
    ├→ 微信工具模块（Task 3）
    │   ├→ 绑定接口（Task 4）
    │   ├→ 微信服务层（Task 5）
    │   │   ├→ 微信路由（Task 6）
    │   │   └→ 后台任务队列（Task 7）
    │
    └→ 用户相关接口（Task 8）

[Checkpoint 1: 后端完成]

    ├→ 前端绑定页面（Task 9）
    ├→ 前端 API 层（Task 10）

[Checkpoint 2: 前端完成]

    ├→ 单元测试（Task 11）
    ├→ 集成测试（Task 12）
    ├→ 手动测试和部署验证（Task 13）

[Checkpoint 3: 完成]
```

---

## 第一阶段：后端基础设施

### Task 1：数据库迁移 - 新增微信字段

**描述：** 为 `users` 表新增微信绑定字段，创建临时绑定码表。

**验收标准：**
- [ ] `users` 表新增 `wechat_openid`（VARCHAR, UNIQUE, nullable）
- [ ] `users` 表新增 `wechat_bound_at`（DATETIME, nullable）
- [ ] `users` 表新增 `wechat_nickname`（VARCHAR, nullable）
- [ ] 新建 `wechat_binding_codes` 表（id, user_id, code, expires_at, created_at）
- [ ] 创建索引：`idx_wechat_openid`、`idx_wechat_code`
- [ ] 现有用户数据无损，可以向后兼容

**文件修改：**
- 创建：`backend/app/database_migrations/001_add_wechat_fields.py`（迁移脚本）
- 修改：`backend/app/models/user.py`（新增 ORM 字段）
- 创建：`backend/app/models/wechat_binding_code.py`（新 ORM 模型）

**验证步骤：**
```bash
python backend/app/database.py  # 执行初始化，验证表创建
sqlite3 backend/data/edubuddy.db ".schema users"  # 检查 users 表结构
```

**依赖：** None

**预计范围：** Small（2 文件修改）

---

### Task 2：环境变量配置

**描述：** 在 `config.py` 中新增微信相关的环境变量配置。

**验收标准：**
- [ ] `WECHAT_APP_ID` 配置读取
- [ ] `WECHAT_APP_SECRET` 配置读取
- [ ] `WECHAT_TOKEN` 配置读取（用于回调验证）
- [ ] `WECHAT_ENCODING_AES_KEY` 配置读取（可选）
- [ ] `WECHAT_ENABLE_ENCRYPTION` 配置读取（默认 false）
- [ ] `WECHAT_BIND_CODE_EXPIRY_MINUTES` 配置读取（默认 10）
- [ ] `.env` 示例文件更新
- [ ] 所有配置项有默认值或必填标记

**文件修改：**
- 修改：`backend/app/config.py`
- 修改：`.env.example`

**验证步骤：**
```python
from app.config import settings
assert settings.wechat_token is not None
assert settings.wechat_bind_code_expiry_minutes == 10
```

**依赖：** None

**预计范围：** Small（1 文件修改）

---

### Task 3：微信工具模块

**描述：** 实现微信消息处理的核心工具函数（签名校验、XML 解析、消息生成等）。

**验收标准：**
- [ ] `validate_wechat_signature(request) → bool` — SHA1 签名校验
- [ ] `parse_wechat_xml(body: bytes) → dict` — XML 消息解析
- [ ] `generate_wechat_reply(to_openid, content) → str` — 生成 XML 回复
- [ ] `split_message(text, max_length=2048, max_parts=5) → List[str]` — 消息分段
- [ ] `get_wechat_access_token() → str` — 获取 access_token（缓存，1 小时过期）
- [ ] `send_wechat_customer_message(openid, content) → bool` — 通过客服接口推送
- [ ] 所有函数有单元测试，覆盖 > 90%
- [ ] 错误处理完善（无效 XML、网络超时等）

**文件修改：**
- 创建：`backend/app/utils/wechat_utils.py`（核心工具）
- 创建：`tests/test_wechat_utils.py`（单元测试）

**验证步骤：**
```python
from app.utils.wechat_utils import parse_wechat_xml, validate_wechat_signature
# 测试签名校验
# 测试 XML 解析
# 测试消息分段
```

**依赖：** Task 2（需要读取 WECHAT_TOKEN）

**预计范围：** Medium（核心逻辑 ~200 行代码）

---

### Task 4：绑定接口（用户相关）

**描述：** 实现后端接口支持用户生成绑定码和解除绑定。

**验收标准：**
- [ ] `POST /api/user/wechat/bind-code` — 生成绑定码
  - 请求：认证用户
  - 响应：`{ code: "123456", expires_in: 600 }`（秒）
  - 生成的码保存到 `wechat_binding_codes` 表，有效期 10 分钟
  - 同用户旧码自动失效
- [ ] `DELETE /api/user/wechat/unbind` — 解除绑定
  - 请求：认证用户
  - 响应：`{ success: true }`
  - 清除 `wechat_openid`、`wechat_bound_at`、`wechat_nickname`
- [ ] `GET /api/user/wechat/status` — 获取绑定状态
  - 响应：`{ is_bound: bool, nickname: string, bound_at: datetime }`
- [ ] 仅学生角色可绑定微信
- [ ] 单元测试 > 80%

**文件修改：**
- 创建：`backend/app/routers/user_wechat.py`（新路由）
- 修改：`backend/app/main.py`（注册路由）
- 创建：`tests/test_user_wechat.py`（单元测试）

**验证步骤：**
```bash
curl -X POST http://localhost:8000/api/user/wechat/bind-code \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
# 验证返回 { code: "...", expires_in: 600 }
```

**依赖：** Task 1, 2, 3

**预计范围：** Medium（3 个接口，~100 行代码）

---

### Task 5：微信服务层

**描述：** 实现微信消息处理的业务逻辑服务。

**验收标准：**
- [ ] `handle_bind_command(openid, code) → bool` — 处理绑定指令
  - 查询绑定码，验证有效性
  - 找到对应用户，保存 openid
  - 返回成功/失败
- [ ] `send_ai_response_async(openid, user_id, message) → Task` — 异步 AI 处理
  - RAG 检索
  - 调用 AI 服务流式生成
  - 分段推送至微信
  - 错误处理和降级
- [ ] `rate_limit_check(user_id, limit_per_minute=3, limit_per_day=100) → bool` — 速率限制
- [ ] 所有方法异步化（async）
- [ ] 单元测试 > 85%

**文件修改：**
- 创建：`backend/app/services/wechat_service.py`（业务逻辑）
- 创建：`tests/test_wechat_service.py`（单元测试）

**验证步骤：**
```python
from app.services.wechat_service import rate_limit_check
# 测试绑定流程
# 测试 AI 异步处理
# 测试速率限制
```

**依赖：** Task 1, 3, 4

**预计范围：** Large（~300 行代码，含 AI 集成）

---

### Task 6：微信回调路由

**描述：** 实现微信官方服务器回调接收和分发。

**验收标准：**
- [ ] `GET /api/wechat/callback` — 服务器接入验证（微信服务器验证）
  - 校验签名
  - 返回 `echostr` 参数
- [ ] `POST /api/wechat/callback` — 接收用户消息和事件
  - 校验签名
  - 解密消息（如果启用）
  - 解析 XML
  - 路由到相应处理函数
  - 立即返回成功 XML
  - 启动后台任务
- [ ] 仅接受文本消息，其他消息类型返回提示
- [ ] 完善的错误处理和日志
- [ ] 单元测试 > 85%

**文件修改：**
- 创建：`backend/app/routers/wechat.py`（回调路由）
- 修改：`backend/app/main.py`（注册路由）
- 创建：`tests/test_wechat_routes.py`（单元测试）

**验证步骤：**
```bash
# 模拟微信服务器验证请求
curl "http://localhost:8000/api/wechat/callback?signature=...&timestamp=...&nonce=...&echostr=..."
# 验证返回 echostr 值

# 模拟用户消息
curl -X POST http://localhost:8000/api/wechat/callback \
  -H "Content-Type: application/xml" \
  -d "<xml>...</xml>"
# 验证立即返回 success
```

**依赖：** Task 2, 3, 5

**预计范围：** Medium（~150 行代码）

---

### Task 7：后台任务队列配置

**描述：** 设置后台任务队列（用于异步推送 AI 回复）。

**验收标准：**
- [ ] FastAPI 后台任务集成（`BackgroundTasks`）或 Celery（如使用）
- [ ] `background_tasks.add_task()` 在回调中调用
- [ ] 任务不阻塞 HTTP 响应
- [ ] 任务失败时有重试机制（最多 3 次）
- [ ] 任务执行结果可查询（可选）
- [ ] 单元测试 > 80%

**文件修改：**
- 修改：`backend/app/main.py`（配置任务队列）
- 修改：`backend/app/routers/wechat.py`（调用后台任务）
- 创建/修改：`tests/test_background_tasks.py`

**验证步骤：**
```python
from fastapi import BackgroundTasks
# 验证后台任务运行
```

**依赖：** Task 5, 6

**预计范围：** Small（集成现有框架）

---

## 第二阶段：用户相关接口

### Task 8：用户模型扩展（schema 层）

**描述：** 在用户 schema 中新增微信相关字段。

**验收标准：**
- [ ] `UserResponse` schema 新增 `wechat_openid`（可选）
- [ ] `UserResponse` 新增 `wechat_bound_at`（可选）
- [ ] `UserResponse` 新增 `wechat_nickname`（可选）
- [ ] `UserUpdate` schema 新增绑定状态字段（仅后端设置）
- [ ] 序列化时不暴露敏感信息

**文件修改：**
- 修改：`backend/app/schemas/user.py`

**依赖：** Task 1

**预计范围：** XS（1 文件修改）

---

## 第三阶段：前端集成

### Task 9：前端绑定页面

**描述：** 在账户设置页面新增微信绑定功能。

**验收标准：**
- [ ] 账户设置页面新增"微信绑定"标签
- [ ] 未绑定时：显示"生成绑定码"按钮
  - 点击后调用 API 生成码
  - 显示 6 位绑定码和 10 分钟倒计时
  - 显示"复制"和"刷新"按钮
  - 显示操作说明："在微信给公众号发送：bind 123456"
- [ ] 已绑定时：显示微信昵称、绑定时间、"解除绑定"按钮
- [ ] 解除绑定前显示确认对话框
- [ ] 加载态和错误提示
- [ ] 移动端适配（响应式）
- [ ] 单元测试 > 70%

**文件修改：**
- 修改：`frontend/src/views/AccountSettings.vue`
- 创建：`frontend/src/components/WechatBindingSection.vue`（绑定组件）
- 创建：`tests/AccountSettings.spec.ts`

**验证步骤：**
```bash
npm run dev  # 启动前端
# 导航到账户设置
# 验证微信绑定界面显示正常
# 验证生成绑定码功能
```

**依赖：** Task 4

**预计范围：** Medium（2-3 个新/修改组件）

---

### Task 10：前端 API 层

**描述：** 为微信绑定功能新增 API 客户端。

**验收标准：**
- [ ] `POST /api/user/wechat/bind-code` 调用封装
- [ ] `DELETE /api/user/wechat/unbind` 调用封装
- [ ] `GET /api/user/wechat/status` 调用封装
- [ ] 错误处理和拦截器集成
- [ ] TypeScript 类型定义完整
- [ ] 单元测试 > 80%

**文件修改：**
- 创建：`frontend/src/api/wechat.ts`
- 修改：`frontend/src/api/index.ts`（导出）
- 创建：`tests/api/wechat.spec.ts`

**验证步骤：**
```typescript
import { userApi } from "@/api";
// 验证 API 调用
```

**依赖：** Task 4

**预计范围：** Small（~50 行代码）

---

## 第四阶段：测试

### Task 11：单元测试

**描述：** 为后端各模块编写单元测试。

**验收标准：**
- [ ] `test_wechat_utils.py`：签名校验、XML 解析、消息分段 > 95%
- [ ] `test_wechat_service.py`：绑定、AI 处理、速率限制 > 90%
- [ ] `test_user_wechat.py`：绑定接口、解绑接口 > 85%
- [ ] `test_wechat_routes.py`：回调路由 > 85%
- [ ] 所有测试用例运行通过
- [ ] 代码覆盖率 > 85%

**文件修改：**
- 创建/修改：`tests/test_wechat_*.py`（各模块测试）

**验证步骤：**
```bash
pytest backend/tests/test_wechat_*.py -v --cov=app
# 验证覆盖率 > 85%
```

**依赖：** Task 3, 4, 5, 6

**预计范围：** Large（~500 行测试代码）

---

### Task 12：集成测试

**描述：** 测试完整的绑定和消息处理流程。

**验收标准：**
- [ ] 测试完整绑定流程：生成码 → 发送 bind 指令 → 绑定成功
- [ ] 测试完整消息处理流程：发送问题 → AI 处理 → 推送回复
- [ ] 测试错误场景：未绑定用户、码过期、API 异常等
- [ ] 测试速率限制生效
- [ ] 所有测试用例运行通过
- [ ] 测试覆盖主要业务流程

**文件修改：**
- 创建：`tests/integration/test_wechat_flow.py`

**验证步骤：**
```bash
pytest tests/integration/test_wechat_flow.py -v
# 验证所有集成测试通过
```

**依赖：** Task 11

**预计范围：** Large（~300 行测试代码）

---

### Task 13：手动测试和部署验证

**描述：** 人工测试微信回调流程，验证端到端功能。

**验收标准：**
- [ ] 能在微信开发者工具中模拟回调
- [ ] 能成功生成绑定码
- [ ] 能通过微信发送 `bind` 指令并绑定成功
- [ ] 能通过微信发送问题并收到 AI 回复（如有真实公众号）
- [ ] 错误消息显示正常
- [ ] 性能可接受（响应 < 5 秒）
- [ ] 日志记录完整
- [ ] 生产环境配置验证

**验证检查清单：**
- [ ] 服务器 IP 已添加到微信白名单
- [ ] 所有环境变量已配置
- [ ] 数据库迁移已执行
- [ ] 后端和前端均构建成功
- [ ] 无未处理的异常或警告
- [ ] 监控和告警已配置

**依赖：** Task 1-12

**预计范围：** Large（人工验证 + 部署）

---

## Checkpoint：阶段完成点

### Checkpoint 1：后端完成
**完成条件：** Task 1-7 全部完成

**验证清单：**
- [ ] 所有后端单元测试通过
- [ ] 后端代码构建无错误无警告
- [ ] 数据库迁移成功
- [ ] 所有后端接口可调用（通过 curl/Postman）
- [ ] 日志输出正常

**操作：** 提交一个 commit，包含所有后端代码

---

### Checkpoint 2：前端完成
**完成条件：** Task 8-10 全部完成

**验证清单：**
- [ ] 前端代码构建成功
- [ ] TypeScript 类型检查通过
- [ ] 微信绑定 UI 显示正常
- [ ] API 调用集成正确
- [ ] 前端单元测试通过

**操作：** 提交一个 commit，包含所有前端代码

---

### Checkpoint 3：测试完成
**完成条件：** Task 11-13 全部完成

**验证清单：**
- [ ] 所有单元测试通过，覆盖率 > 85%
- [ ] 所有集成测试通过
- [ ] 手动测试验证功能正常
- [ ] 生产环境配置完成
- [ ] 安全审计完成（签名校验、隐私、SQL 注入等）

**操作：** 提交一个 commit（测试代码 + 文档）+ 创建 Pull Request

---

## 风险和缓解

| 风险 | 影响 | 概率 | 缓解策略 |
|------|------|------|---------|
| 微信 API 限流 | 无法推送回复 | 中 | 实现指数退避重试，监控 API 调用频率 |
| access_token 过期 | 推送失败 | 中 | 实现 token 缓存和自动刷新（1 小时） |
| AI 生成超时 | 用户收不到回复 | 中 | 设置 30 秒超时，推送部分结果或超时提示 |
| 用户快速绑定切换 | 旧 openid 可能冲突 | 低 | 旧码自动失效，openid 唯一性约束 |
| 数据库迁移失败 | 无法启动应用 | 低 | 编写回滚脚本，备份数据库 |
| 网络连接中断 | 消息丢失 | 低 | 后台任务重试 3 次，记录失败日志 |

---

## 未解决的问题

1. **微信公众号账户** — 需要真实的微信公众号 App ID 和 App Secret
2. **服务器公网 IP** — 微信回调需要公网 IP 或域名
3. **消息加密密钥** — 如启用消息加密，需要从微信后台获取
4. **敏感词过滤** — 是否需要对用户输入和 AI 输出进行敏感词检查？（当前跳过）
5. **长期数据分析** — 是否需要记录微信对话用于数据分析？（当前不记录）

---

## 时间表

| 阶段 | 任务 | 预计时间 | 开始日期 | 完成日期 |
|------|------|---------|---------|---------|
| 后端基础 | Task 1-7 | 1 天 | 2026-06-18 | 2026-06-19 |
| 前端集成 | Task 8-10 | 0.5 天 | 2026-06-19 | 2026-06-19 |
| 测试和验证 | Task 11-13 | 0.5-1 天 | 2026-06-19 | 2026-06-20 |
| **总计** | | **2-3 天** | | |

---

## 参考资源

- [微信官方开发文档](https://developers.weixin.qq.com/doc/offiaccount/)
- [EduBuddy 快速参考](../MEMORY.md)
- [设计文档](2026-06-18-wechat-integration-design.md)
