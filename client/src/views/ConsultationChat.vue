<template>
  <div class="chat-page">
    <div class="chat-header card">
      <router-link to="/consultations" class="back-link">← 返回</router-link>
      <h2>{{ consultation?.title || '在线咨询' }}</h2>
      <span :class="'tag tag-' + consultation?.status">
        {{ consultation?.status === 'active' ? '进行中' : '已结束' }}
      </span>
      <button
        v-if="consultation?.status === 'active'"
        class="btn btn-sm btn-outline"
        @click="handleClose"
      >结束对话</button>
    </div>

    <div ref="messageBox" class="chat-messages">
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="message-item"
        :class="{ mine: msg.sender_id === user?.id }"
      >
        <div class="message-sender">
          {{ msg.sender_name }}
          <span class="role-tag">{{ msg.sender_role === 'counselor' ? '咨询师' : '学生' }}</span>
        </div>
        <div class="message-bubble">{{ msg.content }}</div>
        <div class="message-time">{{ msg.created_at?.substring(11, 16) }}</div>
      </div>
      <div v-if="!messages.length" class="empty-state">暂无消息，发送第一条消息吧</div>
    </div>

    <div v-if="consultation?.status === 'active'" class="chat-input card">
      <input
        v-model="inputText"
        class="form-input"
        placeholder="输入消息..."
        @keyup.enter="handleSend"
      />
      <button class="btn btn-primary" :disabled="!inputText.trim() || sending" @click="handleSend">
        发送
      </button>
    </div>
  </div>
</template>

<script setup>
/**
 * 在线咨询聊天页面
 */
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { getConsultations, getMessages, sendMessage, closeConsultation } from '../api'

const route = useRoute()
const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
const consultation = ref(null)
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const messageBox = ref(null)
let pollTimer = null

onMounted(() => {
  loadChat()
  // 定时拉取新消息，实现师生双向对答
  pollTimer = setInterval(refreshMessages, 3000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function refreshMessages() {
  if (!route.params.id) return
  try {
    const mRes = await getMessages(route.params.id)
    const prevCount = messages.value.length
    messages.value = mRes.data
    if (mRes.data.length > prevCount) scrollToBottom()
    window.dispatchEvent(new Event('notification-read'))
  } catch (e) { /* 轮询静默失败 */ }
}

async function loadChat() {
  try {
    const [cRes, mRes] = await Promise.all([
      getConsultations({ page: 1, page_size: 100 }),
      getMessages(route.params.id)
    ])
    consultation.value = cRes.data.list.find(c => c.id == route.params.id)
    messages.value = mRes.data
    scrollToBottom()
    window.dispatchEvent(new Event('notification-read'))
  } catch (e) { console.error(e) }
}

/** 发送消息 */
async function handleSend() {
  if (!inputText.value.trim()) return
  sending.value = true
  try {
    await sendMessage(route.params.id, { content: inputText.value })
    inputText.value = ''
    const mRes = await getMessages(route.params.id)
    messages.value = mRes.data
    scrollToBottom()
    window.dispatchEvent(new Event('notification-read'))
  } catch (e) {
    alert(e.message)
  } finally {
    sending.value = false
  }
}

/** 结束对话 */
async function handleClose() {
  if (!confirm('确定结束此咨询对话？')) return
  try {
    await closeConsultation(route.params.id)
    loadChat()
  } catch (e) { alert(e.message) }
}

/** 滚动到消息底部 */
function scrollToBottom() {
  nextTick(() => {
    if (messageBox.value) {
      messageBox.value.scrollTop = messageBox.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 48px);
}
.chat-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  margin-bottom: 0;
  border-radius: 8px 8px 0 0;
}
.chat-header h2 { font-size: 18px; flex: 1; }
.back-link { font-size: 16px; color: #4a90a4; }

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f8f9fa;
}

.message-item {
  margin-bottom: 16px;
  max-width: 70%;
}
.message-item.mine {
  margin-left: auto;
  text-align: right;
}
.message-sender { font-size: 14px; color: var(--text-muted); margin-bottom: 4px; }
.role-tag {
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 8px;
  background: #eef4f7;
  color: var(--primary);
  font-size: 13px;
}
.message-item.mine .role-tag {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}
.message-bubble {
  display: inline-block;
  padding: 10px 16px;
  border-radius: 12px;
  background: #fff;
  font-size: 16px;
  line-height: 1.5;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.message-item.mine .message-bubble {
  background: #4a90a4;
  color: #fff;
}
.message-time { font-size: 13px; color: var(--text-muted); margin-top: 4px; }

.chat-input {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: 0 0 8px 8px;
}
.chat-input .form-input { flex: 1; }
</style>
