import api from './index'

export const aiApi = {
  getSessions: (params?: { page?: number; size?: number }) =>
    api.get('/ai/sessions', { params }),

  getMessages: (sessionId: string) =>
    api.get(`/ai/sessions/${sessionId}/messages`),

  feedback: (messageId: number, data: { rating: string; reason?: string }) =>
    api.post(`/ai/messages/${messageId}/feedback`, data),

  addToWrongBook: (messageId: number, data: { subject: string; tags: string[] }) =>
    api.post(`/ai/messages/${messageId}/add-to-wrong-book`, data),

  deleteSession: (sessionId: string) =>
    api.delete(`/ai/sessions/${sessionId}`),
}
