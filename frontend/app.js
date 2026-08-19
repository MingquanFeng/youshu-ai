// app.js — 微信小程序启动入口
import { login } from './api/bill';
import { setToken, setUser } from './utils/storage';

App({
  globalData: {
    apiBase: 'http://127.0.0.1:8000/api/v1',
    token: '',
    user: null
  },

  onLaunch() {
    // 同步缓存的 token 和 apiBase (页面加载时同步拿到)
    const token = wx.getStorageSync('token') || '';
    const apiBase = wx.getStorageSync('apiBase') || 'http://127.0.0.1:8000/api/v1';
    this.globalData.token = token;
    this.globalData.apiBase = apiBase;

    // 懒登录: 全局只跑一次, 所有页面都用同一个 token
    // 解决"扫码直接落在 recognize 页"等非 index 入口场景
    if (!token) {
      this.maybeLogin();
    }
  },

  maybeLogin() {
    if (wx.getStorageSync('token')) return;
    const code = 'mock-dev-code';
    login(code)
      .then((res) => {
        setToken(res.token);
        setUser(res);
        this.globalData.token = res.token;
        this.globalData.user = res;
        console.log('[app] 懒登录成功');
      })
      .catch((err) => {
        console.warn('[app] 懒登录失败', err);
      });
  }
});
