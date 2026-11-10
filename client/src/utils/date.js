/** 格式化为中文日期时间 */
export function formatDateTime(value) {
  if (!value) return ''
  const date = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return String(value).substring(0, 16)
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const y = date.getFullYear()
  const m = date.getMonth() + 1
  const d = date.getDate()
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  return `${y}年${m}月${d}日 ${weekdays[date.getDay()]} ${hh}:${mm}`
}

export function formatTime(value) {
  if (!value) return ''
  const raw = String(value)
  const date = new Date(raw.replace(' ', 'T'))
  if (!Number.isNaN(date.getTime())) {
    const hh = String(date.getHours()).padStart(2, '0')
    const mm = String(date.getMinutes()).padStart(2, '0')
    return `${hh}:${mm}`
  }
  const match = raw.match(/(\d{1,2}):(\d{2})/)
  if (match) {
    return `${match[1].padStart(2, '0')}:${match[2]}`
  }
  return raw.length >= 16 ? raw.substring(11, 16) : raw
}
