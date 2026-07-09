<template>
  <div class="user-management">
    <el-card class="card-container">
      <template #header>
        <div class="flex justify-between items-center">
          <span>{{ $t('admin.user_management_title', { n: adminStore.userList.total }) }}</span>
          <div class="search-group">
            <el-input
              v-model="searchText"
              :placeholder="$t('admin.search_placeholder')"
              clearable
              style="width: 200px; margin-right: 10px"
              @keyup.enter="handleSearchAndReset"
            />
            <el-select
              v-model="roleFilter"
              :placeholder="$t('admin.filter_role')"
              clearable
              style="width: 150px; margin-right: 10px"
              @change="handleSearchAndReset"
            >
              <el-option :label="$t('auth.student')" value="student" />
              <el-option :label="$t('auth.teacher')" value="teacher" />
              <el-option :label="$t('auth.parent')" value="parent" />
            </el-select>
            <el-button type="primary" @click="handleSearchAndReset">{{ $t('admin.search_btn') }}</el-button>
            <el-tooltip :content="$t('admin.load_all_tooltip')" placement="top">
              <el-button @click="handleLoadAll" :loading="isLoadingAll">
                {{ $t('admin.load_all') }}
              </el-button>
            </el-tooltip>
          </div>
        </div>
      </template>

      <el-alert
        v-if="adminStore.userListError"
        :title="$t('admin.error_fmt', { msg: adminStore.userListError })"
        type="error"
        closable
        style="margin-bottom: 20px"
      />
      <div class="batch-actions" v-if="selectedUsers.length">
        <span>{{ $t('admin.selected_users', { n: selectedUsers.length }) }}</span>
        <el-popconfirm
          :title="$t('admin.bulk_delete_confirm')"
          :confirm-button-text="$t('admin.confirm_delete')"
          :cancel-button-text="$t('common.cancel')"
          @confirm="handleBatchDelete"
        >
          <template #reference>
            <el-button type="danger" size="small">{{ $t('admin.bulk_delete_btn') }}</el-button>
          </template>
        </el-popconfirm>
        <el-button size="small" @click="selectedUsers = []">{{ $t('admin.cancel_select') }}</el-button>
      </div>

      <div class="content-wrapper">
        <el-empty v-if="!adminStore.userListLoading && !adminStore.userList.items.length" :description="$t('admin.no_user_data')" />
        <div v-if="adminStore.userList.items.length" class="table-container">
        <el-table
          :data="adminStore.userList.items"
          :loading="adminStore.userListLoading"
          stripe
          style="width: 100%; height: 100%"
          @selection-change="handleSelectionChange"
        >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="email" :label="$t('admin.email_col')" min-width="150" show-overflow-tooltip />
        <el-table-column prop="nickname" :label="$t('admin.nickname_col')" min-width="100" />
        <el-table-column prop="role" :label="$t('admin.role_col')" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ getRoleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="grade" :label="$t('admin.grade_col')" width="70" />
        <el-table-column prop="login_count" :label="$t('admin.login_count_col')" width="90" align="right" />
        <el-table-column prop="last_login" :label="$t('admin.last_login_col')" min-width="140">
          <template #default="{ row }">
            <span style="font-size: 12px">{{ formatTime(row.last_login) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" :label="$t('admin.status_col')" width="70" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              @change="handleToggleStatus(row)"
              size="small"
            />
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" min-width="130" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="handleViewDetail(row.id)"
              style="padding: 4px 8px"
            >
              {{ $t('admin.detail_btn') }}
            </el-button>
            <el-popconfirm
              :title="$t('admin.delete_user_confirm')"
              :confirm-button-text="$t('admin.delete_btn')"
              :cancel-button-text="$t('common.cancel')"
              @confirm="handleDeleteUser(row.id)"
            >
              <template #reference>
                <el-button type="danger" link size="small" style="padding: 4px 8px">{{ $t('admin.delete_btn') }}</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
        </el-table>
        </div>
      </div>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="adminStore.userList.total"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 20px; text-align: right"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'

const { t } = useI18n()
const router = useRouter()
const adminStore = useAdminStore()

const searchText = ref('')
const roleFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(50)  // default page size: 50 users per page
const selectedUsers = ref<any[]>([])
const isLoadingAll = ref(false)

onMounted(() => {
  handleSearch()
})

watch([currentPage, pageSize], () => {
  handleSearch()
})

const handleSelectionChange = (selection: any[]) => {
  selectedUsers.value = selection
}

const handleBatchDelete = async () => {
  if (!selectedUsers.value.length) {
    ElMessage.warning(t('admin.select_users_first'))
    return
  }

  let successCount = 0
  let failCount = 0

  for (const user of selectedUsers.value) {
    const success = await adminStore.deleteUser(user.id)
    if (success) {
      successCount++
    } else {
      failCount++
    }
  }

  selectedUsers.value = []

  if (successCount > 0) {
    if (failCount > 0) {
      ElMessage.success(t('admin.bulk_delete_partial', { success: successCount, fail: failCount }))
    } else {
      ElMessage.success(t('admin.bulk_delete_success', { n: successCount }))
    }
    await handleSearch()
  } else {
    ElMessage.error(t('admin.bulk_delete_failed'))
  }
}

const handleLoadAll = async () => {
  isLoadingAll.value = true
  try {
    // Calculate total pages to load
    const total = adminStore.userList.total
    const pageSizeTemp = 100  // use max page size temporarily
    const totalPages = Math.ceil(total / pageSizeTemp)

    if (totalPages === 1) {
      // Only need to load one page
      await adminStore.fetchUserList(1, pageSizeTemp, searchText.value || undefined, roleFilter.value || undefined)
      ElMessage.success(t('admin.load_all_success', { n: total }))
    } else {
      // Load all pages then merge results
      let allUsers: any[] = []
      for (let page = 1; page <= totalPages; page++) {
        await adminStore.fetchUserList(page, pageSizeTemp, searchText.value || undefined, roleFilter.value || undefined)
        allUsers = allUsers.concat(adminStore.userList.items)
      }
      // Update display after loading all
      currentPage.value = 1
      pageSize.value = 100
      await adminStore.fetchUserList(1, 100, searchText.value || undefined, roleFilter.value || undefined)
      ElMessage.success(t('admin.load_all_success', { n: allUsers.length }))
    }
  } catch (error) {
    ElMessage.error(t('admin.load_failed'))
  } finally {
    isLoadingAll.value = false
  }
}

const getRoleLabel = (role: string) => {
  const roleMap: Record<string, string> = {
    student: t('auth.student'),
    teacher: t('auth.teacher'),
    parent: t('auth.parent'),
    admin: t('auth.admin')
  }
  return roleMap[role] || role
}

const formatTime = (time: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const handleSearchAndReset = async () => {
  currentPage.value = 1
  await handleSearch()
}

const handleSearch = async () => {
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
    ElMessage.success(t(row.is_active ? 'admin.user_disabled' : 'admin.user_enabled'))
    await handleSearch()
  } else {
    const errorMsg = adminStore.userListError || t('admin.toggle_failed')
    ElMessage.error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg))
  }
}

const handleDeleteUser = async (userId: number) => {
  const success = await adminStore.deleteUser(userId)
  if (success) {
    ElMessage.success(t('admin.user_deleted'))
    await handleSearch()
  } else {
    const errorMsg = adminStore.userListError || t('admin.delete_failed')
    ElMessage.error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg))
  }
}

const handleViewDetail = (userId: number) => {
  router.push(`/admin/users/${userId}`)
}
</script>

<style scoped>
.user-management {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
  box-sizing: border-box;
}

:deep(.el-card) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

:deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px 16px;
  margin-bottom: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border-left: 4px solid #409eff;
  flex-shrink: 0;
}

:deep(.el-empty) {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.batch-actions span {
  color: #606266;
  font-weight: 500;
}

.card-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  margin: 0;
}

.table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

:deep(.table-container .el-table) {
  flex: 1;
  overflow-y: auto;
}

:deep(.el-pagination) {
  flex-shrink: 0;
  padding: 12px 20px;
  text-align: right;
  border-top: 1px solid #ebeef5;
  background-color: #fff;
}

.search-group {
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