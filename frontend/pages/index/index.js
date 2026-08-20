// pages/index/index.js — 首页（懒登录 + 本月剩余 + 今天流水）
import { listBills } from '../../api/bill';
import { monthlyAnalysis } from '../../api/analysis';

// 分类中文 → key (icon 颜色, 与 detail.js 保持一致)
const CAT_KEY_MAP = {
  餐饮: 'food',
  交通: 'transport',
  购物: 'shop',
  居家: 'home',
  娱乐: 'fun',
  医疗: 'medical',
  工资: 'income'
};

// 简单日期格式化
function todayStr() {
  const d = new Date();
  return d.toISOString().slice(0, 10); // YYYY-MM-DD
}

function dateLabel(d = new Date()) {
  const m = d.getMonth() + 1;
  const day = d.getDate();
  const week = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()];
  return `${m}月${day}日 星期${week}`;
}

function greeting(d = new Date()) {
  const h = d.getHours();
  if (h < 6) return '凌晨好';
  if (h < 12) return '早上好';
  if (h < 14) return '中午好';
  if (h < 18) return '下午好';
  return '晚上好';
}

// 把后端 list item 转成 txn-row props
function toTxnProps(item) {
  return {
    iconBg: `var(--cat-${CAT_KEY_MAP[item.category] || 'other'}-soft)`,
    iconChar: (item.category || '?').charAt(0),
    title: item.merchant || item.category || '—',
    sub: `${(item.bill_time_short || '').slice(5, 16)} · ${item.pay_method || '未指定'}`,
    amount: item.amount_sign,
    amountStyle: item.amount_color || '',
    _id: item.id
  };
}

Page({
  data: {
    tabs: [
      { icon: '▣', label: '首页', handler: '' },
      { icon: '▤', label: '统计', handler: 'goBill' },
      { icon: '⊞', label: '资产', handler: 'goAnalysis' }
    ],
    greeting: greeting(),
    todayLabel: dateLabel(),
    monthly: {
      income_str: '0.00',
      expense_str: '0.00',
      remain_str: '0.00',
      bar_pct: 0
    },
    today: [],
    loading: false,
    errorMsg: ''
  },

  onLoad() {
    this.fetchAll();
  },

  onShow() {
    // 每次进入首页刷新 (识别页保存后跳回首页能即时看到)
    this.fetchAll();
  },

  onPullDownRefresh() {
    this.fetchAll().finally(() => wx.stopPullDownRefresh());
  },

  async fetchAll() {
    this.setData({ loading: true, errorMsg: '' });
    try {
      const [monthly, today] = await Promise.all([
        monthlyAnalysis(),
        listBills({ date: todayStr(), size: 10 })
      ]);

      // 后端 income(正) expense(正绝对值) total(净支出=expense-income)
      const income = Number(monthly.income || 0);
      const expense = Number(monthly.expense || 0);
      // 进度条: 支出 / 收入 (但不能除0)
      const barPct = income > 0 ? Math.round((expense / income) * 100) : 0;

      // 今天流水
      const txns = (today.items || []).map(toTxnProps);

      this.setData({
        monthly: {
          income_str: income.toFixed(2),
          expense_str: expense.toFixed(2),
          remain_str: (income - expense).toFixed(2),
          bar_pct: barPct
        },
        today: txns,
        greeting: greeting(),
        todayLabel: dateLabel(),
        loading: false
      });
    } catch (e) {
      this.setData({
        loading: false,
        errorMsg: (e && e.message) || '加载失败, 请下拉重试'
      });
    }
  },

  goRecognize() {
    wx.navigateTo({ url: '/pages/recognize/recognize' });
  },
  goBill() {
    wx.navigateTo({ url: '/pages/bill/list/list' });
  },
  goAnalysis() {
    wx.navigateTo({ url: '/pages/analysis/analysis' });
  },
  goIndex() {
    wx.reLaunch({ url: '/pages/index/index' });
  },

  onTabSelect(e) {
    const { handler } = e.detail || {};
    if (handler && typeof this[handler] === 'function') this[handler]();
  },
  onFabTap(e) {
    const { handler } = e.detail || {};
    if (handler && typeof this[handler] === 'function') this[handler]();
  },
  onTxnTap() {
    // 列表项点击 → 进入 list 页查看全部
    this.goBill();
  }
});
