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
  locale.value = newLang  // Immediately update i18n locale to trigger reactive re-render
}
</script>
