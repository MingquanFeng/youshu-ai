export interface DailyItem {
  date: string
  total: number
}

export interface DailyResp {
  days: DailyItem[]
}

export interface CategoryItem {
  category: string
  amount: number
  percent: number
}

export interface CategoryResp {
  categories: CategoryItem[]
  total: number
}

export interface MonthlyResp {
  total: number
  top_category: string
  advice: string
}
