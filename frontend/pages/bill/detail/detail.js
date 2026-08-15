// pages/bill/detail/detail.js — 账单详情 + 编辑 + 删除
import { getBillDetail, removeBill, updateBill } from '../../../api/bill'
import { formatBillTime } from '../../../utils/format'

Page({
  data: {
    bill: null,
    form: { amount: 0, category: '', merchant: '', remark: '' },
    loading: false,
    saving: false,
    notFound: false,
    errorMsg: '',
    billId: 0
  },

  onLoad(options) {
    const id = Number(options.id)
    if (!id) {
      this.setData({ notFound: true })
      return
    }
    this.setData({ billId: id })
    this.fetchDetail()
  },

  async fetchDetail() {
    this.setData({ loading: true, errorMsg: '' })
    try {
      const res = await getBillDetail(this.data.billId)
      this.setData({
        bill: {
          ...res,
          bill_time_short: formatBillTime(res.bill_time),
          amount_str: Number(res.amount).toFixed(2)
        },
        form: {
          amount: res.amount,
          category: res.category,
          merchant: res.merchant,
          remark: res.remark
        }
      })
    } catch (e) {
      if (e && e.code === 40400) {
        this.setData({ notFound: true })
      } else {
        this.setData({ errorMsg: (e && e.message) || '加载失败' })
      }
    } finally {
      this.setData({ loading: false })
    }
  },

  reload() {
    this.fetchDetail()
  },

  onAmountInput(e) {
    this.setData({ 'form.amount': Number(e.detail.value) })
  },
  onFieldInput(e) {
    const { field } = e.currentTarget.dataset
    this.setData({ ['form.' + field]: e.detail.value })
  },

  async save() {
    if (this.data.saving) return
    if (!this.data.form.amount || this.data.form.amount <= 0) {
      wx.showToast({ title: '请输入有效金额', icon: 'none' })
      return
    }
    this.setData({ saving: true })
    try {
      await updateBill(this.data.billId, this.data.form)
      wx.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 600)
    } catch (e) {
      wx.showToast({ title: (e && e.message) || '保存失败', icon: 'none' })
    } finally {
      this.setData({ saving: false })
    }
  },

  confirmDelete() {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条账单吗？',
      success: (res) => {
        if (!res.confirm) return
        this.doDelete()
      }
    })
  },

  async doDelete() {
    this.setData({ saving: true })
    try {
      await removeBill(this.data.billId)
      wx.showToast({ title: '已删除', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 600)
    } catch (e) {
      wx.showToast({ title: (e && e.message) || '删除失败', icon: 'none' })
    } finally {
      this.setData({ saving: false })
    }
  },

  goBack() {
    wx.navigateBack()
  }
})