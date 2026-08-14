import { request, uploadFile } from '@/utils/request'
import type { BillItem, BillListParams, BillListResp } from '@/types/bill'

export const login = (code: string) =>
  request<{ token: string; user_id: number }>('/user/login', { method: 'POST', data: { code } })

export const uploadImage = (filePath: string) =>
  uploadFile('/bill/upload', filePath)

export const recognizeImage = (image_id: string) =>
  request('/bill/recognize', { method: 'POST', data: { image_id } })

export const saveBill = (body: any) =>
  request('/bill/save', { method: 'POST', data: body })

export const listBills = (params: BillListParams): Promise<BillListResp> =>
  request<BillListResp>('/bill/list', { data: params })

export const getBillDetail = (id: number) =>
  request<BillItem>(`/bill/${id}`)

export const updateBill = (id: number, data: Partial<BillItem>) =>
  request<{ id: number }>(`/bill/${id}`, { method: 'PUT', data })

export const removeBill = (id: number) =>
  request<{ id: number }>(`/bill/${id}`, { method: 'DELETE' })
