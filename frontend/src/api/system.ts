import api from './index'

export const systemApi = {
  /**
   * 获取系统信息（包括当前 LLM 模型）
   */
  getSystemInfo() {
    return api.get('/system/info')
  },
}
