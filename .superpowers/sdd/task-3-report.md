# Task 3 Report: passwordValidator 工具函数

## 状态：✅ 完成

## 完成时间
2026-06-24

## 实现内容

### 文件创建
- **路径：** `frontend/src/utils/passwordValidator.ts`

### 接口定义
```typescript
export interface PasswordValidationResult {
  score: number  // 0-100
  strength: 'weak' | 'medium' | 'strong'
  issues: string[]
}
```

### 函数实现
```typescript
export async function validatePasswordStrength(
  password: string
): Promise<PasswordValidationResult>
```

- 调用 `api.post('/auth/password/validate', { password })`
- 网络错误时返回 `{ score: 0, strength: 'weak', issues: ['无法验证密码强度，请检查网络'] }`

### API 实例
- 使用项目已有的 `api` 实例（`frontend/src/api/index.ts`）
- 该实例基于 axios，baseURL 为 `/api`，已配置 JWT 拦截器

## Commit
- `92272bf` feat: add passwordValidator utility for backend password strength validation

## 完成条件验证
- [x] 文件 `frontend/src/utils/passwordValidator.ts` 存在
- [x] 导出 `PasswordValidationResult` interface（字段精确）
- [x] 导出 `validatePasswordStrength` 函数
- [x] 正确使用项目 API 实例（`src/api/index.ts`）
- [x] TypeScript 类型签名正确
- [x] 一个 commit
