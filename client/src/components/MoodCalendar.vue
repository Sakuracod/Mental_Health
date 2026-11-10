<template>
  <div class="mood-calendar">
    <div class="calendar-header">
      <button type="button" class="nav-btn" @click="changeMonth(-1)">‹</button>
      <h3 class="calendar-title">{{ year }}年{{ month }}月</h3>
      <button type="button" class="nav-btn" @click="changeMonth(1)">›</button>
      <button type="button" class="today-btn" @click="goToday">今天</button>
    </div>

    <div class="weekday-row">
      <span v-for="w in weekdays" :key="w" class="weekday">{{ w }}</span>
    </div>

    <div class="calendar-grid">
      <div
        v-for="(cell, idx) in cells"
        :key="idx"
        class="calendar-cell"
        :class="{
          'other-month': !cell.inMonth,
          'is-today': cell.isToday,
          'has-mood': cell.mood,
          clickable: cell.inMonth
        }"
        @click="cell.inMonth && handleDayClick(cell)"
      >
        <span class="day-num">{{ cell.day }}</span>
        <span v-if="cell.mood" class="day-mood" :title="cell.mood.mood_label">
          {{ emojis[cell.mood.mood_level] }}
        </span>
        <span v-if="cell.mood && cell.mood.count > 1" class="day-count">{{ cell.mood.count }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getMoodCalendar } from '../api'

const props = defineProps({
  refreshKey: { type: Number, default: 0 }
})

const router = useRouter()
const today = new Date()
const year = ref(today.getFullYear())
const month = ref(today.getMonth() + 1)
const moodDays = ref({})
const loading = ref(false)

const weekdays = ['日', '一', '二', '三', '四', '五', '六']
const emojis = { 1: '😢', 2: '😔', 3: '😐', 4: '😊', 5: '😄' }

const cells = computed(() => {
  const firstDay = new Date(year.value, month.value - 1, 1)
  const startWeekday = firstDay.getDay()
  const daysInMonth = new Date(year.value, month.value, 0).getDate()
  const prevMonthDays = new Date(year.value, month.value - 1, 0).getDate()

  const result = []
  const todayStr = formatDate(today)

  for (let i = startWeekday - 1; i >= 0; i--) {
    const day = prevMonthDays - i
    const m = month.value === 1 ? 12 : month.value - 1
    const y = month.value === 1 ? year.value - 1 : year.value
    const dateStr = formatDateStr(y, m, day)
    result.push({
      day,
      inMonth: false,
      date: dateStr,
      isToday: dateStr === todayStr,
      mood: moodDays.value[dateStr] || null
    })
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = formatDateStr(year.value, month.value, day)
    result.push({
      day,
      inMonth: true,
      date: dateStr,
      isToday: dateStr === todayStr,
      mood: moodDays.value[dateStr] || null
    })
  }

  const remaining = 42 - result.length
  for (let day = 1; day <= remaining; day++) {
    const m = month.value === 12 ? 1 : month.value + 1
    const y = month.value === 12 ? year.value + 1 : year.value
    const dateStr = formatDateStr(y, m, day)
    result.push({
      day,
      inMonth: false,
      date: dateStr,
      isToday: dateStr === todayStr,
      mood: moodDays.value[dateStr] || null
    })
  }

  return result
})

function formatDate(d) {
  return formatDateStr(d.getFullYear(), d.getMonth() + 1, d.getDate())
}

function formatDateStr(y, m, d) {
  return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

async function loadCalendar() {
  loading.value = true
  try {
    const res = await getMoodCalendar({ year: year.value, month: month.value })
    const map = {}
    for (const day of res.data.days || []) {
      map[day.date] = day
    }
    moodDays.value = map
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function changeMonth(delta) {
  let m = month.value + delta
  let y = year.value
  if (m < 1) { m = 12; y-- }
  if (m > 12) { m = 1; y++ }
  month.value = m
  year.value = y
}

function goToday() {
  year.value = today.getFullYear()
  month.value = today.getMonth() + 1
}

function handleDayClick(cell) {
  router.push(`/mood/day/${cell.date}`)
}

watch([year, month], loadCalendar)
watch(() => props.refreshKey, loadCalendar)

onMounted(loadCalendar)
</script>

<style scoped>
.mood-calendar {
  width: 100%;
}

.calendar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.calendar-title {
  flex: 1;
  text-align: center;
  font-size: 19px;
  font-weight: 600;
}

.nav-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border-light, #e8ecef);
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 20px;
  color: var(--primary);
  transition: var(--transition);
}

.nav-btn:hover {
  background: #e8f4f8;
  border-color: var(--primary);
}

.today-btn {
  padding: 6px 12px;
  border: 1px solid var(--primary);
  border-radius: 8px;
  background: #fff;
  color: var(--primary);
  font-size: 15px;
  cursor: pointer;
}

.weekday-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 8px;
  max-width: min(560px, 100%);
  margin-left: auto;
  margin-right: auto;
}

.weekday {
  text-align: center;
  font-size: 16px;
  color: var(--text-muted, var(--text-muted));
  font-weight: 500;
  padding: 4px 0;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  max-width: min(560px, 100%);
  margin: 0 auto;
}

.calendar-cell {
  position: relative;
  height: 46px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: var(--transition);
}

.calendar-cell.clickable {
  cursor: pointer;
}

.calendar-cell.clickable:hover {
  background: rgba(69, 106, 93, 0.08);
  border-color: rgba(69, 106, 93, 0.2);
}

.calendar-cell.other-month {
  opacity: 0.35;
  pointer-events: none;
}

.calendar-cell.is-today {
  border-color: var(--primary);
  background: rgba(69, 106, 93, 0.08);
}

.calendar-cell.has-mood {
  background: #fafcfd;
}

.day-num {
  font-size: 18px;
  font-weight: 500;
  color: var(--text);
  line-height: 1;
}

.is-today .day-num {
  color: var(--primary);
  font-weight: 700;
  font-size: 19px;
}

.day-mood {
  font-size: 20px;
  line-height: 1;
  margin-top: 2px;
}

.day-count {
  position: absolute;
  top: 3px;
  right: 4px;
  font-size: 12px;
  background: var(--primary);
  color: #fff;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (min-width: 1400px) {
  .calendar-title {
    font-size: 21px;
  }

  .weekday {
    font-size: 17px;
  }

  .weekday-row,
  .calendar-grid {
    max-width: min(640px, 100%);
  }

  .calendar-cell {
    height: 52px;
  }

  .day-num {
    font-size: 19px;
  }

  .is-today .day-num {
    font-size: 20px;
  }

  .day-mood {
    font-size: 22px;
  }
}

@media (min-width: 1800px) {
  .weekday-row,
  .calendar-grid {
    max-width: min(720px, 100%);
  }

  .calendar-cell {
    height: 58px;
  }

  .day-num {
    font-size: 20px;
  }

  .day-mood {
    font-size: 24px;
  }
}
</style>
