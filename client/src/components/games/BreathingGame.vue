<template>
  <div class="game-wrap">
    <div class="breath-visual">
      <div class="breath-ring" :class="phase" :style="{ transform: `scale(${scale})` }">
        <span class="breath-emoji">{{ phaseEmoji }}</span>
      </div>
      <p class="phase-text">{{ phaseText }}</p>
      <p class="phase-count">{{ countdown }}</p>
    </div>

    <div v-if="sessionDone" class="session-done">
      <p>🌿 已完成 {{ targetRounds }} 轮呼吸练习</p>
      <button class="btn btn-primary" @click="restartSession">再练 {{ targetRounds }} 轮</button>
    </div>

    <div v-else class="breath-controls">
      <button v-if="!running" class="btn btn-primary" @click="start">开始练习</button>
      <button v-else class="btn btn-outline" @click="stop">暂停</button>
      <span class="cycle-info">已完成 {{ cycles }} / {{ targetRounds }} 轮</span>
    </div>

    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
    </div>

    <p class="breath-tip">盒式呼吸：吸气 4 秒 → 屏息 4 秒 → 呼气 4 秒 → 屏息 4 秒（共 {{ targetRounds }} 轮）</p>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'

const targetRounds = 5

const PHASES = [
  { key: 'inhale', text: '吸气', emoji: '🌬️', duration: 4 },
  { key: 'hold1', text: '屏息', emoji: '⏸️', duration: 4 },
  { key: 'exhale', text: '呼气', emoji: '💨', duration: 4 },
  { key: 'hold2', text: '屏息', emoji: '⏸️', duration: 4 },
]

const running = ref(false)
const phaseIndex = ref(0)
const countdown = ref(4)
const cycles = ref(0)
const sessionDone = ref(false)
let timer = null

const phase = computed(() => PHASES[phaseIndex.value].key)
const phaseText = computed(() => PHASES[phaseIndex.value].text)
const phaseEmoji = computed(() => PHASES[phaseIndex.value].emoji)

const progressPercent = computed(() =>
  Math.min(100, (cycles.value / targetRounds) * 100)
)

const scale = computed(() => {
  const p = PHASES[phaseIndex.value].key
  if (p === 'inhale') return 1 + (4 - countdown.value) * 0.08
  if (p === 'exhale') return 1.32 - (4 - countdown.value) * 0.08
  if (p === 'hold1') return 1.32
  return 1
})

function tick() {
  countdown.value--
  if (countdown.value <= 0) {
    const next = (phaseIndex.value + 1) % PHASES.length
    if (next === 0) {
      cycles.value++
      if (cycles.value >= targetRounds) {
        stop()
        sessionDone.value = true
        return
      }
    }
    phaseIndex.value = next
    countdown.value = PHASES[next].duration
  }
}

function start() {
  sessionDone.value = false
  running.value = true
  if (cycles.value >= targetRounds) {
    cycles.value = 0
  }
  phaseIndex.value = 0
  countdown.value = PHASES[0].duration
  timer = setInterval(tick, 1000)
}

function stop() {
  running.value = false
  if (timer) clearInterval(timer)
  timer = null
}

function restartSession() {
  cycles.value = 0
  sessionDone.value = false
  start()
}

onUnmounted(stop)
</script>

<style scoped>
.breath-visual {
  text-align: center;
  padding: 20px 0 32px;
}

.breath-ring {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(107, 201, 160, 0.3), rgba(61, 139, 158, 0.15));
  border: 3px solid var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  transition: transform 1s ease;
}

.breath-emoji { font-size: 52px; }

.phase-text {
  font-size: 24px;
  font-weight: 600;
  color: var(--primary);
}

.phase-count {
  font-size: 52px;
  font-weight: 700;
  color: var(--primary-light);
  margin-top: 4px;
}

.breath-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 12px;
}

.cycle-info {
  font-size: 16px;
  color: var(--text-secondary);
  font-weight: 600;
}

.progress-bar {
  max-width: 320px;
  height: 8px;
  background: rgba(69, 106, 93, 0.12);
  border-radius: 999px;
  margin: 0 auto 16px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  border-radius: 999px;
  transition: width 0.4s ease;
}

.session-done {
  text-align: center;
  margin-bottom: 16px;
}

.session-done p {
  font-size: 19px;
  margin-bottom: 14px;
  color: var(--primary);
}

.breath-tip {
  text-align: center;
  font-size: 15px;
  color: var(--text-muted);
}
</style>
