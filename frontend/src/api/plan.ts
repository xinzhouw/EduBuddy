import api from './index'

export const planApi = {
  generate: (data: { subjects: string[]; exam_date: string; daily_hours: number; weak_subjects: string[] }) =>
    api.post('/plan/generate', data),
  getCurrent: () => api.get('/plan/current'),
  getToday: () => api.get('/plan/today'),
  markTaskDone: (taskId: number, is_done: boolean) =>
    api.put(`/plan/tasks/${taskId}/done`, { is_done }),
  recordPomodoro: (data: { subject?: string; duration_minutes: number; completed: boolean }) =>
    api.post('/plan/pomodoro', data),
}
