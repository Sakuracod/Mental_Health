<template>
  <div class="game-wrap">
    <div class="game-stats">
      <span>第 <strong>{{ round }}</strong>/{{ totalRounds }} 局</span>
      <span>进度 <strong>{{ current - 1 }}/{{ total }}</strong></span>
      <span>用时 <strong>{{ formatTime(elapsed) }}</strong></span>
      <span v-if="bestTime">最佳 <strong>{{ formatTime(bestTime) }}</strong></span>
    </div>

    <div v-if="sessionDone" class="game-result">
      <p>🎯 {{ totalRounds }} 局全部完成！</p>
      <p class="result-detail">总用时 {{ formatTime(totalElapsed) }}，平均 {{ formatTime(avgTime) }}/局</p>
      <p v-if="isNewBest" class="new-best">刷新了个人最佳总用时！</p>
      <button class="btn btn-primary" @click="restartSession">再挑战一次</button>
    </div>

    <div v-else-if="roundDone" class="game-result">
      <p>第 {{ round }} 局完成！用时 {{ formatTime(elapsed) }}</p>
      <button class="btn btn-primary" @click="nextRound">
        {{ round >= totalRounds ? '查看总成绩' : `开始第 ${round + 1} 局` }}
      </button>
    </div>

    <div v-else class="focus-grid">
      <button
        v-for="n in numbers"
        :key="n"
        class="focus-cell"
        :class="{
          done: clicked.has(n),
          next: n === current,
          wrong: wrongFlash === n,
        }"
        :disabled="clicked.has(n)"
        @click="tap(n)"
      >
        {{ n }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const totalRounds = 3
const total = 16

const round = ref(1)
const numbers = ref([])
const current = ref(1)
const clicked = ref(new Set())
const elapsed = ref(0)
const totalElapsed = ref(0)
const roundDone = ref(false)
const sessionDone = ref(false)
const wrongFlash = ref(null)
const bestTime = ref(null)
const isNewBest = ref(false)
let timer = null

const STORAGE_KEY = 'game_focus_best_total'

const avgTime = computed(() =>
  totalRounds > 0 ? Math.round(totalElapsed.value / totalRounds) : 0
)

function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function formatTime(s) {
  return `${s}s`
}

function initRound() {
  numbers.value = shuffle(Array.from({ length: total }, (_, i) => i + 1))
  current.value = 1
  clicked.value = new Set()
  elapsed.value = 0
  roundDone.value = false
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    if (!roundDone.value && !sessionDone.value) elapsed.value++
  }, 1000)
}

function restartSession() {
  round.value = 1
  totalElapsed.value = 0
  sessionDone.value = false
  isNewBest.value = false
  initRound()
}

function nextRound() {
  totalElapsed.value += elapsed.value
  round.value++
  if (round.value > totalRounds) {
    sessionDone.value = true
    roundDone.value = false
    if (timer) clearInterval(timer)
    if (!bestTime.value || totalElapsed.value < bestTime.value) {
      bestTime.value = totalElapsed.value
      localStorage.setItem(STORAGE_KEY, String(totalElapsed.value))
      isNewBest.value = true
    }
    return
  }
  initRound()
}

function tap(n) {
  if (n !== current.value) {
    wrongFlash.value = n
    setTimeout(() => { wrongFlash.value = null }, 300)
    return
  }
  clicked.value.add(n)
  current.value++
  if (current.value > total) {
    roundDone.value = true
    if (timer) clearInterval(timer)
  }
}

onMounted(() => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) bestTime.value = parseInt(saved, 10)
  initRound()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.focus-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.focus-cell {
  aspect-ratio: 1;
  border: 2px solid var(--border);
  border-radius: 12px;
  background: #fff;
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  transition: all 0.2s;
}

.focus-cell.next {
  border-color: var(--primary);
  background: rgba(61, 139, 158, 0.08);
  box-shadow: 0 0 0 3px rgba(61, 139, 158, 0.15);
}

.focus-cell.done {
  opacity: 0.25;
  cursor: default;
}

.focus-cell.wrong {
  animation: shake 0.3s;
  border-color: var(--danger);
  background: #fff0f0;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.game-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 24px;
  justify-content: center;
  margin-bottom: 24px;
  font-size: 16px;
  color: var(--text-secondary);
}

.game-stats strong { color: var(--primary); font-size: 20px; margin-left: 4px; }

.game-result { text-align: center; padding: 32px; }
.game-result p { font-size: 20px; margin-bottom: 12px; }
.result-detail { font-size: 16px !important; color: var(--text-secondary); }
.new-best { color: var(--accent) !important; font-size: 16px !important; }
</style>
