<template>
  <div class="password-group">
    <!-- 密码输入框 -->
    <el-input
      v-model="password"
      type="password"
      placeholder="请输入密码"
      :show-password="true"
      @input="handlePasswordChange"
    />

    <!-- 实时反馈（仅当输入时显示）-->
    <div v-if="password" class="feedback">
      <!-- 强度进度条 -->
      <div class="strength-container">
        <el-progress
          :percentage="validation.score"
          :color="strengthColor"
          :show-text="false"
        />
        <span class="strength-text" :class="validation.strength">
          {{ strengthLabel }}
        </span>
      </div>

      <!-- 缺陷列表 -->
      <div v-if="validation.issues.length" class="issues">
        <div v-for="issue in validation.issues" :key="issue" class="issue">
          <span class="icon">❌</span>
          <span>{{ issue }}</span>
        </div>
      </div>

      <!-- 成功标记 -->
      <div v-else class="success">
        <span class="icon">✅</span>
        <span>密码符合要求</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { validatePasswordStrength, type PasswordValidationResult } from '@/utils/passwordValidator'
import { debounce } from 'lodash-es'

const password = ref('')
const validation = ref<PasswordValidationResult>({
  score: 0,
  strength: 'weak',
  issues: []
})

const strengthLabel = computed(() => {
  const labels = {
    weak: '弱',
    medium: '中等',
    strong: '强'
  }
  return labels[validation.value.strength]
})

const strengthColor = computed(() => {
  const colors = {
    weak: '#F56C6C',
    medium: '#E6A23C',
    strong: '#67C23A'
  }
  return colors[validation.value.strength]
})

const handlePasswordChange = debounce(async () => {
  if (!password.value) {
    validation.value = { score: 0, strength: 'weak', issues: [] }
    return
  }

  validation.value = await validatePasswordStrength(password.value)
}, 300)

// 外部可调用此方法获取当前密码值（注意：返回的是值，不是 ref）
defineExpose({
  get password() {
    return password.value
  },
  get validation() {
    return validation.value
  }
})
</script>

<style scoped>
.password-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feedback {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.strength-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.strength-container :deep(.el-progress) {
  flex: 1;
}

.strength-text {
  font-size: 12px;
  font-weight: bold;
  min-width: 40px;
  text-align: right;
}

.strength-text.weak { color: #F56C6C; }
.strength-text.medium { color: #E6A23C; }
.strength-text.strong { color: #67C23A; }

.issues {
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
}

.issue {
  display: flex;
  align-items: center;
  gap: 6px;
  line-height: 1.8;
}

.icon {
  flex-shrink: 0;
}

.success {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  color: #67C23A;
}
</style>
