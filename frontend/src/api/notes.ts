import api from './index'

export const notesApi = {
  list: (params?: { subject?: string; page?: number; size?: number }) =>
    api.get('/notes', { params }),
  create: (data: { title: string; subject: string; content: string }) =>
    api.post('/notes', data),
  get: (id: number) => api.get(`/notes/${id}`),
  update: (id: number, data: { title?: string; content?: string; subject?: string }) =>
    api.put(`/notes/${id}`, data),
  delete: (id: number) => api.delete(`/notes/${id}`),
  aiSummarize: (id: number) => api.post(`/notes/${id}/ai-summarize`),
  generateFlashcards: (id: number) => api.post(`/notes/${id}/generate-flashcards`),
}

export const flashcardsApi = {
  list: (params?: { subject?: string; page?: number }) =>
    api.get('/flashcards', { params }),
  create: (data: { front: string; back: string; subject: string; tags: string[] }) =>
    api.post('/flashcards', data),
}
