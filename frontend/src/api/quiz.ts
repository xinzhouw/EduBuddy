import api from './index'

export const quizApi = {
  generate: (data: {
    subject: string
    topic: string
    difficulty: number
    question_types: string[]
    count: number
  }) => api.post('/quiz/generate', data),

  submit: (sessionId: string, data: { answers: Array<{ question_id: number; answer: string; time_spent: number }> }) =>
    api.post(`/quiz/sessions/${sessionId}/submit`, data),

  getSessions: (params?: { page?: number; size?: number }) =>
    api.get('/quiz/sessions', { params }),

  getRecommendedDifficulty: (subject: string, topic: string) =>
    api.get('/quiz/recommended-difficulty', { params: { subject, topic } }),
}
