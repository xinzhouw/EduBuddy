# 密码重置功能设计文档

**日期**: 2026-06-26  
**功能**: 用户忘记密码时通过邮箱验证码重置密码

## 背景与目标

当前登录失败时会提示用户"如果忘记密码，可以尝试重置密码"，但系统中尚无密码重置功能。本功能补充这一缺口，允许用户通过邮箱验证码安全地重置密码。

## 功能需求

### 核心功能
1. 用户输入邮箱，系统发送 6 位验证码到该邮箱
2. 用户输入验证码和新密码，系统验证并重置密码
3. 重置成功后跳转回登录页

### 参数要求
- **验证码有效期**: 15 分钟
- **验证码格式**: 6 位数字
- **重试次数限制**: 最多 5 次输入失败，超过则锁定 1 小时
- **发送限流**: 30 秒内最多发送 1 次验证码
- **邮件服务**: SMTP

---

## 整体架构

### 数据流
```
用户点击"忘记密码" 
  ↓
输入邮箱 → POST /api/auth/forgot-password
  ↓
后端生成验证码 → 通过 SMTP 发送邮件 → 返回成功
  ↓
用户输入验证码 + 新密码 → POST /api/auth/reset-password
  ↓
后端验证 → 更新密码 → 返回成功
  ↓
跳转回登录页，提示"密码已重置，请使用新密码登录"
```

---

## 后端设计

### 新增数据库字段（User 表）

```python
class User(Base):
    __tablename__ = "users"
    
    # ... 现有字段 ...
    
    # 密码重置相关
    password_reset_code: str = Column(String(6), nullable=True)  # 6位验证码
    reset_code_expiry: datetime = Column(DateTime, nullable=True)  # 验证码过期时间
    reset_attempts: int = Column(Integer, default=0)  # 验证码输入失败次数
    reset_code_locked_until: datetime = Column(DateTime, nullable=True)  # 账户被锁定的过期时间
```

**可选**：使用 Redis 存储速率限制数据，减少数据库查询

### 新增 API 端点

#### 端点 1: POST /api/auth/forgot-password

**请求：**
```json
{
  "email": "user@example.com"
}
```

**响应（成功 200）：**
```json
{
  "code": 200,
  "message": "验证码已发送到邮箱，请在 15 分钟内使用",
  "data": {
    "email": "user@example.com"
  }
}
```

**响应（邮箱不存在 400）：**
```json
{
  "code": 400,
  "error_code": "EMAIL_NOT_FOUND",
  "message": "邮箱不存在，请先注册账户"
}
```

**响应（限流 429）：**
```json
{
  "code": 429,
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "请求过于频繁，请在 30 秒后重试",
  "retry_after": 25
}
```

**业务逻辑：**
1. 验证邮箱格式
2. 检查邮箱是否存在，不存在返回 400（对外不区分是否存在，防止用户枚举）
3. 检查速率限制：30 秒内最多发送 1 次，超限返回 429
4. 生成 6 位随机数字验证码
5. 保存验证码到数据库：
   - `password_reset_code` = 验证码
   - `reset_code_expiry` = 当前时间 + 15 分钟
   - `reset_attempts` = 0（重置计数器）
6. 通过 SMTP 发送邮件（包含验证码、有效期、安全提示）
7. 返回 200 成功（即使邮箱不存在，也返回相同的成功消息，防止枚举）

#### 端点 2: POST /api/auth/reset-password

**请求：**
```json
{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "NewPassword@123"
}
```

**响应（成功 200）：**
```json
{
  "code": 200,
  "message": "密码已重置，请使用新密码登录"
}
```

**响应（验证码错误 400）：**
```json
{
  "code": 400,
  "error_code": "INVALID_CODE",
  "message": "验证码错误，还有 3 次尝试机会"
}
```

**响应（验证码过期 400）：**
```json
{
  "code": 400,
  "error_code": "CODE_EXPIRED",
  "message": "验证码已过期，请重新申请"
}
```

**响应（账户被锁定 403）：**
```json
{
  "code": 403,
  "error_code": "TOO_MANY_ATTEMPTS",
  "message": "验证码输入失败次数过多，账户已锁定 1 小时"
}
```

**响应（密码强度不足 400）：**
```json
{
  "code": 400,
  "error_code": "WEAK_PASSWORD",
  "message": "密码强度不足，请参考密码要求"
}
```

**业务逻辑：**
1. 验证邮箱是否存在
2. 检查是否被锁定（`reset_code_locked_until > 当前时间`）
   - 如果被锁定，返回 403
3. 检查验证码是否正确
   - 如果错误，`reset_attempts` +1
   - 如果 `reset_attempts >= 5`：
     - 设置 `reset_code_locked_until` = 当前时间 + 1 小时
     - 返回 403
   - 否则返回 400（包含剩余尝试次数）
4. 检查验证码是否过期（`reset_code_expiry < 当前时间`）
   - 如果过期，返回 400
5. 验证新密码强度（调用现有的 `validate_password_strength`）
   - 如果不符合要求，返回 400
6. 检查新密码是否与旧密码相同
   - 如果相同，返回 400
7. 更新用户密码：
   - `password` = bcrypt hash（新密码）
   - `password_reset_code` = NULL
   - `reset_code_expiry` = NULL
   - `reset_attempts` = 0
   - `reset_code_locked_until` = NULL
8. 返回 200 成功

### 邮件服务模块

**文件**: `backend/app/services/email_service.py`

**功能**：
- 连接 SMTP 服务器
- 生成 6 位随机数字验证码
- 发送密码重置邮件

**SMTP 配置（.env）**：
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@edubuddy.com
SMTP_FROM_NAME=EduBuddy
```

**邮件模板**：
```
尊敬的 [用户昵称]，

您正在重置 EduBuddy 账户密码。

您的验证码：[6位数字]

此验证码在 15 分钟内有效。

⚠️ 安全提示：如果这不是您的操作，请立即忽略此邮件。

— EduBuddy 团队
```

### 错误码定义

```python
class PasswordResetErrorCode:
    EMAIL_NOT_FOUND = "EMAIL_NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INVALID_CODE = "INVALID_CODE"
    CODE_EXPIRED = "CODE_EXPIRED"
    TOO_MANY_ATTEMPTS = "TOO_MANY_ATTEMPTS"
    WEAK_PASSWORD = "WEAK_PASSWORD"
    SERVER_ERROR = "SERVER_ERROR"
```

---

## 前端设计

### 新增路由

```typescript
{
  path: '/forgot-password',
  component: ForgotPasswordView,
  meta: { requiresAuth: false }  // 不需要登录
}
```

### 新增页面（ForgotPasswordView.vue）

**布局**：左侧品牌区 + 右侧表单区（与登录页保持一致）

**两步表单**：

**步骤 1：邮箱输入**
- 邮箱输入框（必填、格式验证）
- "发送验证码"按钮
  - 初始状态：可点击
  - 发送后：禁用 + 显示倒计时（如"重新发送(30s)"）
- "返回登录"链接

**步骤 2：验证码 + 新密码**（邮箱填写后显示）
- 验证码输入框（6 位数字，实时验证）
- 新密码输入框（显示密码强度条，复用现有的 `passwordValidator`）
- 确认密码输入框（必须与新密码一致）
- "重置密码"按钮
- 提示信息：
  - 验证码过期时间
  - 密码要求
  - "重新发送验证码"链接

### 用户交互流程

1. 用户输入邮箱 → 点击"发送验证码"
2. 前端显示加载状态 → 后端发送邮件
3. 成功后，按钮变为"重新发送(30s)"并禁用
4. 同时显示验证码、新密码、确认密码输入框
5. 用户输入验证码 + 新密码（密码强度实时显示）
6. 点击"重置密码"
7. 前端验证：
   - 验证码必填、必须 6 位数字
   - 新密码和确认密码一致
   - 密码符合强度要求
8. 调用 POST /api/auth/reset-password
9. 错误处理：
   - 验证码错误 → 显示对话框"验证码错误，还有 X 次尝试"
   - 验证码过期 → 显示对话框"验证码已过期，请重新申请"
   - 账户被锁定 → 显示对话框"验证码输入失败次数过多，账户已锁定 1 小时"
   - 其他错误 → 显示对话框
10. 成功 → 显示 Toast"密码已重置，请使用新密码登录" → 跳转回登录页

### 新增 API 调用（auth.ts）

```typescript
export const authApi = {
  // ... 现有方法 ...
  
  forgotPassword: (email: string) =>
    api.post('/auth/forgot-password', { email }),

  resetPassword: (email: string, code: string, newPassword: string) =>
    api.post('/auth/reset-password', {
      email,
      code,
      new_password: newPassword
    })
}
```

### 修改登录页面（LoginView.vue）

在登录表单下方添加"忘记密码？"链接：
```vue
<div class="text-center text-gray-500 mt-4 text-xs sm:text-sm">
  <RouterLink to="/forgot-password" class="text-blue-500 hover:text-blue-600">
    忘记密码？
  </RouterLink>
</div>
```

---

## 错误处理

### 前端错误消息映射

```typescript
const FORGOT_PASSWORD_ERROR_MESSAGES = {
  EMAIL_NOT_FOUND: {
    title: '邮箱未找到',
    message: '该邮箱未注册或不存在，请先注册账户'
  },
  RATE_LIMIT_EXCEEDED: {
    title: '请求过于频繁',
    message: '请在 30 秒后再试'
  },
  INVALID_CODE: {
    title: '验证码错误',
    message: '验证码不正确，请重新输入'
  },
  CODE_EXPIRED: {
    title: '验证码已过期',
    message: '验证码已过期，请重新申请'
  },
  TOO_MANY_ATTEMPTS: {
    title: '尝试次数过多',
    message: '验证码输入失败次数过多，账户已锁定 1 小时，请稍后再试'
  },
  WEAK_PASSWORD: {
    title: '密码强度不足',
    message: '请按照密码要求设置更强的密码'
  },
  SERVER_ERROR: {
    title: '邮件发送失败',
    message: '无法发送验证码，请稍后重试'
  }
}
```

---

## 安全考虑

### 1. 防止邮箱枚举攻击
- 邮箱不存在时，后端仍返回 HTTP 200 和"验证码已发送"消息
- 对外不区分邮箱是否存在，与登录流程保持一致

### 2. 防止暴力破解
- 验证码 5 次输入失败后锁定账户 1 小时
- 锁定期间无法再请求新的验证码
- 记录所有重置密码尝试（建议添加审计日志）

### 3. 验证码安全
- 验证码 15 分钟后自动过期
- 验证码生成使用 `secrets.randbelow()` 确保密码学强度
- 可选：在数据库中哈希存储验证码

### 4. 密码安全
- 新密码必须满足强度要求（8+ 字符、大小写、数字、特殊字符）
- 新密码不能与当前密码相同
- 可选：密码更新后清除所有现有的 JWT token，强制用户重新登录

### 5. 邮件安全
- SMTP 凭证存储在 `.env`，不提交到 Git
- 邮件中只显示验证码，不暴露用户密码或其他敏感信息
- 邮件中包含安全提示（如果不是本人请忽略）

### 6. 会话安全
- 重置密码成功后，用户需要使用新密码重新登录
- 不自动登录用户（防止中间人攻击）

---

## 测试范围

### 后端测试
- [ ] 邮箱不存在 → 返回 200（防止枚举）
- [ ] 有效邮箱 → 发送验证码成功
- [ ] 30 秒内重复请求 → 返回 429
- [ ] 验证码正确 + 密码符合要求 → 重置成功
- [ ] 验证码错误 5 次 → 账户被锁定
- [ ] 验证码过期 → 返回 400
- [ ] 密码强度不足 → 返回 400
- [ ] 邮件服务故障 → 返回 500

### 前端测试
- [ ] 邮箱输入和格式验证
- [ ] 发送验证码后按钮显示倒计时
- [ ] 验证码输入框只接受 6 位数字
- [ ] 密码强度条实时显示
- [ ] 新密码和确认密码一致性验证
- [ ] 错误对话框显示正确消息
- [ ] 成功后跳转到登录页

---

## 不在本次范围内

- OAuth/社交登录
- 二次验证（二次因素认证）
- 安全问题（如"您的宠物名字"）
- 生物识别重置（如指纹、人脸识别）
- 邮件模板个性化（如品牌徽标）

---

## 验收标准

- ✅ 用户可通过邮箱验证码重置密码
- ✅ 验证码 15 分钟内有效，6 位数字
- ✅ 5 次验证失败后账户锁定 1 小时
- ✅ 30 秒内限流，最多发送 1 次验证码
- ✅ 新密码必须满足强度要求
- ✅ 错误消息清晰且有帮助
- ✅ 邮件通过 SMTP 成功发送
- ✅ 安全性得到保留（不泄露邮箱存在性）
- ✅ 所有错误场景都有对应的测试
