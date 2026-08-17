// pages/analysis/analysis.js — 消费分析（无图表版）
import { monthlyAnalysis, dailyAnalysis, categoryAnalysis } from '../../api/analysis'

Page({
  data: {
    monthly: { total: 0, top_category: '', advice: '', total_str: '0.00' },
    categories: [],
    daily: [],
    loading: true,
    tabs: [
      { icon: '▣', label: '首页', handler: 'goIndex' },
      { icon: '▤', label: '统计', handler: 'goBill' },
      { icon: '⊞', label: '资产', handler: '' }
    ]
  },

  onShow() {
    this.loadAll()
  },

  async loadAll() {
    this.setData({ loading: true })
    try {
      const [mRes, cRes, dRes] = await Promise.allSettled([
        monthlyAnalysis(),
        categoryAnalysis(1),
        dailyAnalysis(30)
      ])

      const failedCount = [mRes, cRes, dRes].filter(r => r.status === 'rejected').length
      if (failedCount > 0) {
        wx.showToast({ title: '分析加载失败', icon: 'none' })
      }

      const monthly = mRes.status === 'fulfilled' ? mRes.value : null
      const category = cRes.status === 'fulfilled' ? cRes.value : null
      const daily = dRes.status === 'fulfilled' ? dRes.value : null

      const catKeyMap = { '餐饮': 'food', '交通': 'transport', '购物': 'shop', '居家': 'home', '娱乐': 'fun', '医疗': 'medical', '工资': 'income' }
      const categories = (category && category.categories || []).map(c => ({
        ...c,
        amount_str: Number(c.amount).toFixed(2),
        percent_str: (Number(c.percent) * 100).toFixed(1) + '%',
        bar_width: Math.max(0, Math.min(100, Number(c.percent) * 100)) + '%',
        category_key: catKeyMap[c.category] || 'other'
      }))

      const dailyRaw = (daily && daily.days || [])
      const maxDaily = dailyRaw.reduce((m, d) => Math.max(m, Number(d.total) || 0), 0)
      const dailyList = dailyRaw.map(d => ({
        ...d,
        date_short: d.date.slice(5),
        total_str: Number(d.total).toFixed(2),
        bar_width: maxDaily > 0 ? Math.max(0, Math.min(100, (Number(d.total) / maxDaily) * 100)) + '%' : '0%'
      }))

      this.setData({
        monthly: {
          total: monthly ? monthly.total : 0,
          top_category: monthly ? monthly.top_category : '',
          advice: monthly ? monthly.advice : '',
          total_str: monthly ? Number(monthly.total).toFixed(2) : '0.00'
        },
        categories,
        daily: dailyList,
        loading: false
      })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  goIndex() {
    wx.reLaunch({ url: '/pages/index/index' })
  },
  goBill() {
    wx.reLaunch({ url: '/pages/bill/list/list' })
  },
  goAnalysis() {
    wx.reLaunch({ url: '/pages/analysis/analysis' })
  },
  goRecognize() {
    wx.navigateTo({ url: '/pages/recognize/recognize' })
  },

  // 组件事件分发
  onTabSelect(e) {
    const { handler } = e.detail || {}
    if (handler && typeof this[handler] === 'function') this[handler]()
  }
})