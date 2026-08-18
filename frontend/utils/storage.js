// utils/storage.js — 简化版 wx.storage 封装

export function getToken() {
  try {
    return wx.getStorageSync('token') || '';
  } catch (e) {
    return '';
  }
}

export function setToken(t) {
  try {
    wx.setStorageSync('token', t);
  } catch (e) {}
}

export function clearToken() {
  try {
    wx.removeStorageSync('token');
  } catch (e) {}
}

export function getUser() {
  try {
    return wx.getStorageSync('user') || null;
  } catch (e) {
    return null;
  }
}

export function setUser(u) {
  try {
    wx.setStorageSync('user', u);
  } catch (e) {}
}

export function getApiBase() {
  try {
    return (
      wx.getStorageSync('apiBase') ||
      (typeof getApp === 'function' && getApp().globalData.apiBase) ||
      'http://127.0.0.1:8000/api/v1'
    );
  } catch (e) {
    return 'http://127.0.0.1:8000/api/v1';
  }
}
