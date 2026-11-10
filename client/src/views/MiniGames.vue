<template>
  <div class="games-page">
    <section class="hero-banner">
      <div class="hero-content">
        <p class="hero-label">Play & Heal</p>
        <h1>心理小游戏</h1>
        <p class="hero-desc">通过轻松有趣的互动小游戏，调节情绪、训练专注、培养积极心态</p>
        <div class="hero-stats">
          <div class="stat-item">
            <strong>{{ GAMES.length }}</strong>
            <span>小游戏</span>
          </div>
          <div class="stat-item">
            <strong>{{ GAME_CATEGORIES.length }}</strong>
            <span>训练类型</span>
          </div>
        </div>
      </div>
      <div class="hero-deco">
        <div class="deco-ring r1"></div>
        <div class="deco-ring r2"></div>
        <span class="deco-emoji">🎮</span>
      </div>
    </section>

    <section class="category-section">
      <div class="category-tabs">
        <button
          class="category-tab"
          :class="{ active: activeCategory === '全部' }"
          @click="activeCategory = '全部'"
        >
          全部
          <span class="tab-badge">{{ GAMES.length }}</span>
        </button>
        <button
          v-for="cat in GAME_CATEGORIES"
          :key="cat"
          class="category-tab"
          :class="{ active: activeCategory === cat }"
          @click="activeCategory = cat"
        >
          {{ cat }}
          <span class="tab-badge">{{ countByCategory(cat) }}</span>
        </button>
      </div>
    </section>

    <section class="game-grid">
      <div
        v-for="game in filteredGames"
        :key="game.slug"
        class="game-card"
        :style="{ '--card-color': game.color }"
      >
        <div class="card-top">
          <span class="card-icon">{{ game.icon }}</span>
          <div class="card-meta">
            <span class="tag">{{ game.category }}</span>
            <span class="duration">⏱ {{ game.duration }}</span>
          </div>
        </div>

        <h3>{{ game.name }}</h3>
        <p class="card-desc">{{ game.desc }}</p>
        <span class="benefit">✨ {{ game.benefit }}</span>

        <div class="card-footer">
          <router-link :to="`/games/${game.slug}`" class="play-btn">开始 →</router-link>
          <button class="info-btn" @click="openGuide(game)">📖 游戏说明</button>
        </div>
      </div>
    </section>

    <GameGuideModal
      :visible="showGuide"
      :game="guideGame"
      :is-first-time="false"
      @close="showGuide = false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { GAMES, GAME_CATEGORIES } from '../data/games'
import GameGuideModal from '../components/GameGuideModal.vue'

const activeCategory = ref('全部')
const showGuide = ref(false)
const guideGame = ref(null)

const filteredGames = computed(() => {
  if (activeCategory.value === '全部') return GAMES
  return GAMES.filter(g => g.category === activeCategory.value)
})

function countByCategory(cat) {
  return GAMES.filter(g => g.category === cat).length
}

function openGuide(game) {
  guideGame.value = game
  showGuide.value = true
}
</script>

<style scoped>
.games-page {
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
  max-width: 520px;
  line-height: 1.7;
}

.hero-stats {
  display: flex;
  gap: 28px;
  margin-top: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
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
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
  font-weight: 600;
}

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

.game-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.game-card {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: var(--radius);
  border: 1px solid var(--border-light);
  border-left: 4px solid var(--card-color);
  padding: 22px 24px 0;
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
  min-height: 260px;
}

.game-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: color-mix(in srgb, var(--card-color) 30%, var(--border-light));
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;
}

.card-icon {
  font-size: 38px;
  line-height: 1;
}

.card-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.tag {
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--card-color) 12%, white);
  color: var(--card-color);
  font-weight: 600;
}

.duration {
  font-size: 14px;
  color: var(--text-muted);
}

.game-card h3 {
  font-size: 19px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text);
}

.card-desc {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.65;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.benefit {
  display: block;
  font-size: 14px;
  color: var(--accent);
  margin-top: 12px;
  line-height: 1.5;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding: 14px 0;
  border-top: 1px solid var(--border-light);
}

.play-btn {
  font-size: 16px;
  font-weight: 600;
  color: var(--card-color);
  text-decoration: none;
  transition: var(--transition);
}

.play-btn:hover {
  opacity: 0.8;
}

.info-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 8px;
  background: #f8fafb;
  font-size: 15px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: var(--transition);
}

.info-btn:hover {
  background: color-mix(in srgb, var(--card-color) 10%, white);
  color: var(--card-color);
}

@media (max-width: 1100px) {
  .game-grid {
    grid-template-columns: repeat(2, 1fr);
  }
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
  .game-grid { grid-template-columns: 1fr; }
}
</style>
