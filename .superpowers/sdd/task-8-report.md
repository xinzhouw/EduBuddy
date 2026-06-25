# Task 8 Report: E2E 测试 — 密码强度功能

## 状态: COMPLETED

## 完成时间
2026-06-24

## 已完成内容

### 1. 项目配置探查
- 项目原无 Cypress 依赖（package.json 仅含 vite / vue-tsc 等运行时依赖）
- 无既有 Cypress 配置文件或测试目录
- 前端开发服务器：Vite，端口 5173；路由模式：`createWebHistory`

### 2. 页面选择器分析
读取以下组件，确认实际 DOM 结构：
- `frontend/src/views/auth/RegisterView.vue` — 注册页
- `frontend/src/views/auth/LoginView.vue` — 登录页
- `frontend/src/views/profile/ProfileView.vue` — 个人资料页
- `frontend/src/components/PasswordInput.vue` — 密码输入 + 实时强度反馈组件
- `frontend/src/components/ChangePasswordDialog.vue` — 修改密码对话框

**关键选择器：**
| 元素 | 选择器 |
|------|--------|
| 注册/对话框密码输入框 | `input[placeholder="请输入密码"]` |
| 注册确认密码 | `input[placeholder="再次输入密码"]` |
| 注册昵称 | `input[placeholder="昵称"]` |
| 注册/登录邮箱 | `input[placeholder="邮箱地址"]` |
| 登录密码 | `input[placeholder="密码"]` |
| 修改密码旧密码 | `input[placeholder="请输入旧密码"]` |
| 修改密码确认密码 | `input[placeholder="请再次输入新密码"]` |
| 强度标签 | `.strength-text` |
| 成功提示 | `.success` |
| 缺陷条目 | `.issue` |
| ElMessage 消息框 | `.el-message` |
| 对话框标题 | `.el-dialog__title` |
| 注册按钮 | `cy.contains('button', '注 册')` |
| 登录按钮 | `cy.contains('button', '登 录')` |
| 对话框修改按钮 | `cy.get('.el-dialog').contains('button', '修改')` |

**注意事项：**
- 注册/登录按钮文本含空格：`"注 册"`、`"登 录"`（模板中有全角空格）
- PasswordInput 内部使用 300ms 防抖；测试中在强密码输入后加 `cy.wait(400)` 确保校验完成
- 登录成功后路由守卫跳到 `/`（首页），`beforeEach` 随后显式 `cy.visit('/profile')`

### 3. 新增文件

#### `frontend/tests/e2e/password-strength.cy.ts`
8 个测试用例，分为两个 `describe` 块：

**注册页面密码强度反馈（4 用例）：**
1. 弱密码显示"弱"标签及缺陷消息
2. 强密码显示"强"标签及"密码符合要求"
3. 弱密码注册被拒绝，停留在注册页（ElMessage 显示"密码不符合要求"）
4. 强密码注册成功，跳转到 `/login` 并显示"注册成功"

**修改密码对话框（4 用例）：**
5. 打开修改密码对话框（验证标题 + 可见性）
6. 旧密码错误时显示错误提示，对话框保持打开
7. 新密码过弱时显示"新密码不符合要求"，对话框保持打开
8. 修改密码成功后显示"密码已修改"并关闭对话框

#### `frontend/cypress.config.ts`
- `baseUrl: 'http://localhost:5173'`
- `specPattern: 'tests/e2e/**/*.cy.{ts,js}'`
- `supportFile: false`（无需额外 support 文件）
- `video: false`

### 4. Git Commit
- commit: `fd2bcb7`
- message: `test: 添加密码强度功能 E2E 测试（Task 8）`
- 2 files changed, 242 insertions(+)

## 运行说明
```bash
# 安装 Cypress（尚未加入 devDependencies）
cd frontend
npm install --save-dev cypress

# 运行前确保前后端已启动
# 后端：uvicorn app.main:app --port 8000
# 前端：npm run dev

# 无界面运行
npx cypress run --spec "tests/e2e/password-strength.cy.ts"

# 交互模式
npx cypress open
```

## 注意
- "修改密码成功"用例使用新密码 `NewSecurePass456!`；若重复运行，该账号的密码已被修改，
  后续运行需提前重置密码或更换测试账号。建议在 CI 中每次重新创建测试用户。
- `test@example.com` 账号需在测试环境中预先存在，密码为 `SecurePass123!`。
