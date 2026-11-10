<template>
  <div class="mood-page">
    <h1 class="page-title">心情日记</h1>

    <div class="mood-layout">
      <div class="card diary-card">
        <h2 class="section-title">记录今天的心情</h2>
        <div class="mood-selector">
          <button
            v-for="(label, level) in moodLabels"
            :key="level"
            class="mood-btn"
            :class="{ active: form.mood_level == level }"
            @click="form.mood_level = Number(level)"
          >
            <span class="mood-emoji">{{ emojis[level] }}</span>
            <span>{{ label }}</span>
          </button>
        </div>
        <div class="form-group">
          <textarea
            v-model="form.content"
            class="form-textarea"
            placeholder="写下今天的心情和感受..."
            rows="4"
          ></textarea>
        </div>
        <div class="form-group">
          <input v-model="form.tags" class="form-input" placeholder="标签，如：学业,运动（逗号分隔）" />
        </div>

        <MediaUploadField
          v-model="form.media_list"
          label="添加照片或视频（可选）"
          button-text="📷 选择照片/视频"
          :upload-fn="uploadMoodMedia"
          @error="onUploadError"
        />

        <button class="btn btn-primary" :disabled="!form.mood_level || saving" @click="handleSave">
          {{ saving ? '保存中...' : '保存记录' }}
        </button>
        <div v-if="msg" class="alert" :class="msgType">{{ msg }}</div>
      </div>

      <div class="card stats-card">
        <h2 class="section-title">近30天心情统计</h2>
        <div class="stats-chart">
          <div v-for="s in stats" :key="s.mood_level" class="stat-bar-item">
            <span class="stat-emoji">{{ emojis[s.mood_level] }}</span>
            <span class="stat-label">{{ s.mood_label }}</span>
            <div class="stat-bar-bg">
              <div class="stat-bar-fill" :style="{ width: barWidth(s.count) }"></div>
            </div>
            <span class="stat-count">{{ s.count }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card calendar-card">
      <h2 class="section-title"><span>📅</span> 心情日历</h2>
      <p class="calendar-hint">点击日期查看当天的心情记录</p>
      <MoodCalendar :refresh-key="calendarKey" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  getMoodLabels, createMoodDiary,
  uploadMoodMedia, getMoodStats
} from '../api'
import MoodCalendar from '../components/MoodCalendar.vue'
import MediaUploadField from '../components/MediaUploadField.vue'

const moodLabels = ref({})
const stats = ref([])
const calendarKey = ref(0)
const form = ref({ mood_level: 0, content: '', tags: '', media_list: [] })
const saving = ref(false)
const msg = ref('')
const msgType = ref('alert-success')

const emojis = { 1: '😢', 2: '😔', 3: '😐', 4: '😊', 5: '😄' }

onMounted(() => loadData())

async function loadData() {
  try {
    const [labelRes, statsRes] = await Promise.all([
      getMoodLabels(), getMoodStats()
    ])
    moodLabels.value = labelRes.data
    stats.value = statsRes.data
    calendarKey.value++
  } catch (e) { console.error(e) }
}

function onUploadError(message) {
  msg.value = message
  msgType.value = 'alert-error'
}

async function handleSave() {
  saving.value = true
  msg.value = ''
  try {
    const payload = {
      mood_level: form.value.mood_level,
      content: form.value.content,
      tags: form.value.tags
    }
    if (form.value.media_list.length) {
      payload.media_list = form.value.media_list
    }
    await createMoodDiary(payload)
    msg.value = '心情记录保存成功！'
    msgType.value = 'alert-success'
    form.value = { mood_level: 0, content: '', tags: '', media_list: [] }
    loadData()
  } catch (e) {
    msg.value = e.message
    msgType.value = 'alert-error'
  } finally {
    saving.value = false
  }
}

function barWidth(count) {
  const max = Math.max(...stats.value.map(s => s.count), 1)
  return (count / max * 100) + '%'
}
</script>

<style scoped>
.mood-page {
  width: 100%;
}

.mood-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

.section-title span {
  margin-right: 4px;
}

.mood-selector {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.mood-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 14px;
  border: 2px solid #e8ecef;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.mood-btn.active {
  border-color: var(--primary);
  background: rgba(228, 237, 229, 0.75);
}

.mood-emoji {
  font-size: 26px;
}

.form-group {
  margin-bottom: 16px;
}

.alert {
  margin-top: 12px;
}

.mood-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: stretch;
}

.stats-card {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.stats-chart {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 14px;
  min-height: 300px;
  padding: 4px 0 8px;
}

.stat-bar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
}

.stat-emoji {
  width: 32px;
  text-align: center;
  font-size: 24px;
  line-height: 1;
  flex-shrink: 0;
}

.stat-label {
  width: 72px;
  font-size: 17px;
  font-weight: 500;
  flex-shrink: 0;
  color: var(--text);
}

.stat-bar-bg {
  flex: 1;
  height: 26px;
  background: #f0f0f0;
  border-radius: 13px;
  overflow: hidden;
}

.stat-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  border-radius: 13px;
  transition: width 0.3s;
}

.stat-count {
  width: 36px;
  text-align: right;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.calendar-card {
  margin-top: 24px;
  padding: 28px;
}

.calendar-hint {
  font-size: 15px;
  color: var(--text-muted);
  margin: -8px 0 16px;
}

@media (max-width: 900px) {
  .mood-layout {
    grid-template-columns: 1fr;
  }
}

/* 宽屏下适度放大字号与控件，避免内容显得过小 */
@media (min-width: 1400px) {
  .section-title {
    font-size: 20px;
    margin-bottom: 18px;
  }

  .mood-btn {
    padding: 12px 18px;
    font-size: 15px;
  }

  .mood-emoji {
    font-size: 30px;
  }

  .stats-chart {
    min-height: 340px;
    gap: 16px;
  }

  .stat-emoji {
    width: 36px;
    font-size: 28px;
  }

  .stat-label {
    width: 80px;
    font-size: 18px;
  }

  .stat-bar-bg {
    height: 30px;
    border-radius: 15px;
  }

  .stat-bar-fill {
    border-radius: 15px;
  }

  .stat-count {
    width: 40px;
    font-size: 18px;
  }

  .calendar-hint {
    font-size: 16px;
  }

  .calendar-card {
    padding: 32px;
  }
}

@media (min-width: 1800px) {
  .section-title {
    font-size: 22px;
  }

  .mood-btn {
    padding: 14px 20px;
    font-size: 16px;
  }

  .mood-emoji {
    font-size: 34px;
  }

  .stats-chart {
    min-height: 380px;
    gap: 18px;
  }

  .stat-emoji {
    width: 40px;
    font-size: 32px;
  }

  .stat-label {
    width: 88px;
    font-size: 19px;
  }

  .stat-bar-bg {
    height: 34px;
  }

  .stat-count {
    font-size: 19px;
  }
}
</style>
