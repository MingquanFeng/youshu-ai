// pages/bill/list/list.js — 账单列表（分页 + 下拉 + 上拉）
import { listBills } from '../../../api/bill'
import { formatBillTime } from '../../../utils/format'

const PAGE_SIZE = 20

Page({
  data: {
    items: [],
    page: 1,
    total: 0,
    loading: false,
    refreshing: false,
    errorMsg: '',
    hasMore: false,
    tabs: [
      { icon: '▣', label: '首页', handler: 'goIndex' },
      { icon: '▤', label: '统计', handler: '' },
      { icon: '⊞', label: '资产', handler: 'goAnalysis' }
    ]
  },

  onLoad() {
    this.loadPage(1, 'reset')
  },

  onShow() {
    // 从详情/识别页返回时刷新
    if (this.data.items.length > 0) {
      this.loadPage(1, 'reset')
    }
  },

  onPullDownRefresh() {
    this.setData({ refreshing: true })
    this.loadPage(1, 'reset').then(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    if (this.data.loading || !this.data.hasMore || this.data.refreshing) return
    this.loadPage(this.data.page + 1, 'append')
  },

  async loadPage(p, mode) {
    if (this.data.loading) return
    this.setData({ loading: true, errorMsg: '' })
    try {
      const res = await listBills({ page: p, size: PAGE_SIZE })
      const mapped = res.items.map(b => {
        const cat = (b.category || '其他')
        const isIncome = b.amount > 0 || cat === '工资' || cat === 'income'
        return {
          ...b,
          bill_time_short: formatBillTime(b.bill_time),
          amount_str: Number(b.amount).toFixed(2),
          amount_sign: isIncome ? '+¥ ' + Number(b.amount).toFixed(2) : '−¥ ' + Number(b.amount).toFixed(2),
          amount_color: isIncome ? 'color: var(--color-success);' : '',
          icon_char: cat.charAt(0),
          icon_bg: 'var(--cat-' + ({ '餐饮': 'food', '交通': 'transport', '购物': 'shop', '居家': 'home', '娱乐': 'fun', '医疗': 'medical', '工资': 'income' }[cat] || 'other') + '-soft);'
        }
      })
      const merged = mode === 'reset' ? mapped : this.data.items.concat(mapped)
      this.setData({
        items: merged,
        page: res.page,
        total: res.total,
        hasMore: merged.length < res.total
      })
    } catch (e) {
      this.setData({ errorMsg: (e && e.message) || '加载失败，请稍后重试' })
    } finally {
      this.setData({ loading: false, refreshing: false })
    }
  },

  onItemTap(e) {
    const { item } = e.currentTarget.dataset
    wx.navigateTo({ url: '/pages/bill/detail/detail?id=' + item.id })
  },

  goRecognize() {
    wx.navigateTo({ url: '/pages/recognize/recognize' })
  },
  goIndex() {
    wx.reLaunch({ url: '/pages/index/index' })
  },
  goBill() {
    wx.reLaunch({ url: '/pages/bill/list/list' })
  },
  goAnalysis() {
    wx.navigateTo({ url: '/pages/analysis/analysis' })
  },

  // 组件事件分发
  onTabSelect(e) {
    const { handler } = e.detail || {}
    if (handler && typeof this[handler] === 'function') this[handler]()
  },
  onFabTap(e) {
    const { handler } = e.detail || {}
    if (handler && typeof this[handler] === 'function') this[handler]()
  },
  // txn-row 通过 dataset 传 item
  onTxnTapWithItem(e) {
    const { item } = e.currentTarget.dataset || {}
    if (item) wx.navigateTo({ url: '/pages/bill/detail/detail?id=' + item.id })
  }
})