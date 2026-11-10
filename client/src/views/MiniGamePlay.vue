<template>
  <div class="play-page">
    <div v-if="!game" class="not-found card">
      <p>未找到该游戏</p>
      <router-link to="/games" class="btn btn-primary">返回游戏列表</router-link>
    </div>

    <template v-else>
      <div class="play-header card">
        <router-link to="/games" class="back-link">← 返回游戏列表</router-link>
        <div class="play-title-row">
          <div class="play-title">
            <span class="title-icon" :style="{ background: `linear-gradient(135deg, ${game.color}22, ${game.color}11)` }">
              {{ game.icon }}
            </span>
            <div>
              <div class="title-meta">
                <span class="meta-tag">{{ game.category }}</span>
                <span class="meta-duration">⏱ {{ game.duration }}</span>
              </div>
              <h1>{{ game.name }}</h1>
              <p>{{ game.benefit }}</p>
            </div>
          </div>
          <button class="btn btn-outline guide-btn" @click="openGuide">📖 游戏说明</button>
        </div>
      </div>

      <div class="play-area card">
        <component :is="GameComponent" />
      </div>

      <GameGuideModal
        :visible="showGuide"
        :game="game"
        :is-first-time="isFirstTime"
        @close="closeGuide"
      />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, defineAsyncComponent, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getGameBySlug, hasSeenGuide, markGuideSeen } from '../data/games'
import GameGuideModal from '../components/GameGuideModal.vue'

const route = useRoute()
const game = computed(() => getGameBySlug(route.params.slug))
const showGuide = ref(false)
const isFirstTime = ref(false)

const componentMap = {
  memory: defineAsyncComponent(() => import('../components/games/MemoryGame.vue')),
  breathing: defineAsyncComponent(() => import('../components/games/BreathingGame.vue')),
  bubbles: defineAsyncComponent(() => import('../components/games/BubbleGame.vue')),
  focus: defineAsyncComponent(() => import('../components/games/FocusGame.vue')),
  gratitude: defineAsyncComponent(() => import('../components/games/GratitudeGame.vue')),
  coloring: defineAsyncComponent(() => import('../components/games/ColoringGame.vue')),
}

const GameComponent = computed(() => componentMap[route.params.slug] || null)

function openGuide() {
  isFirstTime.value = false
  showGuide.value = true
}

function closeGuide() {
  showGuide.value = false
  if (game.value) markGuideSeen(game.value.slug)
}

onMounted(() => {
  const slug = route.params.slug
  if (game.value && !hasSeenGuide(slug)) {
    isFirstTime.value = true
    showGuide.value = true
  }
})
</script>

<style scoped>
.play-page {
  width: 100%;
}

.not-found {
  text-align: center;
  padding: 48px;
  max-width: 480px;
  margin: 0 auto;
}

.not-found p {
  margin-bottom: 16px;
  color: var(--text-secondary);
}

.play-header {
  padding: 24px 28px;
  margin-bottom: 20px;
}

.back-link {
  font-size: 16px;
  color: var(--text-secondary);
  display: inline-block;
  margin-bottom: 16px;
}

.back-link:hover {
  color: var(--primary);
}

.play-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.play-title {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
}

.title-icon {
  font-size: 45px;
  width: 76px;
  height: 76px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.title-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.meta-tag {
  font-size: 13px;
  padding: 2px 8px;
  border-radius: 8px;
  background: rgba(61, 139, 158, 0.1);
  color: var(--primary);
  font-weight: 600;
}

.meta-duration {
  font-size: 14px;
  color: var(--text-muted);
}

.play-title h1 {
  font-size: clamp(20px, 2.5vw, 26px);
  margin-bottom: 4px;
}

.play-title p {
  font-size: 16px;
  color: var(--text-secondary);
}

.guide-btn {
  flex-shrink: 0;
  white-space: nowrap;
}

.play-area {
  padding: clamp(20px, 3vw, 36px) clamp(16px, 3vw, 32px);
}

@media (max-width: 640px) {
  .play-title-row {
    flex-direction: column;
    align-items: stretch;
  }

  .guide-btn {
    align-self: flex-end;
  }
}
</style>
