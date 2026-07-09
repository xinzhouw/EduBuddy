import api from './index'

export const updateUserLanguagePreference = async (language: 'zh' | 'en') => {
  const response = await api.patch('/users/preferences', { language })
  return response.data
}
