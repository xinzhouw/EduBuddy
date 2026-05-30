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

  /**
   * 从图片或文档中提取题目学科和知识点
   * 支持：JPG / PNG / GIF / WebP / PDF / DOCX
   */
  extractTopicFromFile: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/quiz/extract-topic', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /**
   * 从图片中识别手写/打印的答案内容
   * 支持：JPG / PNG / GIF / WebP
   * questionContent 可选，传入题目原文可提升识别准确性
   */
  extractAnswerFromFile: (file: File, questionContent: string = '') => {
    const form = new FormData()
    form.append('file', file)
    form.append('question_content', questionContent)
    return api.post('/quiz/extract-answer', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
