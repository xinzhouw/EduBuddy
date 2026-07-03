# 登录错误处理改进设计文档

**日期**: 2026-06-26  
**功能**: 用户登录失败时显示具体的错误原因

## 背景

当前登录系统存在的问题：
- 后端返回统一的错误消息 "邮箱或密码错误"（安全性考虑）
- 前端在登录失败时没有向用户显示任何错误信息，导致用户体验不佳
- 用户无法区分不同的失败原因（如账户被禁用、登录过于频繁、网络错误等）

## 目标

1. 在保留安全性的前提下，根据错误类型向用户显示有意义的错误提示
2. 通过模态对话框展示错误信息，提高用户体验
3. 为不同的错误类型提供相应的建议或操作提示

## 错误码分类

### 错误码定义表

| 错误码 | HTTP 状态 | 用户看到的消息 | 内部含义 | 建议操作 |
|--------|---------|-------------|--------|---------|
| `INVALID_CREDENTIALS` | 401 | 邮箱或密码错误 | 邮箱不存在或密码错误 | 检查邮箱和密码，或注册新账户 |
| `ACCOUNT_DISABLED` | 403 | 账户已禁用，请联系管理员 | 用户 `is_active = False` | 联系客服 |
| `ACCOUNT_LOCKED` | 403 | 登录次数过多，账户已锁定，请 1 小时后重试 | 失败尝试过多导致账户锁定 | 稍后重试或重置密码 |
| `RATE_LIMIT_EXCEEDED` | 429 | 登录过于频繁，请在 {retry_after} 秒后重试 | IP 或用户被限流 | 等待倒计时后重试 |
| `SERVER_ERROR` | 500 | 服务器错误，请稍后重试 | 后端异常 | 稍后重试 |
| `NETWORK_ERROR` | - | 网络连接失败，请检查网络 | 前端网络异常 | 检查网络连接 |

## 实现方案

### 方案类型

**方案 A：最小改动（已批准）**
- 在错误响应中添加 `error_code` 字段
- 前端根据 error_code 显示对应的用户友好提示
- 保留安全性：对外仍显示通用消息
- 内部逻辑清晰且易于扩展

### 后端改动

#### 响应格式

**错误响应结构（标准格式）：**
```json
{
  "code": 401,
  "error_code": "INVALID_CREDENTIALS",
  "message": "邮箱或密码错误",
  "data": null,
  "retry_after": null
}
```

**速率限制错误（包含 retry_after）：**
```json
{
  "code": 429,
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "登录过于频繁，请在 30 秒后重试",
  "data": null,
  "retry_after": 30
}
```

#### 修改的文件

**`app/routers/auth.py` - login 端点：**
- 在 `INVALID_CREDENTIALS` 错误时添加 `error_code` 字段
- 在 `ACCOUNT_DISABLED` 错误时返回 `error_code: "ACCOUNT_DISABLED"`
- 在 `ACCOUNT_LOCKED` 错误时返回 `error_code: "ACCOUNT_LOCKED"`（如果实现账户锁定功能）
- 在速率限制错误时返回 `error_code: "RATE_LIMIT_EXCEEDED"` 和 `retry_after` 值
- 在服务器错误时返回 `error_code: "SERVER_ERROR"`

**错误返回示例：**
```python
# 邮箱不存在或密码错误（统一消息保留安全性）
raise HTTPException(
    status_code=401,
    detail={
        "error_code": "INVALID_CREDENTIALS",
        "message": "邮箱或密码错误"
    }
)

# 账户被禁用
raise HTTPException(
    status_code=403,
    detail={
        "error_code": "ACCOUNT_DISABLED",
        "message": "账户已禁用，请联系管理员"
    }
)

# 登录过于频繁
raise HTTPException(
    status_code=429,
    detail={
        "error_code": "RATE_LIMIT_EXCEEDED",
        "message": "登录过于频繁，请在 30 秒后重试",
        "retry_after": 30
    }
)
```

### 前端改动

#### 错误消息映射

**`frontend/src/utils/errorMessages.ts`（新建文件）：**
```typescript
export const LOGIN_ERROR_MESSAGES = {
  INVALID_CREDENTIALS: {
    title: '登录失败',
    message: '邮箱或密码错误，请检查后重试',
    suggestion: '如果忘记密码，可以尝试重置密码'
  },
  ACCOUNT_DISABLED: {
    title: '账户已禁用',
    message: '你的账户已被禁用，无法登录',
    suggestion: '请联系管理员或客服获取帮助'
  },
  ACCOUNT_LOCKED: {
    title: '账户已锁定',
    message: '由于多次登录失败，账户已暂时锁定',
    suggestion: '请 1 小时后重试，或通过邮箱重置密码'
  },
  RATE_LIMIT_EXCEEDED: {
    title: '登录过于频繁',
    message: '登录尝试过于频繁，请稍后再试',
    suggestion: null // 会显示倒计时
  },
  SERVER_ERROR: {
    title: '服务器错误',
    message: '服务器出现错误，请稍后重试',
    suggestion: '如果问题持续，请联系技术支持'
  },
  NETWORK_ERROR: {
    title: '网络连接失败',
    message: '无法连接到服务器，请检查网络',
    suggestion: '请检查网络连接后重试'
  }
}
```

#### 登录视图修改

**`frontend/src/views/auth/LoginView.vue`：**
1. 添加错误对话框组件
2. 改进 `handleLogin` 错误处理逻辑
3. 根据 error_code 显示对应的错误提示
4. 对于速率限制错误，显示倒计时并禁用登录按钮

**关键改动：**
```typescript
// 错误处理
try {
  await authStore.login(form.email, form.password)
  // 登录成功跳转
  router.push('/')
} catch (error: any) {
  const errorCode = error.response?.data?.error_code || 'NETWORK_ERROR'
  const errorInfo = LOGIN_ERROR_MESSAGES[errorCode] || LOGIN_ERROR_MESSAGES.SERVER_ERROR
  
  // 显示错误对话框
  showErrorDialog(errorInfo)
  
  // 如果是速率限制，显示倒计时
  if (errorCode === 'RATE_LIMIT_EXCEEDED') {
    const retryAfter = error.response?.data?.retry_after || 60
    disableLoginButtonWithCountdown(retryAfter)
  }
}
```

#### 认证存储修改

**`frontend/src/stores/auth.ts`：**
- 在 `login` 方法中不捕获异常，让错误传播给调用方（LoginView.vue）
- 保持错误对象的完整性，包括 `error_code` 和 `retry_after`

### 前端新增/修改的文件

1. **新建** `frontend/src/utils/errorMessages.ts` — 错误消息映射表
2. **修改** `frontend/src/views/auth/LoginView.vue` — 错误对话框和处理逻辑
3. **可选** `frontend/src/stores/auth.ts` — 完善错误传播

## 用户交互流程

### 正常登录流程
1. 用户输入邮箱和密码
2. 点击"登 录"按钮
3. 前端验证表单
4. 调用后端 `/api/auth/login`
5. 登录成功 → 跳转到首页

### 失败流程（示例：邮箱或密码错误）
1. 用户输入邮箱和密码
2. 点击"登 录"按钮
3. 后端返回 `error_code: "INVALID_CREDENTIALS"`
4. 前端显示模态对话框："邮箱或密码错误，请检查后重试"
5. 用户点击"确定"关闭对话框
6. 用户可重新输入或注册新账户

### 失败流程（示例：登录过于频繁）
1. 用户多次登录失败
2. 后端返回 `error_code: "RATE_LIMIT_EXCEEDED"` 和 `retry_after: 30`
3. 前端显示模态对话框："登录过于频繁，请在 30 秒后重试"
4. 登录按钮禁用，显示倒计时（30 → 29 → ... → 0）
5. 倒计时结束后，登录按钮重新启用

## 安全性考虑

1. **防止用户枚举**：对于 `INVALID_CREDENTIALS` 错误，仍显示统一的 "邮箱或密码错误" 消息给用户
2. **错误码仅用于内部处理**：error_code 字段仅用于前端区分错误类型，不泄露系统实现细节
3. **速率限制**：已有的速率限制机制继续生效，防止暴力攻击
4. **HTTPS 传输**：确保所有通信通过 HTTPS，防止中间人攻击

## 测试范围

### 后端测试
- [ ] 邮箱不存在 → `INVALID_CREDENTIALS`
- [ ] 密码错误 → `INVALID_CREDENTIALS`
- [ ] 账户被禁用 → `ACCOUNT_DISABLED`
- [ ] 登录过于频繁 → `RATE_LIMIT_EXCEEDED`（需要模拟）
- [ ] 服务器异常 → `SERVER_ERROR`（需要模拟）

### 前端测试
- [ ] 错误对话框正确显示
- [ ] 不同错误码显示不同的消息
- [ ] 速率限制时显示倒计时
- [ ] 登录按钮在倒计时期间禁用
- [ ] 网络错误时显示 `NETWORK_ERROR` 消息

## 扩展点

1. **账户锁定功能**：后续可添加多次失败后自动锁定账户的逻辑
2. **重置密码流程**：可在 `INVALID_CREDENTIALS` 错误对话框中添加"忘记密码"链接
3. **审计日志**：记录登录失败的原因和次数，便于安全分析
4. **国际化**：将错误消息提取到 i18n 配置中，支持多语言

## 不在本次范围内

- 实现账户锁定功能（仅返回 error_code 结构）
- 修改现有的速率限制逻辑
- 实现重置密码功能
- 添加国际化支持

---

## 验收标准

1. ✅ 后端返回的登录失败响应包含 `error_code` 字段
2. ✅ 前端根据 error_code 显示对应的用户友好提示
3. ✅ 错误信息在模态对话框中展示
4. ✅ 速率限制错误显示倒计时，登录按钮禁用
5. ✅ 网络错误能被正确捕获和显示
6. ✅ 安全性保留：不泄露具体的邮箱存在性或密码是否正确
