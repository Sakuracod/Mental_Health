<template>
  <div>
    <h1 class="page-title">咨询预约</h1>

    <div class="appointment-layout">
      <!-- 左侧：新建预约 -->
      <div v-if="user?.role === 'student'" class="card">
        <h2 class="section-title">新建预约</h2>
        <div v-if="errorMsg" class="alert alert-error">{{ errorMsg }}</div>
        <div v-if="successMsg" class="alert alert-success">{{ successMsg }}</div>

        <form @submit.prevent="handleCreate">
          <div class="form-group">
            <label>真实姓名 *</label>
            <input
              v-model="form.student_real_name"
              class="form-input"
              placeholder="请填写您的真实姓名"
              required
            />
            <p class="field-hint">预约咨询需使用真实姓名，便于咨询师确认身份</p>
          </div>
          <div class="form-group">
            <label>选择咨询师</label>
            <select v-model="form.counselor_id" class="form-select" required>
              <option value="">请选择</option>
              <option v-for="c in counselors" :key="c.id" :value="c.id">
                {{ c.real_name }} - {{ c.title }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>预约日期</label>
            <input v-model="form.appointment_date" type="date" class="form-input" required />
          </div>
          <div class="form-group">
            <label>时间段</label>
            <select v-model="form.time_slot" class="form-select" required>
              <option value="">请选择</option>
              <option v-for="t in timeSlots" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>预约原因</label>
            <textarea v-model="form.reason" class="form-textarea" placeholder="简要描述您想咨询的问题"></textarea>
          </div>
          <button type="submit" class="btn btn-primary" :disabled="submitting">提交预约</button>
        </form>
      </div>

      <!-- 咨询师列表 -->
      <div class="card">
        <h2 class="section-title">咨询师团队</h2>
        <div
          v-for="c in counselors"
          :key="c.id"
          class="counselor-card clickable"
          @click="goCounselorDetail(c.id)"
        >
          <div class="counselor-name">{{ c.real_name }}</div>
          <div class="counselor-title">{{ c.title }}</div>
          <div class="counselor-specialty">擅长：{{ c.specialty }}</div>
          <p class="counselor-intro">{{ c.introduction }}</p>
          <span class="view-detail">查看详细介绍 →</span>
        </div>
      </div>
    </div>

    <!-- 预约记录 -->
    <div class="card" style="margin-top:24px">
      <h2 class="section-title">预约记录</h2>
      <table v-if="appointments.length" class="table">
        <thead>
          <tr>
            <th>学生</th>
            <th>咨询师</th>
            <th>日期</th>
            <th>时间段</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in appointments" :key="a.id">
            <td>{{ a.student_name }}</td>
            <td>{{ a.counselor_name }}</td>
            <td>{{ a.appointment_date }}</td>
            <td>{{ a.time_slot }}</td>
            <td><span :class="'tag tag-' + a.status">{{ statusMap[a.status] }}</span></td>
            <td>
              <button
                v-if="canConfirm(a)"
                class="btn btn-sm btn-primary"
                @click="updateStatus(a.id, 'confirmed')"
              >确认</button>
              <button
                v-if="canComplete(a)"
                class="btn btn-sm btn-primary"
                @click="updateStatus(a.id, 'completed')"
              >完成</button>
              <button
                v-if="canCancel(a)"
                class="btn btn-sm btn-danger"
                @click="handleCancel(a.id)"
              >取消</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">暂无预约记录</div>
    </div>
  </div>
</template>

<script setup>
/**
 * 咨询预约页面
 * 学生可创建预约，咨询师可确认/完成预约
 */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getCounselors, getTimeSlots, getAppointments,
  createAppointment, updateAppointmentStatus, cancelAppointment
} from '../api'

const route = useRoute()
const router = useRouter()

const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
const counselors = ref([])
const timeSlots = ref([])
const appointments = ref([])
const form = ref({ student_real_name: '', counselor_id: '', appointment_date: '', time_slot: '', reason: '' })
const submitting = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const statusMap = {
  pending: '待确认', confirmed: '已确认',
  completed: '已完成', cancelled: '已取消'
}

onMounted(() => {
  if (user.value?.real_name) {
    form.value.student_real_name = user.value.real_name
  }
  loadData().then(() => {
    if (route.query.counselor) {
      form.value.counselor_id = String(route.query.counselor)
    }
  })
})

function goCounselorDetail(id) {
  router.push({ path: `/counselors/${id}`, query: { from: 'appointments' } })
}

async function loadData() {
  try {
    const [cRes, tRes, aRes] = await Promise.all([
      getCounselors(), getTimeSlots(), getAppointments({ page: 1, page_size: 20 })
    ])
    counselors.value = cRes.data
    timeSlots.value = tRes.data
    appointments.value = aRes.data.list
  } catch (e) { console.error(e) }
}

/** 创建预约 */
async function handleCreate() {
  submitting.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    await createAppointment(form.value)
    successMsg.value = '预约提交成功！'
    form.value = {
      student_real_name: user.value?.real_name || '',
      counselor_id: '', appointment_date: '', time_slot: '', reason: ''
    }
    loadData()
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    submitting.value = false
  }
}

/** 更新预约状态 */
async function updateStatus(id, status) {
  try {
    await updateAppointmentStatus(id, { status })
    loadData()
  } catch (e) { alert(e.message) }
}

/** 取消预约 */
async function handleCancel(id) {
  if (!confirm('确定取消此预约？')) return
  try {
    await cancelAppointment(id)
    loadData()
  } catch (e) { alert(e.message) }
}

function canConfirm(a) {
  return user.value?.role === 'counselor' && a.status === 'pending'
}
function canComplete(a) {
  return user.value?.role === 'counselor' && a.status === 'confirmed'
}
function canCancel(a) {
  return ['pending', 'confirmed'].includes(a.status)
}
</script>

<style scoped>
.appointment-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.section-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.counselor-card {
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}
.counselor-card.clickable {
  cursor: pointer;
  transition: background 0.2s;
  padding: 16px;
  margin: 0 -16px;
  border-radius: 8px;
}
.counselor-card.clickable:hover {
  background: #f8fbfc;
}
.view-detail {
  display: inline-block;
  margin-top: 8px;
  font-size: 14px;
  color: #4a90a4;
  font-weight: 600;
}
.counselor-name { font-weight: 600; font-size: 17px; }
.counselor-title { color: #4a90a4; font-size: 15px; margin: 4px 0; }
.counselor-specialty { font-size: 15px; color: var(--text-secondary); }
.counselor-intro { font-size: 15px; color: var(--text-muted); margin-top: 6px; }
.field-hint { font-size: 14px; color: var(--text-muted); margin-top: 6px; }
</style>
