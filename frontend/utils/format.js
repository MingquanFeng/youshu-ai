// utils/format.js — 时间格式化 + 金额格式化

export function formatBillTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (!isNaN(d.getTime())) {
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const hh = String(d.getHours()).padStart(2, '0')
    const mi = String(d.getMinutes()).padStart(2, '0')
    return mm + '-' + dd + ' ' + hh + ':' + mi
  }
  // fallback: 字符串切片
  const tIdx = iso.indexOf('T')
  if (tIdx < 5) return iso
  return iso.slice(5, 10) + ' ' + iso.slice(tIdx + 1, tIdx + 6)
}

export function formatYuan(n) {
  if (n == null || isNaN(n)) return '¥0.00'
  return '¥' + Number(n).toFixed(2)
}

export function formatPercent(n) {
  if (n == null || isNaN(n)) return '0%'
  return (Number(n) * 100).toFixed(1) + '%'
}