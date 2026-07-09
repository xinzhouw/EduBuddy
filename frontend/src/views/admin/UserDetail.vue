<template>
  <div class="user-detail">
    <el-button @click="$router.back" class="mb-3">← {{ $t('common.back') }}</el-button>

    <el-row :gutter="20" class="mb-5">
      <el-col :xs="24" :md="8">
        <el-card v-loading="adminStore.userDetailLoading">
          <template #header>
            <span>{{ $t('admin.user_detail_title') }}</span>
          </template>
          <div v-if="adminStore.userDetail" class="user-info">
            <div class="info-item">
              <span class="label">{{ $t('admin.label_email') }}</span>
              <span>{{ adminStore.userDetail.email }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('admin.label_nickname') }}</span>
              <span>{{ adminStore.userDetail.nickname }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('admin.label_role') }}</span>
              <el-tag>{{ getRoleLabel(adminStore.userDetail.role) }}</el-tag>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('admin.label_grade') }}</span>
              <span>{{ adminStore.userDetail.grade || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('admin.label_status') }}</span>
              <el-switch
                :model-value="adminStore.userDetail.is_active"
                @change="handleToggleStatus"
              />
            </div>
            <div class="info-item">
              <span class="label">{{ $t('admin.label_created_at') }}</span>
              <span>{{ formatTime(adminStore.userDetail.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('admin.label_last_login') }}</span>
              <span>{{ formatTime(adminStore.userDetail.last_login) }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('admin.label_total_logins') }}</span>
              <span>{{ adminStore.userDetail.login_count }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ $t('admin.label_recent_logins') }}</span>
              <span>{{ adminStore.userDetail.login_7d }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="16">
        <el-card>
          <template #header>
            <span>{{ $t('admin.feature_stats_title') }}</span>
          </template>
          <el-empty
            v-if="!adminStore.userDetail?.feature_stats.length"
            :description="$t('admin.no_data')"
          />
          <div v-else id="feature-stats-chart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <span>{{ $t('admin.activity_log_title') }}</span>
          <div>
            <el-select
              v-model="logFilter.feature"
              :placeholder="$t('admin.filter_feature')"
              clearable
              style="width: 150px; margin-right: 10px"
              @change="handleFetchLogs"
            >
              <el-option :label="$t('admin.feature_ai_chat')" value="ai_chat" />
              <el-option :label="$t('admin.feature_notes')" value="notes" />
              <el-option :label="$t('admin.feature_wrong_book')" value="wrong_book" />
              <el-option :label="$t('admin.feature_quiz')" value="quiz" />
              <el-option :label="$t('admin.feature_study_plan')" value="study_plan" />
              <el-option :label="$t('admin.feature_homework')" value="homework" />
            </el-select>
            <el-button @click="handleFetchLogs">{{ $t('common.refresh') }}</el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="adminStore.auditLogs.items"
        :loading="adminStore.auditLogsLoading"
        stripe
        size="small"
      >
        <el-table-column prop="timestamp" :label="$t('admin.time_col')" width="160">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="feature" :label="$t('admin.feature_col')" width="100">
          <template #default="{ row }">
            <el-tag>{{ getFeatureLabel(row.feature) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action" :label="$t('common.actions')" width="80" />
        <el-table-column prop="endpoint" :label="$t('admin.endpoint_col')" min-width="200" show-overflow-tooltip />
        <el-table-column prop="ip_address" :label="$t('admin.ip_col')" width="120" />
        <el-table-column prop="city" :label="$t('admin.city_col')" width="100" />
        <el-table-column prop="country" :label="$t('admin.country_col')" width="100" />
        <el-table-column prop="status_code" :label="$t('admin.status_code_col')" width="80" align="center" />
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
import { useI18n } from 'vue-i18n'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const { t } = useI18n()
const route = useRoute()
const adminStore = useAdminStore()
const userId = parseInt(route.params.id as string)

const logFilter = ref({ feature: '' })
const logPage = ref(1)
const logPageSize = ref(20)

const getRoleLabel = (role: string) => {
  const roleMap: Record<string, string> = {
    student: t('auth.student'),
    teacher: t('auth.teacher'),
    parent: t('auth.parent'),
    admin: t('auth.admin')
  }
  return roleMap[role] || role
}

const getFeatureLabel = (feature: string) => {
  const featureMap: Record<string, string> = {
    ai_chat: t('admin.feature_ai_chat'),
    notes: t('admin.feature_notes'),
    wrong_book: t('admin.feature_wrong_book'),
    quiz: t('admin.feature_quiz'),
    study_plan: t('admin.feature_study_plan'),
    homework: t('admin.feature_homework'),
    monitor: t('admin.feature_monitor'),
    auth: t('admin.feature_auth'),
    admin: t('admin.feature_admin')
  }
  return featureMap[feature] || feature
}

const formatTime = (time: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const handleToggleStatus = async (value: boolean) => {
  const success = await adminStore.toggleUserStatus(userId, value)
  if (success) {
    ElMessage.success(t('admin.update_status_success'))
  } else {
    ElMessage.error(t('admin.update_status_failed'))
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
