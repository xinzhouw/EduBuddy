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
