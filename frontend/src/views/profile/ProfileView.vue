<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <!-- 头部卡片 -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg">
      <div class="absolute -top-10 -right-10 w-48 h-48 bg-white/10 rounded-full"></div>
      <div class="absolute -bottom-8 -right-24 w-64 h-64 bg-white/5 rounded-full"></div>
      <div class="relative p-6 flex items-center gap-5">
        <div class="w-20 h-20 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-4xl font-black shrink-0 border border-white/20">
          {{ form.nickname?.[0]?.toUpperCase() || 'U' }}
        </div>
        <div class="min-w-0">
          <h1 class="text-2xl font-bold truncate">{{ form.nickname || '同学' }}</h1>
          <p class="text-blue-100 text-sm mt-1">{{ authStore.user?.email }}</p>
          <p class="text-blue-200 text-xs mt-1">{{ form.grade || '未设置年级' }}</p>
        </div>
      </div>
    </div>

    <!-- 基本信息 -->
    <div class="card">
      <div class="flex items-center gap-2 mb-5">
        <span class="w-1 h-5 bg-gradient-to-b from-blue-500 to-indigo-500 rounded-full inline-block"></span>
        <h3 class="font-bold text-gray-800">基本信息</h3>
      </div>

      <el-form :model="form" label-position="top" class="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" placeholder="请输入昵称" maxlength="50" />
        </el-form-item>

        <el-form-item label="年级">
          <el-select v-model="form.grade" placeholder="选择年级" class="w-full">
            <el-option v-for="g in grades" :key="g" :label="g" :value="g" />
          </el-select>
        </el-form-item>

        <el-form-item label="手机号码">
          <el-input v-model="form.phone" placeholder="请输入手机号码" maxlength="20" />
        </el-form-item>

        <el-form-item label="性别">
          <el-select v-model="form.gender" placeholder="选择性别" clearable class="w-full">
            <el-option label="男" value="male" />
            <el-option label="女" value="female" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="年龄">
          <el-input-number v-model="form.age" :min="1" :max="120" controls-position="right" class="w-full" />
        </el-form-item>

        <el-form-item label="邮箱（不可修改）">
          <el-input :model-value="authStore.user?.email" disabled />
        </el-form-item>
      </el-form>

      <div class="flex justify-end mt-2">
        <el-button type="primary" :loading="saving" @click="saveProfile">保存修改</el-button>
      </div>
    </div>

    <!-- 修改密码 -->
    <div class="card">
      <div class="flex items-center gap-2 mb-5">
        <span class="w-1 h-5 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full inline-block"></span>
        <h3 class="font-bold text-gray-800">修改密码</h3>
      </div>

      <el-form :model="pwdForm" label-position="top" class="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
        <el-form-item label="旧密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="请输入旧密码" />
        </el-form-item>
        <el-form-item label="新密码（至少6位）">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="请输入新密码" />
        </el-form-item>
      </el-form>

      <div class="flex justify-end mt-2">
        <el-button :loading="changingPwd" @click="changePwd">更新密码</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const grades = ['初一', '初二', '初三', '高一', '高二', '高三']

const form = reactive({
  nickname: '',
  grade: '',
  phone: '',
  gender: '' as string,
  age: undefined as number | undefined,
})

const pwdForm = reactive({ old_password: '', new_password: '' })

const saving = ref(false)
const changingPwd = ref(false)

function syncForm() {
  const u = authStore.user
  if (!u) return
  form.nickname = u.nickname || ''
  form.grade = u.grade || ''
  form.phone = u.phone || ''
  form.gender = u.gender || ''
  form.age = u.age ?? undefined
}

async function saveProfile() {
  saving.value = true
  try {
    const res: any = await authApi.updateMe({
      nickname: form.nickname,
      grade: form.grade,
      phone: form.phone,
      gender: form.gender || undefined,
      age: form.age,
    })
    // 同步到 store 与本地缓存
    authStore.user = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
    ElMessage.success('资料已更新')
  } catch {
  } finally {
    saving.value = false
  }
}

async function changePwd() {
  if (!pwdForm.old_password || !pwdForm.new_password) {
    ElMessage.warning('请填写旧密码和新密码')
    return
  }
  if (pwdForm.new_password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  changingPwd.value = true
  try {
    await authApi.changePassword(pwdForm)
    ElMessage.success('密码修改成功')
    pwdForm.old_password = ''
    pwdForm.new_password = ''
  } catch {
  } finally {
    changingPwd.value = false
  }
}

onMounted(async () => {
  // 拉取最新资料，确保新字段同步
  try {
    await authStore.fetchMe()
  } catch {}
  syncForm()
})
</script>

<style scoped>
@reference "../../style.css";
.card {
  @apply bg-white rounded-2xl border border-gray-100 shadow-sm p-6;
}
</style>
