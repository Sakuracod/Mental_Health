<template>
  <div class="detail-page">
    <router-link to="/relaxation" class="back-link">← 返回放松训练</router-link>

    <div v-if="loading" class="empty-state card">加载中...</div>

    <template v-else-if="item">
      <section class="player-section" :class="item.media_type">
        <div class="player-wrap">
          <video
            v-if="item.media_type === 'video'"
            ref="playerRef"
            :src="mediaUrl"
            controls
            autoplay
            playsinline
            class="media-player video-player"
          >
            您的浏览器不支持视频播放
          </video>
          <div v-else class="audio-player-wrap">
            <div class="audio-visual">
              <span class="visual-icon">{{ item.cover_icon }}</span>
              <div class="visual-waves">
                <span v-for="i in 5" :key="i" class="wave" :class="{ playing: isPlaying }"></span>
              </div>
            </div>
            <audio
              ref="playerRef"
              :src="mediaUrl"
              controls
              class="media-player audio-player"
              @play="isPlaying = true"
              @pause="isPlaying = false"
              @ended="isPlaying = false"
            >
              您的浏览器不支持音频播放
            </audio>
          </div>
        </div>
      </section>

      <section class="info-section card">
        <div class="info-header">
          <div class="info-tags">
            <span class="tag tag-category">{{ item.category }}</span>
            <span class="type-tag">{{ item.media_type === 'video' ? '🎬 视频引导' : '🎵 音频训练' }}</span>
            <span class="duration-tag">⏱ {{ item.duration }}</span>
          </div>
          <h1>{{ item.title }}</h1>
          <p class="description">{{ item.description }}</p>
          <div class="action-bar">
            <button class="action-btn" :class="{ active: item.is_liked }" @click="handleLike">
              {{ item.is_liked ? '❤️' : '🤍' }} {{ item.like_count || 0 }} 点赞
            </button>
            <button class="action-btn" :class="{ active: item.is_favorited }" @click="handleFavorite">
              {{ item.is_favorited ? '⭐' : '☆' }} {{ item.is_favorited ? '已收藏' : '收藏' }}
            </button>
          </div>
        </div>

        <div class="tips-box">
          <h3>训练建议</h3>
          <ul>
            <li>选择安静、舒适的环境，减少外界干扰</li>
            <li>佩戴耳机可获得更好的沉浸体验</li>
            <li>训练过程中如感到不适，可随时暂停休息</li>
          </ul>
        </div>
      </section>

      <section v-if="related.length" class="related-section">
        <h2 class="section-title">同分类推荐</h2>
        <div class="related-grid">
          <router-link
            v-for="r in related"
            :key="r.id"
            :to="`/relaxation/${r.id}`"
            class="related-card card"
          >
            <span class="related-icon">{{ r.cover_icon }}</span>
            <div>
              <h4>{{ r.title }}</h4>
              <span class="related-meta">{{ r.media_type === 'video' ? '视频' : '音频' }} · {{ r.duration }}</span>
            </div>
          </router-link>
        </div>
      </section>
    </template>

    <div v-else class="empty-state card">内容不存在或已下架</div>
  </div>
</template>

<script setup>
/**
 * 放松训练详情页 - 沉浸式音频/视频播放
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getRelaxationAudio, getRelaxationAudios, likeRelaxation, unlikeRelaxation, favoriteRelaxation, unfavoriteRelaxation } from '../api'

const route = useRoute()
const item = ref(null)
const related = ref([])
const loading = ref(true)
const isPlaying = ref(false)
const playerRef = ref(null)

const mediaUrl = computed(() => resolveMediaUrl(item.value?.audio_url))

onMounted(() => loadDetail())

watch(() => route.params.id, () => {
  if (playerRef.value) playerRef.value.pause?.()
  isPlaying.value = false
  loadDetail()
})

async function loadDetail() {
  loading.value = true
  try {
    const [detailRes, listRes] = await Promise.all([
      getRelaxationAudio(route.params.id),
      getRelaxationAudios()
    ])
    item.value = detailRes.data
    related.value = (listRes.data || [])
      .filter(a => a.id !== item.value.id && a.category === item.value.category)
      .slice(0, 3)
  } catch (e) {
    item.value = null
    console.error(e)
  } finally {
    loading.value = false
  }
}

function resolveMediaUrl(url) {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  if (url.startsWith('/')) return url
  return `/static/media/relaxation/${url}`
}

async function handleLike() {
  if (!item.value) return
  try {
    if (item.value.is_liked) {
      const res = await unlikeRelaxation(item.value.id)
      item.value.is_liked = false
      item.value.like_count = res.data.like_count
    } else {
      const res = await likeRelaxation(item.value.id)
      item.value.is_liked = true
      item.value.like_count = res.data.like_count
    }
  } catch (e) { alert(e.message) }
}

async function handleFavorite() {
  if (!item.value) return
  try {
    if (item.value.is_favorited) {
      await unfavoriteRelaxation(item.value.id)
      item.value.is_favorited = false
    } else {
      await favoriteRelaxation(item.value.id)
      item.value.is_favorited = true
    }
  } catch (e) { alert(e.message) }
}
</script>

<style scoped>
.detail-page {
  max-width: 960px;
  margin: 0 auto;
}

.back-link {
  display: inline-block;
  margin-bottom: 20px;
  font-size: 16px;
  color: var(--primary);
  font-weight: 500;
}

.player-section {
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: 24px;
  box-shadow: var(--shadow-lg);
}

.player-section.video {
  background: #1a1a2e;
}

.player-section.audio {
  background: linear-gradient(160deg, #2d6f80, #3d8b9e);
  padding: 40px 32px;
}

.player-wrap {
  width: 100%;
}

.video-player {
  width: 100%;
  max-height: 540px;
  display: block;
  background: #000;
}

.audio-player-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28px;
}

.audio-visual {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.visual-icon {
  font-size: 84px;
  filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.2));
}

.visual-waves {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 40px;
}

.wave {
  width: 6px;
  height: 12px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.35);
  transition: height 0.3s;
}

.wave.playing {
  animation: wave 0.8s ease-in-out infinite;
}

.wave.playing:nth-child(1) { animation-delay: 0s; }
.wave.playing:nth-child(2) { animation-delay: 0.15s; }
.wave.playing:nth-child(3) { animation-delay: 0.3s; }
.wave.playing:nth-child(4) { animation-delay: 0.15s; }
.wave.playing:nth-child(5) { animation-delay: 0s; }

@keyframes wave {
  0%, 100% { height: 12px; }
  50% { height: 36px; }
}

.audio-player {
  width: 100%;
  max-width: 560px;
}

.info-section {
  padding: 32px;
  margin-bottom: 28px;
}

.info-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.type-tag,
.duration-tag {
  padding: 3px 12px;
  border-radius: 12px;
  font-size: 14px;
  background: #f0f4f8;
  color: var(--text-secondary);
}

.info-header h1 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--text);
}

.description {
  font-size: 17px;
  color: var(--text-secondary);
  line-height: 1.8;
}

.action-bar {
  display: flex;
  gap: 12px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 8px 18px;
  border: 1.5px solid var(--border);
  border-radius: 20px;
  background: #fff;
  cursor: pointer;
  font-size: 16px;
  transition: var(--transition);
}

.action-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.action-btn.active {
  border-color: var(--primary);
  background: rgba(61, 139, 158, 0.08);
  color: var(--primary);
}

.tips-box {
  margin-top: 28px;
  padding: 20px 24px;
  background: #f8fbfd;
  border-radius: var(--radius);
  border-left: 4px solid var(--primary);
}

.tips-box h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--text);
}

.tips-box ul {
  padding-left: 18px;
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.9;
}

.related-section {
  margin-bottom: 32px;
}

.related-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}

.related-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  color: inherit;
  transition: var(--transition);
}

.related-card:hover {
  border-color: var(--primary);
  transform: translateX(4px);
}

.related-icon {
  font-size: 34px;
  flex-shrink: 0;
}

.related-card h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.related-meta {
  font-size: 14px;
  color: var(--text-muted);
}

@media (max-width: 768px) {
  .player-section.audio { padding: 28px 20px; }
  .info-section { padding: 24px 20px; }
  .info-header h1 { font-size: 24px; }
}
</style>
