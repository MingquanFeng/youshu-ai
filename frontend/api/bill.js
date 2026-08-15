// api/bill.js — 账单相关 API 封装
import { request, uploadFile } from '../utils/request'

/** POST /user/login  body {code} → {token, user_id, nickname, avatar} */
export function login(code) {
  return request('/user/login', { method: 'POST', data: { code } })
}

/** POST /bill/upload  multipart → {image_id, image_url} */
export function uploadImage(filePath) {
  return uploadFile('/bill/upload', filePath)
}

/** POST /bill/recognize  body {image_id} → RecognizeResult */
export function recognizeImage(imageId) {
  return request('/bill/recognize', { method: 'POST', data: { image_id: imageId } })
}

/** POST /bill/save  body SaveBillIn → {id} */
export function saveBill(body) {
  return request('/bill/save', { method: 'POST', data: body })
}

/** GET /bill/list?page&size&category&date → BillListResp */
export function listBills(params) {
  return request('/bill/list', { method: 'GET', data: params })
}

/** GET /bill/{id} → BillItem */
export function getBillDetail(id) {
  return request('/bill/' + id, { method: 'GET' })
}

/** PUT /bill/{id}  body Partial<BillItem> → {id} */
export function updateBill(id, data) {
  return request('/bill/' + id, { method: 'PUT', data })
}

/** DELETE /bill/{id} → {id, deleted_at} */
export function removeBill(id) {
  return request('/bill/' + id, { method: 'DELETE' })
}