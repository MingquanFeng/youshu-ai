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
    hasMore: false
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
      const mapped = res.items.map(b => ({
        ...b,
        bill_time_short: formatBillTime(b.bill_time),
        amount_str: Number(b.amount).toFixed(2)
      }))
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
  }
})