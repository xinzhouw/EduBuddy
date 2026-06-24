/**
 * E2E Tests: Password Strength Enhancement
 *
 * 覆盖以下场景：
 * 1. 注册页面实时密码强度反馈（弱 / 强）
 * 2. 弱密码注册被拒绝
 * 3. 强密码注册成功
 * 4. 修改密码对话框 — 打开
 * 5. 修改密码 — 旧密码错误
 * 6. 修改密码 — 新密码过弱
 * 7. 修改密码 — 成功
 *
 * 选择器说明：
 * - 注册页密码框：PasswordInput 组件渲染 el-input，placeholder="请输入密码"
 * - 确认密码框：placeholder="再次输入密码"
 * - 昵称框：placeholder="昵称"
 * - 邮箱框（注册）：placeholder="邮箱地址"
 * - 邮箱框（登录）：placeholder="邮箱地址"
 * - 登录密码框：placeholder="密码"
 * - 修改密码对话框旧密码：placeholder="请输入旧密码"
 * - 修改密码对话框新密码：placeholder="请输入密码"（PasswordInput 组件内）
 * - 修改密码对话框确认密码：placeholder="请再次输入新密码"
 *
 * 强度标签由 PasswordInput 渲染 .strength-text span，内容为 "弱" / "中等" / "强"
 * 成功提示文字：.success span — "密码符合要求"
 * 缺陷提示文字：.issue span — 如 "密码长度至少8个字符"
 *
 * 注意：cy.visit() 使用相对路径，需在 cypress.config.ts 中配置 baseUrl
 * 例如：baseUrl: 'http://localhost:5173'
 */

describe('Password Strength Enhancement', () => {
  // 固定强密码；注册时使用时间戳保证邮箱唯一
  const strongPassword = 'SecurePass123!'
  const weakPassword = 'weak'

  // ─────────────────────────────────────────────────────────────────────────────
  // 注册页面 — 实时反馈 & 注册流程
  // ─────────────────────────────────────────────────────────────────────────────
  describe('注册页面密码强度反馈', () => {
    beforeEach(() => {
      cy.visit('/register')
    })

    it('弱密码显示"弱"标签及缺陷消息', () => {
      // PasswordInput 渲染的 el-input，placeholder="请输入密码"
      cy.get('input[placeholder="请输入密码"]').type(weakPassword)

      // 等待防抖（300ms）后强度标签出现
      // .strength-text span 内容为 "弱"
      cy.get('.strength-text').should('be.visible').and('contain', '弱')

      // 至少一条缺陷提示（.issue 内有 span 文本）
      cy.get('.issue').should('have.length.at.least', 1)
      // 密码长度不足，典型提示
      cy.contains('密码长度至少').should('be.visible')
    })

    it('强密码显示"强"标签及"密码符合要求"', () => {
      cy.get('input[placeholder="请输入密码"]').type(strongPassword)

      cy.get('.strength-text').should('be.visible').and('contain', '强')

      // .success 区域显示"密码符合要求"
      cy.get('.success').should('be.visible').and('contain', '密码符合要求')
    })

    it('弱密码注册被拒绝，停留在注册页', () => {
      const testEmail = `test_weak_${Date.now()}@example.com`

      // 昵称
      cy.get('input[placeholder="昵称"]').type('TestUser')
      // 邮箱
      cy.get('input[placeholder="邮箱地址"]').type(testEmail)
      // 年级（学生角色默认选中，el-select placeholder="选择年级"）
      cy.get('.el-select').first().click()
      cy.get('.el-select-dropdown__item').contains('高一').click()
      // 密码（PasswordInput）
      cy.get('input[placeholder="请输入密码"]').type(weakPassword)
      // 确认密码
      cy.get('input[placeholder="再次输入密码"]').type(weakPassword)

      // 点击注册按钮
      cy.contains('button', '注 册').click()

      // handleRegister 在密码不符合要求时调用 ElMessage.error('密码不符合要求')
      // Element Plus Message 渲染在 .el-message 容器中
      cy.get('.el-message').should('be.visible').and('contain', '密码不符合要求')

      // 仍在注册页面
      cy.url().should('include', '/register')
    })

    it('强密码注册成功，跳转到登录页并提示注册成功', () => {
      const uniqueEmail = `test_${Date.now()}_ok@example.com`

      cy.get('input[placeholder="昵称"]').type('TestUser')
      cy.get('input[placeholder="邮箱地址"]').type(uniqueEmail)

      // 选择年级
      cy.get('.el-select').first().click()
      cy.get('.el-select-dropdown__item').contains('高一').click()

      // 强密码
      cy.get('input[placeholder="请输入密码"]').type(strongPassword)

      // 确认密码（等待防抖，确保 PasswordInput 内部 password.value 已更新）
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(400)
      cy.get('input[placeholder="再次输入密码"]').type(strongPassword)

      cy.contains('button', '注 册').click()

      // authStore.register 成功后 ElMessage.success('注册成功，请登录')
      cy.get('.el-message').should('be.visible').and('contain', '注册成功')

      // 路由跳转到 /login
      cy.url().should('include', '/login')
    })
  })

  // ─────────────────────────────────────────────────────────────────────────────
  // 修改密码对话框
  // ─────────────────────────────────────────────────────────────────────────────
  describe('修改密码对话框', () => {
    // 使用已知测试账号登录，并在每个用例前打开对话框
    // 注意：测试环境需要存在账号 test@example.com / strongPassword
    // 若该账号不存在，需在 CI 脚本或 cypress/fixtures 中预先创建

    beforeEach(() => {
      // 先登录
      cy.visit('/login')
      cy.get('input[placeholder="邮箱地址"]').type('test@example.com')
      cy.get('input[placeholder="密码"]').type(strongPassword)
      cy.contains('button', '登 录').click()

      // 登录成功后路由守卫跳到 /（首页），再导航到 /profile
      cy.url().should('not.include', '/login')
      cy.visit('/profile')

      // 点击"修改密码"按钮，打开对话框
      cy.contains('button', '修改密码').click()

      // 验证对话框标题可见
      cy.get('.el-dialog__title').should('contain', '修改密码')
    })

    it('打开修改密码对话框', () => {
      // beforeEach 已完成断言，此用例专门验证对话框打开状态
      cy.get('.el-dialog').should('be.visible')
      cy.get('.el-dialog__title').should('contain', '修改密码')
    })

    it('旧密码错误时显示错误提示，对话框保持打开', () => {
      // ChangePasswordDialog：旧密码 placeholder="请输入旧密码"
      cy.get('input[placeholder="请输入旧密码"]').type('WrongPass123!')

      // 新密码（PasswordInput 组件，placeholder="请输入密码"）
      cy.get('.el-dialog input[placeholder="请输入密码"]').type('NewPass123!')
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(400)

      // 确认新密码
      cy.get('input[placeholder="请再次输入新密码"]').type('NewPass123!')

      // 点击"修改"按钮
      cy.get('.el-dialog').contains('button', '修改').click()

      // 后端返回旧密码错误（HTTP 400，detail 通常包含"旧密码"）
      cy.get('.el-message').should('be.visible')
      cy.get('.el-message')
        .invoke('text')
        .should('match', /旧密码|密码错误|incorrect|wrong/i)

      // 对话框仍然打开
      cy.get('.el-dialog').should('be.visible')
      cy.get('.el-dialog__title').should('contain', '修改密码')
    })

    it('新密码过弱时显示"新密码不符合要求"，对话框保持打开', () => {
      cy.get('input[placeholder="请输入旧密码"]').type(strongPassword)

      // 输入弱新密码，触发前端校验
      cy.get('.el-dialog input[placeholder="请输入密码"]').type(weakPassword)
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(400)

      // 不填确认密码也可触发前端校验
      cy.get('.el-dialog').contains('button', '修改').click()

      // ChangePasswordDialog.handleSubmit 调用 ElMessage.error('新密码不符合要求')
      cy.get('.el-message').should('be.visible').and('contain', '新密码不符合要求')

      // 对话框仍然打开
      cy.get('.el-dialog').should('be.visible')
    })

    it('修改密码成功后显示"密码已修改"并关闭对话框', () => {
      const newPassword = 'NewSecurePass456!'

      cy.get('input[placeholder="请输入旧密码"]').type(strongPassword)

      cy.get('.el-dialog input[placeholder="请输入密码"]').type(newPassword)
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(400)

      cy.get('input[placeholder="请再次输入新密码"]').type(newPassword)

      cy.get('.el-dialog').contains('button', '修改').click()

      // ChangePasswordDialog 成功后 ElMessage.success('密码已修改')
      cy.get('.el-message').should('be.visible').and('contain', '密码已修改')

      // 对话框关闭（v-model:visible=false 后 DOM 不再可见）
      cy.get('.el-dialog').should('not.exist')
    })
  })
})
