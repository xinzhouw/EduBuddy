import api from './index'

export const adviceApi = {
  /** 获取今日建议（首次登录触发生成） */
  getToday: () => api.get('/advice/today'),

  /** 记录建议执行行为 */
  recordAction: (adviceId: number, adviceItemId: string) =>
    api.post(`/advice/${adviceId}/action`, { advice_item_id: adviceItemId }),

  /** 获取近7天建议历史 */
  getHistory: () => api.get('/advice/history'),
}
