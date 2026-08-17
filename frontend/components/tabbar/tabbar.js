// components/tabbar/tabbar.js — 3-tab 底部导航
// props: active (Number 索引), items (Array<{icon, label, handler}>)
// event: select (detail: {index, handler})
Component({
  options: { styleIsolation: 'apply-shared' },
  properties: {
    active: { type: Number, value: 0 },
    items: { type: Array, value: [] }
  },
  methods: {
    onTap(e) {
      const { index, handler } = e.currentTarget.dataset
      if (this.data.active === index) return
      this.triggerEvent('select', { index, handler })
    }
  }
})