<template>
  <view class="page">
    <view v-for="b in bills" :key="b.id" class="item">
      <view class="left">
        <text class="merchant">{{ b.merchant || b.category }}</text>
        <text class="meta">{{ b.category }} · {{ formatTime(b.bill_time) }}</text>
      </view>
      <text class="amount">¥ {{ b.amount }}</text>
    </view>
    <view v-if="!bills.length" class="empty">暂无账单</view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listBills } from '@/api/bill'

const bills = ref<any[]>([])

onMounted(async () => {
  const res = await listBills({ page: 1, size: 50 })
  bills.value = res.items
})

const formatTime = (s: string) => s.slice(0, 16).replace('T', ' ')
</script>

<style lang="scss">
.page { padding: 24rpx; }
.item {
  background: #fff; padding: 24rpx; border-radius: 12rpx;
  display: flex; justify-content: space-between; margin-bottom: 16rpx;
}
.merchant { font-size: 30rpx; font-weight: 600; display: block; }
.meta { font-size: 22rpx; color: #888; display: block; margin-top: 6rpx; }
.amount { color: #ef4444; font-size: 32rpx; align-self: center; }
.empty { text-align: center; color: #aaa; padding: 80rpx 0; }
</style>
