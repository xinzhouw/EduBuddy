import api from './index'

export const homeworkApi = {
  /** 获取批改历史列表 */
  getHistory: (params?: { page?: number; size?: number; subject?: string }) =>
    api.get('/homework/history', { params }),

  /** 获取单条批改详情 */
  getDetail: (gradingId: number) =>
    api.get(`/homework/history/${gradingId}`),

  /** 删除批改记录 */
  deleteGrading: (gradingId: number) =>
    api.delete(`/homework/history/${gradingId}`),

  /** 识别图片中的作业文字（预览用） */
  recognizeImage: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/homework/recognize', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

/**
 * 提交文本作业进行 AI 批改（流式 SSE）
 */
export function createTextGradingStream(
  data: { title: string; subject: string; grade_level?: string; content: string },
  token: string,
  onChunk: (delta: string) => void,
  onDone: (gradingId: number, score: number) => void,
  onError: (msg: string) => void,
): () => void {
  let aborted = false
  const controller = new AbortController()

  fetch('/api/homework/grade/text', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: '请求失败' }))
        onError(err.detail || '请求失败')
        return
      }
      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done || aborted) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const payload = JSON.parse(line.slice(6))
            if (payload.type === 'content') {
              onChunk(payload.delta)
            } else if (payload.type === 'done') {
              onDone(payload.grading_id, payload.score ?? 0)
            } else if (payload.type === 'error') {
              onError(payload.message || 'AI批改失败')
            }
          } catch {}
        }
      }
    })
    .catch((err) => {
      if (!aborted) onError(err.message || '网络错误')
    })

  return () => {
    aborted = true
    controller.abort()
  }
}

/**
 * 上传文件作业进行 AI 批改（流式 SSE）
 */
export function createFileGradingStream(
  formData: FormData,
  token: string,
  onChunk: (delta: string) => void,
  onDone: (gradingId: number, score: number) => void,
  onError: (msg: string) => void,
): () => void {
  let aborted = false
  const controller = new AbortController()

  fetch('/api/homework/grade/file', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: '请求失败' }))
        onError(err.detail || '请求失败')
        return
      }
      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done || aborted) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const payload = JSON.parse(line.slice(6))
            if (payload.type === 'content') {
              onChunk(payload.delta)
            } else if (payload.type === 'done') {
              onDone(payload.grading_id, payload.score ?? 0)
            } else if (payload.type === 'error') {
              onError(payload.message || 'AI批改失败')
            }
          } catch {}
        }
      }
    })
    .catch((err) => {
      if (!aborted) onError(err.message || '网络错误')
    })

  return () => {
    aborted = true
    controller.abort()
  }
}
