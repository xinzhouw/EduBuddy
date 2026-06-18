# 微信公众号 AI 问答集成设计

**文档时间：** 2026-06-18  
**状态：** 已批准  
**优先级：** 高

---

## 1. 概述

### 需求
为 EduBuddy 平台的 AI 问答功能接入微信公众号，使用户可以通过微信直接与 AI 对话。

### 设计方案
采用**方案 A：微信服务器 → FastAPI 代理**的架构，复用现有的 AI 服务、RAG 检索和系统提示词。

### 核心特性
- ✅ 微信公众号消息回调集成
- ✅ 用户账户绑定验证（通过 6 位绑定码）
- ✅ RAG 知识库检索增强回答
- ✅ OpenAI 流式 AI 生成
- ✅ 微信 5 秒超时处理（异步推送）
- ✅ 消息签名校验和安全验证
- ✅ 错误处理和降级策略

---

## 2. 架构设计

### 2.1 整体数据流

```
微信用户发送消息
         ↓
微信服务器回调 (POST /api/wechat/callback)
         ↓
签名校验和消息解密
         ↓
XML 消息解析
         ↓
通过 openid 查询用户（从数据库）
         ↓
调用 AI 服务：
  ├─ RAG 检索知识库
  ├─ 构建系统提示词
  └─ 调用 OpenAI API
         ↓
响应内容分段处理
         ↓
立即返回成功 XML 给微信
         ↓
异步推送 AI 回复（客服接口）
         ↓
用户在微信收到回复
```

### 2.2 超时处理

微信要求回调 5 秒内返回。为了处理更耗时的 AI 生成，采用以下策略：

1. **立即返回成功响应** — 返回 `<xml><ToUserName>...</ToUserName></xml>` success 标记
2. **后台任务处理** — 启动异步任务生成 AI 回复
3. **客服接口推送** — 使用微信的客服消息接口异步推送最终回复
4. **长文本分段** — 如果回复超过 2048 字，分段推送（最多 5 段）

### 2.3 消息格式

**微信发来的消息（XML）：**
```xml
<xml>
  <ToUserName><![CDATA[official_account_id]]></ToUserName>
  <FromUserName><![CDATA[user_openid]]></FromUserName>
  <CreateTime>1348831860</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[用户消息内容]]></Content>
  <MsgId>1234567890123456</MsgId>
</xml>
```

**我们的回复（XML）：**
```xml
<xml>
  <ToUserName><![CDATA[user_openid]]></ToUserName>
  <FromUserName><![CDATA[official_account_id]]></FromUserName>
  <CreateTime>1348831860</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[AI 回复内容]]></Content>
</xml>
```

---

## 3. 用户身份和绑定流程

### 3.1 绑定流程

```
学生在 web 平台登录
     ↓
进入"账户设置" → "微信绑定"
     ↓
点击"生成绑定码"
     ↓
后端生成 6 位随机码，保存到 wechat_binding_codes 表，有效期 10 分钟
     ↓
前端显示绑定码和操作说明
     ↓
学生在微信给公众号发送：bind 123456
     ↓
后端接收，验证绑定码
     ↓
码有效 → 保存 wechat_openid 到 users 表 → 回复"绑定成功"
码无效或过期 → 回复"绑定码无效或已过期"
```

### 3.2 数据库改动

**修改 users 表：**
```sql
ALTER TABLE users ADD COLUMN wechat_openid VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN wechat_bound_at DATETIME;
ALTER TABLE users ADD COLUMN wechat_nickname VARCHAR(255);

CREATE INDEX idx_wechat_openid ON users(wechat_openid);
```

**新增表：wechat_binding_codes（临时绑定码）**
```sql
CREATE TABLE wechat_binding_codes (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    code VARCHAR(6) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_wechat_code ON wechat_binding_codes(code);
```

### 3.3 身份验证

每条微信消息到来时：
1. 从微信消息中提取 `FromUserName`（即 openid）
2. 查询：`SELECT * FROM users WHERE wechat_openid = ?`
3. **找到用户** → 处理消息
4. **未找到用户** → 回复提示绑定

---

## 4. 消息处理流程

### 4.1 回调接收和验证

**路由：** `GET/POST /api/wechat/callback`

**GET 请求（微信服务器验证接入）：**
- 微信会发送：`?signature=...&timestamp=...&nonce=...&echostr=...`
- 我们需要校验签名，然后返回 `echostr` 参数

**POST 请求（微信转发用户消息）：**
- 微信推送用户消息（XML 格式）
- 需要校验签名和可选的消息加密

### 4.2 消息处理（伪代码）

```python
@router.post("/api/wechat/callback")
async def wechat_callback(request: Request):
    # 1. 验证签名
    if not validate_wechat_signature(request):
        return Response(status_code=403)
    
    # 2. 获取请求体
    body = await request.body()
    
    # 3. 如果启用加密，解密消息
    if settings.wechat_enable_encryption:
        body = decrypt_wechat_message(body)
    
    # 4. 解析 XML 消息
    msg_dict = parse_wechat_xml(body)
    openid = msg_dict.get('FromUserName')
    content = msg_dict.get('Content', '').strip()
    msg_type = msg_dict.get('MsgType', 'text')
    
    # 5. 仅处理文本消息
    if msg_type != 'text' or not content:
        return generate_wechat_reply(openid, "暂不支持此类消息")
    
    # 6. 检查特殊指令
    if content.startswith('bind '):
        # 处理绑定指令
        code = content[5:].strip()
        await wechat_service.handle_bind_command(openid, code)
        return generate_wechat_reply(openid, "绑定成功")
    
    # 7. 查询用户
    user = db.query(User).filter(
        User.wechat_openid == openid
    ).first()
    
    if not user:
        return generate_wechat_reply(
            openid,
            "请先在 EduBuddy 平台绑定你的微信账户"
        )
    
    # 8. 立即返回成功给微信
    response = generate_wechat_reply(openid, "")  # 空回复
    
    # 9. 启动后台任务处理 AI
    background_tasks.add_task(
        wechat_service.send_ai_response_async,
        user_openid=openid,
        user_id=user.id,
        user_message=content
    )
    
    return response
```

### 4.3 AI 处理流程（异步）

```python
async def send_ai_response_async(
    user_openid: str,
    user_id: int,
    user_message: str
):
    try:
        # 1. RAG 检索
        rag_context = await rag_service.retrieve(user_message)
        
        # 2. 调用 AI 服务流式生成
        ai_response = ""
        async for chunk in await ai_service.chat_stream(
            messages=[{'role': 'user', 'content': user_message}],
            context=rag_context
        ):
            ai_response += chunk
        
        # 3. 分段处理（最多 2048 字/段）
        response_parts = split_message(ai_response, max_length=2048, max_parts=5)
        
        # 4. 通过客服接口推送
        for part in response_parts:
            await send_wechat_customer_message(
                access_token=get_wechat_access_token(),
                openid=user_openid,
                content=part
            )
    
    except Exception as e:
        # 错误处理：推送错误提示
        await send_wechat_customer_message(
            access_token=get_wechat_access_token(),
            openid=user_openid,
            content="抱歉，AI 处理出错，请稍后重试"
        )
        logger.error(f"WeChat AI response error: {e}")
```

---

## 5. 错误处理和边界情况

| 场景 | 处理方案 |
|------|---------|
| **用户未绑定微信** | 回复："请先在 EduBuddy 平台绑定微信账户。访问：[链接]" |
| **绑定码无效或过期** | 回复："绑定码无效或已过期，请重新生成" |
| **用户账户被禁用** | 回复："你的账户已被禁用，无法使用此功能" |
| **AI 生成超时（> 30 秒）** | 推送："AI 正在思考中，请稍候..."，然后推送部分结果或超时提示 |
| **RAG 检索失败** | 降级：直接调用 OpenAI，不注入知识库上下文 |
| **OpenAI API 错误** | 回复："AI 服务暂时不可用，请稍后重试" |
| **用户消息为空** | 忽略，不回复 |
| **响应过长（> 2048 字）** | 分段推送，最多 5 段 |
| **分段推送失败** | 重试 3 次，失败后放弃 |

### 5.1 速率限制

为防止滥用，建议在用户级别实施速率限制：
- 每个用户每分钟最多 3 条消息
- 每个用户每天最多 100 条消息

实现方式：Redis 或数据库记录最近的请求时间戳。

### 5.2 安全措施

1. **消息签名校验** — 所有来自微信的请求必须通过签名验证（SHA1）
2. **消息加密** — 如启用微信消息加密模式，需正确解密（AES-128-CBC）
3. **用户隐私** — 不暴露其他用户数据
4. **敏感词过滤** — 对用户输入和 AI 输出进行可选的敏感词检查
5. **SQL 注入防护** — 使用参数化查询（SQLAlchemy 自动处理）
6. **access_token 管理** — 定期刷新微信 access_token，避免过期

---

## 6. 前端改动

### 6.1 新增页面/组件

**AccountSettings.vue（修改）：**
- 在"账户设置"中添加"微信绑定"部分
- 显示绑定状态和绑定码

**WechatBindingModal.vue（新增）：**
- 绑定弹窗：显示绑定码、倒计时、复制按钮
- 解除绑定确认

### 6.2 API 调用

新增后端接口：
- `POST /api/user/wechat/bind-code` — 生成绑定码
- `DELETE /api/user/wechat/unbind` — 解除绑定

---

## 7. 后端代码结构

### 7.1 新增文件

```
backend/app/
├── routers/
│   └── wechat.py                  # 微信回调处理
├── services/
│   └── wechat_service.py          # 微信业务逻辑
├── schemas/
│   └── wechat.py                  # Pydantic schema
└── utils/
    └── wechat_utils.py            # 微信工具函数
```

### 7.2 文件职责

**routers/wechat.py：**
- `GET/POST /api/wechat/callback` — 微信回调入口
- `GET /api/wechat/verify` — 服务器接入验证

**services/wechat_service.py：**
- `handle_text_message()` — 处理文本消息
- `handle_bind_command()` — 处理绑定指令
- `send_ai_response_async()` — 异步推送 AI 回复

**utils/wechat_utils.py：**
- `validate_wechat_signature()` — 签名校验
- `parse_wechat_xml()` — XML 解析
- `generate_wechat_reply()` — 生成 XML 回复
- `decrypt_wechat_message()` — 消息解密（可选）
- `get_wechat_access_token()` — 获取 access_token
- `send_wechat_customer_message()` — 发送客服消息

---

## 8. 环境变量配置

在 `.env` 中新增：

```env
# WeChat Official Account
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
WECHAT_TOKEN=your_token
WECHAT_ENCODING_AES_KEY=your_aes_key
WECHAT_ENABLE_ENCRYPTION=false

# 可选：绑定码有效期（分钟）
WECHAT_BIND_CODE_EXPIRY_MINUTES=10
```

---

## 9. 依赖库

需要新增的 Python 包：
```
wechat-python-sdk>=1.0        # 微信 SDK
```

或者手动实现微信消息处理（不依赖外部库）。

---

## 10. 测试策略

### 10.1 单元测试
- 签名校验逻辑
- XML 解析和生成
- 绑定码生成和验证
- 消息分段逻辑

### 10.2 集成测试
- 完整的绑定流程
- 完整的消息处理流程
- 错误场景处理

### 10.3 手动测试
- 在微信开发者工具中测试消息回调
- 在真实微信平台测试（需申请公众号）

---

## 11. 上线检查清单

- [ ] 微信公众号已申请并配置
- [ ] 服务器 IP 已添加到微信白名单
- [ ] 所有环境变量已配置
- [ ] 数据库迁移已完成
- [ ] 单元测试通过率 > 90%
- [ ] 集成测试全部通过
- [ ] 安全审计完成（签名校验、SQL 注入、隐私等）
- [ ] 错误日志记录完整
- [ ] 速率限制已配置
- [ ] 监控和告警已设置

---

## 12. 时间表和资源

**预计工作量：** 2-3 天

**关键里程碑：**
1. Day 1：后端路由、消息处理、绑定流程
2. Day 2：前端绑定界面、集成测试
3. Day 3：安全审计、部署测试

**依赖：**
- 微信公众号账户和 App ID
- 服务器公网 IP（用于微信回调）

---

## 附录：参考链接

- [微信公众平台开发文档](https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Service_Center_messages.html)
- [微信消息加密文档](https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Message_encryption_and_decryption_instructions.html)
