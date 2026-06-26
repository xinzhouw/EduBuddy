import api from './index'

export const authApi = {
  register: (data: { email: string; password: string; nickname: string; grade: string; role?: string }) =>
    api.post('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),

  getMe: () => api.get('/auth/me'),

  updateMe: (data: { nickname?: string; grade?: string; phone?: string; gender?: string; age?: number }) =>
    api.put('/auth/me', data),

  changePassword: (data: { old_password: string; new_password: string }) =>
    api.put('/auth/password', data),

  deleteMe: () => api.delete('/auth/me'),

  forgotPassword: (email: string) =>
    api.post('/auth/forgot-password', { email }),

  resetPassword: (email: string, code: string, newPassword: string) =>
    api.post('/auth/reset-password', {
      email,
      code,
      new_password: newPassword
    })
}
