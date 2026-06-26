<template>
  <div class="admin-dashboard">
    <el-alert
      v-if="adminStore.dashboardStatsError"
      :title="`错误：${adminStore.dashboardStatsError}`"
      type="error"
      closable
      style="margin-bottom: 20px"
    />
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
}, { deep: true })

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
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 20px;
  box-sizing: border-box;
  background-color: #f5f7fa;
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
