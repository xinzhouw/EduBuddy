export interface LoginErrorInfo {
  title: string
  message: string
  suggestion: string | null
}

export const LOGIN_ERROR_MESSAGES: Record<string, LoginErrorInfo> = {
  INVALID_CREDENTIALS: {
    title: '登录失败',
    message: '邮箱或密码错误，请检查后重试',
    suggestion: '如果忘记密码，可以尝试重置密码'
  },
  ACCOUNT_DISABLED: {
    title: '账户已禁用',
    message: '你的账户已被禁用，无法登录',
    suggestion: '请联系管理员或客服获取帮助'
  },
  ACCOUNT_LOCKED: {
    title: '账户已锁定',
    message: '由于多次登录失败，账户已暂时锁定',
    suggestion: '请 1 小时后重试，或通过邮箱重置密码'
  },
  RATE_LIMIT_EXCEEDED: {
    title: '登录过于频繁',
    message: '登录尝试过于频繁，请稍后再试',
    suggestion: null // 会显示倒计时
  },
  SERVER_ERROR: {
    title: '服务器错误',
    message: '服务器出现错误，请稍后重试',
    suggestion: '如果问题持续，请联系技术支持'
  },
  NETWORK_ERROR: {
    title: '网络连接失败',
    message: '无法连接到服务器，请检查网络',
    suggestion: '请检查网络连接后重试'
  }
}
