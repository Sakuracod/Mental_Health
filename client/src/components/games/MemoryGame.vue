<template>
  <div class="game-wrap">
    <div class="game-stats">
      <span>第 <strong>{{ round }}</strong>/{{ totalRounds }} 局</span>
      <span>步数 <strong>{{ moves }}</strong></span>
      <span>配对 <strong>{{ matched }}/{{ pairs.length }}</strong></span>
      <span>用时 <strong>{{ formatTime(elapsed) }}</strong></span>
    </div>

    <div v-if="sessionDone" class="game-result">
      <p>🎉 三局全部完成！</p>
      <p class="result-detail">总步数 {{ totalMoves }}，总用时 {{ formatTime(totalElapsed) }}</p>
      <button class="btn btn-primary" @click="restartSession">再玩一次</button>
    </div>

    <div v-else-if="roundWon" class="game-result">
      <p>🎉 第 {{ round }} 局完成！</p>
      <p class="result-detail">{{ moves }} 步，用时 {{ formatTime(elapsed) }}</p>
      <button class="btn btn-primary" @click="nextRound">进入第 {{ round + 1 }} 局</button>
    </div>

    <div v-else class="card-grid" :class="{ large: pairs.length > 6 }">
      <button
        v-for="(card, i) in cards"
        :key="i"
        class="memory-card"
        :class="{ flipped: card.flipped || card.matched, matched: card.matched }"
        :disabled="card.matched || lock"
        @click="flip(i)"
      >
        <div class="card-inner">
          <div class="card-back">?</div>
          <div class="card-front">
            <span class="card-emoji">{{ card.emoji }}</span>
            <span class="card-label">{{ card.label }}</span>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const totalRounds = 3

const ALL_PAIRS = [
  { emoji: '😊', label: '开心' },
  { emoji: '😌', label: '平静' },
  { emoji: '😰', label: '焦虑' },
  { emoji: '😢', label: '低落' },
  { emoji: '😠', label: '愤怒' },
  { emoji: '🧘', label: '放松' },
  { emoji: '😲', label: '惊讶' },
  { emoji: '😴', label: '疲惫' },
  { emoji: '🤗', label: '温暖' },
]

const pairs = computed(() => ALL_PAIRS.slice(0, round.value >= 3 ? 9 : round.value >= 2 ? 8 : 6))

const cards = ref([])
const round = ref(1)
const moves = ref(0)
const totalMoves = ref(0)
const elapsed = ref(0)
const totalElapsed = ref(0)
const lock = ref(false)
const first = ref(null)
const roundWon = ref(false)
const sessionDone = ref(false)
let timer = null

const matched = computed(() => cards.value.filter(c => c.matched).length / 2)
const allMatched = computed(() => matched.value === pairs.value.length && cards.value.length > 0)

function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function formatTime(s) {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return m ? `${m}:${String(sec).padStart(2, '0')}` : `${sec}s`
}

function initRound() {
  const deck = shuffle(
    pairs.value.flatMap((p, id) => [
      { ...p, pairId: id, flipped: false, matched: false },
      { ...p, pairId: id, flipped: false, matched: false },
    ])
  )
  cards.value = deck
  moves.value = 0
  first.value = null
  lock.value = false
  roundWon.value = false
  elapsed.value = 0
}

function restartSession() {
  round.value = 1
  totalMoves.value = 0
  totalElapsed.value = 0
  sessionDone.value = false
  initRound()
}

function nextRound() {
  totalMoves.value += moves.value
  totalElapsed.value += elapsed.value
  round.value++
  initRound()
}

async function flip(i) {
  const card = cards.value[i]
  if (card.flipped || card.matched || lock.value || roundWon.value) return
  card.flipped = true

  if (first.value === null) {
    first.value = i
    return
  }

  moves.value++
  lock.value = true
  const a = cards.value[first.value]
  const b = card

  if (a.pairId === b.pairId) {
    a.matched = true
    b.matched = true
    first.value = null
    lock.value = false
    if (allMatched.value) {
      if (timer) clearInterval(timer)
      if (round.value >= totalRounds) {
        totalMoves.value += moves.value
        totalElapsed.value += elapsed.value
        sessionDone.value = true
      } else {
        roundWon.value = true
      }
    }
  } else {
    await new Promise(r => setTimeout(r, 700))
    a.flipped = false
    b.flipped = false
    first.value = null
    lock.value = false
  }
}

onMounted(() => {
  initRound()
  timer = setInterval(() => {
    if (!roundWon.value && !sessionDone.value) elapsed.value++
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.game-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 24px;
  justify-content: center;
  margin-bottom: 24px;
  font-size: 16px;
  color: var(--text-secondary);
}

.game-stats strong {
  color: var(--primary);
  font-size: 20px;
  margin-left: 4px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  width: 100%;
  max-width: 560px;
  margin: 0 auto;
}

.card-grid.large {
  max-width: 640px;
  gap: 10px;
}

.memory-card {
  aspect-ratio: 3/4;
  perspective: 600px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.memory-card:disabled { cursor: default; }

.card-inner {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.4s;
  border-radius: 12px;
}

.memory-card.flipped .card-inner,
.memory-card.matched .card-inner {
  transform: rotateY(180deg);
}

.card-back, .card-front {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.card-back {
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  color: #fff;
  font-size: 30px;
  font-weight: 700;
}

.card-front {
  background: #fff;
  border: 2px solid var(--border);
  transform: rotateY(180deg);
}

.memory-card.matched .card-front {
  border-color: var(--accent);
  background: #f0faf5;
}

.card-emoji { font-size: 34px; }
.card-label { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }

.game-result {
  text-align: center;
  padding: 32px;
}

.game-result p { font-size: 20px; margin-bottom: 8px; }

.result-detail {
  color: var(--text-secondary);
  font-size: 16px !important;
  margin-bottom: 20px !important;
}

@media (max-width: 480px) {
  .card-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
