<template>
  <view class="page">
    <!-- 加载中 -->
    <view v-if="loading" class="state-wrap">
      <text class="state-text">加载中…</text>
    </view>

    <!-- 账单不存在 -->
    <view v-else-if="notFound" class="state-wrap">
      <text class="state-text state-err">账单不存在</text>
      <button class="back-btn" @tap="goBack">返回列表</button>
    </view>

    <!-- 加载失败 -->
    <view v-else-if="errorMsg" class="state-wrap">
      <text class="state-text state-err">{{ errorMsg }}</text>
      <button class="back-btn" @tap="reload">重试</button>
    </view>

    <!-- 详情内容 -->
    <view v-else-if="bill" class="content">
      <!-- 顶部展示 -->
      <view class="card display-card">
        <view class="display-row">
          <text class="label">商家</text>
          <text class="value">{{ bill.merchant || '-' }}</text>
        </view>
        <view class="display-row">
          <text class="label">分类</text>
          <text class="badge">{{ bill.category }}</text>
        </view>
        <view class="display-row amount-row">
          <text class="label">金额</text>
          <text class="amount">¥ {{ bill.amount.toFixed(2) }}</text>
        </view>
        <view class="display-row">
          <text class="label">支付方式</text>
          <text class="value">{{ bill.pay_method || '-' }}</text>
        </view>
        <view class="display-row">
          <text class="label">时间</text>
          <text class="value">{{ formatTime(bill.bill_time) }}</text>
        </view>
        <view class="display-row">
          <text class="label">备注</text>
          <text class="value">{{ bill.remark || '-' }}</text>
        </view>
      </view>

      <!-- 中部表单 -->
      <view class="card form-card">
        <text class="card-title">编辑</text>
        <view class="form-row">
          <text class="form-label">金额</text>
          <input
            class="form-input"
            type="digit"
            :value="form.amount"
            @input="(e: any) => (form.amount = Number(e.detail.value))"
          />
        </view>
        <view class="form-row">
          <text class="form-label">分类</text>
          <input
            class="form-input"
            type="text"
            v-model="form.category"
          />
        </view>
        <view class="form-row">
          <text class="form-label">商家</text>
          <input
            class="form-input"
            type="text"
            v-model="form.merchant"
          />
        </view>
        <view class="form-row">
          <text class="form-label">备注</text>
          <textarea
            class="form-textarea"
            v-model="form.remark"
          />
        </view>
      </view>

      <!-- 底部操作 -->
      <view class="actions">
        <button class="save-btn" :disabled="saving" @tap="save">
          {{ saving ? '保存中…' : '保存' }}
        </button>
        <button class="delete-btn" :disabled="saving" @tap="confirmDelete">
          删除
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { reactive, ref } from 'vue'
import { getBillDetail, removeBill, updateBill } from '@/api/bill'
import type { BillItem } from '@/types/bill'

const bill = ref<BillItem | null>(null)
const form = ref<Partial<BillItem>>({})
const loading = ref(false)
const saving = ref(false)
const notFound = ref(false)
const errorMsg = ref('')
const billId = ref<number>(0)

const formatTime = (iso: string) => {
  if (!iso) return ''
  const [d, t] = iso.split('T')
  return `${d.slice(5)} ${t.slice(0, 5)}`
}

onLoad((options: any) => {
  const id = Number(options?.id)
  if (!id) {
    notFound.value = true
    return
  }
  billId.value = id
  loading.value = true
  getBillDetail(id)
    .then((res) => {
      bill.value = res
      form.value = {
        amount: res.amount,
        category: res.category,
        merchant: res.merchant,
        remark: res.remark
      }
    })
    .catch((e: any) => {
      if (e?.code === 40400) {
        notFound.value = true
      } else {
        errorMsg.value = e?.message || '加载失败'
      }
    })
    .finally(() => {
      loading.value = false
    })
})

function save() {
  if (saving.value) return
  if (form.value.amount == null || form.value.amount <= 0) {
    uni.showToast({ title: '请输入有效金额', icon: 'none' })
    return
  }
  saving.value = true
  updateBill(billId.value, form.value)
    .then(() => {
      uni.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => uni.navigateBack(), 600)
    })
    .catch((e: any) => {
      uni.showToast({ title: e?.message || '保存失败', icon: 'none' })
    })
    .finally(() => {
      saving.value = false
    })
}

function confirmDelete() {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这条账单吗？',
    success: (res: { confirm: boolean }) => {
      if (!res.confirm) return
      saving.value = true
      removeBill(billId.value)
        .then(() => {
          uni.showToast({ title: '已删除', icon: 'success' })
          setTimeout(() => uni.navigateBack(), 600)
        })
        .catch((e: any) => {
          uni.showToast({ title: e?.message || '删除失败', icon: 'none' })
        })
        .finally(() => {
          saving.value = false
        })
    }
  })
}

function goBack() {
  uni.navigateBack()
}

function reload() {
  errorMsg.value = ''
  loading.value = true
  getBillDetail(billId.value)
    .then((res) => {
      bill.value = res
      form.value = {
        amount: res.amount,
        category: res.category,
        merchant: res.merchant,
        remark: res.remark
      }
    })
    .catch((e: any) => {
      if (e?.code === 40400) {
        notFound.value = true
      } else {
        errorMsg.value = e?.message || '加载失败'
      }
    })
    .finally(() => {
      loading.value = false
    })
}
</script>

<style lang="scss">
.page {
  padding: 24rpx;
  background-color: #f8fafc;
  min-height: 100vh;
}

.state-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 160rpx 0;
  gap: 32rpx;
}
.state-text {
  color: #6b7280;
  font-size: 28rpx;
}
.state-err {
  color: #b91c1c;
}
.back-btn {
  background: #2563eb;
  color: #fff;
  font-size: 26rpx;
  border-radius: 999rpx;
  padding: 0 40rpx;
  line-height: 64rpx;
}

.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 28rpx 24rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, .04);
}
.display-card {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}
.display-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.label {
  color: #6b7280;
  font-size: 26rpx;
}
.value {
  color: #111827;
  font-size: 28rpx;
}
.badge {
  display: inline-block;
  font-size: 22rpx;
  color: #2563eb;
  background: #eff6ff;
  padding: 2rpx 12rpx;
  border-radius: 6rpx;
}
.amount {
  color: #ef4444;
  font-size: 36rpx;
  font-weight: 700;
}

.card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16rpx;
  display: block;
}
.form-card {
  display: flex;
  flex-direction: column;
}
.form-row {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
  gap: 16rpx;
}
.form-label {
  width: 120rpx;
  color: #374151;
  font-size: 26rpx;
}
.form-input {
  flex: 1;
  height: 72rpx;
  background: #f9fafb;
  border: 1rpx solid #e5e7eb;
  border-radius: 8rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  color: #111827;
}
.form-textarea {
  flex: 1;
  height: 144rpx;
  background: #f9fafb;
  border: 1rpx solid #e5e7eb;
  border-radius: 8rpx;
  padding: 16rpx 20rpx;
  font-size: 28rpx;
  color: #111827;
}

.actions {
  display: flex;
  gap: 24rpx;
  margin-top: 16rpx;
}
.save-btn {
  flex: 1;
  background: #2563eb;
  color: #fff;
  font-size: 28rpx;
  border-radius: 999rpx;
  line-height: 80rpx;
  box-shadow: 0 4rpx 12rpx rgba(37, 99, 235, .25);
}
.save-btn[disabled] {
  opacity: .6;
}
.delete-btn {
  flex: 1;
  background: #fff;
  color: #ef4444;
  border: 1rpx solid #fecaca;
  font-size: 28rpx;
  border-radius: 999rpx;
  line-height: 80rpx;
}
.delete-btn[disabled] {
  opacity: .6;
}
</style>
