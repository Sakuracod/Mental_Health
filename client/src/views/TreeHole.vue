<template>

  <div>

    <div class="page-header">

      <h1 class="page-title">栖心树洞</h1>

      <p class="page-subtitle">倾诉你的心声，彼此温暖回应（支持匿名发布，所有用户均可回复）</p>

    </div>



    <!-- 发布留言 -->

    <div class="card post-form">

      <h2 class="section-title"><span>✏️</span> 写下你的心声</h2>

      <textarea

        v-model="newPost.content"

        class="form-textarea"

        placeholder="在这里倾诉你的烦恼、困惑或心情……"

        rows="4"

      ></textarea>



      <MediaUploadField

        v-model="newPost.media_list"

        button-text="📷 添加图片/视频"

        :upload-fn="uploadTreeHoleMedia"

        @error="onUploadError"

      />



      <div class="form-actions">

        <label class="anon-check">

          <input v-model="newPost.is_anonymous" type="checkbox" />

          匿名发布

        </label>

        <button

          class="btn btn-primary"

          :disabled="posting || (!newPost.content.trim() && !newPost.media_list.length)"

          @click="handlePost"

        >

          {{ posting ? '发布中...' : '发布留言' }}

        </button>

      </div>

    </div>



    <!-- 留言列表 -->

    <div class="posts-list">

      <router-link

        v-for="post in posts"

        :key="post.id"

        :to="`/tree-hole/${post.id}`"

        class="card post-card"

      >

        <div class="post-header">

          <span class="post-author">🕊️ {{ post.display_name }}</span>

          <span class="post-date">{{ formatListDate(post.created_at) }}</span>

        </div>

        <p v-if="post.content" class="post-content">{{ truncate(post.content) }}</p>

        <div v-if="getMediaList(post).length" class="post-media-hint">

          📎 含 {{ mediaCountLabel(post) }}

        </div>

        <div class="post-footer">

          <span v-if="post.reply_count > 0" class="reply-badge">💬 {{ post.reply_count }} 条回复</span>

          <span class="view-link">查看详情 →</span>

        </div>

      </router-link>

    </div>



    <div v-if="!posts.length" class="empty-state card">还没有留言，做第一个倾诉者吧</div>

  </div>

</template>



<script setup>

/**

 * 栖心树洞列表页

 */

import { ref, onMounted } from 'vue'

import { getTreeHolePosts, createTreeHolePost, uploadTreeHoleMedia } from '../api'

import MediaUploadField from '../components/MediaUploadField.vue'

import { getMediaList, mediaCountLabel } from '../utils/media'
import { formatDateTime } from '../utils/date'



const posts = ref([])

const newPost = ref({ content: '', is_anonymous: true, media_list: [] })

const posting = ref(false)



onMounted(() => loadPosts())



async function loadPosts() {

  try {

    const res = await getTreeHolePosts({ page: 1, page_size: 30 })

    posts.value = res.data.list

  } catch (e) { console.error(e) }

}



function truncate(text, max = 120) {

  if (!text || text.length <= max) return text

  return text.slice(0, max) + '...'

}

function formatListDate(value) {
  return formatDateTime(value)
}



function onUploadError(message) {

  alert(message)

}



async function handlePost() {

  posting.value = true

  try {

    const payload = {

      content: newPost.value.content,

      is_anonymous: newPost.value.is_anonymous

    }

    if (newPost.value.media_list.length) {

      payload.media_list = newPost.value.media_list

    }

    await createTreeHolePost(payload)

    newPost.value = { content: '', is_anonymous: true, media_list: [] }

    loadPosts()

  } catch (e) { alert(e.message) }

  finally { posting.value = false }

}

</script>



<style scoped>

.post-form { margin-bottom: 24px; }

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

.section-title span { margin-right: 6px; }

.media-upload { margin: 12px 0 4px; }

.upload-area {

  display: flex;

  align-items: center;

  gap: 12px;

  flex-wrap: wrap;

}

.file-input { display: none; }

.btn-outline {

  background: #fff;

  border: 1px dashed var(--primary);

  color: var(--primary);

  padding: 8px 16px;

  border-radius: 8px;

  cursor: pointer;

}

.btn-outline:disabled { opacity: 0.6; cursor: not-allowed; }

.upload-hint { font-size: 14px; color: var(--text-muted); }

.media-preview {

  position: relative;

  display: inline-block;

  max-width: 100%;

}

.preview-image,

.preview-video {

  max-width: 100%;

  max-height: 280px;

  border-radius: 10px;

  display: block;

  background: #eceff2;

}

.remove-media {

  position: absolute;

  top: 8px;

  right: 8px;

}

.form-actions {

  display: flex;

  justify-content: space-between;

  align-items: center;

  margin-top: 12px;

}

.anon-check {

  font-size: 16px;

  color: var(--text-secondary);

  display: flex;

  align-items: center;

  gap: 6px;

  cursor: pointer;

}



.posts-list { display: flex; flex-direction: column; gap: 16px; }

.post-card {

  display: block;

  padding: 24px;

  color: inherit;

  transition: var(--transition);

}

.post-card:hover {

  border-color: var(--primary);

  transform: translateX(4px);

}

.post-header {

  display: flex;

  justify-content: space-between;

  margin-bottom: 10px;

}

.post-author { font-weight: 600; font-size: 16px; color: var(--primary); }

.post-date { font-size: 14px; color: var(--text-muted); }

.post-content {

  font-size: 17px;

  line-height: 1.7;

  color: var(--text);

  margin-bottom: 10px;

}

.post-media-hint {

  font-size: 15px;

  color: var(--text-secondary);

  margin-bottom: 10px;

}

.post-footer {

  display: flex;

  justify-content: space-between;

  align-items: center;

  padding-top: 12px;

  border-top: 1px solid var(--border-light);

}

.reply-badge {

  font-size: 15px;

  color: var(--text-secondary);

}

.view-link {

  font-size: 15px;

  color: var(--primary);

  font-weight: 500;

  opacity: 0;

  transition: var(--transition);

}

.post-card:hover .view-link {

  opacity: 1;

}

@media (min-width: 1400px) {
  .section-title {
    font-size: 20px;
    margin-bottom: 18px;
  }

  .post-form :deep(.form-textarea) {
    font-size: 18px;
    line-height: 1.75;
  }

  .post-card {
    padding: 28px;
  }

  .posts-list {
    gap: 20px;
  }

  .post-author {
    font-size: 18px;
  }

  .post-date {
    font-size: 16px;
  }

  .post-content {
    font-size: 19px;
    line-height: 1.75;
  }

  .post-media-hint,
  .reply-badge,
  .view-link {
    font-size: 16px;
  }

  .anon-check {
    font-size: 17px;
  }

  .form-actions .btn-primary {
    padding: 12px 28px;
    font-size: 17px;
  }
}

@media (min-width: 1800px) {
  .section-title {
    font-size: 22px;
  }

  .post-form :deep(.form-textarea) {
    font-size: 19px;
  }

  .post-card {
    padding: 32px;
  }

  .post-author {
    font-size: 19px;
  }

  .post-date {
    font-size: 17px;
  }

  .post-content {
    font-size: 20px;
  }

  .post-media-hint,
  .reply-badge,
  .view-link {
    font-size: 17px;
  }

  .anon-check {
    font-size: 18px;
  }
}

</style>

