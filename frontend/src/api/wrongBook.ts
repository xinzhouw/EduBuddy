import api from './index'

export const wrongBookApi = {
  list: (params?: { subject?: string; mastery?: string; due_review?: boolean; page?: number; size?: number }) =>
    api.get('/wrong-book', { params }),
  create: (data: { question: string; correct_answer: string; user_wrong_answer?: string; subject: string; tags: string[] }) =>
    api.post('/wrong-book', data),
  get: (id: number) => api.get(`/wrong-book/${id}`),
  updateMastery: (id: number, mastery: string) =>
    api.put(`/wrong-book/${id}/mastery`, { mastery }),
  review: (id: number, data: { answer: string; is_correct: boolean }) =>
    api.post(`/wrong-book/${id}/review`, data),
  delete: (id: number) => api.delete(`/wrong-book/${id}`),
  similarQuiz: (id: number, count = 3) =>
    api.post(`/wrong-book/${id}/similar-quiz`, { count }),
}
