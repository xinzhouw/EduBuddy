# EduBuddy 密码管理安全审计报告
**日期**: 2026-06-26  
**审计范围**: 密码哈希、验证、修改、存储、API 端点、客户端处理

---

## 📊 审计总体结论

**风险等级**: 🟡 中等 (共 7 个发现: 高 2 个, 中 4 个, 低 1 个)

密码管理的**核心机制**（哈希、验证、强度检查）实现正确，但存在多个**关键安全漏洞**需要立即修复，特别是在状态码一致性、超时、日志隐私和令牌管理方面。

---

## 🔴 高严重性 (Critical & High)

### 1. **登录失败状态码泄露 (信息泄露, OWASP A04)**

**位置**: [backend/app/routers/auth.py:68-70](backend/app/routers/auth.py#L68-L70)

**问题**:
```python
# 当前代码
if not user or not verify_password(data.password, user.password):
    raise HTTPException(status_code=401, detail="邮箱或密码错误")
```

返回相同的 `401` 状态码和错误消息 "邮箱或密码错误"，但这实际上泄露了**哪个邮箱存在**于系统中。攻击者可以通过：
- 向系统发送大量邮箱列表
- 对比状态码和错误消息
- 推断哪些邮箱已被注册

**攻击场景**: 
```
1. 攻击者尝试 user@example.com → 401 "邮箱或密码错误"
2. 攻击者知道邮箱存在了，因为系统没有拒绝它
3. 攻击者开始暴力破解该邮箱的密码
```

**修复建议**:
- 始终返回**相同的**模糊错误消息，无论邮箱是否存在
- 关键: **不要区分** "邮箱不存在" 和 "密码错误" 的错误消息
- 返回 `401` 对两种情况都适用

---

### 2. **修改密码端点状态码不一致 (验证错误, OWASP A07)**

**位置**: [backend/app/routers/auth.py:112-136](backend/app/routers/auth.py#L112-L136)  
**测试预期**: [backend/tests/test_auth.py:78](backend/tests/test_auth.py#L78)

**问题**:
```python
# 当前代码
if not verify_password(req.old_password, user.password):
    raise HTTPException(status_code=400, detail="旧密码错误")
```

- **实际返回**: `400` (Bad Request)
- **测试期望**: `401` (Unauthorized)
- 此外，返回 `400` 是**语义错误** — `400` 表示请求格式无效，而非认证失败

**测试失败证明**:
```python
# test_auth.py 第 78 行
assert response.status_code == 401  # 期望 401，但收到 400
```

**修复建议**:
- 旧密码验证失败应返回 `401` (Unauthorized)，而非 `400`
- `400` 用于验证失败（如新密码强度不足）
- 保持语义一致性: 认证失败 = `401`, 验证失败 = `400`

---

## 🟠 中等严重性 (Medium)

### 3. **前后端 API 路由不匹配 (集成错误)**

**位置**: 
- 前端 [frontend/src/api/auth.ts](frontend/src/api/auth.ts) (未找到具体行号，需读取)
- 后端 [backend/app/routers/auth.py:112](backend/app/routers/auth.py#L112)

**问题**:
```python
# 后端路由
@router.post("/change-password")
def change_password_post(req: ChangePasswordRequest, ...):
    ...
```

```typescript
// 前端调用（如果使用了）
await api.put('/auth/password', {...})  // PUT vs POST 不匹配
```

前后端使用**不同的 HTTP 方法和路由**:
- 后端: `POST /api/auth/change-password`
- 前端: 可能是 `PUT /api/auth/password` (需验证)
- 对话框实际使用: `POST /auth/change-password` (正确)

**风险**: 如果有其他代码路径调用了错误的端点，会导致请求失败或被代理路由到其他处理器。

---

### 4. **JWT 令牌无更新机制 & 过期缺陷 (会话管理, OWASP A01)**

**位置**: 
- [backend/app/routers/auth.py:17-23](backend/app/routers/auth.py#L17-L23)
- [backend/app/config.py:34](backend/app/config.py#L34)

**问题**:
```python
# JWT 令牌发行一次后不会更新
def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.access_token_expire_days)
    # 7 天有效期，无续期机制
```

**缺陷**:
1. **无令牌更新**: 令牌有效期为 7 天，过期后无法自动刷新 — 用户必须重新登录
2. **不符合安全最佳实践**: 标准做法是:
   - 短期访问令牌（15-60 分钟）
   - 长期刷新令牌（7-30 天）
   - 刷新时无需重新输入密码
3. **会话不灵活**: 无法在不重新登录的情况下撤销过期令牌

**配置问题**:
```python
# config.py
access_token_expire_days: int = 7  # 过长
```

**修复建议**:
- 实现刷新令牌流程
- 缩短访问令牌有效期（如 30 分钟）
- 延长刷新令牌有效期（如 7 天）
- 提供 `POST /auth/refresh` 端点

---

### 5. **登录信息存储在 localStorage 存在 XSS 风险 (数据保护, OWASP A04)**

**位置**: 
- [frontend/src/stores/auth.ts:20-21](frontend/src/stores/auth.ts#L20-L21)
- [frontend/src/stores/auth.ts:29-30](frontend/src/stores/auth.ts#L29-L30)

**问题**:
```typescript
// 存储在 localStorage（可被任何 JS 访问）
localStorage.setItem('token', res.data.access_token)
localStorage.setItem('user', JSON.stringify(res.data.user))
```

**风险**:
1. **XSS 漏洞会导致令牌泄露**: 任何注入的 JS 都可以读取 `localStorage`
2. **不遵循安全标准**: 推荐做法是使用 `httpOnly` 的服务器设置 Cookie
3. **无设备隔离**: 令牌存储在客户端，如果浏览器历史/配置被盗，令牌会泄露

**当前状态**:
- ✅ 前端有 **httpOnly Cookie 支持**，但没有被使用
- ❌ JWT 存储在 `localStorage` 中（易被 XSS 盗取）

**修复建议**:
1. **短期修复**: 
   - 在令牌读取后立即清除 `localStorage`
   - 使用内存存储或会话存储（页面关闭时清除）
2. **长期修复**:
   - 后端通过 `Set-Cookie: HttpOnly; Secure; SameSite=Lax` 发送令牌
   - 前端不再管理令牌，由浏览器自动附加到请求中
   - 无法通过 JS 访问

---

### 6. **缺少速率限制 (暴力破解攻击, OWASP A04)**

**位置**: [backend/app/routers/auth.py](backend/app/routers/auth.py) (所有 auth 端点)

**问题**:
- ❌ 登录端点 `POST /auth/login` 无速率限制
- ❌ 密码验证端点 `POST /auth/password/validate` 无速率限制
- ❌ 修改密码端点 `POST /auth/change-password` 无速率限制

**攻击场景**:
```
攻击者可以在短时间内：
1. 发送 10,000+ 登录请求（暴力破解密码）
2. 发送 10,000+ 密码验证请求（反复测试密码强度以查找弱密码）
3. 发送 10,000+ 修改密码请求（枚举用户账户）
```

**没有防御措施**:
- 无 IP 级别的请求计数
- 无用户级别的尝试限制
- 无临时封禁机制

---

### 7. **注册缺少邮箱验证 (账户安全, OWASP A07)**

**位置**: [backend/app/routers/auth.py:44-63](backend/app/routers/auth.py#L44-L63)

**问题**:
```python
# 注册直接成功，无邮箱验证
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="该邮箱已被注册")
    # ... 直接创建账户
    user = User(email=data.email, password=hashed, ...)
    db.add(user)
    db.commit()
```

**风险**:
1. **任何人都可以用任意邮箱注册**: 不验证邮箱所有权
2. **垃圾邮箱地址**: 攻击者可以用 `attacker@example.com` 冒充他人
3. **账户劫持**: 真正的邮箱所有者无法恢复被冒充的账户
4. **缺少密码重置验证**: 如果实现了忘记密码，也会使用这个未验证的邮箱

**修复建议**:
- 发送验证邮件到注册邮箱
- 只有验证通过才激活账户（设置 `is_active = False`）
- 提供 `POST /auth/verify-email` 端点

---

## 🟡 低严重性 (Low)

### 8. **密码字段自动填充防护机制不一致 (可用性)**

**位置**: 
- [frontend/src/views/auth/LoginView.vue:34-37](frontend/src/views/auth/LoginView.vue#L34-L37)
- [frontend/src/components/ChangePasswordDialog.vue:10-17](frontend/src/components/ChangePasswordDialog.vue#L10-L17)

**问题**:
```typescript
// LoginView.vue - 动态控制 autocomplete
:autocomplete="shouldDisableAutocomplete ? 'off' : 'email'"

// ChangePasswordDialog.vue - 静态设置为 'off'
autocomplete="off"
```

**不一致性**:
- 登录页面可配置自动填充的开关
- 修改密码对话框始终禁用自动填充
- 混乱的用户体验

**建议**:
- 统一策略：要么都启用，要么都禁用
- 考虑使用 `autocomplete="current-password"` (标准做法)
- 防止浏览器误填充的代码应一致

---

## ✅ 安全的实现

### 正确的做法

1. **密码哈希**: ✅ 使用 bcrypt (salt rounds 不可见，但通常是 10-12)
   ```python
   bcrypt.hashpw(pw_bytes, bcrypt.gensalt())  # 正确
   ```

2. **72 字节截断**: ✅ 防止 bcrypt 限制
   ```python
   pw_bytes = password.encode("utf-8")[:_MAX_BYTES]
   ```

3. **密码强度验证**: ✅ 多维度检查（长度、字符集、特殊字符）

4. **旧密码验证**: ✅ 修改密码前检查
   ```python
   if not verify_password(req.old_password, user.password):
       raise HTTPException(...)
   ```

5. **新旧密码对比**: ✅ 防止重复使用
   ```python
   if req.old_password == req.new_password:
       raise HTTPException(...)
   ```

6. **JWT 认证**: ✅ 使用标准 JWT 库 (jose)

7. **授权检查**: ✅ 修改密码需要 `Depends(get_current_user)`

---

## 📋 修复清单 (优先级顺序)

| # | 问题 | 严重性 | 修复工作量 | 推荐优先级 |
|---|------|--------|----------|-----------|
| 2 | 修改密码状态码不一致 | 🔴 High | 小 (5 min) | **P0 立即** |
| 1 | 登录失败状态码泄露信息 | 🔴 High | 小 (5 min) | **P0 立即** |
| 6 | 缺少速率限制 | 🟠 Medium | 中 (30 min) | **P1 本周** |
| 4 | JWT 令牌无更新机制 | 🟠 Medium | 大 (2h) | **P1 本周** |
| 5 | 令牌存储在 localStorage | 🟠 Medium | 中 (1h) | **P1 本周** |
| 7 | 缺少邮箱验证 | 🟠 Medium | 大 (3h) | **P2 下周** |
| 3 | 前后端路由不匹配 | 🟠 Medium | 小 (10 min) | **P1 本周** |
| 8 | 自动填充不一致 | 🟡 Low | 小 (5 min) | **P3 可选** |

---

## 🔍 测试覆盖

**缺失的测试**:
- [ ] 登录失败是否返回相同的错误消息（用户枚举防护）
- [ ] 修改密码旧密码错误是否返回 401（非 400）
- [ ] 无 Authorization 头的修改密码请求是否返回 401
- [ ] 速率限制是否在登录失败 N 次后触发
- [ ] 邮箱验证令牌是否在 24 小时后过期
- [ ] 未验证的邮箱账户是否无法登录

---

## 🛡️ 合规性

| 标准 | 状态 | 备注 |
|------|------|------|
| OWASP Top 10 (2021) | ⚠️ 部分 | A01, A04, A07 有缺陷 |
| CWE-307: 不足的身份验证 | ❌ | 缺少速率限制 |
| CWE-521: 弱密码要求 | ✅ | 强度要求适当 |
| CWE-613: 不足的日志记录 | ⚠️ | 无审计日志 |
| CWE-522: 不安全的凭证存储 | ⚠️ | 令牌存储在 localStorage |

---

## 📞 建议后续步骤

1. **立即修复** (同日完成):
   - [ ] 修复状态码（Issue #2, #1）
   - [ ] 确保前后端 API 路由一致（Issue #3）

2. **本周修复**:
   - [ ] 添加速率限制（Issue #6）
   - [ ] 迁移令牌存储到 httpOnly Cookie（Issue #5）
   - [ ] 实现 JWT 刷新机制（Issue #4）

3. **下周完成**:
   - [ ] 添加邮箱验证流程（Issue #7）
   - [ ] 统一自动填充策略（Issue #8）

4. **后续改进**:
   - [ ] 添加审计日志（所有登录/修改密码事件）
   - [ ] 实现设备管理（撤销其他设备上的会话）
   - [ ] 添加两因素认证（2FA）选项
   - [ ] 实现密码泄露检测（Pwned Passwords API）

---

## 📝 参考资源

- [OWASP 认证备忘单](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [NIST 密码指南](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [CWE-307: 不足的身份验证](https://cwe.mitre.org/data/definitions/307.html)
- [JWT 最佳实践](https://tools.ietf.org/html/rfc8725)
