// app.js — 微信小程序启动入口
App({
  globalData: {
    apiBase: 'http://127.0.0.1:8000/api/v1',
    token: '',
    user: null
  },

  onLaunch() {
    const token = wx.getStorageSync('token') || ''
    const apiBase = wx.getStorageSync('apiBase') || 'http://127.0.0.1:8000/api/v1'
    this.globalData.token = token
    this.globalData.apiBase = apiBase
  }
})