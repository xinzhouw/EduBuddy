import api from './index'

export const docsApi = {
  upload: (formData: FormData) =>
    api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  list: (params?: { subject?: string; page?: number }) =>
    api.get('/documents', { params }),
  get: (id: number) => api.get(`/documents/${id}`),
  delete: (id: number) => api.delete(`/documents/${id}`),
}

export const statsApi = {
  getOverview: () => api.get('/stats/overview'),
  getStudyTime: (period: string = 'week') => api.get('/stats/study-time', { params: { period } }),
  getAccuracyBySubject: () => api.get('/stats/accuracy-by-subject'),
  getWrongDistribution: () => api.get('/stats/wrong-book-distribution'),
  recordStudyLog: (data: { subject?: string; duration_minutes: number; activity_type: string }) =>
    api.post('/stats/study-log', data),
}
