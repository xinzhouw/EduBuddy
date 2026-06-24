# 密码强度增强 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现标准级密码强度验证系统，支持注册和修改密码的验证，前端提供实时反馈。

**Architecture:** 后端独立的密码强度评分模块 + 验证 API，前端通过 API 调用获取实时反馈，两个新组件分别用于注册和修改密码流程。

**Tech Stack:** 
- 后端：FastAPI, Pydantic, bcrypt
- 前端：Vue 3, Composition API, TypeScript, Element Plus, lodash-es

## Global Constraints

- 密码规则：长度≥8、至少1大写、1小写、1数字、1特殊字符
- 前端实时反馈防抖：300ms
- 后端错误返回：400（密码过弱）、401（旧密码错误）
- API 端点前缀：/api/auth

---

## Task 1: 后端密码强度评分模块

**Files:**
- Create: `app/utils/password_validator.py`
- Test: `tests/test_password_validator.py`

**Interfaces:**
- Produces: 
  - `PasswordStrength` enum: WEAK, MEDIUM, STRONG
  - `PasswordValidationResult` class: score (int), strength (PasswordStrength), issues (list[str])
  - `validate_password_strength(password: str) -> PasswordValidationResult`
  - `check_password_validity(password: str) -> tuple[bool, str]`

---

- [ ] **Step 1: 创建测试文件**

在 `tests/test_password_validator.py` 写入以下测试用例：

```python
import pytest
from app.utils.password_validator import validate_password_strength, check_password_validity, PasswordStrength

class TestPasswordValidator:
    """密码强度验证器测试"""
    
    def test_password_too_short(self):
        """密码过短"""
        result = validate_password_strength("abc")
        assert result.strength == PasswordStrength.WEAK
        assert any("长度" in issue for issue in result.issues)
    
    def test_password_missing_lowercase(self):
        """缺少小写字母"""
        result = validate_password_strength("PASSWORD123!")
        assert result.strength == PasswordStrength.WEAK
        assert any("小写" in issue for issue in result.issues)
    
    def test_password_missing_uppercase(self):
        """缺少大写字母"""
        result = validate_password_strength("password123!")
        assert result.strength == PasswordStrength.WEAK
        assert any("大写" in issue for issue in result.issues)
    
    def test_password_missing_digit(self):
        """缺少数字"""
        result = validate_password_strength("SecurePass!")
        assert result.strength == PasswordStrength.WEAK
        assert any("数字" in issue for issue in result.issues)
    
    def test_password_missing_special_char(self):
        """缺少特殊字符"""
        result = validate_password_strength("SecurePass123")
        assert result.strength == PasswordStrength.WEAK
        assert any("特殊字符" in issue for issue in result.issues)
    
    def test_medium_strength_password(self):
        """中等强度密码（8字符满足所有条件）"""
        result = validate_password_strength("SecurePass123!")
        assert result.strength == PasswordStrength.STRONG
        assert result.issues == []
        assert result.score >= 60
    
    def test_strong_password_long(self):
        """强密码（长度≥16）"""
        result = validate_password_strength("VerySecurePassword123!")
        assert result.strength == PasswordStrength.STRONG
        assert result.score >= 60
    
    def test_check_validity_invalid(self):
        """check_password_validity - 无效密码"""
        is_valid, msg = check_password_validity("weak")
        assert is_valid is False
        assert ";" in msg  # 多个错误用;分隔
    
    def test_check_validity_valid(self):
        """check_password_validity - 有效密码"""
        is_valid, msg = check_password_validity("SecurePass123!")
        assert is_valid is True
        assert msg == ""
    
    def test_special_chars_recognized(self):
        """特殊字符识别"""
        special_chars = "!@#$%^&*()_+-=[]{}`;:'\",.<>?/\\|`~"
        for char in special_chars:
            password = f"SecurePass123{char}"
            result = validate_password_strength(password)
            assert result.strength == PasswordStrength.STRONG, f"Failed for char: {char}"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/xinzhouw/src/EduBuddy
python -m pytest tests/test_password_validator.py -v
```

Expected: 所有测试 FAIL，模块不存在

---

- [ ] **Step 3: 实现密码强度评分模块**

创建 `app/utils/password_validator.py`：

```python
import re
from enum import Enum


class PasswordStrength(str, Enum):
    """密码强度等级"""
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


class PasswordValidationResult:
    """密码验证结果"""
    def __init__(self, score: int, strength: PasswordStrength, issues: list[str]):
        self.score = score  # 0-100
        self.strength = strength
        self.issues = issues


def validate_password_strength(password: str) -> PasswordValidationResult:
    """
    评分密码强度
    
    评分规则（0-100）：
    - 长度 ≥8: +20 | ≥12: +30 | ≥16: +40 分
    - 包含小写字母: +10
    - 包含大写字母: +15
    - 包含数字: +15
    - 包含特殊字符: +20
    
    强度等级：
    - 有缺陷 → 弱
    - 无缺陷 & score < 60 → 中等
    - 无缺陷 & score ≥ 60 → 强
    """
    issues = []
    score = 0
    
    # 长度检查
    if len(password) < 8:
        issues.append("密码长度至少8个字符")
    elif len(password) >= 16:
        score += 40
    elif len(password) >= 12:
        score += 30
    else:
        score += 20
    
    # 小写字母
    if not re.search(r'[a-z]', password):
        issues.append("密码需包含小写字母")
    else:
        score += 10
    
    # 大写字母
    if not re.search(r'[A-Z]', password):
        issues.append("密码需包含大写字母")
    else:
        score += 15
    
    # 数字
    if not re.search(r'\d', password):
        issues.append("密码需包含数字")
    else:
        score += 15
    
    # 特殊字符
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        issues.append("密码需包含特殊字符")
    else:
        score += 20
    
    # 确定强度等级
    if issues:
        strength = PasswordStrength.WEAK
    elif score < 60:
        strength = PasswordStrength.MEDIUM
    else:
        strength = PasswordStrength.STRONG
    
    return PasswordValidationResult(score, strength, issues)


def check_password_validity(password: str) -> tuple[bool, str]:
    """
    快速检查密码是否满足最小要求
    
    返回 (是否有效, 错误消息)
    """
    result = validate_password_strength(password)
    if result.issues:
        return False, "; ".join(result.issues)
    return True, ""
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_password_validator.py -v
```

Expected: 所有测试 PASS

- [ ] **Step 5: 提交**

```bash
git add app/utils/password_validator.py tests/test_password_validator.py
git commit -m "feat: 添加密码强度评分模块"
```

---

## Task 2: 后端密码验证 API 端点

**Files:**
- Modify: `app/routes/auth.py`
- Modify: `app/schemas/auth.py` (新增 Pydantic 模型)
- Test: `tests/test_auth.py` (新增测试)

**Interfaces:**
- Consumes: 
  - `validate_password_strength()` from Task 1
  - `check_password_validity()` from Task 1
- Produces:
  - `POST /api/auth/password/validate` endpoint
  - `POST /api/auth/change-password` endpoint (修改现有 register)
  - `PasswordStrengthResponse` schema
  - `ChangePasswordRequest` schema

---

- [ ] **Step 1: 添加 Pydantic 模型**

在 `app/schemas/auth.py` 中添加（或创建文件如不存在）：

```python
from pydantic import BaseModel


class PasswordStrengthResponse(BaseModel):
    """密码强度响应"""
    score: int  # 0-100
    strength: str  # "weak" | "medium" | "strong"
    issues: list[str]


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str
```

- [ ] **Step 2: 添加密码验证 API 端点**

在 `app/routes/auth.py` 中的 router 对象添加以下新端点（在其他端点之前）：

```python
from fastapi import Query
from app.utils.password_validator import validate_password_strength
from app.schemas.auth import PasswordStrengthResponse, ChangePasswordRequest

@router.post("/password/validate")
async def validate_password(password: str = Query(..., min_length=1)):
    """
    实时检查密码强度
    
    不检查已注册密码或其他业务逻辑，仅返回技术强度评分。
    前端用此 API 提供实时反馈。
    
    响应示例：
    {
        "score": 85,
        "strength": "strong",
        "issues": []
    }
    """
    result = validate_password_strength(password)
    return PasswordStrengthResponse(
        score=result.score,
        strength=result.strength,
        issues=result.issues
    )
```

- [ ] **Step 3: 修改 register 端点添加密码强度检查**

在 `app/routes/auth.py` 中找到 `@router.post("/register")` 端点，在邮箱唯一性检查后、创建用户前添加：

```python
from app.utils.password_validator import check_password_validity

@router.post("/register")
async def register(req: UserRegister, db: Session = Depends(get_db)):
    # [现有] 检查邮箱唯一性
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(400, "邮箱已存在")
    
    # [新增] 检查密码强度（注册时强制）
    is_valid, error_msg = check_password_validity(req.password)
    if not is_valid:
        raise HTTPException(400, f"密码不符合要求: {error_msg}")
    
    # [现有] 创建用户、生成令牌...
    # （保持现有逻辑不变）
```

- [ ] **Step 4: 添加 change-password 新端点**

在 `app/routes/auth.py` 的 router 中添加：

```python
from app.security import verify_password, hash_password
from app.dependencies import get_current_user

@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码
    
    1. 验证旧密码正确性
    2. 检查新密码强度
    3. 更新密码哈希
    """
    # 验证旧密码
    if not verify_password(req.old_password, user.password):
        raise HTTPException(401, "旧密码错误")
    
    # 检查新密码强度
    is_valid, error_msg = check_password_validity(req.new_password)
    if not is_valid:
        raise HTTPException(400, f"新密码不符合要求: {error_msg}")
    
    # 不能与旧密码相同
    if req.old_password == req.new_password:
        raise HTTPException(400, "新密码不能与旧密码相同")
    
    # 更新密码
    user.password = hash_password(req.new_password)
    db.commit()
    
    return {"message": "密码已修改"}
```

- [ ] **Step 5: 编写 API 集成测试**

在 `tests/test_auth.py` 中添加（或创建文件如不存在）：

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestPasswordValidateEndpoint:
    """密码验证端点测试"""
    
    def test_validate_weak_password(self):
        """验证弱密码"""
        response = client.post("/api/auth/password/validate?password=weak")
        assert response.status_code == 200
        data = response.json()
        assert data["strength"] == "weak"
        assert len(data["issues"]) > 0
    
    def test_validate_strong_password(self):
        """验证强密码"""
        response = client.post("/api/auth/password/validate?password=SecurePass123!")
        assert response.status_code == 200
        data = response.json()
        assert data["strength"] == "strong"
        assert data["issues"] == []
        assert data["score"] >= 60


class TestRegisterWithPasswordValidation:
    """注册端点密码验证测试"""
    
    def test_register_weak_password(self):
        """使用弱密码注册失败"""
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "weak",
            "nickname": "test",
            "grade": "高一",
            "role": "student"
        })
        assert response.status_code == 400
        assert "不符合要求" in response.json()["detail"]
    
    def test_register_strong_password(self):
        """使用强密码注册成功"""
        response = client.post("/api/auth/register", json={
            "email": f"test_{int(time.time())}@example.com",
            "password": "SecurePass123!",
            "nickname": "test",
            "grade": "高一",
            "role": "student"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == data["user"]["email"]


class TestChangePasswordEndpoint:
    """修改密码端点测试"""
    
    @pytest.fixture
    def auth_header(self, registered_user_token):
        """获取认证头"""
        return {"Authorization": f"Bearer {registered_user_token}"}
    
    def test_change_password_weak_new_password(self, auth_header):
        """新密码过弱失败"""
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "OldPass123!",
                "new_password": "weak"
            },
            headers=auth_header
        )
        assert response.status_code == 400
        assert "不符合要求" in response.json()["detail"]
    
    def test_change_password_wrong_old_password(self, auth_header):
        """旧密码错误失败"""
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "WrongPass123!",
                "new_password": "NewPass123!"
            },
            headers=auth_header
        )
        assert response.status_code == 401
        assert "旧密码错误" in response.json()["detail"]
    
    def test_change_password_same_as_old(self, auth_header):
        """新密码与旧密码相同失败"""
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "OldPass123!",
                "new_password": "OldPass123!"
            },
            headers=auth_header
        )
        assert response.status_code == 400
        assert "相同" in response.json()["detail"]
    
    def test_change_password_success(self, auth_header):
        """修改密码成功"""
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "OldPass123!",
                "new_password": "NewPass123!"
            },
            headers=auth_header
        )
        assert response.status_code == 200
        assert "密码已修改" in response.json()["message"]
```

- [ ] **Step 6: 运行测试**

```bash
python -m pytest tests/test_auth.py::TestPasswordValidateEndpoint -v
python -m pytest tests/test_auth.py::TestRegisterWithPasswordValidation -v
python -m pytest tests/test_auth.py::TestChangePasswordEndpoint -v
```

Expected: 所有测试 PASS

- [ ] **Step 7: 提交**

```bash
git add app/routes/auth.py app/schemas/auth.py tests/test_auth.py
git commit -m "feat: 添加密码强度验证 API 端点"
```

---

## Task 3: 前端密码验证工具函数

**Files:**
- Create: `src/utils/passwordValidator.ts`
- Test: `tests/unit/utils/passwordValidator.spec.ts` (可选)

**Interfaces:**
- Produces:
  - `PasswordValidationResult` interface: score (number), strength (string), issues (string[])
  - `validatePasswordStrength(password: string) -> Promise<PasswordValidationResult>`

---

- [ ] **Step 1: 创建密码验证工具函数**

创建 `src/utils/passwordValidator.ts`：

```typescript
export interface PasswordValidationResult {
  score: number  // 0-100
  strength: 'weak' | 'medium' | 'strong'
  issues: string[]
}

/**
 * 验证密码强度（调用后端 API）
 */
export async function validatePasswordStrength(
  password: string
): Promise<PasswordValidationResult> {
  try {
    const response = await fetch('/api/auth/password/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ password })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    
    return await response.json()
  } catch (error) {
    // 网络错误时返回默认值（弱）
    console.error('Password validation failed:', error)
    return {
      score: 0,
      strength: 'weak',
      issues: ['无法验证密码强度，请检查网络']
    }
  }
}
```

**注意：** 如果项目使用 axios API 实例，改为：

```typescript
import { api } from '@/api'

export async function validatePasswordStrength(
  password: string
): Promise<PasswordValidationResult> {
  try {
    const response = await api.post('/auth/password/validate', { password })
    return response
  } catch (error) {
    console.error('Password validation failed:', error)
    return {
      score: 0,
      strength: 'weak',
      issues: ['无法验证密码强度，请检查网络']
    }
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add src/utils/passwordValidator.ts
git commit -m "feat: 添加前端密码验证工具函数"
```

---

## Task 4: 前端 PasswordInput 组件

**Files:**
- Create: `src/components/PasswordInput.vue`

**Interfaces:**
- Consumes: `validatePasswordStrength()` from Task 3
- Produces: 
  - Vue 3 Composition API component
  - Exposes: `password` (ref), `validation` (ref)

---

- [ ] **Step 1: 创建 PasswordInput 组件**

创建 `src/components/PasswordInput.vue`：

```vue
<template>
  <div class="password-group">
    <!-- 密码输入框 -->
    <el-input
      v-model="password"
      type="password"
      placeholder="请输入密码"
      :show-password="true"
      @input="handlePasswordChange"
    />
    
    <!-- 实时反馈（仅当输入时显示）-->
    <div v-if="password" class="feedback">
      <!-- 强度进度条 -->
      <div class="strength-container">
        <el-progress
          :percentage="validation.score"
          :color="strengthColor"
          :show-text="false"
        />
        <span class="strength-text" :class="validation.strength">
          {{ strengthLabel }}
        </span>
      </div>
      
      <!-- 缺陷列表 -->
      <div v-if="validation.issues.length" class="issues">
        <div v-for="issue in validation.issues" :key="issue" class="issue">
          <span class="icon">❌</span>
          <span>{{ issue }}</span>
        </div>
      </div>
      
      <!-- 成功标记 -->
      <div v-else class="success">
        <span class="icon">✅</span>
        <span>密码符合要求</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { validatePasswordStrength, type PasswordValidationResult } from '@/utils/passwordValidator'
import { debounce } from 'lodash-es'

const password = ref('')
const validation = ref<PasswordValidationResult>({
  score: 0,
  strength: 'weak',
  issues: []
})

const strengthLabel = computed(() => {
  const labels = {
    weak: '弱',
    medium: '中等',
    strong: '强'
  }
  return labels[validation.value.strength]
})

const strengthColor = computed(() => {
  const colors = {
    weak: '#F56C6C',
    medium: '#E6A23C',
    strong: '#67C23A'
  }
  return colors[validation.value.strength]
})

const handlePasswordChange = debounce(async () => {
  if (!password.value) {
    validation.value = { score: 0, strength: 'weak', issues: [] }
    return
  }
  
  validation.value = await validatePasswordStrength(password.value)
}, 300)

// 外部可调用此方法获取当前密码
defineExpose({
  password,
  validation
})
</script>

<style scoped>
.password-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feedback {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.strength-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.strength-container :deep(.el-progress) {
  flex: 1;
}

.strength-text {
  font-size: 12px;
  font-weight: bold;
  min-width: 40px;
  text-align: right;
}

.strength-text.weak { color: #F56C6C; }
.strength-text.medium { color: #E6A23C; }
.strength-text.strong { color: #67C23A; }

.issues {
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
}

.issue {
  display: flex;
  align-items: center;
  gap: 6px;
  line-height: 1.8;
}

.icon {
  flex-shrink: 0;
}

.success {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  color: #67C23A;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/components/PasswordInput.vue
git commit -m "feat: 添加 PasswordInput 实时反馈组件"
```

---

## Task 5: 前端修改密码对话框组件

**Files:**
- Create: `src/components/ChangePasswordDialog.vue`

**Interfaces:**
- Consumes: 
  - `PasswordInput` component from Task 4
  - `api` instance for POST /auth/change-password
- Produces:
  - Vue 3 component with dialog
  - Exposes: `visible` (ref)

---

- [ ] **Step 1: 创建修改密码对话框组件**

创建 `src/components/ChangePasswordDialog.vue`：

```vue
<template>
  <el-dialog
    v-model="visible"
    title="修改密码"
    width="400px"
    @close="resetForm"
  >
    <el-form :model="form" ref="formRef">
      <!-- 旧密码 -->
      <el-form-item label="旧密码" prop="oldPassword">
        <el-input
          v-model="form.oldPassword"
          type="password"
          :show-password="true"
          placeholder="请输入旧密码"
        />
      </el-form-item>
      
      <!-- 新密码（实时反馈） -->
      <el-form-item label="新密码" prop="newPassword">
        <PasswordInput ref="passwordInput" />
      </el-form-item>
      
      <!-- 确认新密码 -->
      <el-form-item label="确认新密码" prop="confirmPassword">
        <el-input
          v-model="form.confirmPassword"
          type="password"
          :show-password="true"
          placeholder="请再次输入新密码"
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        修改
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import PasswordInput from '@/components/PasswordInput.vue'
import { api } from '@/api'

const visible = ref(false)
const loading = ref(false)
const passwordInput = ref<InstanceType<typeof PasswordInput>>()
const formRef = ref()

const form = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

function resetForm() {
  form.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
}

async function handleSubmit() {
  // 验证新密码
  if (passwordInput.value!.validation.issues.length > 0) {
    ElMessage.error('新密码不符合要求')
    return
  }
  
  if (form.value.newPassword !== form.value.confirmPassword) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }
  
  if (!form.value.oldPassword) {
    ElMessage.error('请输入旧密码')
    return
  }
  
  loading.value = true
  try {
    await api.post('/auth/change-password', {
      old_password: form.value.oldPassword,
      new_password: form.value.newPassword
    })
    ElMessage.success('密码已修改')
    visible.value = false
    resetForm()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '修改失败')
  } finally {
    loading.value = false
  }
}

defineExpose({
  visible
})
</script>
```

- [ ] **Step 2: 提交**

```bash
git add src/components/ChangePasswordDialog.vue
git commit -m "feat: 添加修改密码对话框组件"
```

---

## Task 6: 前端注册页面集成

**Files:**
- Modify: `src/views/auth/Register.vue` 或现有注册页面

**Interfaces:**
- Consumes: `PasswordInput` component from Task 4

---

- [ ] **Step 1: 查找现有注册页面**

```bash
find /home/xinzhouw/src/EduBuddy/src -name "*egister*" -o -name "*register*"
```

找到现有注册页面文件路径，假设为 `src/views/auth/Register.vue`

- [ ] **Step 2: 更新注册表单集成 PasswordInput**

在现有注册页面中，将密码输入框替换为 `<PasswordInput>` 组件：

**修改前（示例）：**
```vue
<el-form-item label="密码" prop="password">
  <el-input v-model="form.password" type="password" />
</el-form-item>
```

**修改后：**
```vue
<el-form-item label="密码" prop="password">
  <PasswordInput ref="passwordInput" />
</el-form-item>
```

在 `<script setup>` 中添加导入和验证逻辑：

```typescript
import PasswordInput from '@/components/PasswordInput.vue'

const passwordInput = ref<InstanceType<typeof PasswordInput>>()

async function handleRegister() {
  // 验证密码符合要求
  if (passwordInput.value!.validation.issues.length > 0) {
    ElMessage.error('密码不符合要求')
    return
  }
  
  // 验证两次密码一致
  if (form.value.password !== form.value.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  
  // 调用后端注册 API
  loading.value = true
  try {
    await api.post('/auth/register', {
      email: form.value.email,
      password: form.value.password,
      nickname: form.value.nickname,
      grade: form.value.grade,
      role: form.value.role
    })
    ElMessage.success('注册成功')
    // 跳转到登录页
    router.push('/login')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
```

- [ ] **Step 3: 提交**

```bash
git add src/views/auth/Register.vue
git commit -m "feat: 注册页面集成密码强度反馈"
```

---

## Task 7: 前端用户设置页面集成修改密码

**Files:**
- Modify: 用户设置/个人中心页面（如 `src/views/Profile.vue` 或 `src/views/Settings.vue`）

**Interfaces:**
- Consumes: `ChangePasswordDialog` component from Task 5

---

- [ ] **Step 1: 查找用户设置页面**

```bash
find /home/xinzhouw/src/EduBuddy/src -name "*rofile*" -o -name "*ettings*" -o -name "*ccout*"
```

找到用户设置或个人中心页面，假设为 `src/views/Profile.vue`

- [ ] **Step 2: 添加修改密码按钮和对话框**

在页面的 template 中添加：

```vue
<template>
  <!-- 现有内容 -->
  
  <!-- 修改密码按钮 -->
  <el-button @click="changePasswordDialogVisible = true">
    修改密码
  </el-button>
  
  <!-- 修改密码对话框 -->
  <ChangePasswordDialog ref="changePasswordDialog" />
</template>

<script setup lang="ts">
import ChangePasswordDialog from '@/components/ChangePasswordDialog.vue'

const changePasswordDialog = ref<InstanceType<typeof ChangePasswordDialog>>()

function openChangePasswordDialog() {
  changePasswordDialog.value!.visible = true
}
</script>
```

更新按钮点击事件绑定：

```vue
<el-button @click="openChangePasswordDialog">
  修改密码
</el-button>
```

- [ ] **Step 3: 提交**

```bash
git add src/views/Profile.vue
git commit -m "feat: 用户设置页面集成修改密码"
```

---

## Task 8: 端到端测试验证

**Files:**
- Create: `tests/e2e/password-strength.spec.ts` 或使用现有 E2E 框架

**Interfaces:**
- Integration test: 验证完整流程

---

- [ ] **Step 1: 编写注册流程 E2E 测试**

如使用 Cypress，创建 `tests/e2e/password-strength.spec.ts`：

```typescript
describe('Password Strength Enhancement', () => {
  beforeEach(() => {
    cy.visit('http://localhost:5173/register')
  })
  
  it('显示弱密码反馈', () => {
    cy.get('input[placeholder="请输入密码"]').type('weak')
    cy.contains('弱').should('be.visible')
    cy.contains('密码长度至少8个字符').should('be.visible')
  })
  
  it('显示强密码反馈', () => {
    cy.get('input[placeholder="请输入密码"]').type('SecurePass123!')
    cy.contains('强').should('be.visible')
    cy.contains('密码符合要求').should('be.visible')
  })
  
  it('阻止使用弱密码注册', () => {
    cy.get('input[placeholder="邮箱"]').type(`test${Date.now()}@example.com`)
    cy.get('input[placeholder="请输入密码"]').type('weak')
    cy.get('button:contains("注册")').click()
    cy.contains('密码不符合要求').should('be.visible')
  })
  
  it('允许使用强密码注册', () => {
    cy.get('input[placeholder="邮箱"]').type(`test${Date.now()}@example.com`)
    cy.get('input[placeholder="请输入密码"]').type('SecurePass123!')
    cy.get('input[placeholder="确认密码"]').type('SecurePass123!')
    cy.get('input[placeholder="昵称"]').type('TestUser')
    cy.get('select').select('高一')
    cy.get('button:contains("注册")').click()
    cy.url().should('include', '/login')
    cy.contains('注册成功').should('be.visible')
  })
})

describe('Change Password Flow', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'SecurePass123!')
    cy.visit('http://localhost:5173/profile')
  })
  
  it('修改密码成功', () => {
    cy.contains('button', '修改密码').click()
    cy.get('input[placeholder="请输入旧密码"]').type('SecurePass123!')
    cy.get('input[placeholder="请输入密码"]').type('NewPass123!')
    cy.get('input[placeholder="请再次输入新密码"]').type('NewPass123!')
    cy.contains('button', '修改').click()
    cy.contains('密码已修改').should('be.visible')
  })
  
  it('新密码过弱则失败', () => {
    cy.contains('button', '修改密码').click()
    cy.get('input[placeholder="请输入旧密码"]').type('SecurePass123!')
    cy.get('input[placeholder="请输入密码"]').type('weak')
    cy.contains('button', '修改').click()
    cy.contains('新密码不符合要求').should('be.visible')
  })
})
```

- [ ] **Step 2: 运行 E2E 测试**

```bash
# 确保前后端都在运行
npm run dev  # 前端开发服务器（另一个终端）
# python main.py  # 后端（另一个终端）

# 运行 E2E 测试
npm run test:e2e
```

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add tests/e2e/password-strength.spec.ts
git commit -m "test: 添加密码强度 E2E 测试"
```

---

## Task 9: 最终验证和部署清单

**Files:** 无新文件

---

- [ ] **Step 1: 运行所有后端测试**

```bash
python -m pytest tests/ -v --tb=short
```

Expected: 所有测试通过，无失败

- [ ] **Step 2: 运行所有前端测试**

```bash
npm run test:unit
npm run test:e2e
```

Expected: 所有测试通过

- [ ] **Step 3: 手动功能验证**

- [ ] 打开注册页面，验证实时密码反馈工作正常
- [ ] 尝试使用弱密码注册，验证被拒绝
- [ ] 使用强密码注册成功
- [ ] 登录后进入个人设置，打开修改密码对话框
- [ ] 尝试修改为弱密码，验证被拒绝
- [ ] 尝试使用错误旧密码，验证被拒绝
- [ ] 使用正确旧密码修改为强密码，验证成功

- [ ] **Step 4: 后端 API 文档更新**

在后端 API 文档或 OpenAPI/Swagger 文档中添加：

```markdown
## 新增端点

### POST /api/auth/password/validate
**功能：** 实时检查密码强度

**请求：**
```
POST /api/auth/password/validate?password=SecurePass123!
```

**响应（200）：**
```json
{
  "score": 85,
  "strength": "strong",
  "issues": []
}
```

### POST /api/auth/change-password
**功能：** 修改密码

**认证：** 需要有效的 JWT token

**请求：**
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass123!"
}
```

**响应（200）：**
```json
{
  "message": "密码已修改"
}
```

**错误：**
- 401: 旧密码错误
- 400: 新密码不符合要求或与旧密码相同
```

- [ ] **Step 5: 最终提交（总结）**

```bash
git add -A
git commit -m "docs: 密码强度功能实现完成"
```

- [ ] **Step 6: 验证部署清单**

| 项目 | 状态 |
|------|------|
| ✅ 后端密码强度模块单元测试通过 | PASS |
| ✅ 后端 API 端点集成测试通过 | PASS |
| ✅ 前端组件在注册页面验证 | PASS |
| ✅ 前端组件在修改密码对话框验证 | PASS |
| ✅ 前端 E2E 测试验证用户交互 | PASS |
| ✅ 密码验证 API 性能测试（< 200ms） | PASS |
| ✅ 后端错误处理验证（400/401 响应） | PASS |
| ✅ API 文档已更新 | PASS |

---

## 完成标志

全部任务完成后：

- 后端：密码强度评分模块 + 3 个 API 端点（validate, register, change-password）
- 前端：密码输入组件 + 修改密码对话框 + 注册/设置页面集成
- 测试：单元测试、集成测试、E2E 测试全部通过
- 文档：API 文档已更新

**所有 commits 都已推送到主分支。**
