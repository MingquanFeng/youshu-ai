<template>
  <view class="page">
    <view class="stat">
      <text class="label">本月支出</text>
      <text class="value">¥ {{ data?.total ?? 0 }}</text>
    </view>
    <view class="stat">
      <text class="label">Top 分类</text>
      <text class="value">{{ data?.top_category ?? '-' }}</text>
    </view>
    <view class="advice">{{ data?.advice ?? '' }}</view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { monthlyAnalysis } from '@/api/analysis'

const data = ref<any>(null)
onMounted(async () => { data.value = await monthlyAnalysis() })
</script>

<style lang="scss">
.page { padding: 24rpx; }
.stat {
  background: #fff; padding: 32rpx; border-radius: 16rpx;
  margin-bottom: 16rpx;
}
.label { color: #888; font-size: 24rpx; display: block; }
.value { font-size: 40rpx; font-weight: 700; display: block; margin-top: 8rpx; }
.advice {
  background: #eef2ff; padding: 24rpx; border-radius: 12rpx;
  color: #4f46e5; font-size: 26rpx;
}
</style>
