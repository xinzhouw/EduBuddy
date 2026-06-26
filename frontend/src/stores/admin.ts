import { defineStore } from 'pinia'
import { ref } from 'vue'
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
      console.log('fetchUserList response:', response)
      userList.value = response
    } catch (error: any) {
      console.error('fetchUserList error:', error)
      userListError.value = error.response?.data?.detail || error.response?.data?.message || error.message || '获取用户列表失败'
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
      userDetail.value = response
    } catch (error: any) {
      userDetailError.value = error.response?.data?.detail || error.response?.data?.message || error.message || '获取用户详情失败'
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
      userListError.value = error.response?.data?.detail || error.response?.data?.message || error.message || '修改用户状态失败'
      return false
    }
  }

  // 删除用户
  const deleteUser = async (userId: number) => {
    try {
      await adminUserAPI.deleteUser(userId)
      return true
    } catch (error: any) {
      userListError.value = error.response?.data?.detail || error.response?.data?.message || error.message || '删除用户失败'
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
      auditLogs.value = response
    } catch (error: any) {
      auditLogsError.value = error.response?.data?.detail || error.response?.data?.message || error.message || '获取审计日志失败'
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
      dashboardStats.value = response
    } catch (error: any) {
      dashboardStatsError.value = error.response?.data?.detail || error.response?.data?.message || error.message || '获取统计数据失败'
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
