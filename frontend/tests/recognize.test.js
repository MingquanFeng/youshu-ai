// tests/recognize.test.js — recognize 页 toAbsoluteUrl 测试
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { toAbsoluteUrl } from '../pages/recognize/recognize.js';

describe('toAbsoluteUrl', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // 测试场景: 真机 (非 devtools), getApiBase 应返回 LAN IP
    globalThis.wx.getSystemInfoSync.mockReturnValue({
      platform: 'ios',
      theme: 'light'
    });
    globalThis.wx.getStorageSync.mockReturnValue(''); // storage 没设 apiBase
  });

  it('空值返回空串', () => {
    expect(toAbsoluteUrl('')).toBe('');
    expect(toAbsoluteUrl(null)).toBe('');
    expect(toAbsoluteUrl(undefined)).toBe('');
  });

  it('已是 http 完整 URL 不改', () => {
    expect(toAbsoluteUrl('http://x.com/foo.png')).toBe('http://x.com/foo.png');
  });

  it('已是 https 完整 URL 不改', () => {
    expect(toAbsoluteUrl('https://x.com/foo.png')).toBe('https://x.com/foo.png');
  });

  it('相对路径拼接 baseUrl + path', () => {
    // 真机 → baseUrl 是 http://192.168.18.204:8000/api/v1
    // toAbsoluteUrl 去掉 /api/v1 再拼
    expect(toAbsoluteUrl('/static/uploads/2/foo.png')).toBe(
      'http://192.168.18.204:8000/static/uploads/2/foo.png'
    );
  });

  it('storage 里有 apiBase 时优先用 storage', () => {
    globalThis.wx.getStorageSync.mockImplementation((key) => {
      if (key === 'apiBase') return 'http://staging.example.com/api/v1';
      return '';
    });
    expect(toAbsoluteUrl('/static/x.png')).toBe('http://staging.example.com/static/x.png');
  });

  it('globalData.apiBase 优先级第二', () => {
    globalThis.wx.getStorageSync.mockReturnValue(''); // storage 空
    globalThis.getApp.mockReturnValue({
      globalData: { apiBase: 'http://global.example.com/api/v1' }
    });
    expect(toAbsoluteUrl('/static/x.png')).toBe('http://global.example.com/static/x.png');
  });
});