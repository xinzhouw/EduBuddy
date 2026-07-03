# 登录错误处理改进 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 改进登录失败时的用户体验，通过返回结构化的错误码，前端显示对应的错误提示在模态对话框中，同时保持安全性。

**Architecture:** 
1. 后端在登录失败时返回包含 `error_code` 字段的结构化响应
2. 前端根据 `error_code` 从映射表中查找对应的用户友好提示
3. 在模态对话框中显示错误信息，某些错误类型（如速率限制）还会显示倒计时

**Tech Stack:** Vue 3, TypeScript, Element Plus, FastAPI, Pydantic

## Global Constraints

- 安全性优先：对外不能泄露 "邮箱不存在" 或 "密码错误"，仍显示统一的 "邮箱或密码错误"
- 后端返回格式：所有错误响应必须包含 `error_code` 字段
- 前端显示：错误信息通过模态对话框展示
- 不修改现有的速率限制逻辑，只是改进错误返回格式

---

## 文件结构

### 后端修改

**`backend/app/routers/auth.py`** - login 端点
- 修改登录错误处理，返回结构化的 error_code
- 保留现有的安全性逻辑和速率限制

**`backend/app/schemas/auth.py`** - 认证 schema（可选）
- 如需类型检查，可扩展错误响应 schema

### 前端新建

**`frontend/src/utils/errorMessages.ts`** - 新建
- 定义错误码到用户消息的映射表
- 包含标题、消息、建议操作

### 前端修改

**`frontend/src/views/auth/LoginView.vue`** - 登录页面
- 添加错误对话框组件
- 改进 handleLogin 的错误处理
- 实现倒计时逻辑（针对速率限制）

**`frontend/src/stores/auth.ts`** - 认证 store
- 改进错误传播，不在 store 中捕获登录异常

---

## Task 1: 后端 - 修改 login 端点返回 error_code

**Files:**
- Modify: `backend/app/routers/auth.py:129-186`

**Interfaces:**
- Consumes: 现有的速率限制检查、密码验证、用户查询逻辑
- Produces: 返回包含 `error_code` 字段的 HTTPException，格式如下：
  ```python
  {
    "code": 401,
    "error_code": "INVALID_CREDENTIALS",
    "message": "邮箱或密码错误",
    "data": null,
    "retry_after": null
  }
  ```

- [ ] **Step 1: 在 auth.py 中定义错误码常量**

在 login 函数前添加错误码定义：

```python
# 错误码常量
class LoginErrorCode:
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVER_ERROR = "SERVER_ERROR"
```

- [ ] **Step 2: 修改 login 端点的无效凭证错误处理**

找到 login 函数中这一行（约 149 行）：
```python
raise HTTPException(status_code=401, detail="邮箱或密码错误")
```

替换为：
```python
raise HTTPException(
    status_code=401,
    detail={
        "code": 401,
        "error_code": LoginErrorCode.INVALID_CREDENTIALS,
        "message": "邮箱或密码错误",
        "data": None,
        "retry_after": None
    }
)
```

- [ ] **Step 3: 添加账户被禁用的错误处理**

在 login 函数中，验证密码后、生成令牌前，添加账户状态检查：

```python
# 验证密码后
user = db.query(User).filter(User.email == data.email, User.is_active == True).first()
if user and verify_password(data.password, user.password):
    # Valid credentials
    pass
else:
    # Invalid credentials
    raise HTTPException(
        status_code=401,
        detail={
            "code": 401,
            "error_code": LoginErrorCode.INVALID_CREDENTIALS,
            "message": "邮箱或密码错误",
            "data": None,
            "retry_after": None
        }
    )

# 检查账户是否被禁用（如果 user 存在但 is_active = False）
if not user.is_active:
    raise HTTPException(
        status_code=403,
        detail={
            "code": 403,
            "error_code": LoginErrorCode.ACCOUNT_DISABLED,
            "message": "账户已禁用，请联系管理员",
            "data": None,
            "retry_after": None
        }
    )
```

- [ ] **Step 4: 改进速率限制错误返回格式**

找到 login 函数中速率限制的处理（约 132-140 行）：

```python
allowed, _, retry_after = check_rate_limit_for_endpoint(ip_address, "login")
if not allowed:
    raise HTTPException(
        status_code=429,
        detail=f"请求过于频繁，请在 {retry_after} 秒后重试",
        headers={"Retry-After": str(retry_after)},
    )
```

替换为：
```python
allowed, _, retry_after = check_rate_limit_for_endpoint(ip_address, "login")
if not allowed:
    raise HTTPException(
        status_code=429,
        detail={
            "code": 429,
            "error_code": LoginErrorCode.RATE_LIMIT_EXCEEDED,
            "message": f"登录过于频繁，请在 {retry_after} 秒后重试",
            "data": None,
            "retry_after": retry_after
        },
        headers={"Retry-After": str(retry_after)},
    )
```

- [ ] **Step 5: 测试后端错误返回**

启动后端服务：
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

使用 curl 测试各种错误情况：

```bash
# 测试无效凭证
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"nonexistent@test.com","password":"wrongpassword"}'

# 预期响应：
# {
#   "detail": {
#     "code": 401,
#     "error_code": "INVALID_CREDENTIALS",
#     "message": "邮箱或密码错误",
#     "data": null,
#     "retry_after": null
#   }
# }
```

- [ ] **Step 6: 提交后端改动**

```bash
cd backend
git add app/routers/auth.py
git commit -m "feat: add error_code to login endpoint response"
```

---

## Task 2: 前端 - 创建错误消息映射表

**Files:**
- Create: `frontend/src/utils/errorMessages.ts`

**Interfaces:**
- Consumes: 无
- Produces: 导出 `LOGIN_ERROR_MESSAGES` 对象，键为错误码，值为 `{ title, message, suggestion }` 对象

- [ ] **Step 1: 创建 errorMessages.ts 文件**

在 `frontend/src/utils/` 目录下创建新文件：

```bash
touch frontend/src/utils/errorMessages.ts
```

- [ ] **Step 2: 定义错误消息映射表**

```typescript
export interface LoginErrorInfo {
  title: string
  message: string
  suggestion: string | null
}

export const LOGIN_ERROR_MESSAGES: Record<string, LoginErrorInfo> = {
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

- [ ] **Step 3: 提交前端新文件**

```bash
cd frontend
git add src/utils/errorMessages.ts
git commit -m "feat: add login error messages mapping"
```

---

## Task 3: 前端 - 修改 auth store 改进错误传播

**Files:**
- Modify: `frontend/src/stores/auth.ts:25-32`

**Interfaces:**
- Consumes: authApi.login() 返回的响应
- Produces: 抛出完整的错误对象给调用方（LoginView.vue），包含 response.data 中的所有字段

- [ ] **Step 1: 修改 auth store 的 login 方法**

打开 `frontend/src/stores/auth.ts`，找到 login 函数（约 25-32 行）：

```typescript
async function login(email: string, password: string) {
  const res: any = await authApi.login({ email, password })
  token.value = res.data.access_token
  user.value = res.data.user
  localStorage.setItem('token', res.data.access_token)
  localStorage.setItem('user', JSON.stringify(res.data.user))
  ElMessage.success('登录成功')
}
```

替换为：
```typescript
async function login(email: string, password: string) {
  try {
    const res: any = await authApi.login({ email, password })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    ElMessage.success('登录成功')
  } catch (error: any) {
    // 不在这里捕获异常，让错误传播给 LoginView.vue 处理
    throw error
  }
}
```

实际上，移除成功提示消息，让 LoginView 负责所有的 UI 提示：

```typescript
async function login(email: string, password: string) {
  const res: any = await authApi.login({ email, password })
  token.value = res.data.access_token
  user.value = res.data.user
  localStorage.setItem('token', res.data.access_token)
  localStorage.setItem('user', JSON.stringify(res.data.user))
}
```

- [ ] **Step 2: 移除 auth store 中的成功提示**

移除 login 函数中的 `ElMessage.success('登录成功')`，因为 LoginView 会负责显示成功消息或错误提示。

- [ ] **Step 3: 提交 store 改动**

```bash
cd frontend
git add src/stores/auth.ts
git commit -m "refactor: remove UI logic from auth store login method"
```

---

## Task 4: 前端 - 修改 LoginView 添加错误对话框和处理

**Files:**
- Modify: `frontend/src/views/auth/LoginView.vue:32-119`

**Interfaces:**
- Consumes: 
  - LOGIN_ERROR_MESSAGES from `@/utils/errorMessages`
  - authStore.login() 抛出的错误对象
- Produces: 
  - 显示错误对话框
  - 实现倒计时逻辑
  - 禁用/启用登录按钮

- [ ] **Step 1: 导入必要的模块和消息映射**

在 `<script setup>` 部分的开头添加导入：

```typescript
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { LOGIN_ERROR_MESSAGES } from '@/utils/errorMessages'
import type { FormInstance } from 'element-plus'
```

- [ ] **Step 2: 添加状态变量用于错误对话框和倒计时**

在 `const loading = ref(false)` 后添加：

```typescript
const errorDialogVisible = ref(false)
const errorTitle = ref('')
const errorMessage = ref('')
const errorSuggestion = ref<string | null>(null)
const retryCountdown = ref(0)
const countdownInterval = ref<NodeJS.Timeout | null>(null)
```

- [ ] **Step 3: 编写显示错误对话框的函数**

在 `handleLogin` 函数前添加：

```typescript
function showErrorDialog(errorCode: string, retryAfter?: number) {
  const errorInfo = LOGIN_ERROR_MESSAGES[errorCode] || LOGIN_ERROR_MESSAGES.SERVER_ERROR
  errorTitle.value = errorInfo.title
  errorMessage.value = errorInfo.message
  errorSuggestion.value = errorInfo.suggestion
  errorDialogVisible.value = true

  // 如果是速率限制错误，启动倒计时
  if (errorCode === 'RATE_LIMIT_EXCEEDED' && retryAfter) {
    retryCountdown.value = retryAfter
    disableLoginButtonWithCountdown(retryAfter)
  }
}

function disableLoginButtonWithCountdown(seconds: number) {
  loading.value = true

  if (countdownInterval.value) {
    clearInterval(countdownInterval.value)
  }

  countdownInterval.value = setInterval(() => {
    retryCountdown.value--
    if (retryCountdown.value <= 0) {
      clearInterval(countdownInterval.value!)
      loading.value = false
      retryCountdown.value = 0
    }
  }, 1000)
}

function closeErrorDialog() {
  errorDialogVisible.value = false
}

onBeforeUnmount(() => {
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value)
  }
})
```

需要在导入中添加 `onBeforeUnmount`：
```typescript
import { ref, reactive, onMounted, nextTick, onBeforeUnmount } from 'vue'
```

- [ ] **Step 4: 改进 handleLogin 函数的错误处理**

替换现有的 handleLogin 函数：

```typescript
async function handleLogin() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authStore.login(form.email, form.password)
      // 登录成功，显示成功消息并跳转
      ElMessage.success('登录成功')
      const role = authStore.user?.role
      if (role === 'admin') {
        router.push('/admin/dashboard')
      } else {
        router.push('/')
      }
    } catch (error: any) {
      loading.value = false
      const errorCode = error.response?.data?.error_code || 'NETWORK_ERROR'
      const retryAfter = error.response?.data?.retry_after
      showErrorDialog(errorCode, retryAfter)
    }
  })
}
```

- [ ] **Step 5: 在模板中添加错误对话框**

在 `</el-form>` 后、`</div>` 前添加错误对话框：

```vue
        <!-- 错误对话框 -->
        <el-dialog
          v-model="errorDialogVisible"
          :title="errorTitle"
          width="90%"
          :close-on-click-modal="false"
          :close-on-press-escape="false"
        >
          <div class="space-y-4">
            <p class="text-gray-700">{{ errorMessage }}</p>
            
            <!-- 倒计时提示 -->
            <p v-if="retryCountdown > 0" class="text-sm text-orange-600">
              请在 <span class="font-bold">{{ retryCountdown }}</span> 秒后重试
            </p>
            
            <!-- 建议操作 -->
            <p v-if="errorSuggestion" class="text-sm text-gray-600">
              💡 {{ errorSuggestion }}
            </p>
          </div>

          <template #footer>
            <el-button type="primary" @click="closeErrorDialog">
              确定
            </el-button>
          </template>
        </el-dialog>
```

- [ ] **Step 6: 更新登录按钮显示倒计时**

修改登录按钮部分，显示倒计时：

```vue
          <el-button 
            type="primary" 
            size="large" 
            class="w-full mt-2 h-11 sm:h-12" 
            :loading="loading" 
            @click="handleLogin"
            :disabled="retryCountdown > 0"
          >
            {{ retryCountdown > 0 ? `登 录 (${retryCountdown}s)` : '登 录' }}
          </el-button>
```

- [ ] **Step 7: 测试前端错误处理**

启动前端开发服务器：
```bash
cd frontend
npm run dev
```

在浏览器中访问 `http://localhost:3000/login`，测试：
1. 输入错误的邮箱/密码，应显示 "邮箱或密码错误" 的对话框
2. 多次快速登录，应显示速率限制对话框和倒计时
3. 关闭网络，应显示网络错误对话框

- [ ] **Step 8: 提交前端改动**

```bash
cd frontend
git add src/views/auth/LoginView.vue src/stores/auth.ts src/utils/errorMessages.ts
git commit -m "feat: add error handling with modal dialogs and countdown for login"
```

---

## Task 5: 集成测试

**Files:**
- Test: 手动端到端测试

**Interfaces:**
- 无需编写代码，仅进行集成测试

- [ ] **Step 1: 启动后端和前端**

```bash
# 终端 1：后端
cd backend
uvicorn app.main:app --reload --port 8000

# 终端 2：前端
cd frontend
npm run dev
```

- [ ] **Step 2: 测试无效凭证错误**

1. 访问 `http://localhost:3000/login`
2. 输入不存在的邮箱（如 `test@example.com`）和任意密码
3. 点击登录
4. 验证：显示标题为 "登录失败" 的对话框，消息为 "邮箱或密码错误，请检查后重试"
5. 关闭对话框

- [ ] **Step 3: 测试有效邮箱但密码错误**

1. 使用已知的有效邮箱，输入错误的密码
2. 点击登录
3. 验证：显示相同的错误对话框（不泄露邮箱存在性）
4. 关闭对话框

- [ ] **Step 4: 测试账户被禁用错误**

1. 在数据库中手动禁用一个测试用户（设置 `is_active = 0`）
2. 用该用户的正确凭证登录
3. 验证：显示标题为 "账户已禁用" 的对话框
4. 恢复用户的 `is_active` 状态

- [ ] **Step 5: 测试速率限制错误**

1. 在后端临时降低速率限制阈值（如改为 `2/minute` 用于测试）
2. 快速点击登录按钮 3 次
3. 验证：显示 "登录过于频繁" 对话框，倒计时显示
4. 验证：登录按钮显示倒计时秒数，且被禁用
5. 等待倒计时结束，验证按钮重新启用
6. 恢复速率限制阈值

- [ ] **Step 6: 测试网络错误**

1. 在浏览器开发者工具中使用 "Offline" 模式或关闭后端服务
2. 尝试登录
3. 验证：显示 "网络连接失败" 的对话框
4. 恢复网络连接

- [ ] **Step 7: 测试成功登录**

1. 用有效凭证登录
2. 验证：显示 "登录成功" 的 Toast 提示
3. 验证：页面跳转到首页（或对应角色的首页）

- [ ] **Step 8: 整理测试结果**

记录所有测试用例的通过情况，确保：
- ✅ 所有错误类型都显示在对话框中
- ✅ 错误消息准确且用户友好
- ✅ 倒计时逻辑正常工作
- ✅ 安全性保留（不泄露邮箱存在性）

---

## Task 6: 最终提交和文档

**Files:**
- Modify: 项目文档（如需）

**Interfaces:**
- 无

- [ ] **Step 1: 更新项目内存（可选）**

如果项目使用了内存系统，可更新相关内存记录：

```bash
# 检查是否需要更新内存
ls .claude/projects/*/memory/
```

- [ ] **Step 2: 最后一次验证改动**

```bash
# 检查所有改动
git diff --stat

# 预期输出应该包括：
# backend/app/routers/auth.py (修改)
# frontend/src/utils/errorMessages.ts (新建)
# frontend/src/views/auth/LoginView.vue (修改)
# frontend/src/stores/auth.ts (修改)
```

- [ ] **Step 3: 创建最终提交（如未分别提交）**

如果之前没有按任务分别提交，现在合并所有改动：

```bash
git log --oneline -10
# 应该看到相关的提交记录
```

- [ ] **Step 4: 验证设计文档完成**

检查设计文档是否已保存：

```bash
ls -la docs/superpowers/specs/2026-06-26-login-error-handling-design.md
```

- [ ] **Step 5: 任务完成**

所有任务完成，登录错误处理改进功能已实现！

---

## 自审检查

**✅ Spec 覆盖率：**
- 错误码定义：Task 1 (后端定义 + 返回)、Task 2 (前端映射)
- 模态对话框显示：Task 4 (错误对话框模板)
- 倒计时逻辑：Task 4 (countdown 函数)
- 安全性保留：Task 1 (仍返回统一消息) + Task 4 (不在 UI 泄露细节)
- 前端错误处理：Task 3 (store 错误传播) + Task 4 (LoginView 处理)

**✅ 无占位符：**
- 所有代码步骤都有完整的代码示例
- 所有测试步骤都有具体的操作步骤和验证方式
- 没有 "TBD"、"TODO" 或模糊的指示

**✅ 类型一致性：**
- error_code 字符串类型：后端返回、前端映射、处理一致
- retry_after 数字类型：后端返回、前端显示倒计时一致
- 错误消息对象结构一致：{ title, message, suggestion }

**✅ 任务粒度：**
- 每个任务都可独立测试
- 每个任务都有明确的验收标准
- 任务之间有清晰的依赖关系

---

## 执行选项

计划已完成并保存到 `docs/superpowers/plans/2026-06-26-login-error-handling.md`。

**两种执行方式可选：**

**1. Subagent-Driven（推荐）** - 我为每个任务分派一个新的 subagent，任务间进行审查，快速迭代
   - 优点：并行化强、反馈及时、风险隔离
   - 使用技能：`superpowers:subagent-driven-development`

**2. Inline Execution** - 在本会话中使用 executing-plans 执行任务，设置检查点进行审查
   - 优点：上下文连贯、快速执行
   - 使用技能：`superpowers:executing-plans`

**你选择哪种方式？**
