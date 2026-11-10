<template>
  <div class="game-wrap">
    <div class="round-bar">第 {{ round }} / {{ totalRounds }} 局</div>

    <div v-if="!completed" class="gratitude-form">
      <p class="intro">写下三件让你心怀感激的事，无论大小，都值得被看见。</p>
      <div v-for="(item, i) in entries" :key="i" class="entry-block">
        <label>{{ prompts[i] }}</label>
        <textarea
          v-model="entries[i]"
          :placeholder="placeholders[i % placeholders.length]"
          rows="3"
        />
      </div>
      <button class="btn btn-primary" :disabled="!canSubmit" @click="submit">完成本局</button>
    </div>

    <div v-else-if="!sessionDone" class="gratitude-result">
      <p class="result-title">🌻 第 {{ round }} 局感恩清单</p>
      <div v-for="(item, i) in entries" :key="i" class="result-item">
        <span class="result-label">{{ prompts[i] }}</span>
        <p>{{ item }}</p>
      </div>
      <button class="btn btn-primary" @click="nextRound">开始第 {{ round + 1 }} 局</button>
    </div>

    <div v-else class="gratitude-result">
      <p class="result-title">🌻 {{ totalRounds }} 局全部完成</p>
      <div v-for="(block, bi) in allResults" :key="bi" class="round-block">
        <h4 class="round-label">第 {{ bi + 1 }} 局</h4>
        <div v-for="(item, i) in block.entries" :key="i" class="result-item">
          <span class="result-label">{{ block.prompts[i] }}</span>
          <p>{{ item }}</p>
        </div>
      </div>
      <p class="encourage">{{ encourageText }}</p>
      <button class="btn btn-outline" @click="reset">重新填写</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const totalRounds = 3

const ALL_PROMPTS = [
  '今天谁让你感到温暖？',
  '最近有什么小确幸？',
  '你身上有什么值得欣赏的特质？',
  '今天发生了什么好事？',
  '谁曾给过你帮助？',
  '你身边有什么美好的事物？',
  '今天学到了什么？',
  '有什么让你感到安心的时刻？',
  '你想感谢过去的自己什么？',
]

const placeholders = [
  '可以是一个微笑、一句关心……',
  '一杯好喝的奶茶、一次顺利的考试……',
  '比如善良、坚持、幽默感……',
]

const round = ref(1)
const prompts = ref([])
const entries = ref(['', '', ''])
const completed = ref(false)
const sessionDone = ref(false)
const allResults = ref([])

const encourageTexts = [
  '感恩练习能有效提升积极情绪，建议每天花几分钟回顾美好。',
  '注意到生活中的美好，是照顾心理健康的重要方式。',
  '你已经迈出了关注积极面的一步，继续保持！',
]

const encourageText = ref('')
const canSubmit = computed(() => entries.value.every(e => e.trim().length >= 2))

function pickPrompts() {
  const shuffled = [...ALL_PROMPTS].sort(() => Math.random() - 0.5)
  prompts.value = shuffled.slice(0, 3)
}

function submit() {
  allResults.value.push({
    entries: [...entries.value],
    prompts: [...prompts.value],
  })
  completed.value = true
  if (round.value >= totalRounds) {
    sessionDone.value = true
    encourageText.value = encourageTexts[Math.floor(Math.random() * encourageTexts.length)]
    saveHistory()
  }
}

function saveHistory() {
  const history = JSON.parse(localStorage.getItem('game_gratitude_history') || '[]')
  history.unshift({
    date: new Date().toISOString().slice(0, 10),
    rounds: allResults.value.length,
    entries: allResults.value.flatMap(r => r.entries),
  })
  localStorage.setItem('game_gratitude_history', JSON.stringify(history.slice(0, 10)))
}

function nextRound() {
  round.value++
  entries.value = ['', '', '']
  completed.value = false
  pickPrompts()
}

function reset() {
  round.value = 1
  entries.value = ['', '', '']
  completed.value = false
  sessionDone.value = false
  allResults.value = []
  pickPrompts()
}

pickPrompts()
</script>

<style scoped>
.round-bar {
  text-align: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 16px;
}

.intro {
  text-align: center;
  color: var(--text-secondary);
  margin-bottom: 24px;
  font-size: 17px;
  line-height: 1.7;
}

.entry-block { margin-bottom: 20px; }

.entry-block label {
  display: block;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--primary);
}

.entry-block textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 16px;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.2s;
}

.entry-block textarea:focus {
  outline: none;
  border-color: var(--primary);
}

.gratitude-form .btn {
  display: block;
  margin: 8px auto 0;
}

.gratitude-result {
  max-width: 480px;
  margin: 0 auto;
}

.result-title {
  font-size: 22px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 20px;
}

.round-block { margin-bottom: 20px; }

.round-label {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.result-item {
  padding: 14px 16px;
  background: #fffbf0;
  border-radius: 10px;
  margin-bottom: 12px;
  border-left: 3px solid #f0a030;
}

.result-label {
  font-size: 14px;
  color: var(--text-muted);
  display: block;
  margin-bottom: 4px;
}

.result-item p {
  font-size: 17px;
  line-height: 1.6;
}

.encourage {
  text-align: center;
  color: var(--text-secondary);
  font-size: 16px;
  margin: 20px 0;
  line-height: 1.7;
}

.gratitude-result .btn {
  display: block;
  margin: 0 auto;
}
</style>
