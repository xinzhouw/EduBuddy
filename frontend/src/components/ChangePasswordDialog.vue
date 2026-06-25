<template>
  <el-dialog
    v-model="visible"
    title="修改密码"
    width="400px"
    @close="resetForm"
  >
    <el-form :model="form" ref="formRef">
      <!-- 旧密码 -->
      <el-form-item label="旧密码" prop="oldPassword">
        <el-input
          v-model="form.oldPassword"
          type="password"
          :show-password="true"
          placeholder="请输入旧密码"
        />
      </el-form-item>

      <!-- 新密码（实时反馈） -->
      <el-form-item label="新密码" prop="newPassword">
        <PasswordInput ref="passwordInput" />
      </el-form-item>

      <!-- 确认新密码 -->
      <el-form-item label="确认新密码" prop="confirmPassword">
        <el-input
          v-model="form.confirmPassword"
          type="password"
          :show-password="true"
          placeholder="请再次输入新密码"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        修改
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import PasswordInput from '@/components/PasswordInput.vue'
import api from '@/api'

const visible = ref(false)
const loading = ref(false)
const passwordInput = ref()
const formRef = ref()

const form = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

function resetForm() {
  form.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
}

async function handleSubmit() {
  // 验证旧密码非空
  if (!form.value.oldPassword) {
    ElMessage.error('请输入旧密码')
    return
  }

  // 验证新密码强度
  if (passwordInput.value!.validation.issues.length > 0) {
    ElMessage.error('新密码不符合要求')
    return
  }

  // 验证新密码一致
  if (passwordInput.value!.password !== form.value.confirmPassword) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }

  loading.value = true
  try {
    await api.post('/auth/change-password', {
      old_password: form.value.oldPassword,
      new_password: passwordInput.value!.password
    })
    ElMessage.success('密码已修改')
    visible.value = false
    resetForm()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '修改失败')
  } finally {
    loading.value = false
  }
}

defineExpose({
  open() {
    visible.value = true
  },
  close() {
    visible.value = false
  }
})
</script>
