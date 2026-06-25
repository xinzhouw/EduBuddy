# 管理后台部署清单

## ✅ 前置检查

- [x] 所有后端代码已编写并提交
- [x] 所有前端代码已编写并提交
- [x] 依赖包已安装成功
- [x] GeoIP 数据库已下载（64MB）
- [x] 文档已生成

## 🔧 部署步骤

### 1. 环境准备

#### 1.1 后端环境
```bash
# 验证 Python 版本
python3 --version  # 需要 3.8+

# 进入后端目录
cd backend

# 验证依赖安装
pip3 list | grep -E "(geoip2|apscheduler|fastapi|sqlalchemy)"
# 应该看到：
# - fastapi 0.110.0
# - sqlalchemy 2.0.28
# - geoip2 5.2.0
# - apscheduler 3.11.2
```

#### 1.2 前端环境
```bash
# 验证 Node 版本
node --version  # 需要 14+
npm --version

# 进入前端目录
cd frontend

# 验证依赖
npm ls | grep -E "(vue|element-plus|echarts)"
```

### 2. 数据库初始化

#### 2.1 检查数据库文件
```bash
ls -lh backend/data/edubuddy.db
# 应该存在且大小 > 0
```

#### 2.2 验证新表是否创建
```bash
# 在 Python 中运行（应用启动时会自动创建）
cd backend
python3 -c "
from app.database import init_db
init_db()
print('✓ Database initialized')
"
```

### 3. 创建管理员账户

#### 3.1 使用脚本创建
```bash
cd backend
python3 scripts/create_admin.py admin@example.com password123 "管理员"

# 预期输出：
# ✓ 管理员账户创建成功
#   邮箱：admin@example.com
#   昵称：管理员
#   角色：admin
```

#### 3.2 验证账户创建
```bash
# 通过 Python 验证
python3 -c "
from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
admin = db.query(User).filter(User.email == 'admin@example.com').first()
if admin:
    print(f'✓ Admin user created: {admin.email} (role: {admin.role})')
else:
    print('✗ Admin user not found')
db.close()
"
```

### 4. 启动应用

#### 4.1 启动后端服务
```bash
cd backend

# 开发环境（带热加载）
uvicorn app.main:app --reload --port 8000

# 生产环境
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

验证后端运行：
```bash
# 在另一个终端中
curl http://localhost:8000/health
# 应该返回：{"status": "ok"}
```

#### 4.2 启动前端服务
```bash
cd frontend

# 开发环境
npm run dev
# 输出应该显示：http://localhost:3000

# 生产环境构建
npm run build
npm run preview
```

### 5. 功能验证

#### 5.1 登录验证
1. 打开浏览器访问 http://localhost:3000
2. 输入管理员账户：
   - 邮箱：admin@example.com
   - 密码：password123
3. 点击"登录"
4. 预期：登录成功，跳转到首页

#### 5.2 菜单验证
1. 登录后，查看侧边栏菜单
2. 预期：显示"管理后台"菜单项（仅 admin 用户可见）

#### 5.3 仪表板验证
1. 点击侧边栏"管理后台"
2. 预期：进入仪表板，显示统计信息
3. 检查项：
   - [ ] 最近 7 天活跃用户数显示
   - [ ] 系统总用户数显示
   - [ ] 功能使用排行图表加载
   - [ ] 活跃用户排行表格显示

#### 5.4 用户管理验证
1. 点击侧边栏"用户管理"
2. 预期：显示用户列表
3. 检查项：
   - [ ] 用户列表加载正常
   - [ ] 搜索功能可用
   - [ ] 筛选功能可用
   - [ ] 分页功能可用
   - [ ] 启用/禁用开关可用
   - [ ] "查看详情"和"删除"按钮可用

#### 5.5 用户详情验证
1. 在用户列表中点击某用户的"查看详情"
2. 预期：显示用户信息卡片和活动日志
3. 检查项：
   - [ ] 用户信息正确显示
   - [ ] 登录统计数据显示
   - [ ] 功能使用图表显示
   - [ ] 活动日志表格显示
   - [ ] 日志筛选可用

#### 5.6 审计日志验证
1. 点击侧边栏"审计日志"
2. 预期：显示系统审计日志
3. 检查项：
   - [ ] 日志列表加载正常
   - [ ] 功能筛选可用
   - [ ] 用户 ID 筛选可用
   - [ ] 日期范围筛选可用
   - [ ] 分页功能可用

### 6. API 端点验证

#### 6.1 获取管理员 Token
```bash
# 登录获取 token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }'

# 保存返回的 token
```

#### 6.2 测试用户管理 API
```bash
TOKEN="your-token-here"

# 获取用户列表
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/users

# 获取用户详情
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/users/2

# 获取仪表板统计
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/stats/dashboard

# 获取审计日志
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/audit-logs
```

### 7. 日志和监控

#### 7.1 检查后端日志
```bash
# 后端应该输出类似信息：
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
# INFO:     Scheduler started
```

#### 7.2 检查审计日志记录
```bash
# 登录后进行一些操作（如查看用户列表），然后检查数据库
python3 -c "
from app.database import SessionLocal
from app.models.audit_log import AuditLog

db = SessionLocal()
logs = db.query(AuditLog).limit(5).all()
print(f'Total audit logs: {db.query(AuditLog).count()}')
for log in logs:
    print(f'  - {log.timestamp}: {log.feature} {log.action} {log.endpoint}')
db.close()
"
```

### 8. 性能测试

#### 8.1 加载时间测试
```bash
# 使用浏览器开发者工具 (F12)
# 检查各页面加载时间：
# - 仪表板：< 2s
# - 用户列表：< 1.5s
# - 用户详情：< 1.5s
# - 审计日志：< 1.5s
```

#### 8.2 API 响应时间
```bash
# 使用 curl 测试
time curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/stats/dashboard

# 预期：< 1s
```

### 9. 定时任务验证

#### 9.1 验证定时任务已启动
```bash
# 后端日志应该显示：
# INFO:     Scheduler started

# 或在代码中检查：
from app.tasks.scheduler import start_scheduler
scheduler = start_scheduler()
print(f'Scheduler running: {scheduler.running}')
```

#### 9.2 验证日志清理（可选）
```bash
# 手动执行日志清理
python3 -c "
from app.database import SessionLocal
from app.services.admin_service import AdminService

db = SessionLocal()
deleted = AdminService.cleanup_old_logs(db)
print(f'Deleted {deleted} old audit logs')
"
```

### 10. 权限控制验证

#### 10.1 测试未认证访问
```bash
# 不带 token 访问应返回 401
curl http://localhost:8000/api/admin/users
# 预期：{"detail":"Not authenticated"}
```

#### 10.2 测试非 admin 用户访问
```bash
# 使用学生账户 token
STUDENT_TOKEN="student-token"
curl -H "Authorization: Bearer $STUDENT_TOKEN" \
  http://localhost:8000/api/admin/users
# 预期：{"detail":"仅管理员可访问"}
```

#### 10.3 测试 admin 用户访问
```bash
# 使用管理员 token
ADMIN_TOKEN="admin-token"
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/admin/users
# 预期：正常返回用户列表
```

## 🚀 部署完成标志

部署成功的标志：

- [x] 后端服务正常运行
- [x] 前端页面可正常加载
- [x] 管理员可成功登录
- [x] 所有页面都能加载数据
- [x] API 端点返回正确数据
- [x] 权限控制正常工作
- [x] 定时任务成功启动
- [x] 审计日志正常记录

## 📋 常见问题排查

### 问题 1：数据库表不存在
**症状**：后端启动时出现 "no such table" 错误

**解决方案**：
```bash
# 重新初始化数据库
cd backend
python3 -c "from app.database import init_db; init_db()"
```

### 问题 2：GeoIP 数据库错误
**症状**：日志显示 "Failed to load GeoIP database"

**解决方案**：
- 这是非致命错误，系统可以继续工作
- 地理位置会显示 "Unknown"
- 可选：重新下载数据库

### 问题 3：定时任务未启动
**症状**：日志中没有 "Scheduler started"

**解决方案**：
```bash
# 检查 apscheduler 是否已安装
pip3 list | grep apscheduler

# 如果未安装
pip3 install apscheduler --break-system-packages
```

### 问题 4：前端无法连接后端
**症状**：前端错误 "API 请求失败"

**解决方案**：
1. 检查后端是否运行：`curl http://localhost:8000/health`
2. 检查端口号是否正确（前端代理配置）
3. 检查 CORS 配置是否正确

### 问题 5：权限总是 403
**症状**：登录后仍显示 "仅管理员可访问"

**解决方案**：
1. 检查用户角色是否为 "admin"
2. 检查 token 是否有效
3. 重新登录以获取新 token

## 🔍 监控指标

部署后应监控的指标：

| 指标 | 目标 | 检查方法 |
|------|------|--------|
| 后端可用性 | 99.9% | 健康检查 |
| 前端加载时间 | < 2s | 浏览器开发工具 |
| API 响应时间 | < 1s | curl 测试 |
| 数据库查询时间 | < 500ms | 日志分析 |
| 日志增长率 | < 1GB/月 | 磁盘监控 |

## 📞 支持和反馈

如有问题：
1. 查看 `ADMIN_SETUP.md` 的故障排除部分
2. 查看应用日志输出
3. 检查浏览器控制台错误
4. 参考实现计划文档

## ✅ 最终清单

部署前检查清单：

- [ ] 后端依赖已全部安装
- [ ] 前端依赖已全部安装
- [ ] 数据库文件存在且可写
- [ ] GeoIP 数据库已下载
- [ ] 管理员账户已创建
- [ ] 防火墙允许访问所需端口
- [ ] 磁盘空间充足（至少 1GB）
- [ ] 内存充足（至少 512MB）

---

**部署状态：准备就绪 ✅**

所有准备工作已完成，可以开始部署！
