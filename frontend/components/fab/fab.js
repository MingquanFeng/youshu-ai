// components/fab/fab.js — 浮动主 CTA 按钮
// props: handler (String, 父组件方法名)
// event: tap (detail: {handler})
Component({
  options: { styleIsolation: 'apply-shared' },
  properties: {
    handler: { type: String, value: '' }
  },
  methods: {
    onTap() {
      this.triggerEvent('tap', { handler: this.data.handler })
    }
  }
})