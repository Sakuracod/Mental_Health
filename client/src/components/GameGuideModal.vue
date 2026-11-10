<template>
  <Teleport to="body">
    <div v-if="visible" class="guide-overlay" @click.self="onClose">
      <div class="guide-modal" :style="{ '--guide-color': game?.color }">
        <div class="guide-header">
          <span class="guide-icon">{{ game?.icon }}</span>
          <div>
            <h2>{{ game?.name }} · 游戏说明</h2>
            <p v-if="isFirstTime" class="first-badge">首次游玩引导</p>
          </div>
          <button class="close-btn" @click="onClose" aria-label="关闭">✕</button>
        </div>

        <div class="guide-body">
          <section class="guide-section">
            <h3>游戏介绍</h3>
            <p>{{ game?.guide?.intro }}</p>
          </section>

          <section class="guide-section">
            <h3>操作步骤</h3>
            <ol>
              <li v-for="(step, i) in game?.guide?.steps" :key="i">{{ step }}</li>
            </ol>
          </section>

          <section v-if="game?.guide?.tips?.length" class="guide-section">
            <h3>小贴士</h3>
            <ul>
              <li v-for="(tip, i) in game?.guide?.tips" :key="i">{{ tip }}</li>
            </ul>
          </section>

          <section v-if="game?.guide?.purpose" class="guide-section purpose">
            <h3>心理作用</h3>
            <p>{{ game.guide.purpose }}</p>
          </section>
        </div>

        <div class="guide-footer">
          <button class="btn btn-primary" @click="onClose">
            {{ isFirstTime ? '我知道了，开始游戏' : '关闭' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  game: { type: Object, default: null },
  isFirstTime: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

function onClose() {
  emit('close')
}
</script>

<style scoped>
.guide-overlay {
  position: fixed;
  inset: 0;
  background: rgba(30, 45, 61, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  backdrop-filter: blur(2px);
}

.guide-modal {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 520px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
  border-top: 4px solid var(--guide-color, var(--primary));
}

.guide-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-light);
}

.guide-icon {
  font-size: 38px;
  flex-shrink: 0;
}

.guide-header h2 {
  font-size: 20px;
  margin-bottom: 4px;
}

.first-badge {
  font-size: 14px;
  color: var(--guide-color, var(--primary));
  background: color-mix(in srgb, var(--guide-color, var(--primary)) 12%, white);
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 600;
}

.close-btn {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 20px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  flex-shrink: 0;
}

.close-btn:hover {
  background: var(--border-light);
  color: var(--text);
}

.guide-body {
  padding: 16px 24px;
  overflow-y: auto;
  flex: 1;
}

.guide-section {
  margin-bottom: 18px;
}

.guide-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--guide-color, var(--primary));
  margin-bottom: 8px;
}

.guide-section p {
  font-size: 16px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.guide-section ol {
  padding-left: 20px;
  font-size: 16px;
  color: var(--text-secondary);
  line-height: 1.8;
}

.guide-section ul {
  padding-left: 20px;
  font-size: 16px;
  color: var(--text-secondary);
  line-height: 1.8;
}

.guide-section.purpose {
  background: #f8fafb;
  padding: 12px 14px;
  border-radius: 10px;
  border-left: 3px solid var(--guide-color, var(--primary));
}

.guide-footer {
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border-light);
  text-align: center;
}
</style>
