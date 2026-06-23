<template>
  <nav class="fixed bottom-0 left-0 right-0 h-20 bg-white border-t border-gray-200 flex items-center justify-around px-2 shadow-lg md:hidden">
    <!-- 移动端主菜单项（最多5个） -->
    <RouterLink
      v-for="item in visibleItems"
      :key="item.path"
      :to="item.path"
      class="flex flex-col items-center justify-center gap-1 py-2 px-3 rounded-lg text-xs font-medium transition-all duration-150 h-full flex-1"
      :class="isActive(item.path) ? 'text-blue-600 bg-blue-50' : 'text-gray-600 hover:bg-gray-100'"
      :title="item.label"
    >
      <span class="text-xl">{{ item.icon }}</span>
      <span class="truncate max-w-[50px]">{{ item.label }}</span>
    </RouterLink>

    <!-- 更多菜单 -->
    <button
      v-if="hiddenItems.length > 0"
      class="flex flex-col items-center justify-center gap-1 py-2 px-3 rounded-lg text-xs font-medium transition-all duration-150 h-full text-gray-600 hover:bg-gray-100"
      @click="showMoreMenu = !showMoreMenu"
      title="更多"
    >
      <span class="text-xl">⋯</span>
      <span>更多</span>
    </button>

    <!-- 菜单弹出层 - 使用 Teleport 脱离父容器的限制 -->
    <Teleport to="body">
      <!-- 背景遮罩 - z-index 最低，且必须放在菜单前面，这样菜单会在上层 -->
      <transition name="fade">
        <div
          v-if="showMoreMenu && hiddenItems.length > 0"
          class="fixed inset-0 z-30 md:hidden"
          @click="showMoreMenu = false"
          style="background-color: rgba(0, 0, 0, 0.3)"
        />
      </transition>

      <!-- 菜单容器 - z-index 最高，确保显示在遮罩之上 -->
      <transition name="fade">
        <div
          v-if="showMoreMenu && hiddenItems.length > 0"
          class="fixed bottom-20 right-2 bg-white rounded-t-2xl border-t border-l border-gray-200 shadow-2xl z-50 w-56 md:hidden"
          style="max-height: 60vh; display: flex; flex-direction: column"
          @click.stop
        >
          <div class="overflow-y-auto flex-1 p-3 space-y-1">
            <RouterLink
              v-for="item in hiddenItems"
              :key="item.path"
              :to="item.path"
              class="block w-full text-left flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 hover:bg-gray-100"
              :class="isActive(item.path) ? 'text-blue-600 bg-blue-50' : 'text-gray-700'"
              @click="showMoreMenu = false"
            >
              <span class="text-lg flex-shrink-0">{{ item.icon }}</span>
              <span class="flex-1">{{ item.label }}</span>
            </RouterLink>
          </div>
        </div>
      </transition>
    </Teleport>
  </nav>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const showMoreMenu = ref(false)

// 菜单项配置（与侧边栏保持一致）
const allMenuItems = computed<{ path: string; icon: string; label: string }[]>(() => {
  const role = authStore.user?.role || 'student'
  const studentItems = [
    { path: '/', icon: '🏠', label: '首页' },
    { path: '/ai', icon: '🤖', label: 'AI' },
    { path: '/notes', icon: '📝', label: '笔记' },
    { path: '/stats', icon: '📊', label: '统计' },
    { path: '/profile', icon: '👤', label: '我的' },
    // 隐藏的菜单项
    { path: '/homework', icon: '✍️', label: 'AI 批改' },
    { path: '/quiz', icon: '📚', label: '练习题' },
    { path: '/wrong-book', icon: '❌', label: '错题本' },
    { path: '/plan', icon: '📅', label: '学习计划' },
    { path: '/docs', icon: '📄', label: '文档' },
    { path: '/reading-buddy', icon: '📖', label: '读书郎' },
  ]
  const observerItems = [
    { path: '/', icon: '🏠', label: '首页' },
    { path: '/monitor', icon: '👁️', label: '学生' },
    { path: '/stats', icon: '📊', label: '统计' },
    { path: '/profile', icon: '👤', label: '我的' },
  ]
  return (role === 'teacher' || role === 'parent') ? observerItems : studentItems
})

// 显示在底部导航的项（前5个）
const visibleItems = computed(() => allMenuItems.value.slice(0, 5))

// 隐藏在更多菜单的项
const hiddenItems = computed(() => allMenuItems.value.slice(5))

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<style scoped>
/* 移动端底部导航固定定位，防止被内容遮挡 */
nav {
  z-index: 40;
}

/* 菜单过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
