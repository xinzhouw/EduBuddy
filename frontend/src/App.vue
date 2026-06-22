<template>
  <div id="app">
    <!-- 已登录：显示响应式布局 -->
    <template v-if="authStore.isAuthenticated">
      <!-- PC 布局（≥768px）：侧边栏 + 顶部栏 -->
      <div v-if="!isMobile" class="flex h-screen overflow-hidden">
        <AppSidebar />
        <div class="flex-1 flex flex-col overflow-hidden">
          <AppHeader />
          <main class="flex-1 overflow-y-auto p-6 bg-gray-50">
            <RouterView :key="route.fullPath" />
          </main>
        </div>
      </div>

      <!-- 移动布局（<768px）：全屏内容 + 底部导航 -->
      <div v-else class="flex flex-col h-screen overflow-hidden">
        <AppHeader />
        <main class="flex-1 overflow-y-auto bg-gray-50 pb-20">
          <RouterView :key="route.fullPath" />
        </main>
        <AppBottomNav />
      </div>
    </template>
    <!-- 未登录：只显示路由内容 -->
    <template v-else>
      <RouterView />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppBottomNav from '@/components/layout/AppBottomNav.vue'

const authStore = useAuthStore()
const route = useRoute()
const windowWidth = ref(window.innerWidth)

const isMobile = computed(() => windowWidth.value < 768)

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
/* 确保页面布局稳定，防止布局偏移 */
#app {
  height: 100vh;
  overflow: hidden;
}
</style>
