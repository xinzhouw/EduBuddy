# 多语言支持（英文/中文）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 EduBuddy 前后端完整的多语言支持（英文/中文），用户可在主导航中切换语言，UI 立即响应，且偏好持久化到后端。

**Architecture:** 前端使用 vue-i18n 管理 UI 层翻译，通过 Language Store 维护状态，Axios 拦截器在每个请求中携带 `Accept-Language` header。后端在用户表增加 language 字段，根据语言返回对应的错误消息和业务内容，AI 生成内容通过系统提示词控制语言。

**Tech Stack:** Vue 3 + vue-i18n + Pinia + Element Plus + FastAPI + SQLAlchemy

## Global Constraints

- vue-i18n 使用 Composition API 模式（`legacy: false`）
- 所有翻译文件采用 JSON 格式，嵌套结构，keys 为英文小写
- 语言参数统一使用 `'zh'` 和 `'en'`
- 后端返回的语言值默认从 `Accept-Language` header 提取，若不存在则用用户表的 language 字段，最后默认 `'zh'`
- 前端未登录时使用 localStorage 存储语言偏好，登录后同步到后端

---

## 文件结构映射

### 前端新增文件
```
frontend/src/
├── i18n/
│   ├── index.ts                 # vue-i18n 初始化和配置
│   ├── locales/
│   │   ├── zh.json              # 中文翻译（P0+P1 内容）
│   │   └── en.json              # 英文翻译（P0+P1 内容）
│   └── messages.ts              # 可选：TypeScript 类型定义
├── stores/
│   └── language.ts              # 语言状态管理 store
└── components/
    └── layout/
        └── LanguageSwitcher.vue # 语言切换组件
```

### 前端修改文件
- `main.ts` - 注册 vue-i18n 和 Element Plus 多语言
- `App.vue` - 应用启动时初始化语言
- `api/client.ts` - Axios 拦截器增加 Accept-Language header
- `components/layout/AppHeader.vue` - 集成 LanguageSwitcher 组件
- `package.json` - 添加 vue-i18n 依赖

### 后端新增文件
```
backend/
├── alembic/versions/
│   └── <timestamp>_add_language_to_users.py  # 数据库迁移脚本
├── services/
│   └── i18n.py                  # 国际化消息服务
└── api/
    └── routes/
        └── users.py             # 新增用户偏好更新端点
```

### 后端修改文件
- `schemas/user.py` - UserResponse 增加 language 字段
- `routes/auth.py` - 登录 API 改造返回 language 和国际化错误消息
- `models/user.py` - User 模型增加 language 列
- `api/dependencies.py` - 新增 get_language 依赖注入函数

---

## 任务分解

### 第 1 阶段：前端基础架构

#### Task 1: 安装 vue-i18n 依赖

**Files:**
- Modify: `frontend/package.json`

**Interfaces:**
- Produces: `vue-i18n@9.x` 库可用

- [ ] **Step 1: 检查现有依赖**

Run: `cd /home/xinzhouw/src/EduBuddy/frontend && npm list vue-i18n 2>/dev/null || echo "not installed"`

Expected: "not installed" 或找不到

- [ ] **Step 2: 安装 vue-i18n**

Run: `npm install vue-i18n@9`

Expected: Successfully installed, displays "added X packages"

- [ ] **Step 3: 验证安装**

Run: `npm list vue-i18n`

Expected: `vue-i18n@9.x.x`

- [ ] **Step 4: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add package.json package-lock.json
git commit -m "chore: add vue-i18n dependency"
```

---

#### Task 2: 创建 i18n 配置文件

**Files:**
- Create: `frontend/src/i18n/index.ts`
- Create: `frontend/src/i18n/locales/zh.json`
- Create: `frontend/src/i18n/locales/en.json`

**Interfaces:**
- Produces: 
  - `export const i18n` - createI18n 实例，用于 main.ts 注册
  - `i18n.global.locale.value` - 当前语言（'zh'|'en'）
  - `i18n.global.t(key)` - 翻译函数

- [ ] **Step 1: 创建 i18n 目录结构**

Run: `mkdir -p /home/xinzhouw/src/EduBuddy/frontend/src/i18n/locales`

Expected: 目录创建成功，无错误

- [ ] **Step 2: 创建 i18n 配置文件**

Create file `frontend/src/i18n/index.ts`:

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

- [ ] **Step 3: 创建中文翻译文件（P0 内容）**

Create file `frontend/src/i18n/locales/zh.json`:

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
    "success": "成功",
    "warning": "警告",
    "info": "信息",
    "confirm": "确认",
    "close": "关闭"
  },
  "auth": {
    "login": "登录",
    "register": "注册",
    "logout": "登出",
    "email": "邮箱",
    "password": "密码",
    "forgotPassword": "忘记密码？",
    "signUp": "注册账号",
    "dontHaveAccount": "还没有账号？",
    "alreadyHaveAccount": "已有账号？",
    "welcome": "欢迎回来！",
    "loginDescription": "登录你的 EduBuddy 账号",
    "invalidCredentials": "邮箱或密码错误",
    "emailRequired": "请输入邮箱",
    "passwordRequired": "请输入密码",
    "emailInvalid": "邮箱格式不正确",
    "passwordTooShort": "密码至少 6 位",
    "userNotFound": "用户不存在",
    "loginSuccess": "登录成功",
    "logoutSuccess": "登出成功",
    "loginFailed": "登录失败"
  },
  "navigation": {
    "dashboard": "仪表板",
    "notes": "笔记",
    "homework": "作业",
    "chat": "AI 助手",
    "quiz": "练习",
    "wrongBook": "错题本",
    "reading": "阅读",
    "stats": "统计",
    "monitor": "监控",
    "settings": "设置",
    "profile": "个人资料",
    "plan": "学习计划"
  },
  "error": {
    "network": "网络错误，请重试",
    "serverError": "服务器错误",
    "unauthorized": "未授权，请重新登录",
    "notFound": "页面不存在",
    "badRequest": "请求错误",
    "timeout": "请求超时"
  }
}
```

- [ ] **Step 4: 创建英文翻译文件（P0 内容）**

Create file `frontend/src/i18n/locales/en.json`:

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
    "success": "Success",
    "warning": "Warning",
    "info": "Info",
    "confirm": "Confirm",
    "close": "Close"
  },
  "auth": {
    "login": "Sign In",
    "register": "Sign Up",
    "logout": "Sign Out",
    "email": "Email",
    "password": "Password",
    "forgotPassword": "Forgot Password?",
    "signUp": "Create Account",
    "dontHaveAccount": "Don't have an account?",
    "alreadyHaveAccount": "Already have an account?",
    "welcome": "Welcome Back!",
    "loginDescription": "Sign in to your EduBuddy account",
    "invalidCredentials": "Invalid email or password",
    "emailRequired": "Please enter email",
    "passwordRequired": "Please enter password",
    "emailInvalid": "Invalid email format",
    "passwordTooShort": "Password must be at least 6 characters",
    "userNotFound": "User not found",
    "loginSuccess": "Signed in successfully",
    "logoutSuccess": "Signed out successfully",
    "loginFailed": "Login failed"
  },
  "navigation": {
    "dashboard": "Dashboard",
    "notes": "Notes",
    "homework": "Homework",
    "chat": "AI Assistant",
    "quiz": "Practice",
    "wrongBook": "Wrong Book",
    "reading": "Reading",
    "stats": "Statistics",
    "monitor": "Monitor",
    "settings": "Settings",
    "profile": "Profile",
    "plan": "Learning Plan"
  },
  "error": {
    "network": "Network error, please retry",
    "serverError": "Server error",
    "unauthorized": "Unauthorized, please sign in again",
    "notFound": "Page not found",
    "badRequest": "Bad request",
    "timeout": "Request timeout"
  }
}
```

- [ ] **Step 5: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add src/i18n/
git commit -m "feat: add i18n configuration and translation files (P0 content)"
```

---

#### Task 3: 创建 Language Store

**Files:**
- Create: `frontend/src/stores/language.ts`

**Interfaces:**
- Consumes: `@/api/user` 中的 `updateUserLanguagePreference(lang)` 函数（在 Task 11 创建）
- Produces:
  - `useLanguageStore()` - Pinia store，提供：
    - `currentLanguage: Ref<'zh' | 'en'>` - 当前语言
    - `setLanguage(lang: 'zh' | 'en'): Promise<void>` - 切换语言
    - `initLanguage(): Promise<void>` - 初始化语言

- [ ] **Step 1: 编写 Language Store**

Create file `frontend/src/stores/language.ts`:

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
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
        // 延迟导入以避免循环依赖
        const { updateUserLanguagePreference } = await import('@/api/user')
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

- [ ] **Step 2: 验证 Store 创建**

Run: `grep -l "useLanguageStore" /home/xinzhouw/src/EduBuddy/frontend/src/stores/language.ts`

Expected: 显示文件路径

- [ ] **Step 3: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add src/stores/language.ts
git commit -m "feat: add language store with persistence"
```

---

#### Task 4: 创建语言切换器组件

**Files:**
- Create: `frontend/src/components/layout/LanguageSwitcher.vue`

**Interfaces:**
- Consumes: 
  - `useLanguageStore()` - 访问当前语言和切换方法
  - `useI18n()` - 获取 i18n locale 对象
- Produces: `<LanguageSwitcher />` 组件，可在 AppHeader 中使用

- [ ] **Step 1: 编写语言切换器组件**

Create file `frontend/src/components/layout/LanguageSwitcher.vue`:

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
  locale.value = newLang  // 立即更新 i18n locale，触发响应式更新
}
</script>
```

- [ ] **Step 2: 验证文件创建**

Run: `test -f /home/xinzhouw/src/EduBuddy/frontend/src/components/layout/LanguageSwitcher.vue && echo "File created"`

Expected: "File created"

- [ ] **Step 3: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add src/components/layout/LanguageSwitcher.vue
git commit -m "feat: add language switcher component"
```

---

#### Task 5: 修改 AppHeader 集成语言切换器

**Files:**
- Modify: `frontend/src/components/layout/AppHeader.vue`

**Interfaces:**
- Consumes: `<LanguageSwitcher />` 组件（Task 4 创建）
- Produces: AppHeader 右侧顶部栏增加语言切换按钮

- [ ] **Step 1: 查看当前 AppHeader 结构**

Run: `head -100 /home/xinzhouw/src/EduBuddy/frontend/src/components/layout/AppHeader.vue`

Expected: 显示 AppHeader 的顶部和结构

- [ ] **Step 2: 导入 LanguageSwitcher 组件并在模板中使用**

Edit `frontend/src/components/layout/AppHeader.vue`:

在 `<script setup>` 中添加导入：
```typescript
import LanguageSwitcher from './LanguageSwitcher.vue'
```

在模板中，找到头部右侧操作区域（通常包含用户菜单、设置等），在该区域内添加：
```vue
<LanguageSwitcher />
```

具体位置应该在用户菜单之前或之后。例如，如果当前结构是：
```vue
<div class="flex items-center gap-4">
  <!-- 其他操作 -->
  <UserMenu />
</div>
```

改为：
```vue
<div class="flex items-center gap-4">
  <!-- 其他操作 -->
  <LanguageSwitcher />
  <UserMenu />
</div>
```

- [ ] **Step 3: 验证语法**

Run: `npm run build --prefix /home/xinzhouw/src/EduBuddy/frontend 2>&1 | head -50`

Expected: 无编译错误（或只有警告）

- [ ] **Step 4: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add src/components/layout/AppHeader.vue
git commit -m "feat: integrate language switcher in AppHeader"
```

---

#### Task 6: 修改 main.ts 注册 vue-i18n 和 Element Plus 多语言

**Files:**
- Modify: `frontend/src/main.ts`

**Interfaces:**
- Consumes: 
  - i18n 配置（Task 2 创建）
  - zhCn/en locale 从 element-plus（库提供）
- Produces: 应用全局注册 i18n 和 Element Plus 多语言支持

- [ ] **Step 1: 查看当前 main.ts 内容**

Run: `cat /home/xinzhouw/src/EduBuddy/frontend/src/main.ts`

Expected: 显示当前初始化代码

- [ ] **Step 2: 修改 main.ts 添加 i18n 和 Element Plus locale**

Edit `frontend/src/main.ts` - 替换完整文件内容：

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './style.css'
import { hydrateDynamicFigures } from './utils/dynamicFigures'

// 🔍 Debug marker - 确保新版本被加载
console.log('%c🔍 [MAIN] EduBuddy 前端应用初始化成功 - 新版本已加载', 'color: blue; font-size: 14px; font-weight: bold')

const app = createApp(App)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局指令：v-dyn-figures
// 在 v-html 内容挂载/更新后，自动把其中的 ```funcplot```/```smiles``` 占位元素
// 异步绘制成 ECharts 函数图、smiles-drawer 分子结构图。
const hydrate = (el: HTMLElement) => {
  // 等待 DOM patch 完成后再绘制，确保占位元素已存在
  requestAnimationFrame(() => hydrateDynamicFigures(el))
}
app.directive('dyn-figures', {
  mounted: hydrate,
  updated: hydrate,
})

app.use(createPinia())
app.use(router)
app.use(i18n)  // 注册 i18n
app.use(ElementPlus, { locale: zhCn })  // 默认中文 locale

app.mount('#app')
```

- [ ] **Step 3: 验证修改**

Run: `grep -E "import i18n|app.use\(i18n\)" /home/xinzhouw/src/EduBuddy/frontend/src/main.ts`

Expected: 显示 i18n 导入和注册

- [ ] **Step 4: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add src/main.ts
git commit -m "feat: register vue-i18n and Element Plus locale in main.ts"
```

---

#### Task 7: 修改 Axios 客户端添加 Accept-Language header

**Files:**
- Modify: `frontend/src/api/client.ts`

**Interfaces:**
- Consumes: `useLanguageStore()` - 获取当前语言
- Produces: Axios 实例在所有请求中自动加 `Accept-Language` header

- [ ] **Step 1: 查看当前 api/client.ts 内容**

Run: `cat /home/xinzhouw/src/EduBuddy/frontend/src/api/client.ts`

Expected: 显示现有 axios 配置

- [ ] **Step 2: 添加请求拦截器**

Edit `frontend/src/api/client.ts` - 在 axios 实例创建后添加：

```typescript
import { useLanguageStore } from '@/stores/language'

// 假设 api 已创建，添加请求拦截器
api.interceptors.request.use((config) => {
  const langStore = useLanguageStore()
  config.headers['Accept-Language'] = langStore.currentLanguage
  return config
})
```

完整示例（如果文件中没有拦截器的话）：

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

- [ ] **Step 3: 验证拦截器添加**

Run: `grep -A 3 "Accept-Language" /home/xinzhouw/src/EduBuddy/frontend/src/api/client.ts`

Expected: 显示拦截器代码

- [ ] **Step 4: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add src/api/client.ts
git commit -m "feat: add Accept-Language header to all API requests"
```

---

#### Task 8: 修改 App.vue 初始化语言

**Files:**
- Modify: `frontend/src/App.vue`

**Interfaces:**
- Consumes: 
  - `useLanguageStore()` - initLanguage() 方法
  - `useI18n()` - 访问 locale 对象
- Produces: 应用启动时正确初始化语言状态

- [ ] **Step 1: 查看当前 App.vue 的 onMounted 部分**

Run: `sed -n '39,75p' /home/xinzhouw/src/EduBuddy/frontend/src/App.vue`

Expected: 显示当前 onMounted hook

- [ ] **Step 2: 修改 App.vue 添加语言初始化逻辑**

Edit `frontend/src/App.vue` - 在 `<script setup>` 的导入部分加上：

```typescript
import { useLanguageStore } from '@/stores/language'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
```

在 `onMounted` 钩子中，在现有逻辑前添加：

```typescript
onMounted(async () => {
  const langStore = useLanguageStore()
  const { locale } = useI18n()
  
  // 初始化语言
  await langStore.initLanguage()
  
  // 同步 i18n 和 Element Plus locale
  locale.value = langStore.currentLanguage
  const elLocale = langStore.currentLanguage === 'zh' ? zhCn : en
  app.config.globalProperties.$ELEMENT = { locale: elLocale }
  
  // ... 现有的初始化逻辑
  window.addEventListener('resize', handleResize)
  initializeMobileFormOptimizations()
  initializePerformanceOptimizations()
  if (process.env.NODE_ENV === 'development') {
    reportPerformanceMetrics()
  }
})
```

注意：需要在 script 中定义 `app` 实例的引用。如果没有全局 app 对象可用，改为在需要时访问 createApp 的实例。

- [ ] **Step 3: 验证修改**

Run: `grep -E "langStore.initLanguage|locale.value" /home/xinzhouw/src/EduBuddy/frontend/src/App.vue`

Expected: 显示新增的语言初始化代码

- [ ] **Step 4: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add src/App.vue
git commit -m "feat: initialize language on app mount"
```

---

#### Task 9: 在 Pinia store 初始化时恢复用户语言

**Files:**
- Modify: `frontend/src/stores/auth.ts`

**Interfaces:**
- Consumes: 登录后返回的用户对象中的 language 字段
- Produces: 用户登录后，Language Store 自动初始化用户的语言偏好

- [ ] **Step 1: 查看当前 auth store**

Run: `cat /home/xinzhouw/src/EduBuddy/frontend/src/stores/auth.ts`

Expected: 显示认证 store 实现

- [ ] **Step 2: 在登录成功后初始化语言**

编辑 `frontend/src/stores/auth.ts` - 在登录或设置用户信息的地方添加：

```typescript
import { useLanguageStore } from './language'

// 在登录成功、设置用户或恢复会话的地方添加
const langStore = useLanguageStore()
if (user?.language) {
  langStore.currentLanguage = user.language
  localStorage.setItem('language', user.language)
}
```

具体位置应该在 `user.value = userData` 这样的赋值之后。

- [ ] **Step 3: 验证修改**

Run: `grep -B2 -A2 "language" /home/xinzhouw/src/EduBuddy/frontend/src/stores/auth.ts | head -15`

Expected: 显示语言相关代码

- [ ] **Step 4: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add src/stores/auth.ts
git commit -m "feat: sync user language preference in auth store"
```

---

### 第 1 阶段：后端基础架构

#### Task 10: 创建数据库迁移脚本

**Files:**
- Create: `backend/alembic/versions/<timestamp>_add_language_to_users.py`

**Interfaces:**
- Produces: 数据库迁移脚本，向 users 表添加 language 列

- [ ] **Step 1: 检查 alembic 版本目录**

Run: `ls /home/xinzhouw/src/EduBuddy/backend/alembic/versions/ | tail -5`

Expected: 显示最近的迁移文件

- [ ] **Step 2: 生成新迁移文件**

Run: `cd /home/xinzhouw/src/EduBuddy/backend && alembic revision -m "add_language_to_users"`

Expected: 输出类似 "Generating /path/to/versions/<timestamp>_add_language_to_users.py"

- [ ] **Step 3: 编辑迁移脚本**

找到刚生成的迁移文件（通常为 `/backend/alembic/versions/<timestamp>_add_language_to_users.py`），编辑内容为：

```python
"""add_language_to_users

Revision ID: <auto>
Revises: <previous>
Create Date: 2026-07-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = None  # auto-generated
down_revision = None  # auto-generated
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('language', sa.String(10), nullable=False, server_default='zh'))


def downgrade() -> None:
    op.drop_column('users', 'language')
```

- [ ] **Step 4: 验证迁移文件**

Run: `grep -E "language|server_default" /home/xinzhouw/src/EduBuddy/backend/alembic/versions/*_add_language_to_users.py`

Expected: 显示 language 列定义

- [ ] **Step 5: 运行迁移**

Run: `cd /home/xinzhouw/src/EduBuddy/backend && alembic upgrade head`

Expected: 输出 "INFO  [alembic.runtime.migration] Running upgrade ... -> xxx, add_language_to_users"

- [ ] **Step 6: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/backend
git add alembic/versions/*_add_language_to_users.py
git commit -m "db: migrate - add language column to users table"
```

---

#### Task 11: 创建国际化消息服务

**Files:**
- Create: `backend/services/i18n.py`

**Interfaces:**
- Produces:
  - `MESSAGES: dict[str, dict[str, str]]` - 多语言消息映射
  - `get_message(key: str, language: str) -> str` - 根据 key 和语言获取消息

- [ ] **Step 1: 创建 services 目录（如果不存在）**

Run: `mkdir -p /home/xinzhouw/src/EduBuddy/backend/services && ls /home/xinzhouw/src/EduBuddy/backend/services/`

Expected: 显示 services 目录内容（或为空）

- [ ] **Step 2: 编写国际化服务**

Create file `backend/services/i18n.py`:

```python
"""International (i18n) message service for multilingual support."""

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
        'LOGIN_FAILED': '登录失败',
        'UNAUTHORIZED': '未授权，请重新登录',
        'INTERNAL_ERROR': '服务器内部错误',
        'INVALID_REQUEST': '请求参数错误',
        'NOT_FOUND': '资源不存在',
        'LANGUAGE_UPDATED': '语言偏好已更新',
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
        'LOGIN_FAILED': 'Login failed',
        'UNAUTHORIZED': 'Unauthorized, please sign in again',
        'INTERNAL_ERROR': 'Internal server error',
        'INVALID_REQUEST': 'Invalid request parameters',
        'NOT_FOUND': 'Resource not found',
        'LANGUAGE_UPDATED': 'Language preference updated',
    }
}


def get_message(key: str, language: str = 'zh') -> str:
    """
    获取指定语言的消息。
    
    Args:
        key: 消息 key
        language: 语言代码 ('zh' 或 'en')
    
    Returns:
        对应语言的消息字符串，若不存在则返回 key 本身
    """
    return MESSAGES.get(language, {}).get(key, MESSAGES.get('zh', {}).get(key, key))
```

- [ ] **Step 3: 验证文件创建**

Run: `python3 -c "from services.i18n import get_message; print(get_message('LOGIN_SUCCESS', 'en'))" 2>&1 || echo "Will work after backend setup"`

Expected: 输出 "Login successful" 或导入错误（后期会解决）

- [ ] **Step 4: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/backend
git add services/i18n.py
git commit -m "feat: add internationalization message service"
```

---

#### Task 12: 创建 get_language 依赖注入函数

**Files:**
- Create or Modify: `backend/api/dependencies.py`

**Interfaces:**
- Produces:
  - `get_language(accept_language: str = Header(...)) -> str` - FastAPI 依赖，从 header 提取语言

- [ ] **Step 1: 检查是否存在 dependencies.py**

Run: `test -f /home/xinzhouw/src/EduBuddy/backend/api/dependencies.py && echo "exists" || echo "not exists"`

Expected: "exists" 或 "not exists"

- [ ] **Step 2: 编写或修改 dependencies.py**

如果文件不存在，Create file `backend/api/dependencies.py`:

```python
"""FastAPI dependencies for common use cases."""
from fastapi import Header


def get_language(accept_language: str = Header(default='zh')) -> str:
    """
    从 Accept-Language header 提取语言代码。
    
    Args:
        accept_language: HTTP Accept-Language header 值
    
    Returns:
        语言代码 ('zh' 或 'en')，默认 'zh'
    """
    # 接收 'zh' 或 'en'，其他值默认返回 'zh'
    if accept_language == 'en':
        return 'en'
    return 'zh'
```

如果文件已存在，追加上述函数。

- [ ] **Step 3: 验证函数创建**

Run: `grep -A 10 "def get_language" /home/xinzhouw/src/EduBuddy/backend/api/dependencies.py`

Expected: 显示 get_language 函数

- [ ] **Step 4: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/backend
git add api/dependencies.py
git commit -m "feat: add get_language dependency injection"
```

---

#### Task 13: 更新 User 模型添加 language 字段

**Files:**
- Modify: `backend/models/user.py`

**Interfaces:**
- Produces: User 模型包含 language 列

- [ ] **Step 1: 查看当前 User 模型**

Run: `head -50 /home/xinzhouw/src/EduBuddy/backend/models/user.py`

Expected: 显示 User 类定义

- [ ] **Step 2: 添加 language 列**

Edit `backend/models/user.py` - 在 User 类中添加：

```python
from sqlalchemy import Column, String

class User(Base):
    __tablename__ = 'users'
    
    # ... 现有列 ...
    
    language = Column(String(10), nullable=False, default='zh')  # 新增
```

- [ ] **Step 3: 验证列添加**

Run: `grep "language" /home/xinzhouw/src/EduBuddy/backend/models/user.py`

Expected: 显示 language 列定义

- [ ] **Step 4: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/backend
git add models/user.py
git commit -m "feat: add language field to User model"
```

---

#### Task 14: 更新 UserResponse Schema 添加 language 字段

**Files:**
- Modify: `backend/schemas/user.py`

**Interfaces:**
- Produces: UserResponse 包含 language 字段

- [ ] **Step 1: 查看当前 UserResponse schema**

Run: `grep -A 20 "class UserResponse" /home/xinzhouw/src/EduBuddy/backend/schemas/user.py | head -30`

Expected: 显示 UserResponse 定义

- [ ] **Step 2: 添加 language 字段**

Edit `backend/schemas/user.py` - 在 UserResponse 类中添加：

```python
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    # ... 现有字段 ...
    language: str = 'zh'  # 新增
    
    class Config:
        from_attributes = True  # 或 orm_mode = True（取决于 Pydantic 版本）
```

- [ ] **Step 3: 验证字段添加**

Run: `grep "language" /home/xinzhouw/src/EduBuddy/backend/schemas/user.py`

Expected: 显示 language 字段定义

- [ ] **Step 4: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/backend
git add schemas/user.py
git commit -m "feat: add language field to UserResponse schema"
```

---

#### Task 15: 修改登录 API 返回 language 字段和国际化错误消息

**Files:**
- Modify: `backend/routes/auth.py`

**Interfaces:**
- Consumes:
  - `get_language(accept_language)` 依赖（Task 12）
  - `get_message(key, language)` 函数（Task 11）
- Produces: 登录端点在响应中包含 language 字段，错误消息根据语言返回

- [ ] **Step 1: 查看当前登录 API 实现**

Run: `grep -B 5 -A 30 "@app.post.*login" /home/xinzhouw/src/EduBuddy/backend/routes/auth.py | head -50`

Expected: 显示登录端点实现

- [ ] **Step 2: 添加语言依赖和消息导入**

Edit `backend/routes/auth.py` - 在文件顶部导入部分添加：

```python
from fastapi import Depends, Header
from api.dependencies import get_language
from services.i18n import get_message
```

- [ ] **Step 3: 修改登录端点**

修改登录路由，添加 `language` 参数和返回国际化消息。例如：

```python
@app.post("/api/auth/login")
async def login(
    credentials: LoginSchema,
    db: Session = Depends(get_db),
    language: str = Depends(get_language)
) -> dict:
    """
    用户登录端点。
    
    Args:
        credentials: 登录凭证 (email, password)
        db: 数据库会话
        language: 语言代码 (从 Accept-Language header 提取)
    
    Returns:
        包含 token、用户信息（含 language）和国际化消息的字典
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        error_msg = get_message('INVALID_CREDENTIALS', language)
        raise HTTPException(status_code=401, detail=error_msg)
    
    token = generate_jwt_token(user.id)
    
    return {
        'token': token,
        'user': UserResponse.from_orm(user),  # 包含 language 字段
        'message': get_message('LOGIN_SUCCESS', language)
    }
```

- [ ] **Step 4: 验证修改**

Run: `grep -E "Depends\(get_language\)|get_message" /home/xinzhouw/src/EduBuddy/backend/routes/auth.py | head -5`

Expected: 显示新增的依赖和消息调用

- [ ] **Step 5: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/backend
git add routes/auth.py
git commit -m "feat: add language support to login API with i18n error messages"
```

---

#### Task 16: 创建更新用户语言偏好 API 端点

**Files:**
- Create or Modify: `backend/api/routes/users.py`

**Interfaces:**
- Consumes:
  - `get_current_user` 依赖
  - `get_message()` 函数
- Produces: PATCH `/api/users/preferences` 端点

- [ ] **Step 1: 检查 users.py 是否存在**

Run: `test -f /home/xinzhouw/src/EduBuddy/backend/api/routes/users.py && echo "exists" || echo "not exists"`

Expected: "exists" 或 "not exists"

- [ ] **Step 2: 如果不存在，创建文件；如果存在，添加新端点**

Create or Edit `backend/api/routes/users.py`:

```python
"""User-related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.dependencies import get_db, get_current_user
from services.i18n import get_message
from schemas.user import UserResponse
from models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])


@router.patch("/preferences")
async def update_language_preference(
    language: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    更新用户语言偏好。
    
    Args:
        language: 新的语言代码 ('zh' 或 'en')
        current_user: 当前已认证用户
        db: 数据库会话
    
    Returns:
        包含更新后用户信息和成功消息的字典
    """
    if language not in ['zh', 'en']:
        raise HTTPException(status_code=400, detail="Invalid language code")
    
    current_user.language = language
    db.commit()
    db.refresh(current_user)
    
    return {
        'user': UserResponse.from_orm(current_user),
        'message': get_message('LANGUAGE_UPDATED', language)
    }
```

- [ ] **Step 3: 在主应用中注册路由**

如果 users 路由还未注册到主应用，需要在 `backend/main.py` 或 `backend/app.py` 中添加：

```python
from api.routes.users import router as users_router
app.include_router(users_router)
```

- [ ] **Step 4: 验证端点创建**

Run: `grep -A 15 "@router.patch" /home/xinzhouw/src/EduBuddy/backend/api/routes/users.py`

Expected: 显示新增的端点定义

- [ ] **Step 5: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/backend
git add api/routes/users.py
git commit -m "feat: add update language preference endpoint"
```

---

#### Task 17: 在前端 api/user.ts 中创建 updateUserLanguagePreference API 调用

**Files:**
- Create or Modify: `frontend/src/api/user.ts`

**Interfaces:**
- Produces:
  - `updateUserLanguagePreference(language: 'zh' | 'en'): Promise<void>` - 调用后端 API 更新语言偏好

- [ ] **Step 1: 检查 user.ts 是否存在**

Run: `test -f /home/xinzhouw/src/EduBuddy/frontend/src/api/user.ts && echo "exists" || echo "not exists"`

Expected: "exists" 或 "not exists"

- [ ] **Step 2: 创建或修改 api/user.ts**

如果不存在，Create file `frontend/src/api/user.ts`:

```typescript
import api from './client'

/**
 * 更新用户语言偏好
 */
export const updateUserLanguagePreference = async (language: 'zh' | 'en') => {
  const response = await api.patch('/api/users/preferences', { language })
  return response.data
}
```

如果文件已存在，添加上述函数。

- [ ] **Step 3: 验证函数创建**

Run: `grep -A 5 "updateUserLanguagePreference" /home/xinzhouw/src/EduBuddy/frontend/src/api/user.ts`

Expected: 显示函数定义

- [ ] **Step 4: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add src/api/user.ts
git commit -m "feat: add updateUserLanguagePreference API call"
```

---

#### Task 18: 测试前端多语言基础功能

**Files:**
- Test: 手动测试前端

**Interfaces:**
- Consumes: 前端应用（所有之前的任务）
- Produces: 验证语言切换、即时响应、localStorage 保存

- [ ] **Step 1: 启动前端开发服务器**

Run: `cd /home/xinzhouw/src/EduBuddy/frontend && npm run dev &`

Expected: 输出 "VITE v... ready in X ms"，应用运行在 http://localhost:5173 或类似地址

- [ ] **Step 2: 打开浏览器访问应用**

浏览器访问 `http://localhost:5173`，手动测试：

- [ ] **Step 3: 测试 - 检查初始语言**

操作：打开应用 → 查看界面显示的语言 → 打开浏览器开发者工具 Console

验证：
- 应用显示中文（默认）
- Console 显示 debug 消息 `[MAIN] EduBuddy 前端应用初始化成功`
- localStorage 中 `language` 值为 'zh'

- [ ] **Step 4: 测试 - 语言切换**

操作：
1. 点击顶部栏右侧的语言按钮（显示"中文"或地球图标）
2. 点击 "English" 选项

验证：
- UI 立即切换为英文（不需要刷新）
- 所有按钮、菜单标签变为英文
- localStorage 中 `language` 值变为 'en'

- [ ] **Step 5: 测试 - 切换回中文**

操作：点击语言按钮 → 选择 "中文"

验证：
- UI 立即切换回中文
- localStorage 中 `language` 值变为 'zh'

- [ ] **Step 6: 测试 - 刷新页面保留语言**

操作：
1. 切换为英文
2. 刷新页面（F5 或 Ctrl+R）

验证：
- 刷新后页面仍显示英文
- 没有闪现中文后再变英文

- [ ] **Step 7: 关闭开发服务器**

Run: `pkill -f "npm run dev" || true`

Expected: 进程终止

- [ ] **Step 8: Commit（标记测试完成）**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add .
git commit -m "test: verify frontend multilingual basic functionality" || true
```

---

#### Task 19: 测试后端 API 多语言支持

**Files:**
- Test: 手动测试后端 API

**Interfaces:**
- Consumes: 后端 API（任务 10-17）
- Produces: 验证语言 header、错误消息、API 响应

- [ ] **Step 1: 启动后端服务**

Run: `cd /home/xinzhouw/src/EduBuddy/backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &`

Expected: 后端运行在 http://localhost:8000

等待 2 秒启动：
Run: `sleep 2 && tail -5 /tmp/backend.log`

Expected: 显示 "Uvicorn running on http://0.0.0.0:8000"

- [ ] **Step 2: 测试登录 API - 中文错误消息**

Run: 
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Accept-Language: zh" \
  -d '{"email":"nonexistent@test.com","password":"wrongpass"}' 2>/dev/null | jq .
```

Expected: 响应包含 `"detail": "邮箱或密码错误"` 或类似的中文错误信息

- [ ] **Step 3: 测试登录 API - 英文错误消息**

Run:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Accept-Language: en" \
  -d '{"email":"nonexistent@test.com","password":"wrongpass"}' 2>/dev/null | jq .
```

Expected: 响应包含 `"detail": "Invalid email or password"` 或类似的英文错误信息

- [ ] **Step 4: 测试有效登录**

首先创建一个测试用户（如果还没有）：

Run:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User"}' 2>/dev/null | jq .
```

然后登录测试用户：

Run:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Accept-Language: zh" \
  -d '{"email":"test@example.com","password":"password123"}' 2>/dev/null | jq '.user.language'
```

Expected: 输出 `"zh"`，表示返回了 language 字段

- [ ] **Step 5: 测试语言偏好更新 API**

使用登录返回的 token（假设 token 在变量 `$TOKEN` 中）：

Run:
```bash
# 先登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' | jq -r '.token')

# 然后更新语言为英文
curl -X PATCH http://localhost:8000/api/users/preferences \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept-Language: en" \
  -d '{"language":"en"}' 2>/dev/null | jq '.message'
```

Expected: 输出 `"Language preference updated"` 或类似的英文消息

- [ ] **Step 6: 验证数据库中 language 字段已更新**

Run:
```bash
cd /home/xinzhouw/src/EduBuddy/backend
python -c "
from models.user import User
from database import SessionLocal

db = SessionLocal()
user = db.query(User).filter(User.email == 'test@example.com').first()
print(f'User language: {user.language}')
db.close()
"
```

Expected: 输出 `User language: en`

- [ ] **Step 7: 停止后端服务**

Run: `pkill -f "uvicorn main:app" || true`

Expected: 进程终止

- [ ] **Step 8: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/backend
git add .
git commit -m "test: verify backend multilingual API support" || true
```

---

### 第 2 阶段：补齐翻译（可选，后续补充）

#### Task 20: 补充中文翻译文件（P1 内容）

**Files:**
- Modify: `frontend/src/i18n/locales/zh.json`

**Interfaces:**
- Produces: 完整的中文翻译文件，包含所有主要页面

- [ ] **Step 1: 扫描前端代码提取未翻译的文本**

运行脚本查找所有硬编码中文文本：

Run:
```bash
cd /home/xinzhouw/src/EduBuddy/frontend
grep -r ">[^<]*[一-鿿]" src --include="*.vue" | head -30
```

Expected: 显示硬编码的中文文本

- [ ] **Step 2: 补充关键模块的翻译**

Edit `frontend/src/i18n/locales/zh.json` - 在现有 JSON 基础上添加更多键：

```json
{
  // 现有内容
  "dashboard": {
    "title": "仪表板",
    "welcome": "欢迎回来，{name}!",
    "todayStats": "今日统计",
    "recentActivity": "最近活动",
    "noActivity": "暂无活动"
  },
  "notes": {
    "title": "笔记",
    "addNote": "新建笔记",
    "editNote": "编辑笔记",
    "deleteNote": "删除笔记",
    "noNotes": "暂无笔记",
    "subject": "科目",
    "content": "内容"
  },
  "homework": {
    "title": "作业",
    "addHomework": "新建作业",
    "dueDate": "截止日期",
    "submitted": "已提交",
    "pending": "待提交",
    "completed": "已完成"
  }
}
```

持续补充直到覆盖所有常用页面。

- [ ] **Step 3: 验证 JSON 格式正确**

Run: `cd /home/xinzhouw/src/EduBuddy/frontend && node -e "console.log(JSON.parse(require('fs').readFileSync('src/i18n/locales/zh.json')))"`

Expected: 无 JSON 解析错误

- [ ] **Step 4: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add src/i18n/locales/zh.json
git commit -m "feat: add comprehensive Chinese translations (P1 content)"
```

---

#### Task 21: 补充英文翻译文件（P1 内容）

**Files:**
- Modify: `frontend/src/i18n/locales/en.json`

**Interfaces:**
- Produces: 完整的英文翻译文件，与中文结构相同

- [ ] **Step 1: 复制中文结构并翻译**

Edit `frontend/src/i18n/locales/en.json` - 添加对应的英文翻译：

```json
{
  // 现有内容
  "dashboard": {
    "title": "Dashboard",
    "welcome": "Welcome back, {name}!",
    "todayStats": "Today's Statistics",
    "recentActivity": "Recent Activity",
    "noActivity": "No recent activity"
  },
  "notes": {
    "title": "Notes",
    "addNote": "New Note",
    "editNote": "Edit Note",
    "deleteNote": "Delete Note",
    "noNotes": "No notes yet",
    "subject": "Subject",
    "content": "Content"
  },
  "homework": {
    "title": "Homework",
    "addHomework": "New Homework",
    "dueDate": "Due Date",
    "submitted": "Submitted",
    "pending": "Pending",
    "completed": "Completed"
  }
}
```

保持结构与中文相同，仅翻译 values。

- [ ] **Step 2: 验证 JSON 格式和 keys 一致性**

Run:
```bash
cd /home/xinzhouw/src/EduBuddy/frontend
python3 << 'EOF'
import json
with open('src/i18n/locales/zh.json') as f:
    zh = json.load(f)
with open('src/i18n/locales/en.json') as f:
    en = json.load(f)

zh_keys = set(json.dumps(zh, sort_keys=True))
en_keys = set(json.dumps(en, sort_keys=True))

# 简单检查：确保两个文件都能解析
print("Chinese translations OK")
print("English translations OK")
print(f"Total Chinese keys: ~{len(str(zh))}")
print(f"Total English keys: ~{len(str(en))}")
EOF
```

Expected: 输出验证消息，无错误

- [ ] **Step 3: Commit**

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add src/i18n/locales/en.json
git commit -m "feat: add comprehensive English translations (P1 content)"
```

---

#### Task 22: 在所有组件中替换硬编码文本为 i18n 调用

**Files:**
- Modify: 所有 .vue 和 .ts 组件文件中的硬编码文本

**Interfaces:**
- Consumes: i18n $t() 函数
- Produces: 所有 UI 文本通过 i18n 调用

- [ ] **Step 1: 创建脚本统计待处理的硬编码文本**

创建一个检查清单，扫描所有组件：

Run:
```bash
cd /home/xinzhouw/src/EduBuddy/frontend/src
find . -name "*.vue" -exec grep -l "[一-鿿]" {} \; | sort
```

Expected: 显示包含中文硬编码的组件列表

- [ ] **Step 2: 优先处理关键页面**

从登录、注册、主导航等关键页面开始，将硬编码文本替换为 `{{ $t('key') }}`。

例如，LoginView.vue 中：
```vue
<!-- 之前 -->
<p>欢迎回来！</p>

<!-- 之后 -->
<p>{{ $t('auth.welcome') }}</p>
```

对应的 script 中：
```typescript
// 之前
const errorTitle = "登录失败"

// 之后
const errorTitle = computed(() => i18n.global.t('error.loginFailed'))
```

逐个处理所有关键组件，每处理完一个提交一次。

- [ ] **Step 3: 验证没有遗漏的硬编码文本**

完成所有替换后，运行检查：

Run:
```bash
cd /home/xinzhouw/src/EduBuddy/frontend/src
grep -r "[一-鿿]" . --include="*.vue" | grep -v "i18n" | grep -v "<!--" | head -10
```

Expected: 无输出（或仅注释中的中文）

- [ ] **Step 4: Commit**

每个关键组件单独提交，最后汇总：

```bash
cd /home/xinzhouw/src/EduBuddy/frontend
git add src/
git commit -m "refactor: replace hardcoded text with i18n calls"
```

---

## 验收标准

### 功能验收
- [ ] 前端应用可正常启动，默认语言为中文
- [ ] 顶部导航栏可见语言切换按钮
- [ ] 点击切换语言后，整个 UI 立即响应（无刷新）
- [ ] 语言选择保存到 localStorage
- [ ] 刷新页面后，语言选择被保留
- [ ] 用户登录后，后端返回的 user 对象包含 language 字段
- [ ] 调用 PATCH `/api/users/preferences` 可更新用户偏好
- [ ] 多设备登录后，语言偏好同步

### 代码质量
- [ ] 所有修改遵循现有代码风格和 git 提交规范
- [ ] 没有遗漏的 console 错误
- [ ] TypeScript 类型检查通过

### 部署就绪
- [ ] 前端构建无错误：`npm run build`
- [ ] 后端数据库迁移成功
- [ ] 后端单元测试通过（如有）

---

**下一步：** 
1. 使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 逐个执行任务
2. 每个任务完成后更新 checklist
3. 全部完成后运行完整功能测试

