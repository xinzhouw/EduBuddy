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
