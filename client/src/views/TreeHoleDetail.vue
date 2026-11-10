<template>
  <div class="detail-page">
    <header class="page-top">
      <router-link to="/tree-hole" class="back-link">
        <span class="back-icon">←</span>
        <span>返回栖心树洞</span>
      </router-link>
      <span class="page-tag">🕊️ 树洞详情</span>
    </header>

    <div v-if="loading" class="empty-state card">加载中...</div>

    <template v-else-if="post">
      <article class="card post-detail">
        <div class="post-hero">
          <div class="author-avatar">
            <img v-if="post.avatar && !post.is_anonymous" :src="post.avatar" alt="头像" class="avatar-img" />
            <span v-else>{{ authorInitial }}</span>
          </div>
          <div class="author-info">
            <div class="author-row">
              <span class="post-author">{{ post.display_name }}</span>
              <span v-if="post.is_anonymous" class="anon-tag">匿名</span>
            </div>
            <span class="post-date">{{ formatDateTime(post.created_at) }}</span>
          </div>
          <button v-if="post.is_mine" class="btn btn-sm btn-danger post-delete" @click="handleDeletePost">
            删除
          </button>
        </div>

        <div v-if="post.content" class="post-body">
          <p class="post-content">{{ post.content }}</p>
        </div>
        <MediaGallery :record="post" alt="树洞配图" size="lg" class="post-media" />

        <div class="reply-count-bar">
          <span class="count-pill">💬 {{ post.replies?.length || 0 }} 条回复</span>
        </div>
      </article>

      <section class="replies-section">
        <div class="section-head">
          <h2 class="section-title">温暖回应</h2>
          <span class="section-count">{{ post.replies?.length || 0 }}</span>
        </div>

        <div v-if="post.replies?.length" class="replies-list">
          <div v-for="r in post.replies" :key="r.id" class="reply-item">
            <div class="reply-avatar">
              <img v-if="r.avatar" :src="r.avatar" alt="头像" class="avatar-img" />
              <span v-else>{{ replyInitial(r.display_name) }}</span>
            </div>
            <div class="reply-bubble">
              <div class="reply-header">
                <span class="reply-author">{{ r.display_name }}</span>
                <div class="reply-meta">
                  <span class="reply-date">{{ formatDateTime(r.created_at) }}</span>
                  <button v-if="r.is_mine" class="btn btn-sm btn-danger" @click="handleDeleteReply(r.id)">删除</button>
                </div>
              </div>
              <p v-if="r.content" class="reply-content">{{ r.content }}</p>
              <MediaGallery :record="r" alt="回复配图" class="reply-media" />
            </div>
          </div>
        </div>
        <div v-else class="empty-replies card">
          <span class="empty-icon">🤗</span>
          <p class="empty-title">还没有回复</p>
          <p class="empty-desc">来做第一个温暖回应的人吧</p>
        </div>
      </section>

      <div class="card reply-form-card">
        <div class="form-head">
          <span class="form-icon">✍️</span>
          <h3 class="form-title">写下你的回应</h3>
        </div>
        <textarea
          v-model="replyText"
          class="form-textarea reply-textarea"
          placeholder="写下你的温暖回应，让 TA 感受到陪伴与支持..."
          rows="4"
        ></textarea>

        <MediaUploadField
          v-model="replyMediaList"
          button-text="📷 添加图片/视频"
          :upload-fn="uploadTreeHoleMedia"
          @error="onUploadError"
        />

        <div class="form-footer">
          <span class="form-tip">真诚、友善的回应，是最好的礼物</span>
          <button
            class="btn btn-primary send-btn"
            :disabled="replying || (!replyText.trim() && !replyMediaList.length)"
            @click="handleReply"
          >
            {{ replying ? '发送中...' : '发送回复' }}
          </button>
        </div>
      </div>
    </template>

    <div v-else class="empty-state card">帖子不存在或已删除</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getTreeHolePost, replyTreeHole, uploadTreeHoleMedia,
  deleteTreeHolePost, deleteTreeHoleReply
} from '../api'
import MediaGallery from '../components/MediaGallery.vue'
import MediaUploadField from '../components/MediaUploadField.vue'
import { formatDateTime } from '../utils/date'

const route = useRoute()
const router = useRouter()
const post = ref(null)
const loading = ref(true)
const replyText = ref('')
const replyMediaList = ref([])
const replying = ref(false)

const authorInitial = computed(() => {
  const name = post.value?.display_name || '用'
  return name.charAt(0)
})

function replyInitial(name) {
  return (name || '用').charAt(0)
}

onMounted(() => loadDetail())

watch(() => route.params.id, () => loadDetail())

async function loadDetail() {
  loading.value = true
  try {
    const res = await getTreeHolePost(route.params.id)
    post.value = res.data
  } catch (e) {
    post.value = null
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleReply() {
  if (!replyText.value.trim() && !replyMediaList.value.length) return
  replying.value = true
  try {
    const payload = { content: replyText.value }
    if (replyMediaList.value.length) {
      payload.media_list = replyMediaList.value
    }
    await replyTreeHole(post.value.id, payload)
    replyText.value = ''
    replyMediaList.value = []
    await loadDetail()
  } catch (e) {
    alert(e.message)
  } finally {
    replying.value = false
  }
}

function onUploadError(message) {
  alert(message)
}

async function handleDeletePost() {
  if (!confirm('确定删除这条树洞留言？删除后无法恢复。')) return
  try {
    await deleteTreeHolePost(post.value.id)
    router.push('/tree-hole')
  } catch (e) {
    alert(e.message)
  }
}

async function handleDeleteReply(replyId) {
  if (!confirm('确定删除这条回复？')) return
  try {
    await deleteTreeHoleReply(post.value.id, replyId)
    await loadDetail()
  } catch (e) {
    alert(e.message)
  }
}
</script>

<style scoped>
.detail-page {
  max-width: min(920px, 100%);
  margin: 0 auto;
  padding-bottom: 32px;
}

.page-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.85);
  color: var(--primary);
  font-size: 16px;
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
}

.back-link:hover {
  background: #fff;
  transform: translateX(-2px);
}

.back-icon {
  font-size: 18px;
  line-height: 1;
}

.page-tag {
  font-size: 15px;
  color: var(--text-secondary);
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(228, 237, 229, 0.55);
}

.post-detail {
  padding: 32px;
  margin-bottom: 24px;
  border-left: 4px solid var(--primary);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(249, 252, 250, 0.92));
}

.post-hero {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}

.author-avatar,
.reply-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(69, 106, 93, 0.22);
  overflow: hidden;
}

.author-avatar .avatar-img,
.reply-avatar .avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.author-info {
  flex: 1;
  min-width: 0;
}

.author-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.post-author {
  font-weight: 700;
  font-size: 19px;
  color: var(--primary);
}

.anon-tag {
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(69, 106, 93, 0.1);
  color: var(--primary);
}

.post-date {
  display: block;
  margin-top: 4px;
  font-size: 15px;
  color: var(--text-muted);
}

.post-delete {
  flex-shrink: 0;
}

.post-body {
  padding: 20px 22px;
  margin-bottom: 16px;
  border-radius: 14px;
  background: rgba(248, 250, 249, 0.9);
  border: 1px solid rgba(69, 106, 93, 0.08);
}

.post-content {
  font-size: 20px;
  line-height: 1.9;
  color: var(--text);
  white-space: pre-wrap;
  margin: 0;
}

.post-media {
  margin-bottom: 18px;
}

.reply-count-bar {
  padding-top: 18px;
  border-top: 1px dashed rgba(69, 106, 93, 0.15);
}

.count-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(228, 237, 229, 0.7);
  color: var(--text-secondary);
  font-size: 15px;
}

.replies-section {
  margin-bottom: 24px;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  position: relative;
  padding-left: 12px;
}

.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 18px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--primary), var(--accent));
}

.section-count {
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: var(--primary);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.replies-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.reply-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.reply-avatar {
  width: 38px;
  height: 38px;
  font-size: 16px;
}

.reply-bubble {
  flex: 1;
  min-width: 0;
  padding: 16px 18px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(69, 106, 93, 0.08);
  box-shadow: var(--shadow-sm);
}

.reply-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.reply-author {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary);
}

.reply-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.reply-date {
  font-size: 14px;
  color: var(--text-muted);
}

.reply-content {
  font-size: 17px;
  line-height: 1.75;
  color: var(--text);
  white-space: pre-wrap;
  margin: 0;
}

.reply-media {
  margin-top: 12px;
}

.empty-replies {
  padding: 40px 24px;
  text-align: center;
  border: 1px dashed rgba(69, 106, 93, 0.18);
  background: rgba(255, 255, 255, 0.65);
}

.empty-icon {
  display: block;
  font-size: 38px;
  margin-bottom: 10px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 6px;
}

.empty-desc {
  font-size: 16px;
  color: var(--text-muted);
}

.reply-form-card {
  padding: 28px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(236, 245, 239, 0.88));
  border: 1px solid rgba(69, 106, 93, 0.12);
}

.form-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.form-icon {
  font-size: 22px;
}

.form-title {
  font-size: 19px;
  font-weight: 700;
  margin: 0;
}

.reply-textarea {
  min-height: 110px;
  margin-bottom: 14px;
  border-radius: 12px;
  border-color: rgba(69, 106, 93, 0.15);
  background: rgba(255, 255, 255, 0.92);
}

.form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.form-tip {
  font-size: 15px;
  color: var(--text-muted);
}

.send-btn {
  min-width: 120px;
  padding: 12px 28px;
  border-radius: 999px;
}

.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--text-muted);
}

@media (min-width: 1400px) {
  .detail-page {
    max-width: 980px;
  }

  .post-content {
    font-size: 21px;
  }
}

@media (max-width: 640px) {
  .post-detail,
  .reply-form-card {
    padding: 20px;
  }

  .post-hero {
    flex-wrap: wrap;
  }

  .post-delete {
    width: 100%;
  }

  .form-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .send-btn {
    width: 100%;
  }
}
</style>
