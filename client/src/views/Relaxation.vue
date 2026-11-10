<template>
  <div class="relaxation-page">
    <section class="hero-banner">
      <div class="hero-content">
        <p class="hero-label">Mindfulness & Relaxation</p>
        <h1>放松训练中心</h1>
        <p class="hero-desc">按分类选择适合你的放松方式，点击进入沉浸式训练体验</p>
        <div class="hero-stats">
          <div class="stat-item">
            <strong>{{ allAudios.length }}</strong>
            <span>训练资源</span>
          </div>
          <div class="stat-item">
            <strong>{{ categories.length }}</strong>
            <span>训练分类</span>
          </div>
          <div class="stat-item">
            <strong>{{ videoCount }}</strong>
            <span>视频引导</span>
          </div>
          <div
            class="stat-item stat-clickable"
            :class="{ active: showFavorites }"
            @click="showFavoritesOnly"
          >
            <strong>{{ myFavoriteCount }}</strong>
            <span>⭐ 我的收藏</span>
          </div>
          <div
            class="stat-item stat-clickable"
            :class="{ active: showLiked }"
            @click="showLikedOnly"
          >
            <strong>{{ myLikeCount }}</strong>
            <span>❤️ 我的点赞</span>
          </div>
        </div>
      </div>
      <div class="hero-deco">
        <div class="deco-ring r1"></div>
        <div class="deco-ring r2"></div>
        <span class="deco-emoji">🧘</span>
      </div>
    </section>

    <section class="category-section">
      <div class="category-tabs">
        <button
          class="category-tab"
          :class="{ active: activeCategory === '全部' && !showFavorites && !showLiked }"
          @click="selectAll"
        >
          全部
          <span class="tab-badge">{{ allAudios.length }}</span>
        </button>
        <button
          v-for="cat in categories"
          :key="cat.name"
          class="category-tab"
          :class="{ active: activeCategory === cat.name && !showFavorites && !showLiked }"
          :style="activeCategory === cat.name ? { '--cat-color': cat.color } : {}"
          @click="selectCategory(cat.name)"
        >
          <span class="tab-icon">{{ cat.icon }}</span>
          {{ cat.name }}
          <span class="tab-badge">{{ cat.count }}</span>
        </button>
      </div>
    </section>

    <section v-if="filteredAudios.length" class="media-grid">
      <router-link
        v-for="item in filteredAudios"
        :key="item.id"
        :to="`/relaxation/${item.id}`"
        class="media-card"
        :style="{ '--card-accent': getCategoryStyle(item.category).color }"
      >
        <div class="card-cover" :class="item.media_type">
          <span class="cover-icon">{{ item.cover_icon }}</span>
          <span class="media-type-badge">{{ item.media_type === 'video' ? '视频' : '音频' }}</span>
          <span class="duration-badge">⏱ {{ item.duration }}</span>
        </div>
        <div class="card-body">
          <span class="card-category">{{ item.category }}</span>
          <h3>
            {{ item.title }}
            <span v-if="item.is_favorited" class="fav-mark" title="已收藏">⭐</span>
          </h3>
          <p>{{ item.description }}</p>
          <div class="card-meta">
            <span>❤️ {{ item.like_count || 0 }}</span>
          </div>
          <div class="card-action">
            <span>{{ item.media_type === 'video' ? '观看训练' : '开始聆听' }}</span>
            <span class="arrow">→</span>
          </div>
        </div>
      </router-link>
    </section>

    <div v-else-if="!loading" class="empty-state card">
      {{ emptyMessage }}
    </div>
    <div v-if="loading" class="empty-state card">加载中...</div>
  </div>
</template>

<script setup>
/**
 * 放松训练列表页 - 分类展示，点击进入详情播放
 */
import { ref, computed, onMounted, onActivated } from 'vue'
import { getRelaxationAudios } from '../api'

const allAudios = ref([])
const loading = ref(true)
const activeCategory = ref('全部')
const showFavorites = ref(false)
const showLiked = ref(false)

const CATEGORY_META = {
  '呼吸练习': { icon: '🌬️', color: '#456a5d' },
  '正念冥想': { icon: '🧘', color: '#5a8575' },
  '肌肉放松': { icon: '💆', color: '#6ba888' },
  '音乐疗愈': { icon: '🎹', color: '#d48ab4' },
  '视频引导': { icon: '🎬', color: '#e8a54b' },
}

const categories = computed(() => {
  const map = {}
  allAudios.value.forEach(item => {
    map[item.category] = (map[item.category] || 0) + 1
  })
  return Object.entries(map).map(([name, count]) => ({
    name,
    count,
    icon: CATEGORY_META[name]?.icon || '🎵',
    color: CATEGORY_META[name]?.color || '#456a5d',
  }))
})

const videoCount = computed(() => allAudios.value.filter(a => a.media_type === 'video').length)

const myFavoriteCount = computed(() => allAudios.value.filter(a => a.is_favorited).length)
const myLikeCount = computed(() => allAudios.value.filter(a => a.is_liked).length)

const filteredAudios = computed(() => {
  if (showFavorites.value) return allAudios.value.filter(a => a.is_favorited)
  if (showLiked.value) return allAudios.value.filter(a => a.is_liked)
  if (activeCategory.value === '全部') return allAudios.value
  return allAudios.value.filter(a => a.category === activeCategory.value)
})

const emptyMessage = computed(() => {
  if (showFavorites.value) return '还没有收藏的训练内容'
  if (showLiked.value) return '还没有点赞的训练内容'
  return '该分类下暂无内容'
})

onMounted(() => loadAudios())
onActivated(() => loadAudios())

async function loadAudios() {
  loading.value = true
  try {
    const res = await getRelaxationAudios()
    allAudios.value = res.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

function selectAll() {
  showFavorites.value = false
  showLiked.value = false
  activeCategory.value = '全部'
}

function showFavoritesOnly() {
  showFavorites.value = true
  showLiked.value = false
  activeCategory.value = ''
}

function showLikedOnly() {
  showLiked.value = true
  showFavorites.value = false
  activeCategory.value = ''
}

function selectCategory(name) {
  showFavorites.value = false
  showLiked.value = false
  activeCategory.value = name
}

function getCategoryStyle(category) {
  return CATEGORY_META[category] || { icon: '🎵', color: '#456a5d' }
}
</script>

<style scoped>
.relaxation-page {
  width: 100%;
}

.hero-banner {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 40px 44px;
  margin-bottom: 28px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, #fee8c8 0%, #f0f5f0 55%, #d4f1e0 100%);
  color: #456a5d;
  overflow: hidden;
  border: 1px solid rgba(200, 220, 200, 0.45);
}

.hero-label {
  font-size: 14px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: #456a5d;
  margin-bottom: 10px;
}

.hero-banner h1 {
  font-size: clamp(26px, 3vw, 34px);
  font-weight: 700;
  margin-bottom: 10px;
}

.hero-desc {
  font-size: 16px;
  color: var(--text-secondary);
  max-width: 480px;
  line-height: 1.7;
}

.hero-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 20px 28px;
  margin-top: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 56px;
}

.stat-clickable {
  cursor: pointer;
  padding: 8px 12px;
  margin: -8px -12px;
  border-radius: 10px;
  transition: var(--transition);
}

.stat-clickable:hover {
  background: rgba(228, 237, 229, 0.55);
}

.stat-clickable.active {
  background: rgba(228, 237, 229, 0.75);
}

.stat-clickable.active strong,
.stat-clickable.active span {
  color: inherit;
}

.stat-item strong {
  font-size: 24px;
  font-weight: 700;
  color: #456a5d;
}

.stat-item span {
  font-size: 14px;
  color: var(--text-muted);
}

.hero-deco {
  position: relative;
  width: 160px;
  height: 160px;
  flex-shrink: 0;
}

.deco-ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid rgba(180, 210, 190, 0.25);
}

.r1 { width: 160px; height: 160px; top: 0; right: 0; }
.r2 { width: 110px; height: 110px; top: 25px; right: 25px; border-color: rgba(212, 241, 224, 0.45); }

.deco-emoji {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-40%, -50%);
  font-size: 60px;
}

.category-section {
  margin-bottom: 24px;
}

.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.category-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border: 1.5px solid var(--border);
  border-radius: 24px;
  background: #fff;
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  transition: var(--transition);
}

.category-tab:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.category-tab.active {
  background: var(--cat-color, var(--primary));
  border-color: var(--cat-color, var(--primary));
  color: #fff;
  font-weight: 600;
}

.tab-icon { font-size: 18px; }

.tab-badge {
  min-width: 20px;
  padding: 1px 7px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.08);
  font-size: 13px;
}

.category-tab.active .tab-badge {
  background: rgba(255, 255, 255, 0.25);
}

.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.media-card {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: var(--radius);
  border: 1px solid var(--border-light);
  overflow: hidden;
  color: inherit;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.media-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
  border-color: var(--card-accent);
}

.card-cover {
  position: relative;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, color-mix(in srgb, var(--card-accent) 20%, white), color-mix(in srgb, var(--card-accent) 8%, white));
}

.card-cover.video {
  background: linear-gradient(135deg, #2d3e50, color-mix(in srgb, var(--card-accent) 40%, #2d3e50));
}

.cover-icon {
  font-size: 56px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
}

.media-type-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  padding: 4px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  font-weight: 600;
  color: var(--card-accent);
}

.card-cover.video .media-type-badge {
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
}

.duration-badge {
  position: absolute;
  bottom: 12px;
  right: 12px;
  padding: 4px 10px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 13px;
}

.card-body {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-category {
  display: inline-block;
  width: fit-content;
  padding: 3px 10px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--card-accent) 12%, white);
  color: var(--card-accent);
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}

.card-body h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text);
}

.fav-mark {
  font-size: 15px;
  margin-left: 4px;
}

.card-meta {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.card-body p {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.6;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border-light);
  font-size: 15px;
  font-weight: 600;
  color: var(--card-accent);
}

.card-action .arrow {
  transition: var(--transition);
}

.media-card:hover .arrow {
  transform: translateX(4px);
}

@media (max-width: 768px) {
  .hero-banner {
    flex-direction: column;
    padding: 28px 24px;
    text-align: center;
  }

  .hero-desc { margin: 0 auto; }
  .hero-stats { justify-content: center; }
  .hero-deco { display: none; }
  .media-grid { grid-template-columns: 1fr; }
}
</style>
