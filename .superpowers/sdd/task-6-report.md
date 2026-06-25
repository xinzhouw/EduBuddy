# Task 6 Report — 集成 PasswordInput 到注册页面

**状态：完成 ✅**

## 修改文件

- `frontend/src/views/auth/RegisterView.vue`

## 实施内容

### 1. 模板替换
将原来的 `<el-input type="password" v-model="form.password" ...>` 替换为：
```vue
<el-form-item prop="password">
  <PasswordInput ref="passwordInput" />
</el-form-item>
```
确认密码字段保留原有 `<el-input>` 普通输入框。

### 2. Script 变更
- 新增 `import PasswordInput from '@/components/PasswordInput.vue'`
- 新增 `import { ElMessage } from 'element-plus'`
- 新增 `const passwordInput = ref<InstanceType<typeof PasswordInput>>()`
- 从 `form` 中移除 `password` 字段（不再用 v-model 双向绑定）

### 3. 表单校验器更新
- 新增 `validatePassword`：读取 `passwordInput.value?.validation.value.issues`，空则通过，非空则返回第一条错误信息
- 更新 `validateConfirmPassword`：与 `passwordInput.value?.password.value` 比对，而非 `form.password`

### 4. handleRegister 逻辑更新
- 前置检查：`passwordInput.value?.validation.value.issues.length > 0` 时 `ElMessage.error` 并 `return`
- 从 `passwordInput.value!.password.value` 获取实际密码传给后端
- 二次确认两次密码一致性检查

### 5. 类型检查
`npx vue-tsc --noEmit` 零错误通过。

## Commit
```
a91beda 集成 PasswordInput 到注册页面
```
