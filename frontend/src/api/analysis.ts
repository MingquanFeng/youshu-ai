import { request } from '@/utils/request'
import type { MonthlyResp, DailyResp, CategoryResp } from '@/types/analysis'

export const monthlyAnalysis = (): Promise<MonthlyResp> =>
  request<MonthlyResp>('/analysis/monthly', { method: 'POST' })

export const dailyAnalysis = (days = 30): Promise<DailyResp> =>
  request<DailyResp>('/analysis/daily', { method: 'POST', data: { days } })

export const categoryAnalysis = (months = 1): Promise<CategoryResp> =>
  request<CategoryResp>('/analysis/category', { method: 'POST', data: { months } })
