<template>
  <div class="day-page">
    <header class="page-top">
      <router-link to="/mood" class="back-link">
        <span class="back-icon">←</span>
        <span>返回心情日记</span>
      </router-link>
      <span class="page-tag">💭 日记详情</span>
    </header>

    <div class="card day-header">
      <div class="day-hero">
        <div class="day-avatar">{{ headerEmoji }}</div>
        <div class="day-info">
          <h1 class="page-title">{{ dateLabel }}</h1>
          <p v-if="diaries.length" class="day-summary">
            <span class="count-pill">共 {{ diaries.length }} 条记录</span>
            <span v-if="avgMood" class="avg-pill">平均心情 {{ emojis[Math.round(avgMood)] }}</span>
          </p>
          <p v-else class="day-summary empty">这一天还没有心情记录</p>
        </div>
      </div>
    </div>

    <section v-if="diaries.length" class="diary-section">
      <div class="section-head">
        <h2 class="section-title">当日记录</h2>
        <span class="section-count">{{ diaries.length }}</span>
      </div>

      <div class="diary-list">
        <article v-for="d in diaries" :key="d.id" class="diary-item">
          <div class="mood-avatar">{{ emojis[d.mood_level] }}</div>
          <div class="diary-bubble">
            <div class="diary-header">
              <div class="diary-meta">
                <span class="diary-mood">{{ d.mood_label }}</span>
                <span class="diary-time">{{ formatTime(d.created_at) }}</span>
              </div>
              <button class="btn btn-sm btn-danger" @click="handleDelete(d.id)">删除</button>
            </div>
            <div v-if="d.content" class="diary-body">
              <p class="diary-content">{{ d.content }}</p>
            </div>
            <MediaGallery :record="d" alt="心情配图" size="lg" class="diary-media" />
            <div v-if="d.tags" class="diary-tags">
              <span v-for="tag in parseTags(d.tags)" :key="tag" class="tag-pill">{{ tag }}</span>
            </div>
          </div>
        </article>
      </div>
    </section>

    <div v-else-if="!loading" class="empty-state card">
      <span class="empty-icon">📝</span>
      <p class="empty-title">还没有记录</p>
      <p class="empty-desc">这一天的心情还是空白，去写第一篇日记吧</p>
      <router-link to="/mood" class="btn btn-primary empty-btn">去写日记</router-link>
    </div>

    <div v-if="loading" class="empty-state card">加载中...</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getMoodByDate, deleteMoodDiary } from '../api'
import MediaGallery from '../components/MediaGallery.vue'
import { formatTime } from '../utils/date'

const route = useRoute()
const diaries = ref([])
const loading = ref(true)

const emojis = { 1: '😢', 2: '😔', 3: '😐', 4: '😊', 5: '😄' }

const dateLabel = computed(() => {
  const d = route.params.date
  if (!d) return '心情日记'
  const [y, m, day] = d.split('-')
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  const wd = weekdays[new Date(Number(y), Number(m) - 1, Number(day)).getDay()]
  return `${y}年${Number(m)}月${Number(day)}日 星期${wd}`
})

const headerEmoji = computed(() => {
  if (!diaries.value.length) return '📅'
  const level = Math.round(avgMood.value) || diaries.value[0].mood_level
  return emojis[level] || '📅'
})

const avgMood = computed(() => {
  if (!diaries.value.length) return 0
  const sum = diaries.value.reduce((s, d) => s + d.mood_level, 0)
  return sum / diaries.value.length
})

function parseTags(tags) {
  if (!tags) return []
  return tags.split(/[,，]/).map(t => t.trim()).filter(Boolean)
}

async function loadData() {
  loading.value = true
  try {
    const res = await getMoodByDate(route.params.date)
    diaries.value = res.data.list || []
  } catch (e) {
    diaries.value = []
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleDelete(id) {
  if (!confirm('确定删除这条记录？')) return
  try {
    await deleteMoodDiary(id)
    loadData()
  } catch (e) {
    alert(e.message)
  }
}

onMounted(loadData)
</script>

<style scoped>
.day-page {
  max-width: min(920px, 100%);
  margin: 0 auto;
  padding-bottom: 32px;
}

.page-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.85);
  color: var(--primary);
  font-size: 16px;
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
}

.back-link:hover {
  background: #fff;
  transform: translateX(-2px);
}

.back-icon {
  font-size: 18px;
  line-height: 1;
}

.page-tag {
  font-size: 15px;
  color: var(--text-secondary);
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(228, 237, 229, 0.55);
}

.day-header {
  padding: 32px;
  margin-bottom: 24px;
  border-left: 4px solid var(--primary);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(249, 252, 250, 0.92));
}

.day-hero {
  display: flex;
  align-items: center;
  gap: 16px;
}

.day-avatar,
.mood-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(69, 106, 93, 0.22);
}

.mood-avatar {
  width: 44px;
  height: 44px;
  font-size: 24px;
}

.day-info {
  flex: 1;
  min-width: 0;
}

.day-header .page-title {
  margin-bottom: 10px;
  font-size: 24px;
}

.day-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.day-summary.empty {
  color: var(--text-muted);
  font-size: 16px;
}

.count-pill,
.avg-pill {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 15px;
}

.count-pill {
  background: rgba(228, 237, 229, 0.7);
  color: var(--text-secondary);
}

.avg-pill {
  background: rgba(69, 106, 93, 0.1);
  color: var(--primary);
}

.diary-section {
  margin-bottom: 24px;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  position: relative;
  padding-left: 12px;
  margin: 0;
}

.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 18px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--primary), var(--accent));
}

.section-count {
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: var(--primary);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.diary-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.diary-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.diary-bubble {
  flex: 1;
  min-width: 0;
  padding: 18px 20px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(69, 106, 93, 0.08);
  box-shadow: var(--shadow-sm);
}

.diary-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 10px;
}

.diary-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.diary-mood {
  font-weight: 700;
  font-size: 18px;
  color: var(--primary);
}

.diary-time {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary);
  font-variant-numeric: tabular-nums;
}

.diary-body {
  padding: 16px 18px;
  margin-bottom: 12px;
  border-radius: 12px;
  background: rgba(248, 250, 249, 0.9);
  border: 1px solid rgba(69, 106, 93, 0.08);
}

.diary-content {
  font-size: 18px;
  line-height: 1.85;
  color: var(--text);
  white-space: pre-wrap;
  margin: 0;
}

.diary-media {
  margin-top: 4px;
}

.diary-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.tag-pill {
  font-size: 14px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(69, 106, 93, 0.1);
  color: var(--primary);
}

.empty-state {
  padding: 48px 24px;
  text-align: center;
  border: 1px dashed rgba(69, 106, 93, 0.18);
  background: rgba(255, 255, 255, 0.65);
}

.empty-icon {
  display: block;
  font-size: 42px;
  margin-bottom: 12px;
}

.empty-title {
  font-size: 19px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 6px;
}

.empty-desc {
  font-size: 16px;
  color: var(--text-muted);
  margin-bottom: 20px;
}

.empty-btn {
  border-radius: 999px;
  padding: 12px 28px;
}

@media (min-width: 1400px) {
  .day-page {
    max-width: 980px;
  }

  .diary-content {
    font-size: 19px;
  }
}

@media (max-width: 640px) {
  .day-header,
  .diary-bubble {
    padding: 18px;
  }

  .day-hero {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
