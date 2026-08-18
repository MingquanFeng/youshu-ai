// tests/detail.test.js — bill/detail 页 pure helper 测试
import { describe, it, expect } from 'vitest';
import {
  MAX_AMOUNT,
  CAT_KEY_MAP,
  makeForm,
  shallowClone,
  validateForm,
  isFormDirty
} from '../pages/bill/detail/detail.js';

describe('CAT_KEY_MAP', () => {
  it('含 7 个常用分类', () => {
    expect(Object.keys(CAT_KEY_MAP).sort()).toEqual(
      ['交通', '娱乐', '医疗', '居家', '工资', '购物', '餐饮'].sort()
    );
  });
});

describe('makeForm', () => {
  it('从 bill 构造 form, 缺字段填空串', () => {
    const bill = { amount: 12.5, category: '餐饮', merchant: '麦当劳' };
    const form = makeForm(bill);
    expect(form).toEqual({
      amount: 12.5,
      category: '餐饮',
      merchant: '麦当劳',
      pay_method: '',
      bill_time: '',
      remark: ''
    });
  });

  it('保留原始字段, 不修改 bill 对象', () => {
    const bill = { amount: 1, category: '其他', merchant: '', pay_method: 'wx', bill_time: '2026-01-01', remark: 'r' };
    const snap = JSON.parse(JSON.stringify(bill));
    makeForm(bill);
    expect(bill).toEqual(snap);
  });
});

describe('shallowClone', () => {
  it('返回新对象引用, 修改不影响原', () => {
    const orig = { a: 1, b: 'x' };
    const clone = shallowClone(orig);
    expect(clone).not.toBe(orig);
    clone.a = 2;
    expect(orig.a).toBe(1);
  });

  it('顶层覆盖, 嵌套对象仍共享引用', () => {
    const orig = { nested: { v: 1 } };
    const clone = shallowClone(orig);
    clone.nested.v = 2;
    expect(orig.nested.v).toBe(2);
  });
});

describe('validateForm', () => {
  const validForm = { amount: 12.5, category: '餐饮' };

  it('完整有效 form 返回空 errors', () => {
    expect(validateForm(validForm)).toEqual({});
  });

  it('amount 缺失报错', () => {
    expect(validateForm({ ...validForm, amount: '' }).amount).toBe('请输入金额');
    expect(validateForm({ ...validForm, amount: null }).amount).toBe('请输入金额');
    expect(validateForm({ ...validForm, amount: undefined }).amount).toBe('请输入金额');
  });

  it('amount 非数字报错', () => {
    expect(validateForm({ ...validForm, amount: 'abc' }).amount).toBe('金额必须是数字');
  });

  it('amount ≤ 0 报错', () => {
    expect(validateForm({ ...validForm, amount: 0 }).amount).toBe('金额必须大于 0');
    expect(validateForm({ ...validForm, amount: -5 }).amount).toBe('金额必须大于 0');
  });

  it('amount 超过 MAX_AMOUNT 报错', () => {
    const msg = validateForm({ ...validForm, amount: MAX_AMOUNT + 1 }).amount;
    expect(msg).toBe(`金额不能超过 ${MAX_AMOUNT}`);
  });

  it('amount 等于 MAX_AMOUNT 通过', () => {
    expect(validateForm({ ...validForm, amount: MAX_AMOUNT }).amount).toBeUndefined();
  });

  it('category 空/空白报错', () => {
    expect(validateForm({ ...validForm, category: '' }).category).toBe('请输入分类');
    expect(validateForm({ ...validForm, category: '   ' }).category).toBe('请输入分类');
  });

  it('同时多字段错都报', () => {
    const errs = validateForm({ amount: -1, category: '' });
    expect(errs.amount).toBe('金额必须大于 0');
    expect(errs.category).toBe('请输入分类');
  });
});

describe('isFormDirty', () => {
  const baseForm = {
    amount: 12.5,
    category: '餐饮',
    merchant: '麦当劳',
    pay_method: '微信支付',
    bill_time: '2026-08-11T12:00:00',
    remark: '午饭'
  };

  it('identical 视为未改', () => {
    expect(isFormDirty(baseForm, { ...baseForm })).toBe(false);
  });

  it('originalForm 空 → 视为脏 (从未初始化)', () => {
    expect(isFormDirty(null, baseForm)).toBe(true);
  });

  it('字段 trim 后空串视为等同', () => {
    expect(isFormDirty({ ...baseForm, remark: '' }, { ...baseForm, remark: '   ' })).toBe(false);
  });

  it('数字 amount 改 0 → 脏', () => {
    expect(isFormDirty(baseForm, { ...baseForm, amount: 0 })).toBe(true);
  });

  it('string 数字 amount 视为未改 (trim 后同)', () => {
    expect(isFormDirty({ ...baseForm, amount: 12.5 }, { ...baseForm, amount: '12.5' })).toBe(false);
  });

  it('null undefined 视为空字符串', () => {
    expect(isFormDirty({ ...baseForm, remark: null }, { ...baseForm, remark: undefined })).toBe(false);
  });

  it('category 改变 → 脏', () => {
    expect(isFormDirty(baseForm, { ...baseForm, category: '交通' })).toBe(true);
  });
});