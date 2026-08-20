// pages/recognize/recognize.js — AI 识别页
import { recognizeImage, saveBill, uploadImage } from '../../api/bill';
import { chooseImage, getApiBase } from '../../utils/request';
import { formatBillTime } from '../../utils/format';

// 后端返回的 image_url 是相对路径 (/static/uploads/...),
// 微信 <image> 不支持相对路径, 必须拼成绝对 URL
export function toAbsoluteUrl(rel) {
  if (!rel) return '';
  if (rel.startsWith('http://') || rel.startsWith('https://')) return rel;
  // getApiBase 返回 http://host:port/api/v1, 去掉 /api/v1
  const origin = getApiBase().replace(/\/api\/v1\/?$/, '');
  return origin + rel;
}

// 基础库 3.x <image> 不再支持 HTTP 协议 (必须 HTTPS)
// 临时方案: 把 http:// URL 通过 wx.downloadFile 转到 wxfile:// 本地路径
export function downloadToLocal(url) {
  return new Promise((resolve) => {
    if (!url) return resolve('');
    // 已是 https / wxfile / data: 协议直接用
    if (url.startsWith('https://') || url.startsWith('wxfile://') || url.startsWith('data:')) {
      return resolve(url);
    }
    // 不是 http 也返回原值 (兜底)
    if (!url.startsWith('http://')) return resolve(url);
    wx.downloadFile({
      url,
      success: (res) => resolve(res.tempFilePath || url),
      fail: () => resolve(url) // 失败也返回原值, <image> 会再报错但不阻塞业务
    });
  });
}

const INITIAL_FORM = {
  amount: 0,
  direction: 'expense', // expense | income, 后端 vision 启发判断, 用户可在编辑时切换
  category: '',
  merchant: '',
  bill_time: '',
  pay_method: '',
  remark: ''
};

Page({
  data: {
    imageUrl: '',
    imageId: '',
    result: null,
    form: Object.assign({}, INITIAL_FORM),
    saving: false,
    loading: false,
    errorMsg: '',
    scoreClass: ''
  },

  clearError() {
    this.setData({ errorMsg: '' });
  },

  onAmountInput(e) {
    this.setData({ 'form.amount': Number(e.detail.value) });
  },
  onFieldInput(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({ ['form.' + field]: e.detail.value });
  },

  async pickImage() {
    try {
      const paths = await chooseImage({ count: 1 });
      const path = paths[0];
      this.setData({ errorMsg: '', result: null, form: Object.assign({}, INITIAL_FORM) });
      const up = await uploadImage(path);
      const localUrl = await downloadToLocal(toAbsoluteUrl(up.image_url));
      this.setData({
        imageUrl: localUrl,
        imageId: up.image_id
      });
      await this.recognize();
    } catch (e) {
      this.setData({ errorMsg: (e && e.message) || '上传失败' });
    }
  },

  async recognize() {
    if (!this.data.imageId) {
      this.setData({ errorMsg: '请先选择图片' });
      return;
    }
    this.setData({ loading: true, errorMsg: '' });
    try {
      const r = await recognizeImage(this.data.imageId);
      const score = r.score || 0;
      const scoreClass = score >= 0.85 ? 'score-high' : score >= 0.6 ? 'score-mid' : 'score-low';
      this.setData({
        result: {
          ...r,
          time_short: formatBillTime(r.time),
          amount_str: Number(r.amount).toFixed(2),
          score_pct: (score * 100).toFixed(0) + '%'
        },
        form: {
          amount: Math.abs(r.amount), // UI 永远输入绝对值
          direction: r.direction || 'expense', // 后端 vision 启发判断: 红包/收款 → income
          category: r.category,
          merchant: r.merchant,
          bill_time: r.time,
          pay_method: r.payment,
          remark: ''
        },
        scoreClass
      });
    } catch (e) {
      this.setData({ errorMsg: (e && e.message) || '识别失败' });
    } finally {
      this.setData({ loading: false });
    }
  },

  async save() {
    if (this.data.saving) return;
    if (!this.data.form.amount || this.data.form.amount <= 0) {
      wx.showToast({ title: '请输入有效金额', icon: 'none' });
      return;
    }
    if (!this.data.result) {
      wx.showToast({ title: '请先识别', icon: 'none' });
      return;
    }
    this.setData({ saving: true });
    try {
      // 按 direction 加符号: 支出 = 负, 收入 = 正
      const amt = Number(this.data.form.amount) || 0;
      const signedAmount = this.data.form.direction === 'income' ? Math.abs(amt) : -Math.abs(amt);
      await saveBill({
        amount: signedAmount,
        category: this.data.form.category,
        merchant: this.data.form.merchant,
        bill_time: this.data.form.bill_time,
        pay_method: this.data.form.pay_method,
        remark: this.data.form.remark,
        source: 'image_ai',
        ai_score: this.data.result.score,
        image_id: this.data.imageId
      });
      wx.showToast({ title: '保存成功', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 600);
    } catch (e) {
      wx.showToast({ title: (e && e.message) || '保存失败', icon: 'none' });
    } finally {
      this.setData({ saving: false });
    }
  },

  reset() {
    this.setData({
      result: null,
      imageUrl: '',
      imageId: '',
      form: Object.assign({}, INITIAL_FORM),
      errorMsg: '',
      scoreClass: ''
    });
  }
});
