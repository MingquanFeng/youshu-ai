// components/txn-row/txn-row.js — 流水条目
// props: iconBg, iconChar, title, sub, amount, amountStyle, handler
// event: tap (detail: {handler})
Component({
  options: { styleIsolation: 'apply-shared' },
  properties: {
    iconBg: { type: String, value: 'var(--cat-other-soft)' },
    iconChar: { type: String, value: '' },
    title: { type: String, value: '' },
    sub: { type: String, value: '' },
    amount: { type: String, value: '' },
    amountStyle: { type: String, value: '' },
    handler: { type: String, value: '' }
  },
  methods: {
    onTap() {
      if (!this.data.handler) return
      this.triggerEvent('tap', { handler: this.data.handler })
    }
  }
})