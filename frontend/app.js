// app.js — 微信小程序启动入口
import { login } from './api/bill';
import { setToken, setUser } from './utils/storage';

App({
  globalData: {
    apiBase: '', // 空: 让 utils/request.js 的 getDefaultBase() 兜底 (devtools → 127.0.0.1, 真机 → 云服务器)
    token: '',
    user: null
  },

  onLaunch() {
    // 同步缓存的 token (apiBase 走 utils/request.js 兜底, 不在这里硬编码)
    const token = wx.getStorageSync('token') || '';
    this.globalData.token = token;

    // 懒登录: 全局只跑一次, 所有页面都用同一个 token
    // 解决"扫码直接落在 recognize 页"等非 index 入口场景
    if (!token) {
      this.maybeLogin();
    }
  },

  maybeLogin() {
    // 返回缓存的 Promise, 多次调用复用同一个请求 (避免 race)
    if (this.maybeLoginPromise) return this.maybeLoginPromise;
    if (wx.getStorageSync('token')) {
      return (this.maybeLoginPromise = Promise.resolve());
    }
    const code = 'mock-dev-code';
    this.maybeLoginPromise = login(code)
      .then((res) => {
        setToken(res.token);
        setUser(res);
        this.globalData.token = res.token;
        this.globalData.user = res;
        console.log('[app] 懒登录成功');
      })
      .catch((err) => {
        console.warn('[app] 懒登录失败', err);
        // 失败也要清掉 promise 允许重试
        this.maybeLoginPromise = null;
      });
    return this.maybeLoginPromise;
  }
});
