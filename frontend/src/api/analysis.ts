import { request } from '@/utils/request'

export const monthlyAnalysis = () =>
  request('/analysis/monthly', { method: 'POST' })
