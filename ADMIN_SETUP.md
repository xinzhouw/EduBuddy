# EduBuddy 管理后台设置指南

## 功能概述

管理后台系统包含以下核心功能：

### 1. 用户管理
- 查看所有用户列表（分页、搜索、按角色筛选）
- 查看用户详细信息（个人资料、登录统计、功能使用记录）
- 启用/禁用用户账户
- 删除用户及相关数据（级联删除）

### 2. 登录统计
- 记录每次用户登录时间戳
- 统计用户登录次数
- 显示用户最后登录时间
- 支持按时间范围查询

### 3. 功能访问记录
- 自动记录用户每次 API 调用
- 记录访问的功能类别（AI对话、笔记、错题等）
- 记录 IP 地址和地理位置（城市、国家）
- 记录 HTTP 操作方法和状态码
- 仅保留最近 90 天的日志（自动清理）

### 4. 仪表板统计
- 最近 7 天的活跃用户数
- 系统总用户数
- 最近 30 天功能使用排行
- 最近 7 天活跃用户排行
- 使用 ECharts 图表展示数据

### 5. 审计日志查询
- 按用户、功能、日期范围查询日志
- 支持分页显示（最多 200 条/页）
- 展示详细的访问信息

## 安装和配置

### 1. 后端配置

已自动集成以下模块：

**新增文件：**
- `backend/app/models/audit_log.py` - AuditLog ORM 模型
- `backend/app/middleware/audit_middleware.py` - 请求拦截中间件
- `backend/app/routers/admin.py` - Admin API 路由
- `backend/app/services/admin_service.py` - 业务逻辑服务
- `backend/app/utils/geoip.py` - GeoIP 地理位置工具
- `backend/app/tasks/scheduler.py` - 定时任务调度器
- `backend/scripts/create_admin.py` - 创建管理员脚本

**修改的文件：**
- `backend/app/database.py` - 新增 AuditLog 模型导入
- `backend/app/main.py` - 注册中间件、路由和定时任务
- `backend/app/routers/auth.py` - 记录登录统计
- `backend/app/models/user.py` - 添加登录统计字段
- `backend/requirements.txt` - 添加 geoip2 和 apscheduler 依赖

### 2. 依赖安装

```bash
pip install -r requirements.txt
# 包含的新依赖：
# - geoip2>=4.7.0      (GeoIP 地理位置查询)
# - apscheduler>=3.10.0 (定时任务调度)
```

### 3. 数据库初始化

数据库在应用启动时自动初始化，新增表：
- `audit_logs` - 审计日志表

修改的表：
- `users` - 添加字段：
  - `last_login` (DateTime) - 最后登录时间
  - `login_count` (Integer) - 登录次数计数

### 4. 创建管理员账户

方式一：使用脚本（推荐）

```bash
cd backend
python3 scripts/create_admin.py admin@example.com password123 "管理员"
```

输出示例：
```
✓ 管理员账户创建成功
  邮箱：admin@example.com
  昵称：管理员
  角色：admin
```

方式二：直接数据库操作

需要使用 bcrypt 哈希密码，详见 `app/security.py` 中的 `hash_password()` 函数。

### 5. GeoIP 数据库（可选）

管理后台会自动尝试从以下位置加载 GeoIP 数据库：
- `backend/data/GeoLite2-City.mmdb`

如果不存在，系统会显示 "Unknown" 作为位置信息。

手动下载数据库：
```bash
cd backend/data
# 方式1：GitHub 链接
curl -L "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb" -o GeoLite2-City.mmdb

# 方式2：CDN
curl -L "https://cdn.jsdelivr.net/gh/allinurl/geoip-api/GeoLite2-City.mmdb" -o GeoLite2-City.mmdb
```

## 前端配置

已自动集成以下组件：

**新增文件：**
- `frontend/src/api/admin.ts` - Admin API 客户端
- `frontend/src/stores/admin.ts` - Pinia admin store
- `frontend/src/views/admin/AdminLayout.vue` - 后台布局
- `frontend/src/views/admin/AdminDashboard.vue` - 仪表板页面
- `frontend/src/views/admin/UserManagement.vue` - 用户管理页面
- `frontend/src/views/admin/UserDetail.vue` - 用户详情页面
- `frontend/src/views/admin/AuditLogs.vue` - 审计日志页面

**修改的文件：**
- `frontend/src/router/index.ts` - 添加 admin 路由
- `frontend/src/components/layout/AppSidebar.vue` - 添加 admin 菜单

## 访问管理后台

### 1. 登录

使用创建的管理员账户登录：
- 邮箱：admin@example.com
- 密码：password123

### 2. 访问路由

管理后台可通过以下路由访问：
- `/admin/dashboard` - 仪表板
- `/admin/users` - 用户管理列表
- `/admin/users/:id` - 用户详情和活动日志
- `/admin/audit-logs` - 系统审计日志

admin 用户登录后，侧边栏会显示"管理后台"菜单项。

### 3. 权限控制

- 仅 `admin` 角色用户可访问所有管理后台功能
- 前端路由守卫：`/admin/*` 路由要求 `admin` 角色
- 后端 API：`/api/admin/*` 路由要求 `admin` 角色
- 其他用户尝试访问会被重定向到首页

## 数据清理策略

### 日志清理

定时任务每天凌晨 2:00 执行一次清理：
- 删除 > 90 天的审计日志
- 删除数据库占用空间，但不影响最近 90 天的数据
- 日志删除数量会记录在应用日志中

可在 `backend/app/services/admin_service.py` 中修改：
- `AdminService.cleanup_old_logs()` - 调整清理逻辑
- `backend/app/tasks/scheduler.py` - 修改执行时间 (CronTrigger)

## API 端点

### 用户管理

```
GET /api/admin/users
  查询参数：page, page_size, search, role
  响应：{ total, page, page_size, items: [...] }

GET /api/admin/users/{user_id}
  响应：{ id, email, ..., login_7d, feature_stats: [...] }

PUT /api/admin/users/{user_id}/status
  请求体：{ is_active: boolean }
  响应：{ code: 200, data: { success: true } }

DELETE /api/admin/users/{user_id}
  响应：{ code: 200, data: { success: true } }
```

### 审计日志

```
GET /api/admin/audit-logs
  查询参数：page, page_size, user_id, feature, start_date, end_date
  响应：{ total, page, page_size, items: [...] }
```

### 统计数据

```
GET /api/admin/stats/dashboard
  响应：{
    active_users_7d: number,
    total_users: number,
    feature_top: [...],
    active_user_top: [...]
  }
```

## 功能分类代码

系统自动识别以下功能分类（基于 API 路由前缀）：

| 代码 | 功能 | API 路由前缀 |
|------|------|-------------|
| ai_chat | AI 对话 | /api/ai |
| notes | 笔记管理 | /api/notes |
| wrong_book | 错题集 | /api/wrong-book |
| quiz | 测试/练习 | /api/quiz |
| study_plan | 学习计划 | /api/plan |
| homework | 作业评分 | /api/homework |
| monitor | 学生监护 | /api/monitor |
| auth | 认证 | /api/auth |
| admin | 管理后台 | /api/admin |
| others | 其他 | 其他路由 |

## 故障排除

### Q: 地理位置显示为 "Unknown"
**A:** 这是正常情况，可能原因：
1. GeoIP 数据库未下载
2. 客户端 IP 无法查询（本地 IP、IPv6 等）
3. 数据库格式错误

无需修复，系统可以正常工作。

### Q: 定时任务无法启动
**A:** 检查：
1. `apscheduler` 已安装：`pip list | grep apscheduler`
2. 应用日志中是否有错误信息
3. 系统权限允许后台任务运行

### Q: 无法删除用户
**A:** 确认：
1. 用户不是 admin 角色
2. 用户存在于数据库中
3. 数据库连接正常

### Q: 审计日志为空
**A:** 原因可能：
1. 应用刚启动，还没有请求被记录
2. 只有已认证的请求才被记录
3. 日志可能已被清理（> 90 天）
4. 中间件可能未正确注册

检查：确保 `app.add_middleware(AuditMiddleware)` 已在 `main.py` 中执行。

## 安全建议

1. **强密码：** 创建 admin 账户时使用强密码
2. **权限限制：** 仅为可信人员创建 admin 账户
3. **日志审计：** 定期检查审计日志，监控异常活动
4. **备份：** 定期备份数据库，以防数据丢失
5. **HTTPS：** 生产环境必须使用 HTTPS

## 开发调试

### 查看中间件日志

修改 `backend/app/middleware/audit_middleware.py`，将 `logger.debug()` 改为 `logger.info()` 以查看详细日志。

### 手动触发日志清理

```python
from app.database import SessionLocal
from app.services.admin_service import AdminService

db = SessionLocal()
deleted = AdminService.cleanup_old_logs(db)
print(f"Deleted {deleted} old logs")
db.close()
```

### 测试 API

```bash
# 获取用户列表
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/admin/users

# 获取仪表板统计
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/admin/stats/dashboard

# 获取审计日志
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/admin/audit-logs
```

## 已知限制

1. **日志保留期：** 仅保留最近 90 天（可在代码中调整）
2. **分页限制：** 最大 page_size 为 200 条
3. **地理位置准确度：** 取决于 GeoIP 数据库的准确性
4. **实时性：** 统计数据通常延迟 1-2 秒（异步中间件）

## 后续功能扩展建议

1. **导出功能：** 支持导出用户列表和审计日志为 CSV/Excel
2. **告警规则：** 异常登录检测、批量操作告警
3. **用户操作：** 重置密码、强制登出
4. **权限分级：** 支持更多权限级别（如 super_admin, data_viewer）
5. **数据可视化：** 更多统计图表和趋势分析
6. **批量操作：** 批量启用/禁用/删除用户
7. **操作日志：** 记录管理员的所有操作

## 相关文件

- 设计文档：`docs/superpowers/specs/` (待生成)
- 实现计划：`docs/superpowers/plans/2026-06-25-admin-*.md`
- API 文档：可通过 Swagger UI 查看 (`http://localhost:8000/docs`)

## 支持

如有问题或建议，请查看代码注释或创建 Issue。
