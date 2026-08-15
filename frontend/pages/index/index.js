// pages/index/index.js — 首页（入口 + 懒登录）
import { login } from '../../api/bill'
import { setToken, setUser } from '../../utils/storage'

Page({
  data: {},

  onLoad() {
    this.maybeLogin()
  },

  goRecognize() {
    wx.navigateTo({ url: '/pages/recognize/recognize' })
  },
  goBill() {
    wx.navigateTo({ url: '/pages/bill/list/list' })
  },
  goAnalysis() {
    wx.navigateTo({ url: '/pages/analysis/analysis' })
  },

  maybeLogin() {
    if (wx.getStorageSync('token')) return
    // 开发期：用 mock code 让后端直接通过
    // 真实环境：先 wx.login 拿 code 再发后端
    const code = 'mock-dev-code'
    login(code).then(res => {
      setToken(res.token)
      setUser(res)
      if (typeof getApp === 'function') {
        getApp().globalData.token = res.token
        getApp().globalData.user = res
      }
    }).catch(err => {
      console.warn('懒登录失败', err)
    })
  }
})