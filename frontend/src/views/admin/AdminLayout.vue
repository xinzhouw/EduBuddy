<template>
  <div class="admin-layout">
    <el-container>
      <el-header>
        <div class="header-content">
          <span>EduBuddy 管理后台</span>
          <div class="user-info">
            <span>{{ authStore.user?.nickname }}</span>
            <el-button type="text" @click="handleLogout">退出</el-button>
          </div>
        </div>
      </el-header>
      <el-container>
        <el-aside width="200px" class="admin-sidebar">
          <el-menu
            :default-active="activeMenu"
            router
            background-color="#545c64"
            text-color="#fff"
            active-text-color="#ffd04b"
          >
            <el-menu-item index="/admin/dashboard">
              <el-icon><Monitor /></el-icon>
              <span>仪表板</span>
            </el-menu-item>
            <el-menu-item index="/admin/users">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="/admin/audit-logs">
              <el-icon><Document /></el-icon>
              <span>审计日志</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Monitor, User, Document } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  const path = router.currentRoute.value.path
  if (path.startsWith('/admin/users') && !path.endsWith('/users')) {
    return '/admin/users'
  }
  return path || '/admin/dashboard'
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-container) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-container > .el-container) {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.el-header {
  background-color: #545c64;
  color: #fff;
  padding: 0 20px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  font-size: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.admin-sidebar {
  background-color: #545c64 !important;
  flex-shrink: 0;
  overflow-y: auto;
}

:deep(.el-main) {
  background-color: #f5f7fa;
  padding: 0;
  overflow: auto;
  flex: 1;
  min-width: 0;
}
</style>
