<template>
  <div id="app">
    <!-- 已登录：显示侧边栏布局 -->
    <template v-if="authStore.isAuthenticated">
      <div class="flex h-screen overflow-hidden">
        <AppSidebar />
        <div class="flex-1 flex flex-col overflow-hidden">
          <AppHeader />
          <main class="flex-1 overflow-y-auto p-6 bg-gray-50">
            <RouterView v-slot="{ Component }">
              <Transition name="fade" mode="out-in">
                <component :is="Component" />
              </Transition>
            </RouterView>
          </main>
        </div>
      </div>
    </template>
    <!-- 未登录：只显示路由内容 -->
    <template v-else>
      <RouterView />
    </template>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'

const authStore = useAuthStore()
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
