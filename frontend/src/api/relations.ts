import api from './index'

export const relationsApi = {
  /** 学生生成绑定码（有效期24小时） */
  createBindCode: (relation_type: 'teacher' | 'parent') =>
    api.post('/relations/bind-code', { relation_type }),

  /** 教师/家长使用绑定码绑定学生 */
  bind: (code: string, relation_type: 'teacher' | 'parent') =>
    api.post('/relations/bind', { code, relation_type }),

  /** 获取关联学生列表（教师/家长） */
  getStudents: () => api.get('/relations/students'),

  /** 获取关联的教师/家长列表（学生） */
  getObservers: () => api.get('/relations/observers'),

  /** 解除关联 */
  removeRelation: (relation_id: number) => api.delete(`/relations/${relation_id}`),

  /** 教师创建班级 */
  createClass: (name: string) => api.post('/relations/classes', { name }),

  /** 获取我的班级列表（教师） */
  getClasses: () => api.get('/relations/classes'),

  /** 学生通过邀请码加入班级 */
  joinClass: (invite_code: string) => api.post('/relations/classes/join', { invite_code }),
}

export const monitorApi = {
  /** 获取关联学生列表及摘要（教师/家长） */
  getStudentsSummary: () => api.get('/monitor/students'),

  /** 获取学生学习概览 */
  getStudentOverview: (student_id: number) =>
    api.get(`/monitor/students/${student_id}/overview`),

  /** 获取学生详细统计 */
  getStudentStats: (student_id: number, period: string = 'week') =>
    api.get(`/monitor/students/${student_id}/stats`, { params: { period } }),

  /** 获取学生当前学习计划（只读） */
  getStudentPlan: (student_id: number) =>
    api.get(`/monitor/students/${student_id}/plan`),
}
