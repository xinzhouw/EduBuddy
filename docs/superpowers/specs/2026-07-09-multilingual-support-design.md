# 多语言支持设计文档

**日期**: 2026-07-09  
**项目**: EduBuddy 前端国际化  
**范围**: 英文/中文界面支持与语言切换  

---

## 1. 需求概述

### 功能需求
1. **用户界面国际化**：支持中文和英文两种语言
2. **语言切换功能**：用户可在主导航中快速切换语言
3. **全内容翻译**：包括 UI 文本、系统提示、AI 生成内容等
4. **多设备同步**：用户偏好持久化到后端，多设备保持一致

### 非功能需求
- **即时响应**：切换语言时无需刷新页面，UI 立即响应
- **可扩展性**：架构支持后续添加更多语言（日文、西班牙文等）
- **性能无损**：不增加页面加载时间

---

## 2. 设计方案：混合方案

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     前端应用（Vue 3）                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  vue-i18n 管理静态 UI 文本翻译                             │
│  ├─ zh.json / en.json （~200-300 keys）                  │
│  ├─ $t() 函数自动响应当前语言                              │
│  └─ 组件级即时重新渲染                                    │
│                                                           │
│  Language Store (Pinia)                                  │
│  ├─ currentLanguage: 'zh' | 'en'                         │
│  ├─ setLanguage()：更新状态 + localStorage + API         │
│  └─ initLanguage()：启动时从后端或本地恢复               │
│                                                           │
│  LanguageSwitcher 组件                                   │
│  └─ AppHeader 中的下拉菜单                                │
│                                                           │
│  Axios 拦截器                                            │
│  └─ 所有请求自动加 Accept-Language header                │
│                                                           │
└────────────┬──────────────────────────────────────────┘
             │ Accept-Language: zh / en
             ↓
┌─────────────────────────────────────────────────────────┐
│                  后端 API (FastAPI)                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  中间件：从 Header 提取语言 → Depends(get_language)       │
│                                                           │
│  路由返回值按语言适配：                                   │
│  ├─ 错误消息：国际化模板                                  │
│  ├─ 系统消息：国际化模板                                  │
│  ├─ AI 生成内容：LLM 系统提示词控制                       │
│  └─ 用户生成内容：保持原样                                │
│                                                           │
│  用户表新增 language 字段                                 │
│  └─ 登录时返回用户偏好语言                                │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 工作流程

#### 初始化流程
```
应用启动
  ↓
App.vue onMounted
  ↓
languageStore.initLanguage()
  ├─ 如果已登录：从后端用户偏好读取
  ├─ 如果未登录：从 localStorage 读取
  └─ 如果都没有：默认 'zh'
  ↓
i18n.locale = currentLanguage
  ↓
Element Plus locale 更新
  ↓
UI 渲染完成（应用对应语言）
```

#### 切换语言流程
```
用户点击 LanguageSwitcher 下拉菜单
  ↓
handleSwitch(newLang)
  ↓
languageStore.setLanguage(newLang)
  ├─ currentLanguage.value = newLang
  ├─ localStorage.setItem('language', newLang)
  ├─ API: PATCH /api/users/preferences { language: newLang }
  └─ 后端保存到 users.language
  ↓
i18n.locale.value = newLang （触发响应式更新）
  ↓
Element Plus locale 更新
  ↓
所有组件的 $t() 调用返回新语言文本
  ↓
UI 立即重新渲染（整个页面切换语言）
  ↓
后续 API 调用自动使用新语言
  ├─ Header: Accept-Language: newLang
  ├─ 返回内容按新语言
  └─ 已加载内容保持原语言（用户可手动刷新加载新语言版本）
```

---

## 3. 前端实现细节

### 3.1 文件结构

```
frontend/src/
├── i18n/
│   ├── index.ts                 # vue-i18n 初始化
│   ├── locales/
│   │   ├── zh.json              # 中文翻译 (~200-300 keys)
│   │   └── en.json              # 英文翻译（同结构）
│   └── messages.ts              # 可选：TypeScript 类型定义
├── stores/
│   ├── language.ts              # 新增：语言状态管理
│   └── auth.ts                  # 修改：登录时初始化语言
├── api/
│   ├── client.ts                # 修改：Axios 拦截器
│   └── user.ts                  # 修改：新增 updateLanguagePreference API
├── components/
│   ├── layout/
│   │   ├── AppHeader.vue        # 修改：集成 LanguageSwitcher
│   │   └── LanguageSwitcher.vue # 新增：语言切换组件
│   └── ...
├── App.vue                       # 修改：初始化语言
├── main.ts                       # 修改：注册 vue-i18n 和 Element Plus 多语言
└── ...
```

### 3.2 核心代码

#### `i18n/index.ts` - vue-i18n 配置
```typescript
import { createI18n } from 'vue-i18n'
import zh from './locales/zh.json'
import en from './locales/en.json'

export const i18n = createI18n({
  legacy: false,  // Composition API 模式
  locale: 'zh',   // 默认语言
  fallbackLocale: 'zh',
  messages: {
    zh,
    en
  }
})

export default i18n
```

#### `stores/language.ts` - 语言状态管理
```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { updateUserLanguagePreference } from '@/api/user'
import { useAuthStore } from './auth'

export const useLanguageStore = defineStore('language', () => {
  const currentLanguage = ref<'zh' | 'en'>('zh')

  /**
   * 设置语言：更新状态、本地存储、后端偏好
   */
  const setLanguage = async (lang: 'zh' | 'en') => {
    currentLanguage.value = lang
    localStorage.setItem('language', lang)
    
    // 如果已登录，同步到后端
    const authStore = useAuthStore()
    if (authStore.isAuthenticated) {
      try {
        await updateUserLanguagePreference(lang)
      } catch (error) {
        console.error('Failed to update language preference:', error)
        // 失败时仍保持前端切换，下次登录会同步
      }
    }
  }

  /**
   * 初始化语言：从后端或本地恢复
   */
  const initLanguage = async () => {
    const authStore = useAuthStore()
    
    if (authStore.isAuthenticated && authStore.user) {
      // 已登录：使用后端用户偏好
      const userLang = authStore.user.language || 'zh'
      currentLanguage.value = userLang as 'zh' | 'en'
    } else {
      // 未登录：从 localStorage 读取
      const saved = localStorage.getItem('language') as 'zh' | 'en' | null
      currentLanguage.value = saved || 'zh'
    }
  }

  return {
    currentLanguage,
    setLanguage,
    initLanguage
  }
})
```

#### `components/LanguageSwitcher.vue` - 语言切换组件
```vue
<template>
  <el-dropdown @command="handleSwitch" trigger="click">
    <span class="flex items-center gap-1 cursor-pointer px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors">
      <span class="text-lg">🌐</span>
      <span class="text-sm font-medium">{{ languageLabel }}</span>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="zh" :disabled="langStore.currentLanguage === 'zh'">
          <span>🇨🇳 中文</span>
        </el-dropdown-item>
        <el-dropdown-item command="en" :disabled="langStore.currentLanguage === 'en'">
          <span>🇺🇸 English</span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useLanguageStore } from '@/stores/language'
import { useI18n } from 'vue-i18n'

const langStore = useLanguageStore()
const { locale } = useI18n()

const languageLabel = computed(() => {
  return langStore.currentLanguage === 'zh' ? '中文' : 'English'
})

const handleSwitch = async (newLang: 'zh' | 'en') => {
  await langStore.setLanguage(newLang)
  locale.value = newLang  // 立即更新 i18n，触发 UI 响应式更新
}
</script>
```

#### `api/client.ts` - Axios 拦截器增加 Accept-Language
```typescript
import axios from 'axios'
import { useLanguageStore } from '@/stores/language'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000
})

// 请求拦截器：自动加入 Accept-Language header
api.interceptors.request.use((config) => {
  const langStore = useLanguageStore()
  config.headers['Accept-Language'] = langStore.currentLanguage
  return config
})

export default api
```

#### `main.ts` - 注册 vue-i18n 和 Element Plus 多语言
```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './style.css'

const app = createApp(App)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(i18n)  // 注册 vue-i18n
app.use(ElementPlus, { locale: zhCn })  // 默认中文

app.mount('#app')
```

#### `App.vue` - 初始化语言
```typescript
import { onMounted } from 'vue'
import { useLanguageStore } from '@/stores/language'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'

onMounted(async () => {
  const langStore = useLanguageStore()
  const { locale } = useI18n()
  
  // 初始化语言
  await langStore.initLanguage()
  
  // 同步 i18n 和 Element Plus
  locale.value = langStore.currentLanguage
  const elLocale = langStore.currentLanguage === 'zh' ? zhCn : en
  app.config.globalProperties.$ELEMENT = { locale: elLocale }
  
  // ... 其他初始化逻辑
})
```

#### `components/layout/AppHeader.vue` - 集成语言切换器
```vue
<!-- 在头部右侧添加 LanguageSwitcher -->
<template>
  <header class="flex items-center justify-between px-6 py-4 bg-white border-b">
    <div><!-- Logo/Title --></div>
    <div class="flex items-center gap-4">
      <!-- 其他操作按钮 -->
      <LanguageSwitcher />  <!-- 新增语言切换组件 -->
    </div>
  </header>
</template>

<script setup>
import LanguageSwitcher from './LanguageSwitcher.vue'
</script>
```

### 3.3 翻译文件结构

**`locales/zh.json`** - 中文翻译（样例）
```json
{
  "common": {
    "yes": "是",
    "no": "否",
    "ok": "确定",
    "cancel": "取消",
    "save": "保存",
    "delete": "删除",
    "edit": "编辑",
    "back": "返回",
    "loading": "加载中...",
    "error": "错误",
    "success": "成功"
  },
  "auth": {
    "login": "登录",
    "register": "注册",
    "logout": "登出",
    "email": "邮箱",
    "password": "密码",
    "forgotPassword": "忘记密码？",
    "invalidCredentials": "邮箱或密码错误",
    "emailRequired": "请输入邮箱",
    "passwordRequired": "请输入密码"
  },
  "dashboard": {
    "title": "仪表板",
    "welcome": "欢迎回来，{name}!",
    "todayStats": "今日统计"
  },
  "notes": {
    "title": "笔记",
    "addNote": "新建笔记",
    "editNote": "编辑笔记",
    "deleteNote": "删除笔记",
    "noNotes": "暂无笔记"
  },
  "error": {
    "network": "网络错误，请重试",
    "serverError": "服务器错误",
    "unauthorized": "未授权，请重新登录"
  }
}
```

**`locales/en.json`** - 英文翻译（同结构）
```json
{
  "common": {
    "yes": "Yes",
    "no": "No",
    "ok": "OK",
    "cancel": "Cancel",
    "save": "Save",
    "delete": "Delete",
    "edit": "Edit",
    "back": "Back",
    "loading": "Loading...",
    "error": "Error",
    "success": "Success"
  },
  "auth": {
    "login": "Sign In",
    "register": "Sign Up",
    "logout": "Sign Out",
    "email": "Email",
    "password": "Password",
    "forgotPassword": "Forgot Password?",
    "invalidCredentials": "Invalid email or password",
    "emailRequired": "Please enter email",
    "passwordRequired": "Please enter password"
  },
  "dashboard": {
    "title": "Dashboard",
    "welcome": "Welcome back, {name}!",
    "todayStats": "Today's Statistics"
  },
  "notes": {
    "title": "Notes",
    "addNote": "New Note",
    "editNote": "Edit Note",
    "deleteNote": "Delete Note",
    "noNotes": "No notes yet"
  },
  "error": {
    "network": "Network error, please retry",
    "serverError": "Server error",
    "unauthorized": "Unauthorized, please sign in again"
  }
}
```

---

## 4. 后端实现细节

### 4.1 数据库迁移

```sql
-- 添加 language 字段到 users 表
ALTER TABLE users ADD COLUMN language VARCHAR(10) DEFAULT 'zh';
```

对应的 SQLAlchemy 迁移文件：
```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users', sa.Column('language', sa.String(10), nullable=False, server_default='zh'))

def downgrade():
    op.drop_column('users', 'language')
```

### 4.2 Pydantic Schema 更新

```python
# schemas/user.py
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    language: str = 'zh'  # 新增字段
    
    class Config:
        from_attributes = True
```

### 4.3 国际化消息服务

```python
# services/i18n.py
MESSAGES = {
    'zh': {
        'INVALID_CREDENTIALS': '邮箱或密码错误',
        'EMAIL_NOT_FOUND': '邮箱不存在',
        'USER_ALREADY_EXISTS': '该邮箱已注册',
        'EMAIL_NOT_VERIFIED': '邮箱未验证',
        'PASSWORD_RESET_SENT': '重置密码邮件已发送',
        'PASSWORD_RESET_SUCCESS': '密码已重置',
        'LOGIN_SUCCESS': '登录成功',
        'LOGOUT_SUCCESS': '登出成功',
    },
    'en': {
        'INVALID_CREDENTIALS': 'Invalid email or password',
        'EMAIL_NOT_FOUND': 'Email not found',
        'USER_ALREADY_EXISTS': 'Email already registered',
        'EMAIL_NOT_VERIFIED': 'Email not verified',
        'PASSWORD_RESET_SENT': 'Password reset email sent',
        'PASSWORD_RESET_SUCCESS': 'Password reset successfully',
        'LOGIN_SUCCESS': 'Login successful',
        'LOGOUT_SUCCESS': 'Logged out successfully',
    }
}

def get_message(key: str, language: str = 'zh') -> str:
    return MESSAGES.get(language, {}).get(key, MESSAGES['zh'].get(key, key))
```

### 4.4 依赖注入与路由改造

```python
# routes/auth.py
from fastapi import Depends, Header

def get_language(accept_language: str = Header(default='zh')) -> str:
    """从 Header 提取语言，默认中文"""
    return 'en' if accept_language == 'en' else 'zh'

@app.post("/api/auth/login")
async def login(
    credentials: LoginSchema,
    language: str = Depends(get_language)
) -> LoginResponse:
    """
    语言参数由 Depends(get_language) 自动从 Header 提取
    """
    user = authenticate_user(credentials.email, credentials.password)
    
    if not user:
        error_msg = get_message('INVALID_CREDENTIALS', language)
        raise HTTPException(
            status_code=401,
            detail=error_msg
        )
    
    # 登录成功，返回用户信息（包含 language 偏好）
    return LoginResponse(
        token=generate_token(user),
        user=UserResponse.from_orm(user),
        message=get_message('LOGIN_SUCCESS', language)
    )

@app.get("/api/users/me")
async def get_current_user(
    current_user: User = Depends(get_current_user),
    language: str = Depends(get_language)
) -> UserResponse:
    """返回当前用户信息"""
    return UserResponse.from_orm(current_user)

@app.patch("/api/users/preferences")
async def update_language_preference(
    language: str,
    current_user: User = Depends(get_current_user)
):
    """更新用户语言偏好"""
    current_user.language = language
    db.commit()
    return {"message": "Language preference updated"}
```

### 4.5 AI 生成内容的语言控制

```python
# services/ai.py
def generate_solution(problem_id: str, language: str = 'zh') -> str:
    """根据语言生成解题步骤"""
    
    # 根据语言选择系统提示词
    system_prompts = {
        'zh': """你是一个数学老师。请用简洁清晰的中文步骤解答这道题。
                 如果有数学公式或代码，保持它们不变。
                 只翻译解释性的文字。""",
        'en': """You are a math teacher. Please solve this problem with clear 
                 and concise English steps. If there are mathematical formulas 
                 or code, keep them unchanged. Only translate explanatory text."""
    }
    
    system_prompt = system_prompts.get(language, system_prompts['zh'])
    
    # 调用 LLM（OpenAI、Claude 等）
    response = call_llm(
        system_prompt=system_prompt,
        user_message=f"Please solve problem {problem_id}",
        temperature=0.7,
        max_tokens=2000
    )
    
    return response

@app.post("/api/ai/solve")
async def solve_problem(
    problem_id: str,
    language: str = Depends(get_language)
) -> dict:
    """调用 AI 生成解题步骤"""
    solution = generate_solution(problem_id, language)
    return {"solution": solution}
```

---

## 5. 实现优先级与迁移策略

### 5.1 分阶段实现

#### 阶段 1：基础架构搭建（第 1 周）
- [ ] 安装 `vue-i18n` 依赖
- [ ] 创建 Language Store
- [ ] 建立 `i18n/locales/` 目录和配置
- [ ] 创建 LanguageSwitcher 组件
- [ ] 修改 AppHeader 集成语言切换器
- [ ] 修改 Axios 拦截器
- [ ] 修改 main.ts 注册 vue-i18n
- [ ] 提取关键页面的硬编码文本创建翻译文件
- [ ] 后端：添加 language 字段到 users 表
- [ ] 后端：创建国际化消息服务
- [ ] 后端：改造登录/登出/验证等核心 API

**输出**：框架完成，关键流程（登录/注册）可切换语言

#### 阶段 2：完整翻译（第 2-3 周）
- [ ] 逐个页面补齐英文翻译
- [ ] AI 相关 API 整合语言参数
- [ ] 后端生成内容按语言返回
- [ ] 完整测试和优化

**输出**：全功能多语言支持

### 5.2 翻译优先级（关键路径优先）

| 优先级 | 页面/模块 | 预计文本数 | 预期完成时间 |
|--------|---------|---------|-----------|
| 🔴 **P0** | 登录/注册/忘记密码 | ~30 | 第 1 天 |
| 🔴 **P0** | 主导航、头部、底部 | ~40 | 第 1 天 |
| 🟠 **P1** | 仪表板、笔记、作业 | ~100 | 第 2-3 天 |
| 🟠 **P1** | AI 聊天、解题界面 | ~50 | 第 2 天 |
| 🟡 **P2** | 设置、个人资料、其他 | ~60 | 第 3 天 |

### 5.3 翻译提取工具

为了加快翻译文件的生成，建议创建一个简单脚本来辅助提取硬编码文本：

```bash
# 使用 grep 找出所有可能的硬编码中文文本
grep -r ">[^<]*[一-鿿]" frontend/src --include="*.vue" --include="*.ts"

# 手动逐一提取并转换为 i18n key
# 例如：<p>欢迎回来</p> → {{ $t('auth.welcome') }}
```

---

## 6. 测试与验证策略

### 6.1 单元测试

```typescript
// stores/__tests__/language.spec.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useLanguageStore } from '../language'

describe('Language Store', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('should initialize with default language', () => {
    const store = useLanguageStore()
    expect(store.currentLanguage).toBe('zh')
  })

  it('should switch language and update localStorage', async () => {
    const store = useLanguageStore()
    await store.setLanguage('en')
    expect(store.currentLanguage).toBe('en')
    expect(localStorage.getItem('language')).toBe('en')
  })
})
```

### 6.2 集成测试 - 关键场景

| 场景 | 验证方法 | 预期结果 |
|------|---------|---------|
| **初始化** | 打开应用 → 查看初始语言 | 显示用户偏好的语言（或默认中文） |
| **即时切换** | 点击语言按钮 → 切换为英文 | 整个 UI 立即变为英文，无刷新 |
| **多设备同步** | 设备 A 选英文 → 设备 B 登录同账号 | 设备 B 默认显示英文 |
| **刷新保留** | 切换为英文 → 刷新页面 | 刷新后仍显示英文 |
| **未登录场景** | 未登录时切换 → 登录 | 登录后保持之前选择的语言 |
| **API 响应** | 切换英文 → 加载新数据 | 返回的系统文本为英文 |
| **AI 回复** | 切换英文 → 提问 AI | AI 回复为英文 |
| **Element Plus** | 切换语言 → 检查分页/日期选择器 | 组件内置文本切换为对应语言 |

### 6.3 手动测试清单

```
□ 登录页面
  □ 中文显示正常
  □ 切换到英文后，所有文本变为英文
  □ 切换回中文，所有文本变回中文
  
□ 主页面（已登录）
  □ 语言切换按钮在顶部栏可见
  □ 点击切换后，页面立即响应（无刷新）
  □ 顶部导航、侧边栏、所有按钮都变为新语言
  
□ API 集成
  □ 登录后，用户偏好的语言被保存
  □ 切换语言后，后续 API 请求自动发送 Accept-Language header
  □ 返回的内容按请求语言返回
  
□ AI 功能
  □ 切换语言 → 提问 AI
  □ 验证 AI 回复是当前选择的语言
  
□ 浏览器刷新
  □ 切换语言 → 刷新页面（Ctrl+R）
  □ 页面刷新后，语言选择被保留
  
□ 跨设备
  □ 设备 A：登录 → 选英文
  □ 设备 B：用同账号登录
  □ 验证设备 B 默认显示英文
```

---

## 7. 技术栈与依赖

### 前端依赖
- `vue-i18n@^9.x` - 国际化框架
- `element-plus@^2.14.0` - 已安装，内置多语言支持
- `vue@^3.5.x` - 已安装
- `pinia@^3.0.x` - 已安装

### 后端依赖
- `fastapi` - 已安装
- `sqlalchemy` - 已安装
- 国际化消息服务由后端代码内实现（无额外依赖）

---

## 8. 风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 翻译文件过大 | 页面加载变慢 | 分离翻译文件按模块加载（后期优化） |
| 硬编码文本遗漏 | 某些 UI 仍显示中文 | 建立检查清单，逐页面验证 |
| AI 内容翻译质量 | 用户体验差 | LLM 系统提示词反复调试，测试各类题型 |
| 后端改造复杂 | 时间超期 | 优先改造核心 API，其他 API 可后续迭代 |

---

## 9. 后续优化（非本期范围）

- 使用翻译自动化工具加速翻译过程
- 支持更多语言（日文、西班牙文等）
- 按模块分离翻译文件以优化加载性能
- 集成翻译 CDN 支持（如果翻译量继续增长）
- AI 翻译质量监控与反馈机制

---

## 10. 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| i18n | Internationalization（国际化），支持多语言的缩写 |
| locale | 区域设置，如 `zh` 表示中文，`en` 表示英文 |
| 硬编码文本 | 直接写在代码中的文本（而非翻译文件中的文本） |
| vue-i18n | Vue.js 官方国际化插件 |

### B. 相关文件路径速查

| 文件 | 用途 |
|------|------|
| `src/i18n/index.ts` | i18n 初始化 |
| `src/i18n/locales/zh.json` | 中文翻译 |
| `src/i18n/locales/en.json` | 英文翻译 |
| `src/stores/language.ts` | 语言状态管理 |
| `src/components/LanguageSwitcher.vue` | 语言切换器 |
| `src/api/client.ts` | Axios 配置 |
| `src/main.ts` | 应用入口 |

---

**设计审核完成** ✅  
**准备就绪，可进入实现阶段**
