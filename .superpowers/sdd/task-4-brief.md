# Task 4: 创建语言切换器组件

## 文件修改

**Files:**
- Create: `frontend/src/components/layout/LanguageSwitcher.vue`

## Interfaces

**Consumes:** 
- `useLanguageStore()` - 访问当前语言和切换方法
- `useI18n()` - 获取 i18n locale 对象
- Element Plus el-dropdown 组件

**Produces:** 
- `<LanguageSwitcher />` 组件，可在 AppHeader 中使用

## 任务描述

创建语言切换的 Vue 组件。这是用户切换语言的入口。

### 完整实现

`frontend/src/components/layout/LanguageSwitcher.vue`：

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

## 实现步骤

1. 创建 `frontend/src/components/layout/LanguageSwitcher.vue`
2. 使用 Element Plus 的 el-dropdown 组件
3. 显示当前语言的标签（中文 / English）
4. 提供两个选项：中文 / English
5. handleSwitch 调用 langStore.setLanguage() 并更新 i18n locale
6. 提交到 git

## 验证方式

```bash
grep -l "LanguageSwitcher" frontend/src/components/layout/LanguageSwitcher.vue
```

## 报告位置

完成后写报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-4-i18n-report.md`
