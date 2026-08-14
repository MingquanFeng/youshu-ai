<template>
  <view class="page">
    <!-- 错误条 -->
    <view v-if="errorMsg" class="error-bar">
      <text class="error-text">{{ errorMsg }}</text>
    </view>

    <!-- 列表卡片 -->
    <view v-if="items.length > 0">
      <view
        v-for="b in items"
        :key="b.id"
        class="item"
        @tap="onItemTap(b)"
      >
        <view class="item-left">
          <text class="merchant">{{ b.merchant || b.category }}</text>
          <view class="meta-row">
            <text class="badge">{{ b.category }}</text>
            <text class="meta-time">{{ formatTime(b.bill_time) }}</text>
          </view>
          <text class="source-tag">
            {{ b.source === 'image_ai' ? '🤖 AI 识别' : '✍️ 手动' }}
          </text>
        </view>
        <text class="amount">¥ {{ b.amount.toFixed(2) }}</text>
      </view>
    </view>

    <!-- 空态 -->
    <view v-else-if="!loading" class="empty">
      <text class="empty-text">暂无账单</text>
      <button class="empty-btn" @tap="goRecognize">去记一笔 →</button>
    </view>

    <!-- 底部加载状态 -->
    <view class="footer">
      <text v-if="loading" class="footer-text">加载中…</text>
      <text v-else-if="!hasMore && items.length > 0" class="footer-text">- 已经到底啦 -</text>
      <text v-else-if="hasMore" class="footer-text">上拉加载更多</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import { listBills } from '@/api/bill'
import type { BillItem } from '@/types/bill'

const items = ref<BillItem[]>([])
const page = ref(1)
const size = ref(20)
const total = ref(0)
const loading = ref(false)
const refreshing = ref(false)
const errorMsg = ref('')

const hasMore = computed(() => items.value.length < total.value)

async function loadPage(p: number, mode: 'reset' | 'append') {
  if (loading.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await listBills({ page: p, size: size.value })
    if (mode === 'reset') {
      items.value = res.items
    } else {
      items.value = items.value.concat(res.items)
    }
    page.value = res.page
    total.value = res.total
  } catch (e: any) {
    errorMsg.value = e?.message || '加载失败，请稍后重试'
    uni.showToast({ title: errorMsg.value, icon: 'none' })
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

async function refresh() {
  refreshing.value = true
  await loadPage(1, 'reset')
  uni.stopPullDownRefresh()
}

async function loadMore() {
  if (loading.value || !hasMore.value || refreshing.value) return
  await loadPage(page.value + 1, 'append')
}

function formatTime(iso: string): string {
  // "2026-08-11T12:30:00" → "08-11 12:30"
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) {
    // 兜底：字符串切片
    return iso.slice(5, 10) + ' ' + iso.slice(11, 16)
  }
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${mi}`
}

function onItemTap(b: BillItem) {
  uni.navigateTo({ url: '/pages/bill/detail?id=' + b.id })
}

function goRecognize() {
  uni.navigateTo({ url: '/pages/recognize/recognize' })
}

onMounted(() => loadPage(1, 'reset'))
onPullDownRefresh(() => refresh())
onReachBottom(() => loadMore())
</script>

<style lang="scss">
.page {
  padding: 24rpx;
  background-color: #f8fafc;
  min-height: 100vh;
}

/* 错误条 */
.error-bar {
  background: #fef2f2;
  border: 1rpx solid #fecaca;
  border-radius: 8rpx;
  padding: 16rpx 24rpx;
  margin-bottom: 16rpx;
}
.error-text {
  color: #b91c1c;
  font-size: 24rpx;
}

/* 列表卡片 */
.item {
  background: #fff;
  padding: 28rpx 24rpx;
  border-radius: 16rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, .04);
}
.item-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.merchant {
  font-size: 30rpx;
  font-weight: 600;
  color: #111827;
}
.meta-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.badge {
  display: inline-block;
  font-size: 22rpx;
  color: #2563eb;
  background: #eff6ff;
  padding: 2rpx 12rpx;
  border-radius: 6rpx;
}
.meta-time {
  font-size: 22rpx;
  color: #6b7280;
}
.source-tag {
  font-size: 20rpx;
  color: #9ca3af;
}
.amount {
  color: #ef4444;
  font-size: 32rpx;
  font-weight: 600;
  align-self: center;
}

/* 空态 */
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
  gap: 32rpx;
}
.empty-text {
  color: #9ca3af;
  font-size: 28rpx;
}
.empty-btn {
  background: #2563eb;
  color: #fff;
  font-size: 26rpx;
  border-radius: 999rpx;
  padding: 0 40rpx;
  line-height: 64rpx;
  height: 64rpx;
  box-shadow: 0 4rpx 12rpx rgba(37, 99, 235, .25);
}

/* 底部 */
.footer {
  text-align: center;
  padding: 32rpx 0;
}
.footer-text {
  color: #9ca3af;
  font-size: 22rpx;
}
</style>
