<template>
  <view class="page">
    <view class="upload" @tap="pickImage">
      <text v-if="!imageUrl">点击上传 / 拍照</text>
      <image v-else :src="imageUrl" mode="aspectFit" class="preview" />
    </view>

    <button class="btn" :disabled="!imageUrl || loading" @tap="recognize">
      {{ loading ? '识别中...' : 'AI 识别' }}
    </button>

    <view v-if="result" class="result">
      <view class="row"><text>金额</text><text>¥ {{ result.amount }}</text></view>
      <view class="row"><text>商户</text><text>{{ result.merchant }}</text></view>
      <view class="row"><text>分类</text><text>{{ result.category }}</text></view>
      <view class="row"><text>时间</text><text>{{ result.time }}</text></view>
      <view class="row"><text>支付</text><text>{{ result.payment }}</text></view>
      <button class="btn primary" @tap="save">确认保存</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { uploadImage, recognizeImage, saveBill } from '@/api/bill'

const imageUrl = ref('')
const imageId = ref('')
const result = ref<any>(null)
const loading = ref(false)

const pickImage = () => {
  uni.chooseImage({
    count: 1,
    success: async (res: any) => {
      const path = res.tempFilePaths[0]
      const up = await uploadImage(path)
      imageUrl.value = up.image_url
      imageId.value = up.image_id
    }
  })
}

const recognize = async () => {
  loading.value = true
  try {
    result.value = await recognizeImage(imageId.value)
  } finally {
    loading.value = false
  }
}

const save = async () => {
  await saveBill({
    ...result.value,
    image_id: imageId.value,
    source: 'image_ai'
  })
  uni.showToast({ title: '已保存', icon: 'success' })
  uni.navigateBack()
}
</script>

<style lang="scss">
.page { padding: 24rpx; }
.upload {
  height: 360rpx; background: #f5f5f5; border-radius: 16rpx;
  display: flex; align-items: center; justify-content: center;
  color: #888; margin-bottom: 24rpx;
}
.preview { width: 100%; height: 100%; }
.btn { background: #4f46e5; color: #fff; border-radius: 12rpx; margin: 16rpx 0; }
.btn.primary { background: #16a34a; }
.result { background: #fff; border-radius: 16rpx; padding: 24rpx; }
.row { display: flex; justify-content: space-between; padding: 16rpx 0; border-bottom: 1rpx solid #eee; }
</style>
