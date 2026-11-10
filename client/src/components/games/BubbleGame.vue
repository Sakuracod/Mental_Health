<template>
  <div class="game-wrap">
    <div class="game-stats">
      <span>第 <strong>{{ currentRound }}</strong>/{{ totalRounds }} 局</span>
      <span>本局 <strong>{{ score }}</strong></span>
      <span>总计 <strong>{{ totalScore }}</strong></span>
      <span>剩余 <strong>{{ timeLeft }}s</strong></span>
    </div>

    <div
      class="bubble-area"
      ref="areaRef"
      @pointerdown.prevent="onAreaPointer"
    >
      <button
        v-for="b in bubbles"
        :key="b.id"
        type="button"
        class="bubble"
        :data-id="b.id"
        :style="{
          left: b.x + '%',
          bottom: b.y + '%',
          width: b.size + 'px',
          height: b.size + 'px',
          background: b.color,
        }"
        @pointerdown.stop.prevent="pop(b.id)"
      />
      <div v-if="!playing && !betweenRounds && !sessionDone" class="overlay-start">
        <p>把压力想象成气泡，点击戳破它们</p>
        <p class="overlay-sub">共 {{ totalRounds }} 局，每局 {{ roundSeconds }} 秒</p>
        <button class="btn btn-primary" @click="startSession">开始</button>
      </div>
      <div v-if="betweenRounds" class="overlay-start">
        <p>第 {{ currentRound - 1 }} 局完成！本局 {{ lastRoundScore }} 个</p>
        <button class="btn btn-primary" @click="startRound">开始第 {{ currentRound }} 局</button>
      </div>
      <div v-if="sessionDone" class="overlay-start">
        <p>🎉 {{ totalRounds }} 局全部完成！</p>
        <p>总共戳破 <strong>{{ totalScore }}</strong> 个气泡</p>
        <button class="btn btn-primary" @click="startSession">再玩一次</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'

const COLORS = ['#a8e6cf88', '#b8d4f088', '#f5c6d488', '#c9b8f088', '#a8d8ea88']

const totalRounds = 3
const roundSeconds = 60

const score = ref(0)
const totalScore = ref(0)
const lastRoundScore = ref(0)
const timeLeft = ref(roundSeconds)
const currentRound = ref(1)
const playing = ref(false)
const betweenRounds = ref(false)
const sessionDone = ref(false)
const bubbles = ref([])
const areaRef = ref(null)

let spawnTimer = null
let countdownTimer = null
let moveTimer = null
let idCounter = 0

function spawn() {
  if (!playing.value) return
  bubbles.value.push({
    id: ++idCounter,
    x: 5 + Math.random() * 85,
    y: -8,
    size: 36 + Math.random() * 44,
    speed: 0.35 + Math.random() * 0.55,
    color: COLORS[Math.floor(Math.random() * COLORS.length)],
  })
  if (bubbles.value.length > 24) {
    bubbles.value.shift()
  }
}

function tickMove() {
  if (!playing.value) return
  const next = []
  for (const b of bubbles.value) {
    const y = b.y + b.speed
    if (y < 115) next.push({ ...b, y })
  }
  bubbles.value = next
}

function pop(id) {
  if (!playing.value) return
  const before = bubbles.value.length
  bubbles.value = bubbles.value.filter(b => b.id !== id)
  if (bubbles.value.length < before) score.value++
}

/** 兜底：按点击坐标命中气泡（避免个别环境下事件异常） */
function onAreaPointer(e) {
  if (!playing.value || !areaRef.value) return
  const rect = areaRef.value.getBoundingClientRect()
  const px = e.clientX - rect.left
  const py = e.clientY - rect.top
  const hit = [...bubbles.value].reverse().find(b => {
    const cx = (b.x / 100) * rect.width
    const cy = rect.height - (b.y / 100) * rect.height
    const r = b.size / 2
    const dx = px - cx
    const dy = py - cy
    return dx * dx + dy * dy <= r * r
  })
  if (hit) pop(hit.id)
}

function clearTimers() {
  clearInterval(spawnTimer)
  clearInterval(countdownTimer)
  clearInterval(moveTimer)
  spawnTimer = null
  countdownTimer = null
  moveTimer = null
}

function startRound() {
  betweenRounds.value = false
  sessionDone.value = false
  score.value = 0
  timeLeft.value = roundSeconds
  playing.value = true
  bubbles.value = []
  spawnTimer = setInterval(spawn, 550)
  moveTimer = setInterval(tickMove, 32)
  countdownTimer = setInterval(() => {
    timeLeft.value--
    if (timeLeft.value <= 0) endRound()
  }, 1000)
  spawn()
}

function endRound() {
  playing.value = false
  clearTimers()
  bubbles.value = []
  lastRoundScore.value = score.value
  totalScore.value += score.value

  if (currentRound.value >= totalRounds) {
    sessionDone.value = true
    return
  }
  currentRound.value++
  betweenRounds.value = true
}

function startSession() {
  currentRound.value = 1
  totalScore.value = 0
  sessionDone.value = false
  betweenRounds.value = false
  startRound()
}

onUnmounted(clearTimers)
</script>

<style scoped>
.bubble-area {
  position: relative;
  height: clamp(320px, 45vh, 460px);
  width: 100%;
  background: linear-gradient(180deg, #e8f4f8, #f0f8f4);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--border-light);
  touch-action: manipulation;
  user-select: none;
}

.bubble {
  position: absolute;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.6);
  cursor: pointer;
  z-index: 1;
  transform: translate(-50%, 50%);
  transition: transform 0.12s, opacity 0.12s;
  pointer-events: auto;
  padding: 0;
  appearance: none;
  -webkit-tap-highlight-color: transparent;
}

.bubble:hover { transform: translate(-50%, 50%) scale(1.08); }
.bubble:active { transform: translate(-50%, 50%) scale(0.2); opacity: 0.4; }

.overlay-start {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.85);
  gap: 12px;
  z-index: 2;
}

.overlay-start p {
  font-size: 18px;
  color: var(--text-secondary);
  margin: 0;
}

.overlay-sub {
  font-size: 15px !important;
  color: var(--text-muted) !important;
}

.game-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 24px;
  justify-content: center;
  margin-bottom: 16px;
  font-size: 16px;
  color: var(--text-secondary);
}

.game-stats strong {
  color: var(--primary);
  font-size: 22px;
  margin-left: 4px;
}
</style>
