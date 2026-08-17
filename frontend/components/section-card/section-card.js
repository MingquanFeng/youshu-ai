// components/section-card/section-card.js — 通用卡片容器
// props: padding (String 'normal' | 'tight')
// slot: 默认 — 卡片内部内容
Component({
  options: {
    styleIsolation: 'apply-shared',
    multipleSlots: true
  },
  properties: {
    padding: { type: String, value: 'normal' }
  }
})