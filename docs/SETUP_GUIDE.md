# EduBuddy 环境构筑指南

> **版本**：V1.0  
> **更新日期**：2026-06-05（最后验证：2026-06-05，服务运行正常）  
> **适用场景**：全新部署 / 环境重建 / 开发调试

---

## 目录

1. [系统要求](#1-系统要求)
2. [项目克隆](#2-项目克隆)
3. [环境变量配置](#3-环境变量配置)
4. [方式一：Docker Compose 生产部署（推荐）](#4-方式一docker-compose-生产部署推荐)
5. [方式二：本地开发环境](#5-方式二本地开发环境)
6. [RAG 知识库构建（可选）](#6-rag-知识库构建可选)
7. [功能验证](#7-功能验证)
8. [常见问题排查](#8-常见问题排查)
9. [环境维护与更新](#9-环境维护与更新)

---

## 1. 系统要求

### 硬件要求
| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 10 GB（含 Docker 镜像） | 30 GB+（含 RAG 知识库） |

### 软件依赖
| 软件 | 最低版本 | 验证命令 |
|------|---------|---------|
| Docker | 24.0+ | `docker --version` |
| Docker Compose | v2.20+ | `docker compose version` |
| Git | 2.30+ | `git --version` |
| Node.js（仅本地开发） | 18.0+ | `node --version` |
| Python（仅本地开发） | 3.10+ | `python3 --version` |

> 💡 **提示**：生产部署只需要 Docker 和 Docker Compose，无需安装 Node.js 或 Python。

---

## 2. 项目克隆

```bash
# 克隆仓库
git clone https://github.com/xinzhouw/EduBuddy.git
cd EduBuddy

# 确认项目结构
ls -la
```

项目结构应如下所示：
```
EduBuddy/
├── .env                    ← 环境变量（需手动创建，不提交 Git）
├── .gitignore
├── docker-compose.yml      ← Docker Compose 配置
├── docs/                   ← 项目文档
├── memory-bank/            ← Cline AI 工作记忆
├── agents/                 ← 教材爬虫 & RAG 构建工具
├── backend/                ← Python FastAPI 后端
│   ├── .env                ← 后端专用环境变量（与根目录保持同步）
│   ├── .env.example        ← 环境变量模板
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/                ← FastAPI 应用代码
│   ├── data/               ← SQLite 数据库 & 知识库
│   └── uploads/            ← 用户上传文件
└── frontend/               ← Vue 3 前端
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    └── src/                ← Vue 应用源码
```

---

## 3. 环境变量配置

### 3.1 创建环境变量文件

**⚠️ 重要：根目录 `.env` 和 `backend/.env` 必须内容完全一致！**

```bash
# 以 backend/.env.example 为模板创建配置文件
cp backend/.env.example backend/.env
# 同步到根目录（Docker Compose 读取此文件）
cp backend/.env .env
```

### 3.2 编辑配置项

使用任意编辑器修改 `backend/.env`（修改后务必同步到根目录）：

```bash
# 编辑后端配置
nano backend/.env

# 修改完毕后同步到根目录
cp backend/.env .env
```

### 3.3 配置项说明

```ini
# ================================================================
# OpenAI / 兼容 API 配置（必填）
# ================================================================

# API 密钥
OPENAI_API_KEY=sk-your-api-key-here

# API 接口地址（留空则使用 OpenAI 官方地址）
# 使用 DeepSeek：OPENAI_BASE_URL=https://api.deepseek.com/v1
# 使用通义千问：OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# 使用本地 Ollama：OPENAI_BASE_URL=http://localhost:11434/v1
# 使用 IBM watsonx.ai：OPENAI_BASE_URL=https://api.nextgen-beta.ica.ibm.com/ica/v1
OPENAI_BASE_URL=

# 模型名称（与服务商提供的模型名一致）
# OpenAI：gpt-4o / gpt-4o-mini / gpt-4-turbo
# DeepSeek：deepseek-chat / deepseek-reasoner
# 通义千问：qwen-max / qwen-plus / qwen-turbo
# Claude（via 兼容层）：claude-opus-4-8 / claude-sonnet-4-5
OPENAI_MODEL=gpt-4o

# 是否携带 temperature 参数
# 注意：Claude/Bedrock 等部分模型不接受此参数，使用时设为 false
OPENAI_USE_TEMPERATURE=true

# ================================================================
# 安全配置（必填，生产环境务必修改）
# ================================================================

# JWT 签名密钥（随机字符串，越长越安全）
# 生成示例：openssl rand -hex 32
SECRET_KEY=your-jwt-secret-key-change-this

# ================================================================
# 数据库配置
# ================================================================

# SQLite 数据库路径（Docker 内路径，一般不需要修改）
DATABASE_URL=sqlite:///./data/edubuddy.db

# ================================================================
# 文件上传配置
# ================================================================

UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=20

# ================================================================
# 跨域配置（前端访问地址）
# ================================================================

# 本地开发：http://localhost:5173
# 生产环境（Docker）：http://localhost:80
CORS_ORIGINS=http://localhost:5173,http://localhost:80
```

### 3.4 生成安全密钥

```bash
# 方式1：使用 openssl（推荐）
openssl rand -hex 32

# 方式2：使用 Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 4. 方式一：Docker Compose 生产部署（推荐）

### 4.1 确保环境变量已配置

```bash
# 验证 .env 文件存在且包含必要配置
cat .env | grep -E "OPENAI_API_KEY|OPENAI_MODEL|SECRET_KEY"
```

### 4.2 构建 Docker 镜像

```bash
# 首次构建（或代码变更后重新构建）
docker compose build --no-cache

# 仅构建后端
docker compose build --no-cache backend

# 仅构建前端
docker compose build --no-cache frontend
```

> ⏱️ 首次构建预计耗时：后端 5~10 分钟，前端 3~5 分钟（视网络速度）

### 4.3 启动服务

```bash
# 启动所有服务（后台运行）
docker compose up -d

# 查看启动状态
docker compose ps
```

正常输出示例：
```
NAME                    STATUS          PORTS
edubuddy-backend-1      Up              0.0.0.0:8001->8000/tcp
edubuddy-frontend-1     Up              0.0.0.0:80->80/tcp
```

### 4.4 访问应用

| 服务 | 地址 |
|------|------|
| 前端（Web 应用） | http://localhost:80 |
| 后端 API | http://localhost:8001 |
| API 文档（Swagger） | http://localhost:8001/docs |
| API 文档（ReDoc） | http://localhost:8001/redoc |

### 4.5 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 仅查看后端日志
docker compose logs -f backend

# 仅查看前端（Nginx）日志
docker compose logs -f frontend

# 查看最近 100 行后端日志
docker compose logs --tail=100 backend
```

### 4.6 停止服务

```bash
# 停止服务（保留容器）
docker compose stop

# 停止并删除容器
docker compose down

# 停止、删除容器和镜像（完全清理）
docker compose down --rmi all
```

---

## 5. 方式二：本地开发环境

适合开发调试，支持热重载，修改代码后立即生效。

### 5.1 后端（FastAPI）

```bash
# 进入后端目录
cd backend

# 创建 Python 虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS：
source venv/bin/activate
# Windows：
# venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 确认 .env 文件存在
ls -la .env
# 如果不存在，复制模板：
cp .env.example .env
# 编辑配置：
nano .env
```

**创建必要目录：**
```bash
mkdir -p data uploads
```

**启动后端开发服务器：**
```bash
# 在 backend/ 目录下执行
uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000/docs 确认后端已启动。

### 5.2 前端（Vue 3 + Vite）

```bash
# 新开终端，进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173 确认前端已启动。

> 💡 **Vite 代理说明**：开发模式下，前端 `/api/*` 请求会自动代理到 `http://localhost:8000`，无需手动配置跨域。

### 5.3 本地环境端口说明

| 服务 | 本地地址 |
|------|---------|
| 前端（Vite 开发服务器） | http://localhost:5173 |
| 后端（uvicorn） | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

---

## 6. RAG 知识库构建（可选）

RAG（检索增强生成）功能可让 AI 在回答时参考高中教材原文。不启用时 AI 问答仍可正常使用，只是不会引用教材内容。

### 6.1 安装 RAG 专用依赖

```bash
cd agents/textbook_crawler

# 安装 CPU 版 PyTorch（节省空间，约 800MB）
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 安装其他 RAG 依赖
pip install -r requirements.txt
```

### 6.2 下载高中教材 PDF

```bash
# 下载全部 9 大学科（约 814MB，50本教材）
python download_all_hs.py

# 仅下载指定学科
python download_all_hs.py --subject 数学
python download_all_hs.py --subject 物理
python download_all_hs.py --subject 化学

# 预览下载列表（不实际下载）
python download_all_hs.py --dry-run
```

教材将保存到：`agents/textbook_crawler/cache/pdfs/high_school/{学科}/`

### 6.3 构建向量知识库

```bash
# 使用默认 ONNX embedding（轻量，无需 torch）
python build_knowledge_base.py

# 使用 BGE 中文模型（推荐，检索精度更高）
python build_knowledge_base.py --embedder local

# 使用 OpenAI embedding（精度最高，需消耗 API Token）
python build_knowledge_base.py --embedder openai
```

> ⚠️ **重要**：embedding 模型选择后必须保持一致！如果重建知识库，需要删除旧的 `backend/data/knowledge_base/` 目录后重新构建。

构建完成后，知识库存储于：`backend/data/knowledge_base/chroma/`（约 58MB）

### 6.4 验证知识库

```bash
# 查看知识库统计
curl http://localhost:8001/api/ai/knowledge-base/stats

# 预览检索效果
curl "http://localhost:8001/api/ai/knowledge-base/retrieve?q=二次函数顶点式&subject=数学"
```

---

## 7. 功能验证

### 7.1 后端健康检查

```bash
# 检查后端是否正常响应
curl http://localhost:8001/docs

# 或（本地开发）
curl http://localhost:8000/docs
```

### 7.2 注册账号

1. 打开浏览器，访问 http://localhost:80（或开发环境 http://localhost:5173）
2. 点击「注册」
3. 填写用户名、邮箱、密码、年级
4. 注册成功后自动跳转到仪表盘

### 7.3 测试 AI 问答

1. 点击侧边栏「🤖 AI 问答」
2. 选择学科（如数学）
3. 输入问题（如「解释一元二次方程的求根公式」）
4. 等待 AI 流式输出答案

### 7.4 API 接口测试

```bash
# 用户注册（替换为你的 API 地址）
BASE_URL=http://localhost:8001

curl -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"nickname":"testuser","email":"test@example.com","password":"Test123456","grade":"高一"}'

# 用户登录（获取 Token）
TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123456"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

echo "Token: $TOKEN"

# 获取用户信息
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/auth/me"
```

---

## 8. 常见问题排查

### ❌ 问题1：Docker 构建失败（网络超时）

**现象**：`pip install` 或 `npm install` 时网络超时  
**解决**：

```bash
# 后端：使用国内 pip 镜像（在 Dockerfile 中修改）
# 在 RUN pip install 命令末尾添加：
# -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 前端：前端 Dockerfile 已配置淘宝镜像，通常无需额外设置
# 如仍有问题，手动设置：
npm config set registry https://registry.npmmirror.com
```

### ❌ 问题2：端口冲突

**现象**：`docker compose up` 提示端口已被占用  
**解决**：

```bash
# 查看端口占用
ss -tlnp | grep -E "80|8001"

# 修改 docker-compose.yml 中的端口映射
# 例如将 "80:80" 改为 "8080:80"
```

### ❌ 问题3：后端启动后 AI 功能无法使用（500 错误）

**现象**：AI 问答、练习题生成等功能返回 500  
**排查**：

```bash
# 查看后端日志
docker compose logs backend | grep -E "ERROR|error"

# 确认环境变量已正确加载
docker compose exec backend env | grep OPENAI
```

**常见原因**：
- `OPENAI_API_KEY` 未设置或无效
- `OPENAI_BASE_URL` 地址不正确
- 使用 Claude 等模型时忘记设置 `OPENAI_USE_TEMPERATURE=false`

### ❌ 问题4：前端页面空白 / 样式异常

**现象**：访问后页面空白或样式不生效  
**解决**：

```bash
# 重新构建前端
docker compose build --no-cache frontend
docker compose up -d frontend
```

### ❌ 问题5：数据库报错（表不存在）

**现象**：后端报 `no such table: users` 等错误  
**解决**：

```bash
# 后端启动时会自动调用 init_db() 创建所有表
# 如果表未创建，手动触发：
docker compose exec backend python -c "from app.database import init_db; init_db()"
```

### ❌ 问题6：文件上传失败

**现象**：上传 PDF/图片时提示 413 或存储错误  
**排查**：

```bash
# 确认上传目录存在且有写权限
docker compose exec backend ls -la /app/uploads

# 如不存在，手动创建
docker compose exec backend mkdir -p /app/uploads
```

### ❌ 问题7：RAG 检索无结果

**现象**：AI 回答不引用教材内容  
**排查**：

```bash
# 检查知识库是否存在
ls -la backend/data/knowledge_base/chroma/

# 检查知识库统计
curl http://localhost:8001/api/ai/knowledge-base/stats
```

**解决**：若知识库为空，参考 [第6节](#6-rag-知识库构建可选) 重新构建。

### ❌ 问题8：backend/.env 和根目录 .env 不一致

**现象**：本地后端和 Docker 部署行为不一致  
**解决**：始终以 `backend/.env` 为主，修改后同步到根目录：

```bash
cp backend/.env .env
```

### ❌ 问题9：curl / 浏览器通过代理访问 localhost 返回 403

**现象**：系统设置了 HTTP 代理（如企业网络、VPN），curl 访问 `http://localhost:8001` 时被代理服务器拦截返回 403，或提示 "Connect failed"  
**排查**：

```bash
# 检查代理环境变量
echo $http_proxy
echo $HTTP_PROXY
```

**解决**：在 curl 命令前加 `no_proxy` 绕过代理，或将 localhost 加入代理排除列表：

```bash
# 方式1：单次命令绕过代理
no_proxy="localhost,127.0.0.1" curl http://localhost:8001/

# 方式2：永久加入排除列表（写入 ~/.bashrc 或 ~/.zshrc）
export no_proxy="localhost,127.0.0.1,${no_proxy}"

# 方式3：浏览器访问（浏览器通常默认不代理 localhost）
# 直接在浏览器地址栏输入 http://localhost:80 即可正常访问
```

---

## 9. 环境维护与更新

### 9.1 代码更新后重新部署

```bash
# 拉取最新代码
git pull

# 重新构建并重启
docker compose build --no-cache
docker compose up -d
```

### 9.2 仅更新后端（前端不变）

```bash
docker compose build --no-cache backend
docker compose up -d backend
```

### 9.3 清理旧镜像节省磁盘

```bash
# 删除悬空镜像（旧版本构建产物）
docker image prune -f

# 查看 Docker 磁盘使用
docker system df
```

### 9.4 备份数据库

```bash
# 将数据库文件复制到备份目录
cp backend/data/edubuddy.db backup/edubuddy_$(date +%Y%m%d_%H%M%S).db
```

### 9.5 查看后端虚拟环境（本地开发）

```bash
cd backend
source venv/bin/activate
pip list  # 查看已安装的包
pip install -r requirements.txt  # 更新依赖
```

---

## 附录：端口与服务速查

| 环境 | 服务 | 地址 |
|------|------|------|
| Docker 生产 | Web 前端 | http://localhost:80 |
| Docker 生产 | 后端 API | http://localhost:8001 |
| Docker 生产 | API 文档 | http://localhost:8001/docs |
| 本地开发 | 前端（Vite） | http://localhost:5173 |
| 本地开发 | 后端（uvicorn） | http://localhost:8000 |
| 本地开发 | API 文档 | http://localhost:8000/docs |

## 附录：关键文件速查

| 文件 | 用途 |
|------|------|
| `.env` | 根目录环境变量（Docker Compose 读取） |
| `backend/.env` | 后端环境变量（本地开发读取）|
| `backend/.env.example` | 环境变量模板 |
| `docker-compose.yml` | Docker Compose 服务编排 |
| `backend/Dockerfile` | 后端镜像构建配置 |
| `frontend/Dockerfile` | 前端镜像构建配置 |
| `frontend/nginx.conf` | Nginx 配置（含 API 反向代理、SSE 支持） |
| `frontend/vite.config.ts` | Vite 配置（含开发代理） |
| `backend/data/edubuddy.db` | SQLite 数据库文件 |
| `backend/data/knowledge_base/` | RAG 向量知识库 |
| `backend/uploads/` | 用户上传的文件 |
