# 密码强度增强设计文档

**日期：** 2026-06-24  
**方案：** 前后端分离的密码强度验证系统

---

## 需求概述

在 EduBuddy 的注册和修改密码流程中实现**标准级密码强度验证**，提供前端**实时反馈**，提升账户安全性。

### 检查规则（标准级）

密码需满足以下条件：
- 长度 ≥ 8 字符
- 至少包含 1 个大写字母（A-Z）
- 至少包含 1 个小写字母（a-z）
- 至少包含 1 个数字（0-9）
- 至少包含 1 个特殊字符（!@#$%^&*()_+-=[]{}`;:'",./<>?\\|`~）

### 应用场景

1. **注册流程**（POST /api/auth/register）：后端强制验证，拒绝弱密码
2. **修改密码**（POST /api/auth/change-password）：同样强制验证，需验证旧密码
3. **前端实时反馈**：用户输入密码时即时显示强度等级和具体缺陷

---

## 设计方案 B：前后端分离

### 核心思想

- **后端**：提供密码强度评分逻辑和验证 API
- **前端**：调用 API 获取实时反馈，无需重复实现算法
- **优点**：逻辑一致、易维护、支持国际化

---

## 后端设计

### 1. 密码强度评分模块

**文件：** `app/utils/password_validator.py`

```python
import re
from enum import Enum

class PasswordStrength(str, Enum):
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"

class PasswordValidationResult:
    def __init__(self, score: int, strength: PasswordStrength, issues: list[str]):
        self.score = score  # 0-100
        self.strength = strength
        self.issues = issues

def validate_password_strength(password: str) -> PasswordValidationResult:
    """
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
    """快速检查密码是否满足最小要求，返回 (是否有效, 错误消息)"""
    result = validate_password_strength(password)
    if result.issues:
        return False, "; ".join(result.issues)
    return True, ""
```

### 2. API 端点

**文件：** `app/routes/auth.py`（新增/修改）

**新增 Pydantic 模型：**
```python
class PasswordStrengthResponse(BaseModel):
    score: int  # 0-100
    strength: str  # "weak" | "medium" | "strong"
    issues: list[str]

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
```

**新增端点：**

```python
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

**修改现有端点：**

```python
@router.post("/register")
async def register(req: UserRegister, db: Session = Depends(get_db)):
    # [现有逻辑] 检查邮箱唯一性
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(400, "邮箱已存在")
    
    # [新增] 检查密码强度（注册时强制）
    is_valid, error_msg = check_password_validity(req.password)
    if not is_valid:
        raise HTTPException(400, f"密码不符合要求: {error_msg}")
    
    # [现有逻辑] 创建用户、生成令牌
    hashed_pwd = hash_password(req.password)
    user = User(
        email=req.email,
        password=hashed_pwd,
        nickname=req.nickname,
        grade=req.grade,
        role=req.role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_access_token(user.id)
    return {
        'access_token': token,
        'expires_in': 7 * 24 * 3600,
        'user': UserOut.from_orm(user)
    }

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

### 3. 错误处理

- **密码过弱**：返回 400 + 具体缺陷列表
- **旧密码错误**：返回 401（与登录失败保持一致）
- **密码相同**：返回 400

---

## 前端设计

### 1. 密码验证工具函数

**文件：** `src/utils/passwordValidator.ts`

```typescript
export interface PasswordValidationResult {
  score: number  // 0-100
  strength: 'weak' | 'medium' | 'strong'
  issues: string[]
}

export async function validatePasswordStrength(
  password: string
): Promise<PasswordValidationResult> {
  try {
    const response = await api.post('/auth/password/validate', {
      password
    })
    return response
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

### 2. 密码输入组件（实时反馈）

**文件：** `src/components/PasswordInput.vue`

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
```

### 3. 注册表单集成

在现有注册表单中使用 `<PasswordInput />` 组件：

```vue
<template>
  <div class="register-form">
    <el-form :model="form" @submit.prevent="handleRegister">
      <!-- 邮箱 -->
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" type="email" />
      </el-form-item>
      
      <!-- 密码（实时反馈） -->
      <el-form-item label="密码" prop="password">
        <PasswordInput ref="passwordInput" />
      </el-form-item>
      
      <!-- 确认密码 -->
      <el-form-item label="确认密码" prop="confirmPassword">
        <el-input v-model="form.confirmPassword" type="password" />
      </el-form-item>
      
      <!-- 其他字段... -->
      
      <!-- 提交按钮 -->
      <el-button type="primary" :loading="loading" @click="handleRegister">
        注册
      </el-button>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PasswordInput from '@/components/PasswordInput.vue'

const form = ref({
  email: '',
  password: '',
  confirmPassword: ''
})

const passwordInput = ref<InstanceType<typeof PasswordInput>>()
const loading = ref(false)

async function handleRegister() {
  // 检查密码是否符合要求
  if (passwordInput.value!.validation.issues.length > 0) {
    ElMessage.error('密码不符合要求')
    return
  }
  
  if (form.value.password !== form.value.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  
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
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>
```

### 4. 修改密码对话框

**文件：** `src/components/ChangePasswordDialog.vue`

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
  
  loading.value = true
  try {
    await api.post('/auth/change-password', {
      old_password: form.value.oldPassword,
      new_password: form.value.newPassword
    })
    ElMessage.success('密码已修改')
    visible.value = false
    resetForm()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '修改失败')
  } finally {
    loading.value = false
  }
}

defineExpose({
  visible
})
</script>
```

---

## 测试策略

### 后端单元测试

**文件：** `tests/test_password_validator.py`

```python
import pytest
from app.utils.password_validator import validate_password_strength, PasswordStrength

def test_weak_password_too_short():
    result = validate_password_strength("abc")
    assert result.strength == PasswordStrength.WEAK
    assert "长度" in result.issues[0]

def test_weak_password_missing_uppercase():
    result = validate_password_strength("password123!")
    assert result.strength == PasswordStrength.WEAK
    assert any("大写" in issue for issue in result.issues)

def test_strong_password():
    result = validate_password_strength("SecurePass123!")
    assert result.strength == PasswordStrength.STRONG
    assert result.issues == []
    assert result.score >= 60
```

### API 集成测试

```python
def test_password_validate_endpoint():
    response = client.post("/api/auth/password/validate", json={"password": "weak"})
    assert response.status_code == 200
    assert response.json()["strength"] == "weak"

def test_register_weak_password():
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "weak",
        "nickname": "test",
        "grade": "高一",
        "role": "student"
    })
    assert response.status_code == 400
    assert "不符合要求" in response.json()["detail"]
```

### 前端 E2E 测试

```typescript
// Cypress
describe('Password Strength Enhancement', () => {
  it('shows weak password feedback', () => {
    cy.visit('/register')
    cy.get('input[placeholder="请输入密码"]').type('weak')
    cy.contains('弱').should('be.visible')
    cy.contains('密码长度至少8个字符').should('be.visible')
  })
  
  it('shows strong password feedback', () => {
    cy.get('input[placeholder="请输入密码"]').type('SecurePass123!')
    cy.contains('强').should('be.visible')
    cy.contains('密码符合要求').should('be.visible')
  })
  
  it('prevents registration with weak password', () => {
    cy.get('button[type="submit"]').click()
    cy.contains('密码不符合要求').should('be.visible')
  })
})
```

---

## 性能考虑

### 防抖优化

前端密码输入防抖 300ms，避免过于频繁的 API 调用。

### 缓存策略

若有需要，可在前端缓存相同密码的检查结果。

---

## 部署清单

- [ ] 后端密码强度模块单元测试通过
- [ ] 后端 API 端点集成测试通过
- [ ] 前端组件在注册和修改密码页面验证
- [ ] 前端 E2E 测试验证用户交互
- [ ] 密码验证 API 性能测试（响应时间 < 200ms）
- [ ] 后端错误处理验证（400/401 响应）

---

## 后续优化建议

1. **密码历史记录**：防止重复使用最近 5 个密码
2. **密码过期**：强制定期修改密码（如 90 天）
3. **审计日志**：记录修改密码的操作
4. **密码生成建议**：向用户推荐强密码

---

## 文档更新

- 后端 API 文档：新增 `/auth/password/validate` 和 `/auth/change-password` 端点
- 前端组件文档：`PasswordInput` 和 `ChangePasswordDialog` 使用指南
