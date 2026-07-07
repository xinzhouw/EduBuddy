import api from './index'

export interface ImageInfo {
  id: string
  file_path: string
  original_filename: string
  file_size: number
  file_type: string
  created_at: string
}

/**
 * 获取会话中的所有图片（用户上传的试题图）。
 */
export function getSessionImages(sessionId: string) {
  return api.get(`/ai/chat/${sessionId}/images`)
}

/**
 * 删除单张图片（后端会校验属主权限）。
 */
export function deleteImage(imageId: string) {
  return api.delete(`/ai/chat/images/${imageId}`)
}

/**
 * 构建上传聊天消息用的 FormData。
 * 流式响应仍由视图层用 fetch 处理（axios 不支持浏览器端 SSE 读取），
 * 这里只负责统一组装 multipart 请求体。
 */
export function buildChatFormData(params: {
  sessionId?: string | null
  question: string
  subject: string
  images: File[]
}): FormData {
  const fd = new FormData()
  if (params.sessionId) fd.append('session_id', params.sessionId)
  fd.append('question', params.question)
  fd.append('subject', params.subject)
  params.images.forEach((file) => fd.append('images', file))
  return fd
}
