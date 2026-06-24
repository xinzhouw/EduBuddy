import api from '../api/index'

export interface PasswordValidationResult {
  score: number  // 0-100
  strength: 'weak' | 'medium' | 'strong'
  issues: string[]
}

export async function validatePasswordStrength(
  password: string
): Promise<PasswordValidationResult> {
  try {
    const response = await api.post('/auth/password/validate', { password })
    return response as unknown as PasswordValidationResult
  } catch (error) {
    // 网络错误时返回默认值（弱）
    console.error('Password validation failed:', error)
    return {
      score: 0,
      strength: 'weak',
      issues: ['无法验证密码强度，请检查网络']
    }
  }
}
