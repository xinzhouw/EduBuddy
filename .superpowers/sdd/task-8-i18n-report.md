# Task 8 完成报告：App.vue 初始化语言

## 状态：已完成 ✓

## 修改文件

- `frontend/src/App.vue`

## 变更摘要

### 新增导入

```typescript
import { getCurrentInstance } from 'vue'
import { useLanguageStore } from '@/stores/language'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
```

### 顶层 composable 调用（遵循 Vue 3 规则，必须在 setup 顶层调用）

```typescript
const langStore = useLanguageStore()
const { locale } = useI18n()
```

### onMounted 改为 async，新增语言初始化逻辑

```typescript
onMounted(async () => {
  window.addEventListener('resize', handleResize)

  // 初始化语言
  await langStore.initLanguage()

  // 同步 i18n locale
  locale.value = langStore.currentLanguage

  // 同步 Element Plus locale
  const instance = getCurrentInstance()
  if (instance) {
    const elLocale = langStore.currentLanguage === 'zh' ? zhCn : en
    instance.appContext.app.config.globalProperties.$ELEMENT = { locale: elLocale }
  }

  // ...现有初始化逻辑
})
```

## 实现说明

1. **`useI18n()` 在顶层调用**：Vue 3 Composition API 规则要求 composable 必须在 `setup()` 顶层调用，不能在 `onMounted` 内部调用。

2. **`getCurrentInstance()` 获取 app 引用**：在 `<script setup>` 中没有直接的 `app` 变量，通过 `getCurrentInstance().appContext.app` 访问应用实例来设置 `$ELEMENT` 全局配置。

3. **条件守卫**：`if (instance)` 防止在测试或 SSR 环境中空指针异常。

4. **异步 onMounted**：`initLanguage()` 是异步操作（可能访问后端），所以 `onMounted` 改为 `async`。
