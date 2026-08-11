/** 全局 API 基础配置。 */
export const BASE_URL = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api/v1'

export interface ApiResp<T = any> {
  code: number
  message: string
  data: T
}

const TOKEN_KEY = 'token'

export const setToken = (t: string) => uni.setStorageSync(TOKEN_KEY, t)
export const getToken = () => uni.getStorageSync(TOKEN_KEY) as string

export async function request<T = any>(path: string, opts: any = {}): Promise<T> {
  const token = getToken()
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + path,
      method: opts.method || 'GET',
      data: opts.data,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(opts.header || {})
      },
      success: (res: any) => {
        const body = res.data as ApiResp<T>
        if (body.code === 0) resolve(body.data)
        else if (body.code === 40100) {
          uni.removeStorageSync(TOKEN_KEY)
          uni.showToast({ title: '请重新登录', icon: 'none' })
          reject(body)
        } else reject(body)
      },
      fail: reject
    })
  })
}

export function uploadFile(path: string, filePath: string, name = 'file') {
  const token = getToken()
  return new Promise<any>((resolve, reject) => {
    uni.uploadFile({
      url: BASE_URL + path,
      filePath,
      name,
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success: (res: any) => {
        const body = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
        if (body.code === 0) resolve(body.data)
        else reject(body)
      },
      fail: reject
    })
  })
}
