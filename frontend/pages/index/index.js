// pages/index/index.js — 首页（入口 + 懒登录）
import { login } from '../../api/bill'
import { setToken, setUser } from '../../utils/storage'

Page({
  data: {
    tabs: [
      { icon: '▣', label: '首页', handler: '' },
      { icon: '▤', label: '统计', handler: 'goBill' },
      { icon: '⊞', label: '资产', handler: 'goAnalysis' }
    ]
  },

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
  goIndex() {
    wx.reLaunch({ url: '/pages/index/index' })
  },

  // 组件事件分发: 子组件传 handler 名, 这里统一调用
  onTabSelect(e) {
    const { handler } = e.detail || {}
    if (handler && typeof this[handler] === 'function') this[handler]()
  },
  onFabTap(e) {
    const { handler } = e.detail || {}
    if (handler && typeof this[handler] === 'function') this[handler]()
  },
  onTxnTap(e) {
    const { handler } = e.detail || {}
    if (handler && typeof this[handler] === 'function') this[handler]()
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