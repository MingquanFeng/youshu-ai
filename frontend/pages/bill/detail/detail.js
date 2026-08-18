// pages/bill/detail/detail.js — 账单详情 + 编辑 + 删除
import { getBillDetail, removeBill, updateBill } from '../../../api/bill';
import { formatBillTime } from '../../../utils/format';

// 字段校验规则
export const MAX_AMOUNT = 9999999;

// 分类中文 → key (用于 icon 颜色)
export const CAT_KEY_MAP = {
  餐饮: 'food',
  交通: 'transport',
  购物: 'shop',
  居家: 'home',
  娱乐: 'fun',
  医疗: 'medical',
  工资: 'income'
};

export function makeForm(b) {
  return {
    amount: b.amount,
    category: b.category || '',
    merchant: b.merchant || '',
    pay_method: b.pay_method || '',
    bill_time: b.bill_time || '',
    remark: b.remark || ''
  };
}

export function shallowClone(obj) {
  // 用于 originalForm: 防止与 form 共享引用导致 dirty 永远 false
  return Object.assign({}, obj);
}

// 字段级校验: 返回 { field: msg } 表示错误
export function validateForm(form) {
  const errors = {};
  if (form.amount === '' || form.amount === null || form.amount === undefined) {
    errors.amount = '请输入金额';
  } else if (Number.isNaN(Number(form.amount))) {
    errors.amount = '金额必须是数字';
  } else if (Number(form.amount) <= 0) {
    errors.amount = '金额必须大于 0';
  } else if (Number(form.amount) > MAX_AMOUNT) {
    errors.amount = `金额不能超过 ${MAX_AMOUNT}`;
  }
  if (!form.category || !form.category.trim()) {
    errors.category = '请输入分类';
  }
  return errors;
}

// deep equal for form diff
export function isFormDirty(orig, form) {
  if (!orig) return true;
  const fields = ['amount', 'category', 'merchant', 'pay_method', 'bill_time', 'remark'];
  for (const f of fields) {
    const a = (orig[f] ?? '').toString().trim();
    const b = (form[f] ?? '').toString().trim();
    if (a !== b) return true;
  }
  return false;
}

Page({
  data: {
    bill: null,
    originalForm: null, // 编辑前的 form, 用于 dirty 检查
    form: { amount: 0, category: '', merchant: '', pay_method: '', bill_time: '', remark: '' },
    errors: {}, // 字段错误
    loading: false,
    saving: false,
    notFound: false,
    errorMsg: '', // 全局错误 (toast 替代)
    billId: 0,
    canSave: false,
    maxAmount: MAX_AMOUNT
  },

  onLoad(options) {
    const id = Number(options.id);
    if (!id) {
      this.setData({ notFound: true });
      return;
    }
    this.setData({ billId: id });
    this.fetchDetail();
  },

  async fetchDetail() {
    this.setData({ loading: true, errorMsg: '' });
    try {
      const res = await getBillDetail(this.data.billId);
      const form = makeForm(res);
      this.setData({
        bill: {
          ...res,
          category_key: CAT_KEY_MAP[res.category] || 'other',
          category_char: (res.category || '?').charAt(0),
          bill_time_short: formatBillTime(res.bill_time),
          amount_str: Number(res.amount).toFixed(2)
        },
        // 深拷贝 (此处字段都是 primitive, Object.assign 足够),
        originalForm: shallowClone(form),
        form,
        errors: {},
        canSave: false
      });
    } catch (e) {
      if (e && e.code === 40400) {
        this.setData({ notFound: true });
      } else {
        this.setData({ errorMsg: (e && e.message) || '加载失败' });
      }
    } finally {
      this.setData({ loading: false });
    }
  },

  reload() {
    this.fetchDetail();
  },

  onAmountInput(e) {
    const v = e.detail.value;
    this.setData({ 'form.amount': v }, () => this.recomputeDirtyAndErrors());
  },
  onFieldInput(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({ ['form.' + field]: e.detail.value }, () => this.recomputeDirtyAndErrors());
  },
  onPickerChange(e) {
    this.setData({ 'form.bill_time': e.detail.value }, () => this.recomputeDirtyAndErrors());
  },

  recomputeDirtyAndErrors() {
    const { form, originalForm } = this.data;
    const errors = validateForm(form);
    const dirty = isFormDirty(originalForm, form);
    // 字段没改 + 字段有错 → 都不能保存
    this.setData({ errors, canSave: dirty && Object.keys(errors).length === 0 });
  },

  async save() {
    if (this.data.saving) return;
    if (!this.data.canSave) return;
    this.setData({ saving: true, errorMsg: '' });
    try {
      await updateBill(this.data.billId, this.data.form);
      wx.showToast({ title: '保存成功', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 600);
    } catch (e) {
      // 422 字段错误: { code: 42200, errors: {field: msg} }
      if (e && e.code === 42200 && e.errors) {
        this.setData({ errors: e.errors, errorMsg: '请检查标红字段' });
      } else {
        this.setData({ errorMsg: (e && e.message) || '保存失败，请稍后重试' });
      }
    } finally {
      this.setData({ saving: false });
    }
  },

  clearError() {
    this.setData({ errorMsg: '' });
  },

  confirmDelete() {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条账单吗？删除后无法恢复。',
      confirmText: '删除',
      confirmColor: '#EF4444',
      cancelText: '取消',
      success: (res) => {
        if (!res.confirm) return;
        this.doDelete();
      }
    });
  },

  async doDelete() {
    this.setData({ saving: true, errorMsg: '' });
    try {
      await removeBill(this.data.billId);
      wx.showToast({ title: '已删除', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 600);
    } catch (e) {
      this.setData({ errorMsg: (e && e.message) || '删除失败' });
    } finally {
      this.setData({ saving: false });
    }
  },

  goBack() {
    wx.navigateBack();
  }
});
