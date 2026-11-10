<template>
  <div class="counselor-detail-page">
    <router-link :to="backPath" class="back-link">{{ backLabel }}</router-link>

    <div v-if="loading" class="empty-state card">加载中...</div>

    <template v-else-if="counselor">
      <section class="hero-card card">
        <div class="hero-avatar">
          <img v-if="counselor.avatar" :src="counselor.avatar" alt="头像" />
          <span v-else>{{ counselor.real_name?.charAt(0) }}</span>
        </div>
        <div class="hero-info">
          <h1>{{ counselor.real_name }}</h1>
          <p class="hero-title">{{ counselor.title }}</p>
          <div class="specialty-tags">
            <span v-for="tag in specialtyList" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>
      </section>

      <section class="card info-section">
        <h2 class="section-title">基本信息</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">性别</span>
            <span>{{ genderText }}</span>
          </div>
          <div v-if="counselor.phone" class="info-item">
            <span class="label">联系电话</span>
            <span>{{ counselor.phone }}</span>
          </div>
          <div v-if="counselor.email" class="info-item">
            <span class="label">联系邮箱</span>
            <span>{{ counselor.email }}</span>
          </div>
          <div class="info-item">
            <span class="label">可预约时间</span>
            <span>{{ availableDaysText }}</span>
          </div>
        </div>
      </section>

      <section class="card info-section">
        <h2 class="section-title">擅长领域</h2>
        <p class="text-block">{{ counselor.specialty }}</p>
      </section>

      <section class="card info-section">
        <h2 class="section-title">个人简介</h2>
        <p class="text-block">{{ counselor.introduction }}</p>
      </section>

      <section class="card info-section">
        <h2 class="section-title">详细介绍</h2>
        <p class="text-block detail-bio">{{ counselor.detail_bio }}</p>
      </section>

      <section class="action-bar card">
        <button class="btn btn-primary" @click="goAppointment">预约咨询</button>
        <button class="btn btn-outline" @click="goConsultation">在线咨询</button>
      </section>
    </template>

    <div v-else class="empty-state card">咨询师信息不存在</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCounselor } from '../api'

const route = useRoute()
const router = useRouter()
const counselor = ref(null)
const loading = ref(true)

const backPath = computed(() => {
  return route.query.from === 'consultations' ? '/consultations' : '/appointments'
})

const backLabel = computed(() => {
  return route.query.from === 'consultations' ? '← 返回在线咨询' : '← 返回咨询预约'
})

const weekdayMap = { 1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 7: '周日' }

const specialtyList = computed(() => {
  const text = counselor.value?.specialty || ''
  return text.split(/[,，]/).map(s => s.trim()).filter(Boolean)
})

const genderText = computed(() => {
  const map = { 0: '未知', 1: '男', 2: '女' }
  return map[counselor.value?.gender] || '未知'
})

const availableDaysText = computed(() => {
  const days = (counselor.value?.available_days || '1,2,3,4,5')
    .split(',')
    .map(d => weekdayMap[Number(d.trim())])
    .filter(Boolean)
  return days.length ? days.join('、') : '周一至周五'
})

onMounted(async () => {
  try {
    const res = await getCounselor(route.params.id)
    counselor.value = res.data
  } catch (e) {
    counselor.value = null
    console.error(e)
  } finally {
    loading.value = false
  }
})

function goAppointment() {
  router.push({ path: '/appointments', query: { counselor: counselor.value.id } })
}

function goConsultation() {
  router.push({ path: '/consultations', query: { counselor: counselor.value.id } })
}
</script>

<style scoped>
.counselor-detail-page {
  max-width: 860px;
  margin: 0 auto;
}

.back-link {
  display: inline-block;
  margin-bottom: 16px;
  color: var(--primary);
  font-size: 16px;
}

.hero-card {
  display: flex;
  gap: 24px;
  align-items: center;
  padding: 28px;
  margin-bottom: 20px;
}

.hero-avatar {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #4a90a4, #7ec8a0);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 38px;
  font-weight: 600;
  flex-shrink: 0;
}

.hero-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-info h1 {
  font-size: 28px;
  margin-bottom: 8px;
}

.hero-title {
  color: var(--primary);
  font-size: 17px;
  margin-bottom: 12px;
}

.specialty-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.specialty-tags .tag {
  background: #e8f4f8;
  color: #4a90a4;
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 14px;
}

.info-section {
  margin-bottom: 16px;
  padding: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 14px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 16px;
}

.info-item .label {
  color: var(--text-muted);
  font-size: 14px;
}

.text-block {
  font-size: 17px;
  line-height: 1.8;
  color: var(--text);
}

.detail-bio {
  white-space: pre-wrap;
}

.action-bar {
  display: flex;
  gap: 12px;
  padding: 20px 24px;
  margin-bottom: 24px;
}

.btn-outline {
  background: #fff;
  border: 1px solid var(--primary);
  color: var(--primary);
}
</style>
