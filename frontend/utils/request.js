// utils/request.js — Promise 化的 wx.request + 自动 token + 错误码处理

// === API base 配置 ===
// 开发者工具模拟器 → 本地 loopback
// 真机 / 发布 → 云服务器公网 IP
// 换云服务器 IP 改这里; 生产正式上线建议换成 https://api.example.com 域名
const DEV_LOCAL = 'http://127.0.0.1:8000/api/v1';
const PROD_BASE = 'http://82.156.173.21/api/v1';

function getDefaultBase() {
  try {
    const sys = wx.getSystemInfoSync();
    // 开发者工具模拟器 → 用本地 loopback
    if (sys && sys.platform === 'devtools') return DEV_LOCAL;
  } catch (e) {
    /* 旧基础库或非小程序环境 */
  }
  // 真机 (iOS / Android / macOS / Windows) → 云服务器
  return PROD_BASE;
}

function getToken() {
  try {
    return wx.getStorageSync('token') || '';
  } catch (e) {
    return '';
  }
}

function clearToken() {
  try {
    wx.removeStorageSync('token');
  } catch (e) {}
}

function getApiBase() {
  // 优先级: storage > globalData > 平台默认
  try {
    return wx.getStorageSync('apiBase') || getApp().globalData.apiBase || getDefaultBase();
  } catch (e) {
    return getDefaultBase();
  }
}

// 在调 wx.request 前确保 token 已就绪 (await app.maybeLogin)
// 解决 onLaunch 异步触发懒登录 vs onLoad 立即拉数据的 race
async function ensureLogin() {
  if (wx.getStorageSync('token')) return;
  try {
    const app = getApp();
    if (app && typeof app.maybeLogin === 'function') {
      await app.maybeLogin();
    }
  } catch (e) {
    /* 旧基础库或非小程序环境 */
  }
}

export function request(path, opts = {}) {
  const baseUrl = opts.baseUrl || getApiBase();
  const token = getToken();
  return new Promise((resolve, reject) => {
    ensureLogin().then(() => {
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
          const body = res.data || {};
          if (body.code === 0) {
            resolve(body.data);
          } else if (body.code === 40100) {
            clearToken();
            wx.showToast({ title: '请重新登录', icon: 'none' });
            reject(body);
          } else {
            wx.showToast({ title: body.message || '请求失败', icon: 'none' });
            reject(body);
          }
        },
        fail(err) {
          wx.showToast({ title: '网络异常', icon: 'none' });
          reject(err);
        }
      });
    });
  });
}

export function uploadFile(path, filePath, name = 'file') {
  const baseUrl = getApiBase();
  const token = getToken();
  return new Promise((resolve, reject) => {
    ensureLogin().then(() => {
      wx.uploadFile({
        url: baseUrl + path,
        filePath,
        name,
        header: token ? { Authorization: 'Bearer ' + token } : {},
        success(res) {
          let body = res.data;
          if (typeof body === 'string') {
            try {
              body = JSON.parse(body);
            } catch (e) {
              return reject({ message: '响应解析失败' });
            }
          }
          if (body.code === 0) resolve(body.data);
          else if (body.code === 40100) {
            clearToken();
            wx.showToast({ title: '请重新登录', icon: 'none' });
            reject(body);
          } else {
            wx.showToast({ title: body.message || '上传失败', icon: 'none' });
            reject(body);
          }
        },
        fail(err) {
          wx.showToast({ title: '上传失败', icon: 'none' });
          reject(err);
        }
      });
    });
  });
}

export function chooseImage(opts = {}) {
  return new Promise((resolve, reject) => {
    wx.chooseImage({
      count: opts.count || 1,
      sizeType: opts.sizeType || ['compressed'],
      sourceType: opts.sourceType || ['album', 'camera'],
      success(res) {
        resolve(res.tempFilePaths);
      },
      fail(rej) {
        reject(rej);
      }
    });
  });
}

export { getToken, clearToken, getApiBase };
