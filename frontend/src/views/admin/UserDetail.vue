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
}, { deep: true })
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
