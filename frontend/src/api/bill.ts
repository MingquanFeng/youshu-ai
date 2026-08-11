import { request, uploadFile } from '@/utils/request'

export const login = (code: string) =>
  request<{ token: string; user_id: number }>('/user/login', { method: 'POST', data: { code } })

export const uploadImage = (filePath: string) =>
  uploadFile('/bill/upload', filePath)

export const recognizeImage = (image_id: string) =>
  request('/bill/recognize', { method: 'POST', data: { image_id } })

export const saveBill = (body: any) =>
  request('/bill/save', { method: 'POST', data: body })

export const listBills = (params: { page: number; size: number; category?: string; date?: string }) =>
  request('/bill/list', { data: params })
