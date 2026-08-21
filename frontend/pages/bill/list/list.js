// pages/bill/list/list.js — 账单列表（分页 + 下拉 + 上拉 + 当月统计）
import { listBills } from '../../../api/bill';
import { monthlyAnalysis } from '../../../api/analysis';
import { formatBillTime } from '../../../utils/format';

const PAGE_SIZE = 20;

function monthLabel(d = new Date()) {
  return `${d.getMonth() + 1}月`;
}

Page({
  data: {
    items: [],
    page: 1,
    total: 0,
    loading: false,
    refreshing: false,
    errorMsg: '',
    hasMore: false,
    monthLabel: monthLabel(),
    monthly: { expense_str: '0.00', income_str: '0.00' },
    tabs: [
      { icon: '▣', label: '首页', handler: 'goIndex' },
      { icon: '▤', label: '统计', handler: '' },
      { icon: '⊞', label: '资产', handler: 'goAnalysis' }
    ]
  },

  onLoad() {
    this.loadAll();
  },

  onShow() {
    // 每次进入都刷新 (删除/识别页保存后跳回, 本地 data 可能是旧的, 必须重新拉)
    this.loadAll();
  },

  onPullDownRefresh() {
    this.setData({ refreshing: true });
    this.loadAll().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    if (this.data.loading || !this.data.hasMore || this.data.refreshing) return;
    this.loadPage(this.data.page + 1, 'append');
  },

  async loadAll() {
    // 并发拉本月统计 + 第一页流水
    this.setData({ loading: true, errorMsg: '' });
    try {
      const [monthly, list] = await Promise.all([
        monthlyAnalysis(),
        listBills({ page: 1, size: PAGE_SIZE })
      ]);
      const mapped = (list.items || []).map((b) => this._mapItem(b));
      this.setData({
        monthly: {
          expense_str: Number(monthly.expense || 0).toFixed(2),
          income_str: Number(monthly.income || 0).toFixed(2)
        },
        items: mapped,
        page: list.page || 1,
        total: list.total || 0,
        hasMore: mapped.length < (list.total || 0),
        monthLabel: monthLabel(),
        loading: false
      });
    } catch (e) {
      this.setData({
        loading: false,
        errorMsg: (e && e.message) || '加载失败, 请下拉重试'
      });
    }
  },

  async loadPage(p, mode) {
    if (this.data.loading) return;
    this.setData({ loading: true, errorMsg: '' });
    try {
      const res = await listBills({ page: p, size: PAGE_SIZE });
      const mapped = (res.items || []).map((b) => this._mapItem(b));
      const merged = mode === 'append' ? this.data.items.concat(mapped) : mapped;
      this.setData({
        items: merged,
        page: res.page,
        total: res.total,
        hasMore: merged.length < (res.total || 0)
      });
    } catch (e) {
      this.setData({ errorMsg: (e && e.message) || '加载失败, 请稍后重试' });
    } finally {
      this.setData({ loading: false, refreshing: false });
    }
  },

  _mapItem(b) {
    // amount: 正数=收入, 负数=支出.  按符号直接显示, 不再硬判 cat
    const CAT_KEY = {
      餐饮: 'food',
      交通: 'transport',
      购物: 'shop',
      居家: 'home',
      娱乐: 'fun',
      医疗: 'medical',
      工资: 'income'
    };
    const cat = b.category || '其他';
    const amt = Number(b.amount);
    return {
      ...b,
      bill_time_short: formatBillTime(b.bill_time),
      amount_str: Math.abs(amt).toFixed(2),
      amount_sign: amt >= 0 ? '+¥ ' + Math.abs(amt).toFixed(2) : '−¥ ' + Math.abs(amt).toFixed(2),
      amount_color: amt >= 0 ? 'color: var(--color-success);' : '',
      icon_char: cat.charAt(0),
      icon_bg: 'var(--cat-' + (CAT_KEY[cat] || 'other') + '-soft);'
    };
  },

  onItemTap(e) {
    const { item } = e.currentTarget.dataset;
    wx.navigateTo({ url: '/pages/bill/detail/detail?id=' + item.id });
  },

  goRecognize() {
    wx.navigateTo({ url: '/pages/recognize/recognize' });
  },
  goIndex() {
    wx.reLaunch({ url: '/pages/index/index' });
  },
  goBill() {
    wx.reLaunch({ url: '/pages/bill/list/list' });
  },
  goAnalysis() {
    wx.navigateTo({ url: '/pages/analysis/analysis' });
  },

  // 组件事件分发
  onTabSelect(e) {
    const { handler } = e.detail || {};
    if (handler && typeof this[handler] === 'function') this[handler]();
  },
  onFabTap(e) {
    const { handler } = e.detail || {};
    if (handler && typeof this[handler] === 'function') this[handler]();
  },
  // txn-row 通过 dataset 传 item
  onTxnTapWithItem(e) {
    const { item } = e.currentTarget.dataset || {};
    if (item) wx.navigateTo({ url: '/pages/bill/detail/detail?id=' + item.id });
  }
});
