# Task 19: 测试后端 API 多语言支持

## 任务描述

测试后端 API 是否正确支持多语言。

### 测试清单

1. **启动后端** - `cd backend && python -m uvicorn main:app --reload`
2. **测试登录 API - 中文错误** - 发送登录请求，Accept-Language: zh，验证错误消息为中文
3. **测试登录 API - 英文错误** - 发送登录请求，Accept-Language: en，验证错误消息为英文
4. **测试登录成功** - 使用正确的凭证登录，验证返回的 user 包含 language 字段
5. **测试语言偏好更新** - 使用 token 调用 PATCH /api/users/preferences，验证成功
6. **验证数据库** - 检查 users 表中 language 字段是否正确保存

### 验证命令示例

```bash
# 测试中文错误消息
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Accept-Language: zh" \
  -d '{"email":"wrong@test.com","password":"wrong"}'

# 测试英文错误消息
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Accept-Language: en" \
  -d '{"email":"wrong@test.com","password":"wrong"}'
```

## 报告位置

完成后报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-19-i18n-report.md`
