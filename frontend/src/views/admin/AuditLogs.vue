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
              v-model.number="filterUserId"
              placeholder="用户 ID"
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

      <el-alert
        v-if="adminStore.auditLogsError"
        :title="`错误：${adminStore.auditLogsError}`"
        type="error"
        closable
        style="margin-bottom: 20px"
      />
      <div class="content-wrapper">
        <el-empty v-if="!adminStore.auditLogsLoading && !adminStore.auditLogs.items.length" description="暂无审计日志" />
        <div v-if="adminStore.auditLogs.items.length" class="table-container">
        <el-table
          :data="adminStore.auditLogs.items"
          :loading="adminStore.auditLogsLoading"
          stripe
          size="small"
          style="width: 100%"
          max-height="400"
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
        </div>
      </div>

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

onMounted(() => {
  handleSearch()
})

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
</script>

<style scoped>
.audit-logs {
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

:deep(.el-empty) {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
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