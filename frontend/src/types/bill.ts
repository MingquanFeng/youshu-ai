export interface BillItem {
  id: number
  amount: number
  category: string
  merchant: string
  pay_method: string
  bill_time: string
  remark: string
  source: 'image_ai' | 'manual' | string
  ai_score: number
}

export interface BillListParams {
  page: number
  size: number
  category?: string
  date?: string
}

export interface BillListResp {
  total: number
  page: number
  size: number
  items: BillItem[]
}
