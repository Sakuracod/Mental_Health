<template>
  <div class="game-wrap">
    <div class="toolbar">
      <label class="size-control">
        格子大小
        <input
          v-model.number="gridSize"
          type="range"
          min="5"
          max="20"
          step="1"
          :disabled="sessionDone"
          @change="onGridSizeChange"
        />
        <strong>{{ gridSize }}×{{ gridSize }}</strong>
      </label>
      <span class="round-bar">第 {{ round }} / {{ totalRounds }} 幅</span>
    </div>

    <div class="color-palette">
      <button
        v-for="c in palette"
        :key="c"
        type="button"
        class="color-btn"
        :class="{ active: !eraseMode && activeColor === c }"
        :style="{ background: c }"
        :title="'选用此色'"
        @click="pickColor(c)"
      />
      <button
        type="button"
        class="tool-btn"
        :class="{ active: eraseMode }"
        title="擦除"
        @click="eraseMode = true"
      >
        擦除
      </button>
      <button type="button" class="btn btn-outline btn-sm" @click="clearCurrent">清空本幅</button>
      <button type="button" class="btn btn-outline btn-sm" @click="saveRecord">保存记录</button>
    </div>

    <div
      class="color-grid"
      :style="{ gridTemplateColumns: `repeat(${gridSize}, 1fr)` }"
      @pointerdown="onGridPointer"
      @pointermove="onGridDrag"
      @pointerup="dragging = false"
      @pointerleave="dragging = false"
    >
      <button
        v-for="(cell, i) in cells"
        :key="`${gridSize}-${i}`"
        type="button"
        class="color-cell"
        :data-index="i"
        :style="{ background: cell || '#f8fafb' }"
      />
    </div>

    <div class="color-actions">
      <button v-if="round < totalRounds" class="btn btn-primary" :disabled="sessionDone" @click="nextRound">
        完成，下一幅
      </button>
      <button v-else class="btn btn-primary" :disabled="sessionDone" @click="finishSession">
        完成全部 {{ totalRounds }} 幅
      </button>
    </div>

    <p v-if="saveMsg" class="save-msg">{{ saveMsg }}</p>
    <p v-if="sessionDone" class="done-msg">🎨 三幅涂色已完成，做得很好！</p>
    <p v-else class="color-tip">选择颜色点击或拖动涂色；点「擦除」可去掉格子颜色。可随时保存记录。</p>

    <section v-if="records.length" class="records">
      <div class="records-head">
        <h3>已保存记录</h3>
        <button type="button" class="btn btn-outline btn-sm" @click="clearAllRecords">清空全部记录</button>
      </div>
      <div class="records-list">
        <article v-for="rec in records" :key="rec.id" class="record-card">
          <div
            class="record-preview"
            :style="{ gridTemplateColumns: `repeat(${rec.gridSize}, 1fr)` }"
          >
            <span
              v-for="(cell, i) in rec.cells"
              :key="i"
              class="preview-cell"
              :style="{ background: cell || '#f8fafb' }"
            />
          </div>
          <div class="record-meta">
            <p>{{ formatTime(rec.savedAt) }}</p>
            <p>{{ rec.gridSize }}×{{ rec.gridSize }} · 第 {{ rec.round }} 幅</p>
            <div class="record-actions">
              <button type="button" class="btn btn-outline btn-sm" @click="loadRecord(rec)">载入</button>
              <button type="button" class="btn btn-outline btn-sm danger" @click="deleteRecord(rec.id)">删除</button>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const STORAGE_KEY = 'xinyu_coloring_records'

const totalRounds = 3
const palette = ['#a8e6cf', '#b8d4f0', '#f5c6d4', '#d4c5f0', '#ffe0b2', '#c9e4ca', '#f0e6fa', '#ffd6e0']

const activeColor = ref(palette[0])
const eraseMode = ref(false)
const gridSize = ref(10)
const round = ref(1)
const sessionDone = ref(false)
const cells = ref([])
const records = ref([])
const saveMsg = ref('')
const dragging = ref(false)

let saveTimer = null

function initGrid() {
  const size = gridSize.value
  cells.value = Array(size * size).fill('')
}

function pickColor(c) {
  eraseMode.value = false
  activeColor.value = c
}

function paintAt(i) {
  if (sessionDone.value || i < 0 || i >= cells.value.length) return
  const next = cells.value.slice()
  next[i] = eraseMode.value ? '' : activeColor.value
  cells.value = next
}

function onGridPointer(e) {
  if (sessionDone.value) return
  const btn = e.target.closest('.color-cell')
  if (!btn) return
  dragging.value = true
  paintAt(Number(btn.dataset.index))
}

function onGridDrag(e) {
  if (!dragging.value || sessionDone.value) return
  const el = document.elementFromPoint(e.clientX, e.clientY)
  const btn = el?.closest?.('.color-cell')
  if (!btn) return
  paintAt(Number(btn.dataset.index))
}

function clearCurrent() {
  initGrid()
  saveMsg.value = ''
}

function onGridSizeChange() {
  const size = Math.min(20, Math.max(5, Number(gridSize.value) || 10))
  gridSize.value = size
  initGrid()
}

function nextRound() {
  if (round.value < totalRounds) {
    round.value++
    initGrid()
    saveMsg.value = ''
  }
}

function finishSession() {
  sessionDone.value = true
}

function loadRecords() {
  try {
    records.value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    records.value = []
  }
}

function persistRecords() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records.value))
}

function saveRecord() {
  const snapshot = {
    id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    savedAt: Date.now(),
    gridSize: gridSize.value,
    round: round.value,
    cells: cells.value.slice(),
  }
  records.value = [snapshot, ...records.value].slice(0, 30)
  persistRecords()
  saveMsg.value = '已保存到本机记录'
  clearTimeout(saveTimer)
  saveTimer = setTimeout(() => { saveMsg.value = '' }, 2500)
}

function loadRecord(rec) {
  sessionDone.value = false
  gridSize.value = rec.gridSize
  round.value = rec.round || 1
  cells.value = rec.cells.slice()
  eraseMode.value = false
  saveMsg.value = '已载入该记录，可继续涂改'
  clearTimeout(saveTimer)
  saveTimer = setTimeout(() => { saveMsg.value = '' }, 2500)
}

function deleteRecord(id) {
  records.value = records.value.filter(r => r.id !== id)
  persistRecords()
}

function clearAllRecords() {
  if (!confirm('确定清空全部涂色记录？')) return
  records.value = []
  persistRecords()
}

function formatTime(ts) {
  const d = new Date(ts)
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

onMounted(loadRecords)
initGrid()
</script>

<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 16px 28px;
  margin-bottom: 16px;
}

.size-control {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  color: var(--text-secondary);
}

.size-control input[type="range"] {
  width: 140px;
  accent-color: var(--primary);
}

.size-control strong {
  color: var(--primary);
  min-width: 3.5em;
}

.round-bar {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary);
}

.color-palette {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.color-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform 0.15s;
  padding: 0;
}

.color-btn.active {
  border-color: var(--text);
  transform: scale(1.15);
}

.tool-btn {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
}

.tool-btn.active {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--accent-light, #d4f1e0);
  font-weight: 600;
}

.btn-sm {
  padding: 6px 14px;
  font-size: 14px;
}

.color-grid {
  display: grid;
  gap: 2px;
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
  touch-action: none;
  user-select: none;
}

.color-cell {
  aspect-ratio: 1;
  border: 1px solid var(--border-light);
  border-radius: 3px;
  cursor: crosshair;
  transition: background 0.1s;
  padding: 0;
  pointer-events: auto;
}

.color-actions {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.color-tip, .done-msg, .save-msg {
  text-align: center;
  font-size: 15px;
  color: var(--text-muted);
  margin-top: 16px;
}

.done-msg {
  color: var(--primary);
  font-size: 17px;
  font-weight: 600;
}

.save-msg {
  color: var(--success, #3cb371);
  font-weight: 600;
}

.records {
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
}

.records-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.records-head h3 {
  margin: 0;
  font-size: 17px;
  color: var(--text);
}

.records-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}

.record-card {
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.75);
}

.record-preview {
  display: grid;
  gap: 1px;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: #eef2f5;
}

.preview-cell {
  display: block;
  min-height: 0;
}

.record-meta {
  margin-top: 10px;
  font-size: 13px;
  color: var(--text-muted);
}

.record-meta p {
  margin: 0 0 4px;
}

.record-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.danger {
  color: var(--danger, #e85d5d) !important;
  border-color: rgba(232, 93, 93, 0.35) !important;
}
</style>
