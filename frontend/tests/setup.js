// tests/setup.js — 给所有测试装 wx / Component / Page / App 全局桩
import { vi } from 'vitest';

// 微信小程序运行时全局 (在 utils/request.js 等会用到)
globalThis.wx = {
  getStorageSync: vi.fn((key) => {
    if (key === 'apiBase') return '';
    if (key === 'token') return '';
    return '';
  }),
  setStorageSync: vi.fn(),
  removeStorageSync: vi.fn(),
  getSystemInfoSync: vi.fn(() => ({ platform: 'devtools', theme: 'light', pixelRatio: 2 })),
  showToast: vi.fn(),
  showModal: vi.fn(),
  navigateTo: vi.fn(),
  navigateBack: vi.fn(),
  reLaunch: vi.fn(),
  request: vi.fn(),
  uploadFile: vi.fn(),
  chooseImage: vi.fn(),
  getDeviceInfo: vi.fn(),
  getAppBaseInfo: vi.fn(),
  getMenuButtonBoundingClientRect: vi.fn()
};
globalThis.getApp = vi.fn(() => ({ globalData: {} }));
globalThis.getCurrentPages = vi.fn(() => []);
globalThis.Component = vi.fn((opts) => opts);
globalThis.Page = vi.fn((opts) => opts);
globalThis.App = vi.fn((opts) => opts);
globalThis.Behavior = vi.fn((opts) => opts);