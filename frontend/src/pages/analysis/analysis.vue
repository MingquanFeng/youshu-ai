<template>
  <view class="page">
    <!-- 加载状态 -->
    <view v-if="loading" class="state-wrap">分析中…</view>

    <!-- 顶部 KPI 双卡 -->
    <view class="kpi-row">
      <view class="kpi-card">
        <text class="kpi-label">本月支出</text>
        <text class="kpi-value">¥ {{ monthly?.total ?? 0 }}</text>
      </view>
      <view class="kpi-card">
        <text class="kpi-label">Top 分类</text>
        <text class="kpi-value">{{ monthly?.top_category ?? '-' }}</text>
      </view>
    </view>

    <!-- 中部饼图 -->
    <view class="card">
      <text class="card-title">分类占比</text>
      <block v-if="hasCategory">
        <qiun-data-charts
          type="pie"
          :opts="pieOpts"
          :chartData="pieData"
          :ontouch="true"
          canvas2d
          canvasId="pieCanvas"
          class="chart"
        />
      </block>
      <view v-else class="empty">本月暂无消费</view>
    </view>

    <!-- 下部折线 -->
    <view class="card">
      <text class="card-title">近 30 天趋势</text>
      <block v-if="hasDaily">
        <qiun-data-charts
          type="line"
          :opts="lineOpts"
          :chartData="lineData"
          :ontouch="true"
          canvas2d
          canvasId="lineCanvas"
          class="chart"
        />
      </block>
      <view v-else class="empty">本月暂无消费</view>
    </view>

    <!-- 底部 advice -->
    <view class="advice-card">
      <text class="advice-title">本月建议</text>
      <text class="advice-text">{{ monthly?.advice || '暂无建议' }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { monthlyAnalysis, dailyAnalysis, categoryAnalysis } from '@/api/analysis'
import type { MonthlyResp, DailyResp, CategoryResp } from '@/types/analysis'

const monthly = ref<MonthlyResp | null>(null)
const category = ref<CategoryResp | null>(null)
const daily = ref<DailyResp | null>(null)
const loading = ref(true)

const PIE_COLORS = [
  '#5B8FF9', '#5AD8A6', '#F6BD16', '#E86452',
  '#6DC8EC', '#945FB9', '#FF9845', '#1E9493'
]

const hasCategory = computed(
  () => (category.value?.categories?.length ?? 0) > 0 && (category.value?.total ?? 0) > 0
)
const hasDaily = computed(
  () => (daily.value?.days?.length ?? 0) > 0
)

const pieData = computed(() => {
  const items = category.value?.categories ?? []
  return {
    categories: items.map(c => c.category),
    series: [
      {
        data: items.map(c => ({ name: c.category, value: c.amount }))
      }
    ]
  }
})

const lineData = computed(() => {
  const items = daily.value?.days ?? []
  return {
    categories: items.map(d => d.date.slice(5)),
    series: [
      {
        data: items.map(d => d.total),
        color: '#5B8FF9'
      }
    ]
  }
})

const pieOpts = computed(() => ({
  color: PIE_COLORS,
  padding: [8, 8, 8, 8],
  enableScroll: false,
  legend: { show: true, position: 'right' },
  dataLabel: true,
  dataPointShape: true,
  extra: {
    pie: {
      activeOpacity: 0.5,
      activeRadius: 10,
      offsetAngle: 0,
      labelWidth: 20,
      border: true,
      borderWidth: 2,
      borderColor: '#FFFFFF'
    }
  }
}))

const lineOpts = computed(() => ({
  color: ['#5B8FF9'],
  padding: [16, 16, 8, 16],
  enableScroll: false,
  legend: { show: false },
  xAxis: { disableGrid: true, axisLine: false },
  yAxis: { gridType: 'dash', dashLength: 4, splitNumber: 4 },
  extra: {
    line: {
      type: 'curve',
      width: 2,
      activeType: 'hollow'
    }
  }
}))

onMounted(async () => {
  try {
    const [m, c, d] = await Promise.allSettled([
      monthlyAnalysis(),
      categoryAnalysis(1),
      dailyAnalysis(30)
    ])
    if (m.status === 'fulfilled') monthly.value = m.value
    if (c.status === 'fulfilled') category.value = c.value
    if (d.status === 'fulfilled') daily.value = d.value

    const failedCount = [m, c, d].filter(r => r.status === 'rejected').length
    if (failedCount > 0) {
      uni.showToast({ title: '分析加载失败', icon: 'none' })
    }
  } finally {
    loading.value = false
  }
})
</script>

<style lang="scss">
.page {
  padding: 24rpx;
  background: #f8fafc;
  min-height: 100vh;
}

.state-wrap {
  padding: 120rpx 0;
  text-align: center;
  color: #64748b;
  font-size: 28rpx;
}

.kpi-row {
  display: flex;
  gap: 16rpx;
  margin-bottom: 16rpx;
}
.kpi-card {
  flex: 1;
  background: #fff;
  padding: 28rpx 24rpx;
  border-radius: 16rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}
.kpi-label {
  color: #64748b;
  font-size: 24rpx;
  display: block;
}
.kpi-value {
  font-size: 40rpx;
  font-weight: 700;
  color: #0f172a;
  display: block;
  margin-top: 8rpx;
}

.card {
  background: #fff;
  padding: 24rpx;
  border-radius: 16rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}
.card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #0f172a;
  display: block;
  margin-bottom: 16rpx;
}
.chart {
  width: 100%;
  height: 480rpx;
}
.empty {
  padding: 80rpx 0;
  text-align: center;
  color: #94a3b8;
  font-size: 26rpx;
}

.advice-card {
  background: linear-gradient(135deg, #eef2ff, #f5f3ff);
  padding: 28rpx 24rpx;
  border-radius: 16rpx;
  margin-bottom: 24rpx;
}
.advice-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #4f46e5;
  display: block;
  margin-bottom: 8rpx;
}
.advice-text {
  font-size: 28rpx;
  color: #312e81;
  line-height: 1.6;
  display: block;
}
</style>
