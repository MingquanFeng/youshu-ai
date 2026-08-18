// api/analysis.js — 消费分析 API
import { request } from '../utils/request';

/** POST /analysis/monthly → MonthlyResp */
export function monthlyAnalysis() {
  return request('/analysis/monthly', { method: 'POST' });
}

/** POST /analysis/daily  body {days} → DailyResp */
export function dailyAnalysis(days = 30) {
  return request('/analysis/daily', { method: 'POST', data: { days } });
}

/** POST /analysis/category  body {months} → CategoryResp */
export function categoryAnalysis(months = 1) {
  return request('/analysis/category', { method: 'POST', data: { months } });
}
