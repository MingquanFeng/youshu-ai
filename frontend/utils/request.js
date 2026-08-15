// utils/request.js — Promise 化的 wx.request + 自动 token + 错误码处理
const DEFAULT_BASE = 'http://127.0.0.1:8000/api/v1'

function getToken() {
  try { return wx.getStorageSync('token') || '' } catch (e) { return '' }
}

function clearToken() {
  try { wx.removeStorageSync('token') } catch (e) {}
}

function getApiBase() {
  try {
    return wx.getStorageSync('apiBase') || getApp().globalData.apiBase || DEFAULT_BASE
  } catch (e) {
    return DEFAULT_BASE
  }
}

export function request(path, opts = {}) {
  const baseUrl = opts.baseUrl || getApiBase()
  const token = getToken()
  return new Promise((resolve, reject) => {
    wx.request({
      url: baseUrl + path,
      method: opts.method || 'GET',
      data: opts.data || {},
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: 'Bearer ' + token } : {}),
        ...(opts.header || {})
      },
      success(res) {
        const body = res.data || {}
        if (body.code === 0) {
          resolve(body.data)
        } else if (body.code === 40100) {
          clearToken()
          wx.showToast({ title: '请重新登录', icon: 'none' })
          reject(body)
        } else {
          wx.showToast({ title: body.message || '请求失败', icon: 'none' })
          reject(body)
        }
      },
      fail(err) {
        wx.showToast({ title: '网络异常', icon: 'none' })
        reject(err)
      }
    })
  })
}

export function uploadFile(path, filePath, name = 'file') {
  const baseUrl = getApiBase()
  const token = getToken()
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: baseUrl + path,
      filePath,
      name,
      header: token ? { Authorization: 'Bearer ' + token } : {},
      success(res) {
        let body = res.data
        if (typeof body === 'string') {
          try { body = JSON.parse(body) } catch (e) {
            return reject({ message: '响应解析失败' })
          }
        }
        if (body.code === 0) resolve(body.data)
        else if (body.code === 40100) {
          clearToken()
          wx.showToast({ title: '请重新登录', icon: 'none' })
          reject(body)
        } else {
          wx.showToast({ title: body.message || '上传失败', icon: 'none' })
          reject(body)
        }
      },
      fail(err) {
        wx.showToast({ title: '上传失败', icon: 'none' })
        reject(err)
      }
    })
  })
}

export function chooseImage(opts = {}) {
  return new Promise((resolve, reject) => {
    wx.chooseImage({
      count: opts.count || 1,
      sizeType: opts.sizeType || ['compressed'],
      sourceType: opts.sourceType || ['album', 'camera'],
      success(res) { resolve(res.tempFilePaths) },
      fail(rej) { reject(rej) }
    })
  })
}

export { getToken, clearToken, getApiBase }