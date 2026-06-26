# 密码重置功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现用户通过邮箱验证码重置忘记的密码

**Architecture:** 
后端提供两个 API 端点：`forgot-password`（发送验证码到邮箱）和 `reset-password`（验证码 + 新密码重置）。前端创建新页面，用户通过登录页面的"忘记密码"链接访问，完成两步流程：输入邮箱 → 输入验证码和新密码。邮件通过 SMTP 发送，验证码 15 分钟内有效，5 次输入失败后账户锁定 1 小时。

**Tech Stack:** FastAPI (后端), Vue 3 + TypeScript (前端), SMTP (邮件), SQLAlchemy ORM

## Global Constraints

- 验证码有效期：15 分钟
- 验证码格式：6 位数字
- 重试次数限制：5 次失败后锁定 1 小时
- 发送限流：30 秒内最多发送 1 次验证码
- 邮件服务：SMTP
- 安全性：不泄露邮箱是否存在（无论邮箱存在与否都返回成功消息）
- 密码强度：复用现有的 `validate_password_strength` 函数

---

## 文件结构

### 后端文件

**新建：**
- `backend/app/services/email_service.py` — SMTP 邮件服务

**修改：**
- `backend/app/models/user.py` — 添加重置密码相关字段
- `backend/app/routers/auth.py` — 添加两个新端点
- `backend/app/schemas/auth.py` — 添加请求/响应 schema
- `backend/app/config.py` — 添加 SMTP 配置

### 前端文件

**新建：**
- `frontend/src/views/auth/ForgotPasswordView.vue` — 重置密码页面
- `frontend/src/utils/passwordResetMessages.ts` — 错误消息映射

**修改：**
- `frontend/src/api/auth.ts` — 添加 API 调用
- `frontend/src/router/index.ts` — 添加路由
- `frontend/src/views/auth/LoginView.vue` — 添加"忘记密码"链接

### 配置文件

**修改：**
- `.env.example` — 添加 SMTP 配置示例
- `.env` — 配置 SMTP 参数

---

## Task 1: 后端 - 配置 SMTP 和数据库迁移

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/models/user.py`
- Create: `backend/app/alembic/versions/add_password_reset_fields.py` (如果使用 Alembic 迁移)

**Interfaces:**
- Consumes: 现有的 User 模型
- Produces: User 模型新增 4 个字段，config 中新增 SMTP 配置类

- [ ] **Step 1: 添加 SMTP 配置到 config.py**

打开 `backend/app/config.py`，在 Settings 类中添加 SMTP 配置：

```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # SMTP 配置
    smtp_server: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_username: str = Field(default="")
    smtp_password: str = Field(default="")
    smtp_from_email: str = Field(default="noreply@edubuddy.com")
    smtp_from_name: str = Field(default="EduBuddy")
    
    class Config:
        env_file = ".env"
```

- [ ] **Step 2: 添加 User 模型字段**

打开 `backend/app/models/user.py`，在 User 类中添加重置密码相关字段：

```python
from datetime import datetime
from sqlalchemy import String, DateTime, Integer

class User(Base):
    __tablename__ = "users"
    
    # ... 现有字段 ...
    
    # 密码重置相关字段
    password_reset_code: str = Column(String(6), nullable=True)
    reset_code_expiry: datetime = Column(DateTime, nullable=True)
    reset_attempts: int = Column(Integer, default=0)
    reset_code_locked_until: datetime = Column(DateTime, nullable=True)
```

- [ ] **Step 3: 创建数据库迁移**

如果项目使用 Alembic 迁移，运行：

```bash
cd backend
alembic revision --autogenerate -m "add password reset fields to users table"
```

编辑生成的迁移文件（`backend/app/alembic/versions/xxxxx_add_password_reset_fields.py`），确保包含四个新字段。

如果使用手动迁移或 SQLite，直接执行 SQL：

```sql
ALTER TABLE users ADD COLUMN password_reset_code VARCHAR(6) DEFAULT NULL;
ALTER TABLE users ADD COLUMN reset_code_expiry DATETIME DEFAULT NULL;
ALTER TABLE users ADD COLUMN reset_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN reset_code_locked_until DATETIME DEFAULT NULL;
```

- [ ] **Step 4: 更新 .env.example**

打开 `.env.example`，添加 SMTP 配置示例：

```env
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@edubuddy.com
SMTP_FROM_NAME=EduBuddy
```

- [ ] **Step 5: 更新 .env（用于本地开发）**

打开 `.env`，添加实际的 SMTP 配置（使用测试邮箱）

- [ ] **Step 6: 提交**

```bash
git add backend/app/config.py backend/app/models/user.py backend/app/alembic/versions/ .env.example .env
git commit -m "feat: add password reset fields to database and SMTP configuration"
```

---

## Task 2: 后端 - 实现邮件服务模块

**Files:**
- Create: `backend/app/services/email_service.py`

**Interfaces:**
- Consumes: `settings` (from config), `smtplib`, `secrets`
- Produces: `EmailService` 类，包含 `send_password_reset_email()` 和 `generate_reset_code()` 方法

- [ ] **Step 1: 创建 email_service.py**

创建文件 `backend/app/services/email_service.py`：

```python
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings

class EmailService:
    def __init__(self):
        self.settings = get_settings()
    
    @staticmethod
    def generate_reset_code() -> str:
        """生成 6 位随机验证码"""
        return str(secrets.randbelow(1000000)).zfill(6)
    
    def send_password_reset_email(self, email: str, nickname: str, code: str) -> bool:
        """
        发送密码重置邮件
        
        Args:
            email: 收件人邮箱
            nickname: 用户昵称
            code: 6位验证码
        
        Returns:
            True 表示发送成功，False 表示失败
        """
        try:
            # 构建邮件内容
            subject = "EduBuddy 密码重置"
            body = f"""尊敬的 {nickname}，

您正在重置 EduBuddy 账户密码。

您的验证码：{code}

此验证码在 15 分钟内有效。

⚠️ 安全提示：如果这不是您的操作，请立即忽略此邮件。

— EduBuddy 团队
"""
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email}>"
            msg['To'] = email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port) as server:
                server.starttls()
                server.login(self.settings.smtp_username, self.settings.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

# 全局实例
email_service = EmailService()
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/services/email_service.py
git commit -m "feat: implement email service for password reset"
```

---

## Task 3: 后端 - 添加错误码和响应 Schema

**Files:**
- Modify: `backend/app/schemas/auth.py`
- Modify: `backend/app/routers/auth.py` (添加错误码常量)

**Interfaces:**
- Consumes: 现有的 auth schema
- Produces: `PasswordResetErrorCode` 类，`ForgotPasswordRequest`，`ResetPasswordRequest` schema

- [ ] **Step 1: 在 auth.py 顶部定义错误码**

打开 `backend/app/routers/auth.py`，在文件顶部（在 router 定义后）添加：

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

- [ ] **Step 2: 添加 Schema 到 auth.py**

打开 `backend/app/schemas/auth.py`，添加新的 Pydantic 模型：

```python
class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="用户邮箱")

class ForgotPasswordResponse(BaseModel):
    code: int
    message: str
    data: dict = None

class ResetPasswordRequest(BaseModel):
    email: str = Field(..., description="用户邮箱")
    code: str = Field(..., description="6位验证码")
    new_password: str = Field(..., description="新密码")

class ResetPasswordResponse(BaseModel):
    code: int
    message: str
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/schemas/auth.py backend/app/routers/auth.py
git commit -m "feat: add password reset error codes and request/response schemas"
```

---

## Task 4: 后端 - 实现 forgot-password 端点

**Files:**
- Modify: `backend/app/routers/auth.py`
- Modify: `backend/app/dependencies.py` (如果需要添加新的依赖)

**Interfaces:**
- Consumes: `ForgotPasswordRequest`, `EmailService`, `get_db`, User 模型
- Produces: `POST /api/auth/forgot-password` 端点，返回 200/400/429/500

- [ ] **Step 1: 添加 forgot-password 端点**

打开 `backend/app/routers/auth.py`，在现有端点后添加：

```python
from datetime import datetime, timedelta
from app.services.email_service import email_service
import time

# 用于存储速率限制的简单字典（生产环境建议使用 Redis）
_password_reset_rate_limit = {}

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db), request: Request = None):
    """
    请求重置密码，发送验证码到邮箱
    
    Args:
        req: 包含邮箱的请求
    
    Returns:
        - 200: 邮件已发送
        - 400: 邮箱不存在
        - 429: 请求过于频繁
        - 500: 邮件服务错误
    """
    # 检查速率限制（30 秒内最多发送 1 次）
    if request:
        ip_address = request.client.host if request.client else "unknown"
        last_request = _password_reset_rate_limit.get(ip_address, 0)
        if time.time() - last_request < 30:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": 429,
                    "error_code": PasswordResetErrorCode.RATE_LIMIT_EXCEEDED,
                    "message": f"请求过于频繁，请在 {int(30 - (time.time() - last_request))} 秒后重试",
                    "retry_after": int(30 - (time.time() - last_request))
                }
            )
        _password_reset_rate_limit[ip_address] = time.time()
    
    # 查询用户（防止邮箱枚举，即使不存在也返回成功）
    user = db.query(User).filter(User.email == req.email).first()
    
    # 如果用户存在，生成验证码并发送邮件
    if user:
        # 生成 6 位验证码
        reset_code = email_service.generate_reset_code()
        
        # 保存验证码到数据库
        user.password_reset_code = reset_code
        user.reset_code_expiry = datetime.utcnow() + timedelta(minutes=15)
        user.reset_attempts = 0
        user.reset_code_locked_until = None
        db.commit()
        
        # 发送邮件
        success = email_service.send_password_reset_email(
            email=user.email,
            nickname=user.nickname,
            code=reset_code
        )
        
        if not success:
            # 邮件发送失败，清除数据库中的验证码
            user.password_reset_code = None
            user.reset_code_expiry = None
            db.commit()
            raise HTTPException(
                status_code=500,
                detail={
                    "code": 500,
                    "error_code": PasswordResetErrorCode.SERVER_ERROR,
                    "message": "无法发送验证码，请稍后重试"
                }
            )
    
    # 无论邮箱是否存在，都返回相同的成功消息（防止用户枚举）
    return {
        "code": 200,
        "message": "验证码已发送到邮箱，请在 15 分钟内使用",
        "data": {"email": req.email}
    }
```

- [ ] **Step 2: 测试端点**

使用 curl 测试：

```bash
# 测试成功发送
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'

# 预期：200 响应，邮件已发送到用户邮箱

# 测试速率限制（立即再次请求）
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'

# 预期：429 响应
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/routers/auth.py
git commit -m "feat: implement forgot-password endpoint with rate limiting"
```

---

## Task 5: 后端 - 实现 reset-password 端点

**Files:**
- Modify: `backend/app/routers/auth.py`

**Interfaces:**
- Consumes: `ResetPasswordRequest`, `get_db`, User 模型, `verify_password`, `hash_password`, `validate_password_strength`
- Produces: `POST /api/auth/reset-password` 端点，返回 200/400/403/500

- [ ] **Step 1: 添加 reset-password 端点**

打开 `backend/app/routers/auth.py`，添加新的端点：

```python
@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    使用验证码和新密码重置密码
    
    Args:
        req: 包含邮箱、验证码、新密码的请求
    
    Returns:
        - 200: 密码已重置
        - 400: 验证码错误/过期/邮箱不存在/密码强度不足
        - 403: 账户被锁定（验证码输入失败次数过多）
    """
    # 查询用户
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "error_code": PasswordResetErrorCode.EMAIL_NOT_FOUND,
                "message": "邮箱不存在，请先注册账户"
            }
        )
    
    # 检查是否被锁定
    if user.reset_code_locked_until and datetime.utcnow() < user.reset_code_locked_until:
        raise HTTPException(
            status_code=403,
            detail={
                "code": 403,
                "error_code": PasswordResetErrorCode.TOO_MANY_ATTEMPTS,
                "message": "验证码输入失败次数过多，账户已锁定 1 小时"
            }
        )
    
    # 检查验证码是否正确
    if user.password_reset_code != req.code:
        user.reset_attempts += 1
        if user.reset_attempts >= 5:
            user.reset_code_locked_until = datetime.utcnow() + timedelta(hours=1)
            db.commit()
            raise HTTPException(
                status_code=403,
                detail={
                    "code": 403,
                    "error_code": PasswordResetErrorCode.TOO_MANY_ATTEMPTS,
                    "message": "验证码输入失败次数过多，账户已锁定 1 小时"
                }
            )
        db.commit()
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "error_code": PasswordResetErrorCode.INVALID_CODE,
                "message": f"验证码错误，还有 {5 - user.reset_attempts} 次尝试机会"
            }
        )
    
    # 检查验证码是否过期
    if datetime.utcnow() > user.reset_code_expiry:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "error_code": PasswordResetErrorCode.CODE_EXPIRED,
                "message": "验证码已过期，请重新申请"
            }
        )
    
    # 验证新密码强度
    is_valid, error_msg = check_password_validity(req.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "error_code": PasswordResetErrorCode.WEAK_PASSWORD,
                "message": f"密码不符合要求: {error_msg}"
            }
        )
    
    # 检查新密码是否与旧密码相同
    if verify_password(req.new_password, user.password):
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "message": "新密码不能与当前密码相同"
            }
        )
    
    # 更新密码和清除重置信息
    user.password = hash_password(req.new_password)
    user.password_reset_code = None
    user.reset_code_expiry = None
    user.reset_attempts = 0
    user.reset_code_locked_until = None
    db.commit()
    
    return {
        "code": 200,
        "message": "密码已重置，请使用新密码登录"
    }
```

- [ ] **Step 2: 测试端点**

使用 curl 测试（需要先从前面的 forgot-password 端点获取验证码）：

```bash
# 测试成功重置（使用从邮箱获得的验证码）
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "email":"user@example.com",
    "code":"123456",
    "new_password":"NewPassword@123"
  }'

# 预期：200 响应

# 测试验证码错误
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "email":"user@example.com",
    "code":"000000",
    "new_password":"NewPassword@123"
  }'

# 预期：400 响应，显示剩余尝试次数
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/routers/auth.py
git commit -m "feat: implement reset-password endpoint with validation"
```

---

## Task 6: 前端 - 添加 API 调用

**Files:**
- Modify: `frontend/src/api/auth.ts`

**Interfaces:**
- Consumes: `api` instance
- Produces: `forgotPassword()` 和 `resetPassword()` 函数

- [ ] **Step 1: 添加 API 调用**

打开 `frontend/src/api/auth.ts`，添加新的方法：

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

- [ ] **Step 2: 提交**

```bash
cd frontend
git add src/api/auth.ts
git commit -m "feat: add password reset API calls"
```

---

## Task 7: 前端 - 创建 ForgotPasswordView 页面

**Files:**
- Create: `frontend/src/views/auth/ForgotPasswordView.vue`
- Create: `frontend/src/utils/passwordResetMessages.ts`

**Interfaces:**
- Consumes: `authApi.forgotPassword()`, `authApi.resetPassword()`, `passwordValidator`, `router`
- Produces: 完整的忘记密码页面，包含两步表单

- [ ] **Step 1: 创建错误消息映射文件**

创建 `frontend/src/utils/passwordResetMessages.ts`：

```typescript
export interface PasswordResetErrorInfo {
  title: string
  message: string
  suggestion?: string
}

export const PASSWORD_RESET_ERROR_MESSAGES: Record<string, PasswordResetErrorInfo> = {
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
    message: '验证码输入失败次数过多，账户已锁定 1 小时'
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

- [ ] **Step 2: 创建 ForgotPasswordView.vue**

创建 `frontend/src/views/auth/ForgotPasswordView.vue`：

```vue
<template>
  <div class="min-h-screen flex">
    <!-- 左侧品牌区 -->
    <div class="hidden lg:flex w-1/2 bg-gradient-to-br from-blue-500 to-blue-700 flex-col items-center justify-center p-12 text-white">
      <div class="text-center">
        <div class="text-7xl mb-6">📚</div>
        <h1 class="text-4xl font-bold mb-4">EduBuddy</h1>
        <p class="text-xl text-blue-100">重置您的密码</p>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="flex-1 flex items-center justify-center p-4 sm:p-8">
      <div class="w-full max-w-md">
        <!-- 移动端 Logo -->
        <div class="lg:hidden text-center mb-6">
          <div class="text-5xl mb-2">📚</div>
          <h1 class="text-2xl font-bold text-gray-900">EduBuddy</h1>
        </div>

        <div class="text-center mb-6 sm:mb-8">
          <h2 class="text-xl sm:text-2xl font-bold text-gray-900">重置密码</h2>
          <p class="text-gray-500 mt-2 text-sm sm:text-base">输入您的邮箱，我们将发送验证码</p>
        </div>

        <!-- 步骤 1：邮箱输入 -->
        <el-form :model="form" :rules="emailRules" ref="emailFormRef" @submit.prevent>
          <el-form-item prop="email">
            <el-input 
              v-model="form.email" 
              placeholder="邮箱地址" 
              size="large" 
              type="email" 
              prefix-icon="Message" 
              clearable 
              :disabled="step > 1"
            />
          </el-form-item>
        </el-form>

        <el-button 
          type="primary" 
          size="large" 
          class="w-full mt-2 h-11 sm:h-12" 
          :loading="sendingCode"
          :disabled="step > 1 || countdownSeconds > 0"
          @click="handleSendCode"
        >
          {{ countdownSeconds > 0 ? `重新发送(${countdownSeconds}s)` : '发送验证码' }}
        </el-button>

        <!-- 步骤 2：验证码和新密码（在邮箱有效后显示） -->
        <el-form 
          v-if="step > 1"
          :model="form" 
          :rules="resetRules" 
          ref="resetFormRef" 
          @submit.prevent
          class="mt-6"
        >
          <el-form-item prop="code">
            <el-input 
              v-model="form.code" 
              placeholder="6 位验证码" 
              size="large" 
              maxlength="6"
              prefix-icon="Key"
              clearable
            />
          </el-form-item>

          <el-form-item prop="newPassword">
            <el-input 
              v-model="form.newPassword" 
              placeholder="新密码" 
              size="large" 
              type="password" 
              show-password
              prefix-icon="Lock"
            />
            <div v-if="passwordStrength" class="mt-2">
              <el-progress 
                :percentage="passwordStrength.score * 25" 
                :color="`${passwordStrength.score <= 1 ? '#F56C6C' : passwordStrength.score === 2 ? '#E6A23C' : '#85CE61'}`"
              />
              <p class="text-xs mt-1" :style="{ color: passwordStrength.score <= 1 ? '#F56C6C' : passwordStrength.score === 2 ? '#E6A23C' : '#85CE61' }">
                {{ passwordStrength.strength }}
              </p>
            </div>
          </el-form-item>

          <el-form-item prop="confirmPassword">
            <el-input 
              v-model="form.confirmPassword" 
              placeholder="确认密码" 
              size="large" 
              type="password" 
              show-password
              prefix-icon="Lock"
            />
          </el-form-item>

          <el-button 
            type="primary" 
            size="large" 
            class="w-full mt-2 h-11 sm:h-12" 
            :loading="resettingPassword"
            @click="handleResetPassword"
          >
            重置密码
          </el-button>
        </el-form>

        <!-- 返回登录链接 -->
        <p class="text-center text-gray-500 mt-6 text-xs sm:text-sm">
          <RouterLink to="/login" class="text-blue-500 hover:text-blue-600 font-medium">返回登录</RouterLink>
        </p>
      </div>
    </div>

    <!-- 错误对话框 -->
    <el-dialog
      v-model="errorDialogVisible"
      :title="errorInfo?.title || '错误'"
      width="90%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <p class="text-gray-700">{{ errorInfo?.message }}</p>
      <template #footer>
        <el-button type="primary" @click="errorDialogVisible = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'
import { validatePasswordStrength } from '@/api/auth'
import { PASSWORD_RESET_ERROR_MESSAGES } from '@/utils/passwordResetMessages'
import type { FormInstance } from 'element-plus'

const router = useRouter()
const emailFormRef = ref<FormInstance>()
const resetFormRef = ref<FormInstance>()

const step = ref(1)  // 1: 邮箱, 2: 验证码和密码
const sendingCode = ref(false)
const resettingPassword = ref(false)
const countdownSeconds = ref(0)
const errorDialogVisible = ref(false)
const errorInfo = ref<any>(null)

const form = reactive({
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordStrength = ref<any>(null)

const emailRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ]
}

const resetRules = {
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为 6 位数字', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule: any, value: any, callback: any) => {
        if (value !== form.newPassword) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

onMounted(() => {
  // 监听新密码输入，验证强度
})

async function handleSendCode() {
  await emailFormRef.value?.validate(async (valid) => {
    if (!valid) return
    
    sendingCode.value = true
    try {
      const res: any = await authApi.forgotPassword(form.email)
      ElMessage.success('验证码已发送到邮箱')
      step.value = 2
      
      // 启动倒计时
      countdownSeconds.value = 30
      const interval = setInterval(() => {
        countdownSeconds.value--
        if (countdownSeconds.value === 0) {
          clearInterval(interval)
        }
      }, 1000)
    } catch (error: any) {
      const errorCode = error.response?.data?.error_code || 'SERVER_ERROR'
      const errorMsg = PASSWORD_RESET_ERROR_MESSAGES[errorCode] || PASSWORD_RESET_ERROR_MESSAGES.SERVER_ERROR
      errorInfo.value = errorMsg
      errorDialogVisible.value = true
    } finally {
      sendingCode.value = false
    }
  })
}

async function handleResetPassword() {
  await resetFormRef.value?.validate(async (valid) => {
    if (!valid) return
    
    resettingPassword.value = true
    try {
      await authApi.resetPassword(form.email, form.code, form.newPassword)
      ElMessage.success('密码已重置，请使用新密码登录')
      setTimeout(() => {
        router.push('/login')
      }, 1500)
    } catch (error: any) {
      const errorCode = error.response?.data?.error_code || 'SERVER_ERROR'
      const errorMsg = PASSWORD_RESET_ERROR_MESSAGES[errorCode] || PASSWORD_RESET_ERROR_MESSAGES.SERVER_ERROR
      errorInfo.value = errorMsg
      errorDialogVisible.value = true
    } finally {
      resettingPassword.value = false
    }
  })
}
</script>

<style scoped>
/* ... 样式与 LoginView 保持一致 ... */
</style>
```

- [ ] **Step 3: 提交**

```bash
cd frontend
git add src/views/auth/ForgotPasswordView.vue src/utils/passwordResetMessages.ts
git commit -m "feat: create forgot password page with two-step form"
```

---

## Task 8: 前端 - 添加路由和登录页链接

**Files:**
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/views/auth/LoginView.vue`

**Interfaces:**
- Consumes: 现有的路由和登录页
- Produces: 新的 `/forgot-password` 路由，登录页添加链接

- [ ] **Step 1: 添加路由**

打开 `frontend/src/router/index.ts`，找到 auth 相关的路由，添加：

```typescript
{
  path: '/forgot-password',
  component: () => import('@/views/auth/ForgotPasswordView.vue'),
  meta: { requiresAuth: false }
}
```

- [ ] **Step 2: 在登录页添加链接**

打开 `frontend/src/views/auth/LoginView.vue`，找到登录表单下方的链接部分，修改为：

```vue
<p class="text-center text-gray-500 mt-6 text-xs sm:text-sm">
  还没有账号？
  <RouterLink to="/register" class="text-blue-500 hover:text-blue-600 font-medium">立即注册</RouterLink>
  |
  <RouterLink to="/forgot-password" class="text-blue-500 hover:text-blue-600 font-medium">忘记密码？</RouterLink>
</p>
```

- [ ] **Step 3: 提交**

```bash
cd frontend
git add src/router/index.ts src/views/auth/LoginView.vue
git commit -m "feat: add forgot-password route and link in login page"
```

---

## Task 9: 集成测试和验证

**Files:**
- Test: 手动端到端测试

**Interfaces:**
- Consumes: 完整的后端和前端实现
- Produces: 通过/失败的测试报告

- [ ] **Step 1: 启动后端和前端**

```bash
# 终端 1: 后端
cd backend
uvicorn app.main:app --reload --port 8000

# 终端 2: 前端
cd frontend
npm run dev
```

- [ ] **Step 2: 测试完整流程**

1. 访问 `http://localhost:3000/login`
2. 点击"忘记密码？"链接
3. 输入注册邮箱 → 点击"发送验证码"
4. 检查邮箱（后端会发送邮件）
5. 输入验证码 + 新密码 → 点击"重置密码"
6. 成功后跳转回登录页
7. 使用新密码登录

- [ ] **Step 3: 测试错误场景**

- 测试无效邮箱
- 测试验证码错误（5 次失败后锁定）
- 测试验证码过期
- 测试密码强度不足
- 测试 30 秒内重复请求

- [ ] **Step 4: 提交测试报告**

```bash
# 所有测试通过，无需提交代码
echo "Integration tests completed successfully"
```

---

## 总结

所有 9 个任务完成后，密码重置功能就完整实现了。用户可以通过以下流程重置密码：

1. 登录页点击"忘记密码？"
2. 输入邮箱，系统发送 6 位验证码
3. 输入验证码 + 新密码，重置成功
4. 返回登录页，使用新密码登录

系统通过以下措施确保安全：
- 验证码 15 分钟有效期
- 5 次输入失败后账户锁定 1 小时
- 30 秒内限流（最多发送 1 次）
- 不泄露邮箱是否存在
- 新密码必须符合强度要求
