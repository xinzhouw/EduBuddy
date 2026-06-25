# Task 5 Report: ChangePasswordDialog 组件

## 状态: ✅ 完成

## 完成时间
2026-06-24

## 完成内容

### 创建文件
- `frontend/src/components/ChangePasswordDialog.vue`

### 实现功能
1. el-dialog 模态对话框，标题"修改密码"，宽度 400px
2. 表单包含 3 个字段：旧密码、新密码（PasswordInput 组件）、确认新密码
3. 底部"取消"和"修改"两个按钮
4. 提交验证逻辑：旧密码非空、新密码强度合格、两次密码一致
5. 成功后关闭对话框、清空表单、显示成功消息
6. 错误时显示错误消息
7. 暴露 `visible` ref 供父组件控制

### 关键调整（相比任务规格）
- 文件实际路径为 `frontend/src/components/`（非 `src/components/`）
- api 为默认导出（`import api from '@/api'`，非命名导出 `{ api }`）
- 新密码取自 `passwordInput.value!.password`（PasswordInput 暴露的 ref），而非 `form.value.newPassword`，确保提交数据与验证数据一致

### TypeScript 检查
- vue-tsc --noEmit 通过，无错误

### 提交
- commit: f91fa44 feat: 添加 ChangePasswordDialog 修改密码对话框组件
