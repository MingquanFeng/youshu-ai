<template>
  <view class="app">
    <view class="header">
      <text class="title">AI 记账助手</text>
      <text class="subtitle">上传截图，自动记账</text>
    </view>

    <view class="card" @tap="goRecognize">
      <text class="card-title">📷 AI 记账</text>
      <text class="card-desc">拍照 / 上传支付截图</text>
    </view>

    <view class="row">
      <view class="card small" @tap="goBill">
        <text class="card-title">📋 账单</text>
      </view>
      <view class="card small" @tap="goAnalysis">
        <text class="card-title">📊 分析</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
const goRecognize = () => uni.navigateTo({ url: '/pages/recognize/recognize' })
const goBill = () => uni.navigateTo({ url: '/pages/bill/bill' })
const goAnalysis = () => uni.navigateTo({ url: '/pages/analysis/analysis' })
</script>

<style lang="scss">
.app { padding: 24rpx; }
.header { padding: 24rpx 0 32rpx; }
.title { font-size: 44rpx; font-weight: 700; display: block; }
.subtitle { font-size: 26rpx; color: #888; display: block; margin-top: 8rpx; }
.card {
  background: #fff; border-radius: 16rpx; padding: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,.06); margin-bottom: 24rpx;
}
.card.small { flex: 1; }
.card-title { font-size: 32rpx; font-weight: 600; display: block; }
.card-desc  { font-size: 24rpx; color: #888; display: block; margin-top: 8rpx; }
.row { display: flex; gap: 24rpx; }
</style>
