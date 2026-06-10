import api from './index'

export const planApi = {
  generate: (data: { subjects: string[]; exam_date: string; daily_hours: number; weak_subjects: string[] }) =>
    api.post('/plan/generate', data),
  getCurrent: () => api.get('/plan/current'),
  getToday: () => api.get('/plan/today'),
  getTaskDetail: (taskId: number) => api.get(`/plan/tasks/${taskId}`),
  markTaskDone: (taskId: number, is_done: boolean) =>
    api.put(`/plan/tasks/${taskId}/done`, { is_done }),
  recordPomodoro: (data: { subject?: string; duration_minutes: number; completed: boolean }) =>
    api.post('/plan/pomodoro', data),
}

/**
 * 为今日所有任务批量生成 AI 学习内容（SSE 流式）
 * 每天第一次登录时调用
 */
export function createTodayGenerateStream(
  token: string,
  onProgress: (info: { current: number; total: number; task_id: number; subject: string; topic: string }) => void,
  onTaskDelta: (taskId: number, delta: string) => void,
  onTaskDone: (taskId: number) => void,
  onAllDone: (total: number) => void,
  onError: (taskId: number | null, msg: string) => void,
): () => void {
  let aborted = false
  const controller = new AbortController()

  fetch('/api/plan/today/generate-content', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: '请求失败' }))
        onError(null, err.detail || '请求失败')
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
            if (payload.progress) {
              onProgress(payload.progress)
            } else if (payload.task_id !== undefined && payload.delta !== undefined) {
              onTaskDelta(payload.task_id, payload.delta)
            } else if (payload.task_id !== undefined && payload.task_done) {
              onTaskDone(payload.task_id)
            } else if (payload.task_id !== undefined && payload.error) {
              onError(payload.task_id, payload.error)
            } else if (payload.done) {
              onAllDone(payload.total ?? 0)
            } else if (payload.message) {
              // 已生成完毕
              onAllDone(0)
            }
          } catch {}
        }
      }
    })
    .catch((err) => {
      if (!aborted) onError(null, err.message || '网络错误')
    })

  return () => {
    aborted = true
    controller.abort()
  }
}

/**
 * AI 生成任务学习内容（流式 SSE）
 */
export function createTaskContentStream(
  taskId: number,
  token: string,
  onChunk: (delta: string) => void,
  onDone: () => void,
  onError: (msg: string) => void,
): () => void {
  let aborted = false
  const controller = new AbortController()

  fetch(`/api/plan/tasks/${taskId}/generate-content`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
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
            if (payload.delta) {
              onChunk(payload.delta)
            } else if (payload.done) {
              onDone()
            } else if (payload.error) {
              onError(payload.error)
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
 * AI 生成任务练习题（流式 SSE）
 */
export function createTaskQuizStream(
  taskId: number,
  token: string,
  onChunk: (delta: string) => void,
  onDone: () => void,
  onError: (msg: string) => void,
): () => void {
  let aborted = false
  const controller = new AbortController()

  fetch(`/api/plan/tasks/${taskId}/generate-quiz`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
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
            if (payload.delta) {
              onChunk(payload.delta)
            } else if (payload.done) {
              onDone()
            } else if (payload.error) {
              onError(payload.error)
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
 * 提交练习题答案并由 AI 评判（流式 SSE）
 */
export function createSubmitQuizStream(
  taskId: number,
  token: string,
  answers: Record<string, string>,
  onChunk: (delta: string) => void,
  onDone: (score: number, passed: boolean) => void,
  onError: (msg: string) => void,
): () => void {
  let aborted = false
  const controller = new AbortController()

  const formData = new FormData()
  formData.append('answers', JSON.stringify(answers))

  fetch(`/api/plan/tasks/${taskId}/submit-quiz`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
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
            if (payload.delta) {
              onChunk(payload.delta)
            } else if (payload.done) {
              onDone(payload.score ?? 0, payload.passed ?? false)
            } else if (payload.error) {
              onError(payload.error)
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
 * 提交学习成果并由 AI 评判（流式 SSE）
 */
export function createSubmitStream(
  taskId: number,
  token: string,
  submissionText: string,
  imageFile: File | null,
  onChunk: (delta: string) => void,
  onDone: (score: number, passed: boolean) => void,
  onError: (msg: string) => void,
): () => void {
  let aborted = false
  const controller = new AbortController()

  const formData = new FormData()
  formData.append('submission_text', submissionText)
  if (imageFile) formData.append('file', imageFile)

  fetch(`/api/plan/tasks/${taskId}/submit`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
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
            if (payload.delta) {
              onChunk(payload.delta)
            } else if (payload.done) {
              onDone(payload.score ?? 0, payload.passed ?? false)
            } else if (payload.error) {
              onError(payload.error)
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
