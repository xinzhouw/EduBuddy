<template>
  <nav class="fixed bottom-0 left-0 right-0 h-20 bg-white border-t border-gray-200 flex items-center justify-around px-2 shadow-lg md:hidden">
    <!-- Mobile main menu items (max 5) -->
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

    <!-- More menu -->
    <button
      v-if="hiddenItems.length > 0"
      class="flex flex-col items-center justify-center gap-1 py-2 px-3 rounded-lg text-xs font-medium transition-all duration-150 h-full text-gray-600 hover:bg-gray-100"
      @click="showMoreMenu = !showMoreMenu"
      :title="$t('common.more')"
    >
      <span class="text-xl">⋯</span>
      <span>{{ $t('common.more') }}</span>
    </button>

    <!-- Menu popup layer - Teleport escapes parent container constraints -->
    <Teleport to="body">
      <!-- Background mask - lowest z-index, must come before menu -->
      <transition name="fade">
        <div
          v-if="showMoreMenu && hiddenItems.length > 0"
          class="fixed inset-0 z-30 md:hidden"
          @click="showMoreMenu = false"
          style="background-color: rgba(0, 0, 0, 0.3)"
        />
      </transition>

      <!-- Menu container - highest z-index, displayed above mask -->
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
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const route = useRoute()
const authStore = useAuthStore()
const showMoreMenu = ref(false)

// Menu item configuration (consistent with sidebar)
const allMenuItems = computed<{ path: string; icon: string; label: string }[]>(() => {
  const role = authStore.user?.role || 'student'
  const studentItems = [
    { path: '/', icon: '🏠', label: t('navigation.home') },
    { path: '/ai', icon: '🤖', label: 'AI' },
    { path: '/notes', icon: '📝', label: t('navigation.notes') },
    { path: '/stats', icon: '📊', label: t('navigation.stats') },
    { path: '/profile', icon: '👤', label: t('navigation.profile') },
    // Hidden menu items
    { path: '/homework', icon: '✍️', label: t('navigation.homework_grading') },
    { path: '/quiz', icon: '📚', label: t('navigation.quiz') },
    { path: '/wrong-book', icon: '❌', label: t('navigation.wrong_book') },
    { path: '/plan', icon: '📅', label: t('navigation.study_plan') },
    { path: '/docs', icon: '📄', label: t('navigation.docs') },
    { path: '/reading-buddy', icon: '📖', label: t('navigation.reading_buddy') },
  ]
  const observerItems = [
    { path: '/', icon: '🏠', label: t('navigation.home') },
    { path: '/monitor', icon: '👁️', label: t('auth.student') },
    { path: '/stats', icon: '📊', label: t('navigation.stats') },
    { path: '/profile', icon: '👤', label: t('navigation.profile') },
  ]
  return (role === 'teacher' || role === 'parent') ? observerItems : studentItems
})

// Items visible in bottom nav (first 5)
const visibleItems = computed(() => allMenuItems.value.slice(0, 5))

// Items hidden in more menu
const hiddenItems = computed(() => allMenuItems.value.slice(5))

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<style scoped>
/* Mobile bottom nav fixed position, prevent content overlap */
nav {
  z-index: 40;
}

/* Menu transition animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
