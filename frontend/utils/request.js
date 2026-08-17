// utils/request.js — Promise 化的 wx.request + 自动 token + 错误码处理

// === 开发期 API base 配置 ===
// 真机的 127.0.0.1 是手机本身, 必须用电脑 LAN IP
// 换 wifi / 换电脑要同步改这里; 生产 build 时换成真实域名
const DEV_LOCAL  = 'http://127.0.0.1:8000/api/v1'
const DEV_LAN_IP = 'http://192.168.18.204:8000/api/v1'

function getDefaultBase() {
  try {
    const sys = wx.getSystemInfoSync()
    // 开发者工具模拟器 → 用本地 loopback
    if (sys && sys.platform === 'devtools') return DEV_LOCAL
  } catch (e) { /* 旧基础库或非小程序环境 */ }
  // 真机 (iOS / Android / macOS / Windows) → 用 LAN IP
  return DEV_LAN_IP
}

function getToken() {
  try { return wx.getStorageSync('token') || '' } catch (e) { return '' }
}

function clearToken() {
  try { wx.removeStorageSync('token') } catch (e) {}
}

function getApiBase() {
  // 优先级: storage > globalData > 平台默认
  try {
    return wx.getStorageSync('apiBase') || getApp().globalData.apiBase || getDefaultBase()
  } catch (e) {
    return getDefaultBase()
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