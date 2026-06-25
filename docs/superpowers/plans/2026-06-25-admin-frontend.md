# 管理后台前端实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现管理后台前端，包括仪表板、用户管理、用户详情和审计日志等页面。

**Architecture:** 采用 Vue 3 + Pinia + Element Plus 构建管理后台模块，创建 API 客户端与后端交互，添加路由守卫确保仅 admin 用户访问。

**Tech Stack:**
- 前端框架：Vue 3 + TypeScript
- 状态管理：Pinia
- UI 库：Element Plus
- 数据可视化：ECharts
- 路由：Vue Router 4
- HTTP 客户端：Axios

## Global Constraints

- 仅 admin 角色用户可访问所有管理后台功能
- 管理后台路由前缀：`/admin`
- 侧边栏菜单动态显示，admin 用户看到 Admin 菜单项
- 所有时间显示采用本地时区

---

## Task 1: 创建 Admin API 客户端

**Files:**
- Create: `frontend/src/api/admin.ts`

**Interfaces:**
- Produces: Admin API 客户端函数集合

- [ ] **Step 1: 创建 admin.ts**

Create `frontend/src/api/admin.ts`:

```typescript
import api from './index'

export interface User {
  id: number
  email: string
  nickname: string
  role: string
  grade?: string
  is_active: boolean
  last_login?: string
  login_count: number
  created_at: string
}

export interface UserListResponse {
  total: number
  page: number
  page_size: number
  items: User[]
}

export interface UserDetailResponse extends User {
  login_7d: number
  feature_stats: Array<{
    feature: string
    count: number
  }>
}

export interface AuditLog {
  id: number
  user_id: number
  timestamp: string
  feature: string
  action: string
  endpoint: string
  ip_address: string
  city: string
  country: string
  status_code: number
}

export interface AuditLogResponse {
  total: number
  page: number
  page_size: number
  items: AuditLog[]
}

export interface DashboardStats {
  active_users_7d: number
  total_users: number
  feature_top: Array<{
    feature: string
    count: number
  }>
  active_user_top: Array<{
    user_id: number
    nickname: string
    email: string
    count: number
  }>
}

// 用户管理相关 API
export const adminUserAPI = {
  // 获取用户列表
  getUserList(page: number = 1, page_size: number = 20, search?: string, role?: string) {
    return api.get<UserListResponse>('/admin/users', {
      params: { page, page_size, search, role }
    })
  },

  // 获取用户详情
  getUserDetail(userId: number) {
    return api.get<UserDetailResponse>(`/admin/users/${userId}`)
  },

  // 启用/禁用用户
  toggleUserStatus(userId: number, is_active: boolean) {
    return api.put(`/admin/users/${userId}/status`, { is_active })
  },

  // 删除用户
  deleteUser(userId: number) {
    return api.delete(`/admin/users/${userId}`)
  }
}

// 审计日志相关 API
export const adminAuditAPI = {
  // 获取审计日志
  getAuditLogs(
    page: number = 1,
    page_size: number = 50,
    userId?: number,
    feature?: string,
    startDate?: string,
    endDate?: string
  ) {
    return api.get<AuditLogResponse>('/admin/audit-logs', {
      params: { page, page_size, user_id: userId, feature, start_date: startDate, end_date: endDate }
    })
  }
}

// 统计相关 API
export const adminStatsAPI = {
  // 获取仪表板统计
  getDashboardStats() {
    return api.get<DashboardStats>('/admin/stats/dashboard')
  }
}
```

- [ ] **Step 2: 提交**

```bash
cd frontend
git add src/api/admin.ts
git commit -m "feat: add admin API client"
```

---

## Task 2: 创建 Admin 状态管理 Store

**Files:**
- Create: `frontend/src/stores/admin.ts`

**Interfaces:**
- Produces: Pinia admin store，提供用户管理和统计数据状态

- [ ] **Step 1: 创建 admin store**

Create `frontend/src/stores/admin.ts`:

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { adminUserAPI, adminAuditAPI, adminStatsAPI } from '@/api/admin'
import type { User, UserListResponse, AuditLogResponse, DashboardStats } from '@/api/admin'

export const useAdminStore = defineStore('admin', () => {
  // 用户列表状态
  const userList = ref<UserListResponse>({
    total: 0,
    page: 1,
    page_size: 20,
    items: []
  })
  const userListLoading = ref(false)
  const userListError = ref<string | null>(null)

  // 用户详情状态
  const userDetail = ref<any>(null)
  const userDetailLoading = ref(false)
  const userDetailError = ref<string | null>(null)

  // 审计日志状态
  const auditLogs = ref<AuditLogResponse>({
    total: 0,
    page: 1,
    page_size: 50,
    items: []
  })
  const auditLogsLoading = ref(false)
  const auditLogsError = ref<string | null>(null)

  // 仪表板统计状态
  const dashboardStats = ref<DashboardStats | null>(null)
  const dashboardStatsLoading = ref(false)
  const dashboardStatsError = ref<string | null>(null)

  // 获取用户列表
  const fetchUserList = async (page: number = 1, page_size: number = 20, search?: string, role?: string) => {
    userListLoading.value = true
    userListError.value = null
    try {
      const response = await adminUserAPI.getUserList(page, page_size, search, role)
      userList.value = response.data
    } catch (error: any) {
      userListError.value = error.response?.data?.message || '获取用户列表失败'
    } finally {
      userListLoading.value = false
    }
  }

  // 获取用户详情
  const fetchUserDetail = async (userId: number) => {
    userDetailLoading.value = true
    userDetailError.value = null
    try {
      const response = await adminUserAPI.getUserDetail(userId)
      userDetail.value = response.data
    } catch (error: any) {
      userDetailError.value = error.response?.data?.message || '获取用户详情失败'
    } finally {
      userDetailLoading.value = false
    }
  }

  // 启用/禁用用户
  const toggleUserStatus = async (userId: number, is_active: boolean) => {
    try {
      await adminUserAPI.toggleUserStatus(userId, is_active)
      return true
    } catch (error: any) {
      userListError.value = error.response?.data?.message || '修改用户状态失败'
      return false
    }
  }

  // 删除用户
  const deleteUser = async (userId: number) => {
    try {
      await adminUserAPI.deleteUser(userId)
      return true
    } catch (error: any) {
      userListError.value = error.response?.data?.message || '删除用户失败'
      return false
    }
  }

  // 获取审计日志
  const fetchAuditLogs = async (
    page: number = 1,
    page_size: number = 50,
    userId?: number,
    feature?: string,
    startDate?: string,
    endDate?: string
  ) => {
    auditLogsLoading.value = true
    auditLogsError.value = null
    try {
      const response = await adminAuditAPI.getAuditLogs(page, page_size, userId, feature, startDate, endDate)
      auditLogs.value = response.data
    } catch (error: any) {
      auditLogsError.value = error.response?.data?.message || '获取审计日志失败'
    } finally {
      auditLogsLoading.value = false
    }
  }

  // 获取仪表板统计
  const fetchDashboardStats = async () => {
    dashboardStatsLoading.value = true
    dashboardStatsError.value = null
    try {
      const response = await adminStatsAPI.getDashboardStats()
      dashboardStats.value = response.data
    } catch (error: any) {
      dashboardStatsError.value = error.response?.data?.message || '获取统计数据失败'
    } finally {
      dashboardStatsLoading.value = false
    }
  }

  return {
    // 用户列表
    userList,
    userListLoading,
    userListError,
    fetchUserList,

    // 用户详情
    userDetail,
    userDetailLoading,
    userDetailError,
    fetchUserDetail,
    toggleUserStatus,
    deleteUser,

    // 审计日志
    auditLogs,
    auditLogsLoading,
    auditLogsError,
    fetchAuditLogs,

    // 仪表板统计
    dashboardStats,
    dashboardStatsLoading,
    dashboardStatsError,
    fetchDashboardStats
  }
})
```

- [ ] **Step 2: 提交**

```bash
git add src/stores/admin.ts
git commit -m "feat: add admin pinia store"
```

---

## Task 3: 创建 Admin 仪表板页面

**Files:**
- Create: `frontend/src/views/admin/AdminDashboard.vue`

**Interfaces:**
- Consumes: `useAdminStore()` store
- Produces: 管理后台主页面

- [ ] **Step 1: 创建 AdminDashboard.vue**

Create `frontend/src/views/admin/AdminDashboard.vue`:

```vue
<template>
  <div class="admin-dashboard">
    <el-row :gutter="20" class="mb-5">
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="stat-card">
          <template #header>
            <div class="flex justify-between items-center">
              <span>最近7天活跃用户</span>
              <el-icon><DataAnalysis /></el-icon>
            </div>
          </template>
          <div class="stat-value">{{ adminStore.dashboardStats?.active_users_7d || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="stat-card">
          <template #header>
            <div class="flex justify-between items-center">
              <span>系统总用户数</span>
              <el-icon><User /></el-icon>
            </div>
          </template>
          <div class="stat-value">{{ adminStore.dashboardStats?.total_users || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="stat-card">
          <template #header>
            <div class="flex justify-between items-center">
              <span>热门功能数</span>
              <el-icon><Histogram /></el-icon>
            </div>
          </template>
          <div class="stat-value">{{ adminStore.dashboardStats?.feature_top.length || 0 }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mb-5">
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <span>功能使用排行 (最近30天)</span>
          </template>
          <el-empty v-if="!adminStore.dashboardStats?.feature_top.length" description="暂无数据" />
          <div v-else id="feature-chart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <span>活跃用户排行 (最近7天)</span>
          </template>
          <el-empty v-if="!adminStore.dashboardStats?.active_user_top.length" description="暂无数据" />
          <el-table v-else :data="adminStore.dashboardStats?.active_user_top" size="small">
            <el-table-column prop="nickname" label="昵称" width="120" />
            <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
            <el-table-column prop="count" label="访问次数" width="100" align="right" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useAdminStore } from '@/stores/admin'
import * as echarts from 'echarts'
import { DataAnalysis, User, Histogram } from '@element-plus/icons-vue'

const adminStore = useAdminStore()
const featureChart = ref<echarts.ECharts | null>(null)

onMounted(async () => {
  await adminStore.fetchDashboardStats()
  initFeatureChart()
})

watch(() => adminStore.dashboardStats?.feature_top, () => {
  initFeatureChart()
})

const initFeatureChart = () => {
  if (!adminStore.dashboardStats?.feature_top.length) return

  const chartDom = document.getElementById('feature-chart')
  if (!chartDom) return

  if (!featureChart.value) {
    featureChart.value = echarts.init(chartDom)
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: { left: '3%', right: '3%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: adminStore.dashboardStats!.feature_top.map(f => f.feature)
    },
    yAxis: { type: 'value' },
    series: [
      {
        data: adminStore.dashboardStats!.feature_top.map(f => f.count),
        type: 'bar',
        itemStyle: { color: '#409EFF' }
      }
    ]
  }

  featureChart.value.setOption(option)
}
</script>

<style scoped>
.admin-dashboard {
  padding: 20px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-top: 10px;
}

.mb-5 {
  margin-bottom: 20px;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/views/admin/AdminDashboard.vue
git commit -m "feat: add admin dashboard page"
```

---

## Task 4: 创建用户管理页面

**Files:**
- Create: `frontend/src/views/admin/UserManagement.vue`

**Interfaces:**
- Consumes: `useAdminStore()` store
- Produces: 用户管理列表页面

- [ ] **Step 1: 创建 UserManagement.vue**

Create `frontend/src/views/admin/UserManagement.vue`:

```vue
<template>
  <div class="user-management">
    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <span>用户管理</span>
          <div>
            <el-input
              v-model="searchText"
              placeholder="搜索邮箱或昵称"
              clearable
              style="width: 200px; margin-right: 10px"
              @keyup.enter="handleSearch"
            />
            <el-select
              v-model="roleFilter"
              placeholder="筛选角色"
              clearable
              style="width: 150px; margin-right: 10px"
              @change="handleSearch"
            >
              <el-option label="学生" value="student" />
              <el-option label="教师" value="teacher" />
              <el-option label="家长" value="parent" />
            </el-select>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="adminStore.userList.items"
        :loading="adminStore.userListLoading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column prop="nickname" label="昵称" width="120" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag>{{ getRoleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="grade" label="年级" width="80" />
        <el-table-column prop="login_count" label="登录次数" width="100" align="right" />
        <el-table-column prop="last_login" label="最后登录" width="160">
          <template #default="{ row }">
            {{ formatTime(row.last_login) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              @change="handleToggleStatus(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="handleViewDetail(row.id)"
            >
              查看详情
            </el-button>
            <el-popconfirm
              title="确定删除该用户吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleDeleteUser(row.id)"
            >
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="adminStore.userList.total"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 20px; text-align: right"
        @change="handleSearch"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'

const router = useRouter()
const adminStore = useAdminStore()

const searchText = ref('')
const roleFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const getRoleLabel = (role: string) => {
  const roleMap = {
    student: '学生',
    teacher: '教师',
    parent: '家长',
    admin: '管理员'
  }
  return roleMap[role as keyof typeof roleMap] || role
}

const formatTime = (time: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const handleSearch = async () => {
  currentPage.value = 1
  await adminStore.fetchUserList(
    currentPage.value,
    pageSize.value,
    searchText.value || undefined,
    roleFilter.value || undefined
  )
}

const handleToggleStatus = async (row: any) => {
  const success = await adminStore.toggleUserStatus(row.id, !row.is_active)
  if (success) {
    ElMessage.success(`已${row.is_active ? '禁用' : '启用'}用户`)
    await handleSearch()
  } else {
    ElMessage.error(adminStore.userListError || '操作失败')
  }
}

const handleDeleteUser = async (userId: number) => {
  const success = await adminStore.deleteUser(userId)
  if (success) {
    ElMessage.success('用户已删除')
    await handleSearch()
  } else {
    ElMessage.error(adminStore.userListError || '删除失败')
  }
}

const handleViewDetail = (userId: number) => {
  router.push(`/admin/users/${userId}`)
}

// 初始化加载
handleSearch()
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.flex {
  display: flex;
  align-items: center;
  gap: 10px;
}

.justify-between {
  justify-content: space-between;
}

.items-center {
  align-items: center;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/views/admin/UserManagement.vue
git commit -m "feat: add user management page"
```

---

## Task 5: 创建用户详情页面

**Files:**
- Create: `frontend/src/views/admin/UserDetail.vue`

**Interfaces:**
- Consumes: `useAdminStore()` store、路由参数 user_id
- Produces: 用户详情和活动日志页面

- [ ] **Step 1: 创建 UserDetail.vue**

Create `frontend/src/views/admin/UserDetail.vue`:

```vue
<template>
  <div class="user-detail">
    <el-button @click="$router.back" class="mb-3">← 返回</el-button>

    <el-row :gutter="20" class="mb-5">
      <el-col :xs="24" :md="8">
        <el-card v-loading="adminStore.userDetailLoading">
          <template #header>
            <span>用户信息</span>
          </template>
          <div v-if="adminStore.userDetail" class="user-info">
            <div class="info-item">
              <span class="label">邮箱：</span>
              <span>{{ adminStore.userDetail.email }}</span>
            </div>
            <div class="info-item">
              <span class="label">昵称：</span>
              <span>{{ adminStore.userDetail.nickname }}</span>
            </div>
            <div class="info-item">
              <span class="label">角色：</span>
              <el-tag>{{ getRoleLabel(adminStore.userDetail.role) }}</el-tag>
            </div>
            <div class="info-item">
              <span class="label">年级：</span>
              <span>{{ adminStore.userDetail.grade || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">状态：</span>
              <el-switch
                :model-value="adminStore.userDetail.is_active"
                @change="handleToggleStatus"
              />
            </div>
            <div class="info-item">
              <span class="label">创建时间：</span>
              <span>{{ formatTime(adminStore.userDetail.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">最后登录：</span>
              <span>{{ formatTime(adminStore.userDetail.last_login) }}</span>
            </div>
            <div class="info-item">
              <span class="label">总登录次数：</span>
              <span>{{ adminStore.userDetail.login_count }}</span>
            </div>
            <div class="info-item">
              <span class="label">最近7天登录：</span>
              <span>{{ adminStore.userDetail.login_7d }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="16">
        <el-card>
          <template #header>
            <span>最近30天功能使用统计</span>
          </template>
          <el-empty
            v-if="!adminStore.userDetail?.feature_stats.length"
            description="暂无数据"
          />
          <div v-else id="feature-stats-chart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <span>活动日志</span>
          <div>
            <el-select
              v-model="logFilter.feature"
              placeholder="筛选功能"
              clearable
              style="width: 150px; margin-right: 10px"
              @change="handleFetchLogs"
            >
              <el-option label="AI 对话" value="ai_chat" />
              <el-option label="笔记" value="notes" />
              <el-option label="错题" value="wrong_book" />
              <el-option label="测试" value="quiz" />
              <el-option label="学习计划" value="study_plan" />
              <el-option label="作业" value="homework" />
            </el-select>
            <el-button @click="handleFetchLogs">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="adminStore.auditLogs.items"
        :loading="adminStore.auditLogsLoading"
        stripe
        size="small"
      >
        <el-table-column prop="timestamp" label="时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="feature" label="功能" width="100">
          <template #default="{ row }">
            <el-tag>{{ getFeatureLabel(row.feature) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作" width="80" />
        <el-table-column prop="endpoint" label="端点" min-width="200" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP 地址" width="120" />
        <el-table-column prop="city" label="城市" width="100" />
        <el-table-column prop="country" label="国家" width="100" />
        <el-table-column prop="status_code" label="状态码" width="80" align="center" />
      </el-table>

      <el-pagination
        v-model:current-page="logPage"
        v-model:page-size="logPageSize"
        :page-sizes="[20, 50, 100]"
        :total="adminStore.auditLogs.total"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 20px; text-align: right"
        @change="handleFetchLogs"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const route = useRoute()
const adminStore = useAdminStore()
const userId = parseInt(route.params.id as string)

const logFilter = ref({ feature: '' })
const logPage = ref(1)
const logPageSize = ref(20)

const getRoleLabel = (role: string) => {
  const roleMap = {
    student: '学生',
    teacher: '教师',
    parent: '家长',
    admin: '管理员'
  }
  return roleMap[role as keyof typeof roleMap] || role
}

const getFeatureLabel = (feature: string) => {
  const featureMap = {
    ai_chat: 'AI 对话',
    notes: '笔记',
    wrong_book: '错题',
    quiz: '测试',
    study_plan: '学习计划',
    homework: '作业',
    monitor: '监护',
    auth: '认证',
    admin: '管理'
  }
  return featureMap[feature as keyof typeof featureMap] || feature
}

const formatTime = (time: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const handleToggleStatus = async (value: boolean) => {
  const success = await adminStore.toggleUserStatus(userId, value)
  if (success) {
    ElMessage.success('用户状态已更新')
  } else {
    ElMessage.error('更新失败')
  }
}

const handleFetchLogs = async () => {
  logPage.value = 1
  await adminStore.fetchAuditLogs(
    logPage.value,
    logPageSize.value,
    userId,
    logFilter.value.feature || undefined
  )
}

const initFeatureStatsChart = () => {
  if (!adminStore.userDetail?.feature_stats.length) return

  const chartDom = document.getElementById('feature-stats-chart')
  if (!chartDom) return

  const chart = echarts.init(chartDom)
  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '3%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: adminStore.userDetail!.feature_stats.map(f => getFeatureLabel(f.feature))
    },
    yAxis: { type: 'value' },
    series: [
      {
        data: adminStore.userDetail!.feature_stats.map(f => f.count),
        type: 'bar',
        itemStyle: { color: '#67C23A' }
      }
    ]
  }
  chart.setOption(option)
}

onMounted(async () => {
  await adminStore.fetchUserDetail(userId)
  await handleFetchLogs()
  initFeatureStatsChart()
})

watch(() => adminStore.userDetail?.feature_stats, () => {
  initFeatureStatsChart()
})
</script>

<style scoped>
.user-detail {
  padding: 20px;
}

.mb-3 {
  margin-bottom: 12px;
}

.mb-5 {
  margin-bottom: 20px;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  font-weight: bold;
  min-width: 80px;
}

.flex {
  display: flex;
  align-items: center;
  gap: 10px;
}

.justify-between {
  justify-content: space-between;
}

.items-center {
  align-items: center;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/views/admin/UserDetail.vue
git commit -m "feat: add user detail page"
```

---

## Task 6: 创建审计日志页面

**Files:**
- Create: `frontend/src/views/admin/AuditLogs.vue`

**Interfaces:**
- Consumes: `useAdminStore()` store
- Produces: 审计日志查询页面

- [ ] **Step 1: 创建 AuditLogs.vue**

Create `frontend/src/views/admin/AuditLogs.vue`:

```vue
<template>
  <div class="audit-logs">
    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <span>系统审计日志</span>
          <div class="filter-group">
            <el-select
              v-model="filterFeature"
              placeholder="筛选功能"
              clearable
              style="width: 150px; margin-right: 10px"
            >
              <el-option label="AI 对话" value="ai_chat" />
              <el-option label="笔记" value="notes" />
              <el-option label="错题" value="wrong_book" />
              <el-option label="测试" value="quiz" />
              <el-option label="学习计划" value="study_plan" />
              <el-option label="作业" value="homework" />
              <el-option label="监护" value="monitor" />
            </el-select>
            <el-input
              v-model="filterUserId"
              placeholder="用户 ID"
              type="number"
              clearable
              style="width: 120px; margin-right: 10px"
            />
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 240px; margin-right: 10px"
            />
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="adminStore.auditLogs.items"
        :loading="adminStore.auditLogsLoading"
        stripe
        size="small"
        max-height="600"
      >
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="user_id" label="用户 ID" width="80" />
        <el-table-column prop="timestamp" label="时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="feature" label="功能" width="100">
          <template #default="{ row }">
            <el-tag>{{ getFeatureLabel(row.feature) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作" width="80" />
        <el-table-column prop="endpoint" label="端点" min-width="200" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP" width="130" show-overflow-tooltip />
        <el-table-column prop="city" label="城市" width="100" />
        <el-table-column prop="country" label="国家" width="80" />
        <el-table-column prop="status_code" label="状态码" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status_code === 200 ? 'success' : 'danger'">
              {{ row.status_code }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="adminStore.auditLogs.total"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 20px; text-align: right"
        @change="handleSearch"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'

const adminStore = useAdminStore()

const filterFeature = ref('')
const filterUserId = ref<number | null>(null)
const dateRange = ref<[Date, Date] | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)

const getFeatureLabel = (feature: string) => {
  const featureMap = {
    ai_chat: 'AI 对话',
    notes: '笔记',
    wrong_book: '错题',
    quiz: '测试',
    study_plan: '学习计划',
    homework: '作业',
    monitor: '监护',
    auth: '认证',
    admin: '管理'
  }
  return featureMap[feature as keyof typeof featureMap] || feature
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

const handleSearch = async () => {
  currentPage.value = 1
  const startDate = dateRange.value ? dateRange.value[0].toISOString() : undefined
  const endDate = dateRange.value ? dateRange.value[1].toISOString() : undefined

  await adminStore.fetchAuditLogs(
    currentPage.value,
    pageSize.value,
    filterUserId.value || undefined,
    filterFeature.value || undefined,
    startDate,
    endDate
  )
}

const handleReset = () => {
  filterFeature.value = ''
  filterUserId.value = null
  dateRange.value = null
  currentPage.value = 1
  handleSearch()
}

onMounted(() => {
  handleSearch()
})
</script>

<style scoped>
.audit-logs {
  padding: 20px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.flex {
  display: flex;
  align-items: center;
  gap: 10px;
}

.justify-between {
  justify-content: space-between;
}

.items-center {
  align-items: center;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/views/admin/AuditLogs.vue
git commit -m "feat: add audit logs page"
```

---

## Task 7: 添加 Admin 路由和权限守卫

**Files:**
- Modify: `frontend/src/router/index.ts` - 添加 admin 路由和守卫

**Interfaces:**
- Consumes: 认证信息、用户角色
- Produces: Admin 路由配置和权限守卫

- [ ] **Step 1: 修改 router/index.ts**

在 `frontend/src/router/index.ts` 中添加 admin 路由。找到路由数组，在其中添加：

```typescript
// Admin 后台路由（仅限管理员）
{
  path: '/admin',
  component: () => import('@/views/admin/AdminLayout.vue'),
  meta: { requiresAuth: true, requiredRole: 'admin' },
  children: [
    {
      path: 'dashboard',
      name: 'AdminDashboard',
      component: () => import('@/views/admin/AdminDashboard.vue'),
      meta: { title: '管理后台' }
    },
    {
      path: 'users',
      name: 'UserManagement',
      component: () => import('@/views/admin/UserManagement.vue'),
      meta: { title: '用户管理' }
    },
    {
      path: 'users/:id',
      name: 'UserDetail',
      component: () => import('@/views/admin/UserDetail.vue'),
      meta: { title: '用户详情' }
    },
    {
      path: 'audit-logs',
      name: 'AuditLogs',
      component: () => import('@/views/admin/AuditLogs.vue'),
      meta: { title: '审计日志' }
    }
  ]
}
```

在路由守卫中添加角色检查逻辑：

```typescript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiredRole && authStore.user?.role !== to.meta.requiredRole) {
    next({ name: 'Dashboard' })
    return
  }
  
  next()
})
```

- [ ] **Step 2: 创建 AdminLayout 组件**

Create `frontend/src/views/admin/AdminLayout.vue`:

```vue
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
            <el-menu-item index="AdminDashboard">
              <el-icon><Monitor /></el-icon>
              <span>仪表板</span>
            </el-menu-item>
            <el-menu-item index="UserManagement">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="AuditLogs">
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
  const path = router.currentRoute.value.name
  return path || 'AdminDashboard'
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
}

.el-header {
  background-color: #545c64;
  color: #fff;
  padding: 0 20px;
  display: flex;
  align-items: center;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.admin-sidebar {
  background-color: #545c64 !important;
}

.el-main {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>
```

- [ ] **Step 3: 修改 AppSidebar 添加 Admin 菜单**

修改 `frontend/src/components/layout/AppSidebar.vue`，在菜单中为 admin 用户添加管理后台菜单项：

```vue
<!-- 在菜单中添加 -->
<el-menu-item v-if="authStore.user?.role === 'admin'" index="/admin/dashboard">
  <el-icon><Monitor /></el-icon>
  <span>管理后台</span>
</el-menu-item>
```

- [ ] **Step 4: 提交**

```bash
git add src/router/index.ts src/views/admin/AdminLayout.vue src/components/layout/AppSidebar.vue
git commit -m "feat: add admin routes and layout"
```

---

## Task 8: 创建 Admin 目录和 __init__ 文件

**Files:**
- Create: `frontend/src/views/admin/` 目录结构

**Interfaces:**
- Produces: Admin 页面目录组织

- [ ] **Step 1: 确保目录存在**

```bash
mkdir -p frontend/src/views/admin
```

- [ ] **Step 2: 提交**

```bash
git add -A
git commit -m "feat: create admin views directory structure"
```

---

现在前端实现计划已完成！

