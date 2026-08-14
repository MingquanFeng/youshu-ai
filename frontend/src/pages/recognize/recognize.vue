<template>
  <view class="page">
    <!-- 加载中 -->
    <view v-if="loading" class="state-wrap">
      <text class="state-text">AI 识别中…</text>
    </view>

    <!-- 错误提示 -->
    <view v-else-if="errorMsg" class="state-wrap">
      <text class="state-text state-err">{{ errorMsg }}</text>
      <button class="back-btn" @tap="errorMsg = ''">重试</button>
    </view>

    <!-- 顶部预览图 -->
    <view v-else-if="imageUrl" class="preview-card" @tap="pickImage">
      <image :src="imageUrl" mode="aspectFit" class="preview-img" />
      <text class="preview-hint">点击重新上传 / 拍照</text>
    </view>

    <!-- 未选择图片 -->
    <view v-else class="upload-card" @tap="pickImage">
      <text class="upload-icon">+</text>
      <text class="upload-text">点击上传 / 拍照</text>
    </view>

    <!-- 识别结果展示 -->
    <view v-if="result && !loading" class="card display-card">
      <view class="display-row">
        <text class="label">商家</text>
        <text class="value">{{ result.merchant || '-' }}</text>
      </view>
      <view class="display-row">
        <text class="label">分类</text>
        <text class="badge">{{ result.category }}</text>
      </view>
      <view class="display-row amount-row">
        <text class="label">金额</text>
        <text class="amount">¥ {{ result.amount.toFixed(2) }}</text>
      </view>
      <view class="display-row">
        <text class="label">支付方式</text>
        <text class="value">{{ result.payment || '-' }}</text>
      </view>
      <view class="display-row">
        <text class="label">时间</text>
        <text class="value">{{ formatTime(result.time) }}</text>
      </view>
      <view class="display-row">
        <text class="label">置信度</text>
        <text class="score-badge" :class="scoreClass">
          {{ (result.score * 100).toFixed(0) }}%
        </text>
      </view>
    </view>

    <!-- 编辑表单 -->
    <view v-if="result && !loading" class="card form-card">
      <text class="card-title">编辑（确认后保存）</text>
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
        <text class="form-label">支付方式</text>
        <input
          class="form-input"
          type="text"
          v-model="form.pay_method"
        />
      </view>
      <view class="form-row">
        <text class="form-label">时间</text>
        <input
          class="form-input"
          type="text"
          v-model="form.bill_time"
          placeholder="2026-08-11T12:30:00"
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
    <view v-if="result && !loading" class="actions">
      <button class="reco-btn" :disabled="saving" @tap="reset">
        重新识别
      </button>
      <button class="save-btn" :disabled="saving" @tap="save">
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { recognizeImage, saveBill, uploadImage } from '@/api/bill'
import type { RecognizeResult } from '@/types/bill'

const imageUrl = ref('')
const imageId = ref('')
const result = ref<RecognizeResult | null>(null)
const saving = ref(false)
const loading = ref(false)
const errorMsg = ref('')

interface BillForm {
  amount: number
  category: string
  merchant: string
  bill_time: string
  pay_method: string
  remark: string
}

const form = reactive<BillForm>({
  amount: 0,
  category: '',
  merchant: '',
  bill_time: '',
  pay_method: '',
  remark: ''
})

const scoreClass = computed(() => {
  const s = result.value?.score ?? 0
  if (s >= 0.85) return 'score-high'
  if (s >= 0.6) return 'score-mid'
  return 'score-low'
})

const formatTime = (iso: string) => {
  if (!iso) return ''
  const [d, t] = iso.split('T')
  return `${d.slice(5)} ${t.slice(0, 5)}`
}

function resetForm() {
  form.amount = 0
  form.category = ''
  form.merchant = ''
  form.bill_time = ''
  form.pay_method = ''
  form.remark = ''
}

function pickImage() {
  uni.chooseImage({
    count: 1,
    success: async (res: { tempFilePaths: string[] }) => {
      const path = res.tempFilePaths[0]
      errorMsg.value = ''
      try {
        const up = await uploadImage(path)
        imageUrl.value = up.image_url
        imageId.value = up.image_id
        // 重置上一次识别结果
        result.value = null
        resetForm()
        // 选完图自动识别
        await recognize()
      } catch (e: any) {
        errorMsg.value = e?.message || '上传失败'
      }
    }
  })
}

async function recognize() {
  if (!imageId.value) {
    errorMsg.value = '请先选择图片'
    return
  }
  loading.value = true
  errorMsg.value = ''
  try {
    const r = await recognizeImage(imageId.value)
    result.value = r
    // 关键映射：后端返回 payment，前端表单字段是 pay_method
    form.amount = r.amount
    form.category = r.category
    form.merchant = r.merchant
    form.bill_time = r.time
    form.pay_method = r.payment
    form.remark = ''
  } catch (e: any) {
    errorMsg.value = e?.message || '识别失败'
  } finally {
    loading.value = false
  }
}

function save() {
  if (saving.value) return
  if (!form.amount || form.amount <= 0) {
    uni.showToast({ title: '请输入有效金额', icon: 'none' })
    return
  }
  if (!result.value) {
    uni.showToast({ title: '请先识别', icon: 'none' })
    return
  }
  saving.value = true
  saveBill({
    amount: form.amount,
    category: form.category,
    merchant: form.merchant,
    bill_time: form.bill_time,
    pay_method: form.pay_method,
    remark: form.remark,
    source: 'image_ai',
    ai_score: result.value.score,
    image_id: imageId.value
  })
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

function reset() {
  result.value = null
  imageUrl.value = ''
  imageId.value = ''
  resetForm()
  errorMsg.value = ''
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

.upload-card {
  height: 360rpx;
  background: #fff;
  border: 2rpx dashed #cbd5e1;
  border-radius: 16rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  margin-bottom: 24rpx;
  color: #64748b;
}
.upload-icon {
  font-size: 72rpx;
  color: #94a3b8;
  line-height: 1;
}
.upload-text {
  font-size: 28rpx;
}

.preview-card {
  position: relative;
  height: 360rpx;
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 24rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, .04);
}
.preview-img {
  width: 100%;
  height: 100%;
}
.preview-hint {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, .5);
  color: #fff;
  font-size: 22rpx;
  text-align: center;
  padding: 8rpx 0;
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
.score-badge {
  display: inline-block;
  font-size: 22rpx;
  padding: 2rpx 14rpx;
  border-radius: 999rpx;
  font-weight: 600;
}
.score-high {
  color: #15803d;
  background: #dcfce7;
}
.score-mid {
  color: #b45309;
  background: #fef3c7;
}
.score-low {
  color: #b91c1c;
  background: #fee2e2;
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
  width: 140rpx;
  color: #374151;
  font-size: 26rpx;
  flex-shrink: 0;
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
.reco-btn {
  flex: 1;
  background: #fff;
  color: #2563eb;
  border: 1rpx solid #bfdbfe;
  font-size: 28rpx;
  border-radius: 999rpx;
  line-height: 80rpx;
}
.reco-btn[disabled] {
  opacity: .6;
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
</style>
