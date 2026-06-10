# EduBuddy 生产部署迁移指南

> 适用场景：将 EduBuddy 从开发机迁移到一台全新安装的 Ubuntu 主机（推荐 Ubuntu 22.04 LTS 或 24.04 LTS）。
> 部署方式：**Docker Compose**（推荐，开箱即用，无需手动安装 Python / Node.js 环境）。

本指南提供 **三种迁移方式**，请根据实际情况选择：

| 方式 | 适用场景 | 优点 |
|------|---------|------|
| [**方式 A：Docker Hub 拉取镜像**](#3-方式-a通过-docker-hub-拉取镜像推荐)（**推荐**） | 新主机可访问 Internet，镜像已推送到 Docker Hub | 一条命令即可完成，无需传输大文件，支持多平台 (amd64/arm64) |
| [**方式 B：离线 tar 包迁移**](#4-方式-b离线-tar-包迁移) | 新主机无法访问 Internet / Docker Hub | 完全离线，无需公网 |
| [**方式 C：从源码构建**](#5-方式-c从源码重新构建) | 需要修改代码后部署 | 灵活，可定制 |

---

## 目录

1. [系统要求](#1-系统要求)
2. [在新主机上安装 Docker](#2-在新主机上安装-docker)
3. [方式 A：通过 Docker Hub 拉取镜像（推荐）](#3-方式-a通过-docker-hub-拉取镜像推荐)
4. [方式 B：离线 tar 包迁移](#4-方式-b离线-tar-包迁移)
5. [方式 C：从源码重新构建](#5-方式-c从源码重新构建)
6. [配置环境变量](#6-配置环境变量)
7. [迁移持久化数据（数据库 & 上传文件）](#7-迁移持久化数据数据库--上传文件)
8. [启动容器并验证](#8-启动容器并验证)
9. [防火墙与端口开放](#9-防火墙与端口开放)
10. [配置 HTTPS（可选但强烈推荐）](#10-配置-https可选但强烈推荐)
11. [日常运维命令](#11-日常运维命令)
12. [常见问题排查](#12-常见问题排查)
13. [架构说明图](#13-架构说明图)

---

## 1. 系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Ubuntu 20.04 LTS | Ubuntu 22.04 / 24.04 LTS |
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB RAM | 8 GB RAM |
| 磁盘 | 40 GB | 80 GB（含知识库向量数据约 60MB，用户上传文件） |
| 网络 | 可访问 OpenAI API（或自定义 AI 网关） | 同左 |
| Docker | 24.0+ | 最新稳定版 |
| Docker Compose | V2（`docker compose` 命令，无连字符） | 同左 |

> ⚠️ **注意**：后端 Docker 镜像含 chromadb 等依赖，体积较大（约 3~10 GB），请确保磁盘空间充足。

---

## 2. 在新主机上安装 Docker

### 2.1 一键安装 Docker Engine + Docker Compose V2

```bash
# 更新 apt 包索引
sudo apt-get update

# 安装必要依赖
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# 添加 Docker 官方 GPG 密钥
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 添加 Docker apt 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine 和 Compose 插件
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

> 💡 **离线安装 Docker（新主机无网络）**：在有网络的机器上预先下载 `.deb` 安装包，
> 参考官方文档 <https://docs.docker.com/engine/install/ubuntu/#install-from-a-package>，
> 下载后通过 U 盘或内网传输到新主机，用 `sudo dpkg -i *.deb` 安装。

### 2.2 将当前用户加入 docker 组（免 sudo）

```bash
sudo usermod -aG docker $USER

# 使组成员变更立即生效（或重新登录 SSH）
newgrp docker
```

### 2.3 验证安装

```bash
docker --version
# 期望输出示例：Docker version 26.1.4, build 5650f9b

docker compose version
# 期望输出示例：Docker Compose version v2.27.1
```

---

## 3. 方式 A：通过 Docker Hub 拉取镜像（推荐）

镜像托管于 Docker Hub：
- 后端：`xinzhouw/edubuddy:backend`
- 前端：`xinzhouw/edubuddy:frontend`

两个镜像均以多平台方式构建（`linux/amd64` + `linux/arm64`），可直接在 x86 服务器或 Apple Silicon Mac / ARM 主机上运行。

### 3.1 — （开发机）构建并推送镜像到 Docker Hub

> 此步骤在**开发机（旧主机/CI 环境）**上执行，新代码发布时运行一次。
> 新主机部署时跳过此步，直接从第 3.2 步开始。

```bash
# 登录 Docker Hub（首次需要）
docker login
# 输入 Docker Hub 用户名和密码

# ── 构建并推送后端镜像 ──
# 进入后端源码目录（含 Dockerfile）
cd /home/youruser/src/EduBuddy/backend

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t xinzhouw/edubuddy:backend \
  --push \
  .

# ── 构建并推送前端镜像 ──
# 进入前端源码目录（含 Dockerfile）
cd /home/youruser/src/EduBuddy/frontend

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t xinzhouw/edubuddy:frontend \
  --push \
  .
```

> 💡 **首次使用 buildx 多平台构建**：需要先创建并启用 buildx builder：
> ```bash
> docker buildx create --name multiarch --use
> docker buildx inspect --bootstrap
> ```

---

### 3.2 — （新主机）获取 docker-compose.yml 和配置文件

由于使用 Docker Hub 镜像，新主机**不需要**完整的源码，只需要以下文件：
- `docker-compose.yml`（容器编排配置）
- `.env`（环境变量）
- `backend/` 目录结构（用于持久化数据挂载）

**方法 1：直接创建部署目录和 docker-compose.yml**

```bash
# 创建部署目录
sudo mkdir -p /opt/edubuddy/backend/{data,uploads}
sudo chown -R $USER:$USER /opt/edubuddy
cd /opt/edubuddy

# 创建 docker-compose.yml，使用 Docker Hub 镜像
cat > docker-compose.yml << 'EOF'
services:
  backend:
    image: xinzhouw/edubuddy:backend
    ports:
      - "8001:8000"
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/data:/app/data
    env_file:
      - .env
    environment:
      - DATABASE_URL=sqlite:///./data/edubuddy.db
      - UPLOAD_DIR=./uploads
      - TZ=Asia/Shanghai
    restart: unless-stopped

  frontend:
    image: xinzhouw/edubuddy:frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
EOF
```

**方法 2：从 Git 仓库只拉取配置文件（如有 Git 访问权限）**

```bash
sudo apt-get install -y git
git clone --depth 1 https://github.com/xinzhouw/EduBuddy.git /opt/edubuddy
cd /opt/edubuddy
mkdir -p backend/data backend/uploads
```

---

### 3.3 — 拉取镜像

```bash
cd /opt/edubuddy

# 拉取最新镜像（Docker 会自动选择匹配当前平台的镜像）
docker pull xinzhouw/edubuddy:backend
docker pull xinzhouw/edubuddy:frontend

# 验证镜像已下载
docker images | grep xinzhouw
```

---

### 3.4 — 配置环境变量并启动

参考[第 6 节](#6-配置环境变量)完成 `.env` 文件配置，然后：

```bash
cd /opt/edubuddy

# 直接启动（镜像已拉取，无需构建）
docker compose up -d

# 查看启动日志
docker compose logs -f
```

---

跳过第 4、5 节，继续 [第 6 节：配置环境变量](#6-配置环境变量)。

---

## 4. 方式 B：离线 tar 包迁移

适合新主机**无法访问 Internet / Docker Hub** 的场景。将旧主机上已构建好的镜像打包成 `.tar` 文件传输。

### 步骤 4.1 — 在旧主机上导出镜像

```bash
# 在【旧主机】的项目目录执行
cd /home/youruser/src/EduBuddy

# 确认镜像名称（可能是 edubuddy-backend 或 xinzhouw/edubuddy）
docker images | grep -E "edubuddy"

# 将两个镜像打包（根据实际镜像名修改）
docker save xinzhouw/edubuddy:backend xinzhouw/edubuddy:frontend \
    -o edubuddy-images.tar

# 若镜像名为本地构建的名称，则改为：
# docker save edubuddy-backend:latest edubuddy-frontend:latest -o edubuddy-images.tar

# 查看文件大小
ls -lh edubuddy-images.tar
```

### 步骤 4.2 — 打包配置文件和运行时数据

```bash
# 在【旧主机】项目根目录执行
tar -czf edubuddy-config.tar.gz \
    docker-compose.yml \
    .env \
    backend/.env.example \
    backend/data/ \
    backend/uploads/
```

### 步骤 4.3 — 传输到新主机

```bash
# 通过 scp 传输（替换 user@newhost 和路径）
scp edubuddy-images.tar    user@newhost:/opt/
scp edubuddy-config.tar.gz user@newhost:/opt/

# 若无法直接 SSH，可用 U 盘或内网文件服务器中转
```

### 步骤 4.4 — 在新主机上加载镜像

```bash
# 在【新主机】执行

# 加载镜像（几分钟，视磁盘速度而定）
docker load -i /opt/edubuddy-images.tar

# 验证
docker images | grep -E "edubuddy"
```

### 步骤 4.5 — 解压配置文件

```bash
sudo mkdir -p /opt/edubuddy
sudo chown $USER:$USER /opt/edubuddy
cd /opt/edubuddy
tar -xzf /opt/edubuddy-config.tar.gz

ls -la /opt/edubuddy/
# 应看到：docker-compose.yml  .env  backend/
```

> ⚠️ **注意**：若 `docker-compose.yml` 中的 `image:` 字段引用的是 `xinzhouw/edubuddy:backend`
> 等 Docker Hub 镜像名，而 `docker load` 加载后镜像名也相同，则可以直接使用。
> 若名称不匹配（如旧主机本地构建的 `edubuddy-backend:latest`），可用以下命令打标签：
> ```bash
> docker tag edubuddy-backend:latest xinzhouw/edubuddy:backend
> docker tag edubuddy-frontend:latest xinzhouw/edubuddy:frontend
> ```

参考[第 6 节](#6-配置环境变量)完成 `.env` 配置，然后跳至[第 8 节](#8-启动容器并验证)。

---

## 5. 方式 C：从源码重新构建

适合新主机可以访问互联网，或需要修改代码后部署的场景。

### 步骤 5.1 — 获取项目代码

**选项 1：从 Git 仓库克隆**

```bash
sudo apt-get install -y git
sudo mkdir -p /opt/edubuddy
sudo chown $USER:$USER /opt/edubuddy
git clone https://github.com/xinzhouw/EduBuddy.git /opt/edubuddy
cd /opt/edubuddy
```

**选项 2：从旧主机通过 SCP 传输源码**

```bash
# 在【旧主机】打包源码（排除无需传输的大文件）
cd /home/youruser/src
tar --exclude='EduBuddy/.git' \
    --exclude='EduBuddy/backend/.venv' \
    --exclude='EduBuddy/backend/venv' \
    --exclude='EduBuddy/frontend/node_modules' \
    --exclude='EduBuddy/backend/data/knowledge_base' \
    -czf edubuddy-src.tar.gz EduBuddy/

scp edubuddy-src.tar.gz user@newhost:/opt/

# 在【新主机】解压
sudo mkdir -p /opt/edubuddy
sudo chown $USER:$USER /opt/edubuddy
tar -xzf /opt/edubuddy-src.tar.gz -C /opt/
mv /opt/EduBuddy /opt/edubuddy 2>/dev/null || true
cd /opt/edubuddy
```

### 步骤 5.2 — 构建并启动容器

```bash
cd /opt/edubuddy
mkdir -p backend/data backend/uploads

# ⏳ 首次构建后端镜像需要 10~20 分钟（下载 Python 依赖），请耐心等待
docker compose up -d --build

docker compose logs -f
```

> 💡 **国内网络加速**：
> - 前端 Dockerfile 已配置使用 `npmmirror.com` 镜像，无需修改。
> - 后端 Python 包如需加速，修改 `backend/Dockerfile`：
>   ```dockerfile
>   RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
>   ```

---

## 6. 配置环境变量

EduBuddy 的所有关键配置均通过项目**根目录**下的 `.env` 文件注入（`docker-compose.yml` 中 `env_file: - .env`）。

### 6.1 创建 .env 文件

```bash
cd /opt/edubuddy

# 若 .env 不存在（方式 A 手动创建部署目录时），从模板创建：
cp backend/.env.example .env
# 或直接创建：
# touch .env

# 编辑配置
nano .env
```

### 6.2 必填配置项说明

```dotenv
# ============================================================
# AI 服务配置（必填）
# ============================================================

# OpenAI API Key（必填）
# 可使用官方 OpenAI，或任何 OpenAI 兼容 API（DeepSeek、通义千问等）
OPENAI_API_KEY=sk-your-api-key-here

# AI 服务地址（留空 = 使用 OpenAI 官方地址）
# DeepSeek:    OPENAI_BASE_URL=https://api.deepseek.com/v1
# 通义千问:     OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# IBM watsonx:  OPENAI_BASE_URL=https://your-watsonx-endpoint/v1
# 本地 Ollama:  OPENAI_BASE_URL=http://host.docker.internal:11434/v1
OPENAI_BASE_URL=

# 模型名称
# OpenAI:   gpt-4o
# DeepSeek: deepseek-chat
# 千问:     qwen-max
OPENAI_MODEL=gpt-4o

# 若 AI 网关不支持 temperature 参数（如某些 Claude 网关），设为 false
OPENAI_USE_TEMPERATURE=true

# ============================================================
# 安全配置（必填，生产环境务必修改）
# ============================================================

# JWT 签名密钥，生产环境必须使用强随机字符串（见 6.3 节）
SECRET_KEY=your-jwt-secret-key-change-this-in-production

# ============================================================
# 数据库配置（容器内路径，通常不需修改）
# ============================================================
DATABASE_URL=sqlite:///./data/edubuddy.db

# ============================================================
# 文件上传配置
# ============================================================
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=20

# ============================================================
# 跨域配置
# ============================================================
# 生产环境改为实际的前端访问域名/IP
# 例如：http://192.168.1.100,https://edubuddy.example.com
CORS_ORIGINS=http://localhost,http://localhost:80
```

### 6.3 生成强随机 SECRET_KEY

```bash
openssl rand -hex 32
# 将输出结果填入 .env 中的 SECRET_KEY=
```

### 6.4 确认文件权限（保护敏感信息）

```bash
chmod 600 /opt/edubuddy/.env
```

---

## 7. 迁移持久化数据（数据库 & 上传文件）

Docker Compose 将以下目录挂载为持久化卷：

| 本机路径 | 容器内路径 | 内容 |
|---------|----------|------|
| `./backend/uploads/` | `/app/uploads` | 用户上传的文件（PDF、图片等） |
| `./backend/data/` | `/app/data` | SQLite 数据库 + RAG 知识库 |

> **方式 B** 用户：若已在步骤 4.2 中将 `backend/data/` 和 `backend/uploads/` 一并打包，本节已完成，跳至[第 8 节](#8-启动容器并验证)。

### 7.1 迁移用户数据库（方式 A / C 适用）

```bash
# 在【旧主机】备份
cd /home/youruser/src/EduBuddy
tar -czf edubuddy-data-backup.tar.gz \
    backend/data/edubuddy.db \
    backend/uploads/

# 传输到新主机
scp edubuddy-data-backup.tar.gz user@newhost:/opt/edubuddy/

# 在【新主机】解压
cd /opt/edubuddy
tar -xzf edubuddy-data-backup.tar.gz
```

### 7.2 迁移 RAG 知识库（可选）

RAG 知识库向量数据存储在 `backend/data/knowledge_base/chroma/`，约 58MB。
若不迁移，应用仍可正常运行，仅 AI 问答时无法检索教材内容。

```bash
# 在【旧主机】
tar -czf edubuddy-knowledge-base.tar.gz backend/data/knowledge_base/
scp edubuddy-knowledge-base.tar.gz user@newhost:/opt/edubuddy/

# 在【新主机】
cd /opt/edubuddy
tar -xzf edubuddy-knowledge-base.tar.gz
```

### 7.3 确保目录存在（全新部署时）

```bash
cd /opt/edubuddy
mkdir -p backend/uploads backend/data
```

---

## 8. 启动容器并验证

### 8.1 启动服务

```bash
cd /opt/edubuddy

# 方式 A（Docker Hub 镜像）& 方式 B（离线加载）：直接启动，无需构建
docker compose up -d

# 方式 C（从源码构建）：
docker compose up -d --build
```

### 8.2 确认容器运行状态

```bash
docker compose ps
```

期望输出：

```
NAME                    IMAGE                        COMMAND                  SERVICE    CREATED         STATUS         PORTS
edubuddy-backend-1      xinzhouw/edubuddy:backend    "uvicorn app.main:ap…"   backend    2 minutes ago   Up 2 minutes   0.0.0.0:8001->8000/tcp
edubuddy-frontend-1     xinzhouw/edubuddy:frontend   "/docker-entrypoint.…"   frontend   2 minutes ago   Up 2 minutes   0.0.0.0:80->80/tcp
```

### 8.3 检查后端 API 健康状态

```bash
curl -s http://localhost:8001/
# 期望输出：{"message":"EduBuddy API is running","version":"1.0.0"}
```

### 8.4 检查前端页面

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:80/
# 期望输出：200
```

### 8.5 检查 API 文档（开发/调试用）

浏览器访问 `http://<服务器IP>:8001/docs`，可看到 Swagger UI 交互式 API 文档。

### 8.6 完整功能验证流程

1. 浏览器访问 `http://<服务器IP>/`，看到登录页面
2. 点击「注册」，填写邮箱、密码、昵称、年级，提交注册
3. 使用刚注册的账号登录
4. 进入「AI 问答」页面，选择学科，输入问题，验证 AI 流式回答
5. 进入「文档上传」，上传一份 PDF，验证解析功能

---

## 9. 防火墙与端口开放

| 端口 | 用途 | 是否对外开放 |
|------|------|------------|
| 80 | 前端 Web 应用（Nginx） | ✅ 必须 |
| 443 | HTTPS（配置 SSL 后） | ✅ 推荐 |
| 8001 | 后端 API（调试用） | ⚠️ 可选，生产建议关闭 |
| 22 | SSH 管理 | ✅ 必须 |

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# sudo ufw allow 8001/tcp  # 仅调试时开启

sudo ufw enable
sudo ufw status
```

> ⚠️ **安全建议**：生产环境不应对外开放 8001 端口。前端 Nginx 已通过 Docker 内网
> （`http://backend:8000`）代理所有 `/api/` 请求，外部用户只需访问 80/443 即可。

---

## 10. 配置 HTTPS（可选但强烈推荐）

```bash
# 安装宿主机 Nginx + Certbot
sudo apt-get install -y nginx certbot python3-certbot-nginx

# 修改 docker-compose.yml，将前端端口改为只监听本机，避免与宿主机 Nginx 冲突：
# 将：  - "80:80"
# 改为：- "127.0.0.1:8080:80"
docker compose down && docker compose up -d

# 申请证书
sudo certbot --nginx -d yourdomain.com

# 配置宿主机 Nginx
cat << 'EOF' | sudo tee /etc/nginx/sites-available/edubuddy
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 50m;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/edubuddy /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

同时更新 `.env` 中的 `CORS_ORIGINS` 并重启后端：

```dotenv
CORS_ORIGINS=https://yourdomain.com
```

```bash
docker compose restart backend
```

---

## 11. 日常运维命令

### 查看运行状态

```bash
docker compose ps
docker compose logs -f
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs --tail=100 backend
```

### 更新镜像（方式 A：推送新版到 Docker Hub 后在新主机拉取）

**开发机：构建并推送新版本**

```bash
# 推送后端新版本
cd /path/to/EduBuddy/backend
docker buildx build --platform linux/amd64,linux/arm64 \
    -t xinzhouw/edubuddy:backend --push .

# 推送前端新版本
cd /path/to/EduBuddy/frontend
docker buildx build --platform linux/amd64,linux/arm64 \
    -t xinzhouw/edubuddy:frontend --push .
```

**新主机：拉取并重启**

```bash
cd /opt/edubuddy
docker compose pull          # 拉取最新镜像
docker compose up -d         # 以新镜像重启容器
```

### 更新应用（方式 C：从代码重新构建）

```bash
cd /opt/edubuddy
git pull
docker compose up -d --build
```

### 重启服务

```bash
docker compose restart
docker compose restart backend
docker compose restart frontend
```

### 停止与清理

```bash
docker compose stop
docker compose down
docker compose down --volumes   # ⚠️ 慎用，会删除数据卷

docker system prune -f
docker image prune -f
```

### 数据备份

```bash
cd /opt/edubuddy
tar -czf "edubuddy-backup-$(date +%Y%m%d-%H%M%S).tar.gz" \
    backend/data/edubuddy.db \
    backend/uploads/

# 含知识库的完整备份
tar -czf "edubuddy-full-backup-$(date +%Y%m%d).tar.gz" \
    backend/data/ \
    backend/uploads/
```

### 进入容器调试

```bash
docker compose exec backend bash
docker compose exec backend python -c "from app.database import engine; print(engine.url)"
docker compose exec backend ls -lh /app/data/
```

---

## 12. 常见问题排查

### ❌ 问题：docker compose pull 速度很慢

Docker Hub 在中国大陆访问可能较慢，可配置镜像加速：

```bash
# 编辑 Docker daemon 配置
sudo nano /etc/docker/daemon.json
```

```json
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://registry.docker-cn.com"
  ]
}
```

```bash
sudo systemctl daemon-reload && sudo systemctl restart docker
```

---

### ❌ 问题：docker compose up 后容器立即退出

```bash
# 查看退出原因
docker compose logs backend
docker compose logs frontend
```

**常见原因：**
- `.env` 文件不存在或路径错误（docker-compose.yml 中 `env_file: - .env` 指向根目录）
- `backend/data/` 目录不存在导致 SQLite 无法创建数据库文件
- `OPENAI_API_KEY` 为空（后端启动时 pydantic-settings 验证失败）

---

### ❌ 问题：前端显示空白 / API 请求 502

```bash
docker compose ps
curl http://localhost:8001/
docker compose exec frontend wget -qO- http://backend:8000/
```

**常见原因：**
- `CORS_ORIGINS` 未包含新主机的实际访问 IP / 域名
- 后端容器未正常启动

---

### ❌ 问题：AI 问答无响应 / 500 错误

```bash
docker compose logs -f backend

docker compose exec backend python -c "
from app.config import settings
print('API Key:', settings.openai_api_key[:10] + '...' if settings.openai_api_key else 'NOT SET')
print('Base URL:', settings.openai_base_url or 'OpenAI Official')
print('Model:', settings.openai_model)
"
```

若新主机需要通过代理访问 AI 服务，在 `.env` 中添加：

```dotenv
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080
NO_PROXY=localhost,127.0.0.1,backend
```

---

### ❌ 问题：端口 80 被占用

```bash
sudo lsof -i :80
sudo systemctl stop apache2 nginx 2>/dev/null
docker compose up -d
```

---

### ❌ 问题：磁盘空间不足

```bash
df -h
docker system prune -a -f
sudo journalctl --vacuum-size=500M
```

---

## 13. 架构说明图

```
用户浏览器
    │
    │ HTTP :80 / HTTPS :443
    ▼
┌─────────────────────────────────────────┐
│        Docker Network (bridge)           │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  xinzhouw/edubuddy:frontend      │   │
│  │  (Nginx :80)                     │   │
│  │                                  │   │
│  │  /          → Vue SPA 静态文件   │   │
│  │  /api/*     → proxy → backend:8000│  │
│  │  /uploads/* → proxy → backend:8000│  │
│  └──────────────┬───────────────────┘   │
│                 │ Docker 内网            │
│  ┌──────────────▼───────────────────┐   │
│  │  xinzhouw/edubuddy:backend       │   │
│  │  (Uvicorn :8000)                 │   │
│  │                                  │   │
│  │  FastAPI 应用                    │   │
│  │  ├── SQLite DB (/app/data/)      │   │
│  │  ├── 用户文件 (/app/uploads/)   │   │
│  │  └── RAG 知识库 (ChromaDB)      │   │
│  └──────────────────────────────────┘   │
│                                          │
│  宿主机持久化卷挂载：                     │
│  ./backend/data/    → /app/data/        │
│  ./backend/uploads/ → /app/uploads/     │
└─────────────────────────────────────────┘
         │
         │ HTTPS（外网）
         ▼
    OpenAI / DeepSeek / 通义千问 / IBM watsonx
```

---

## 快速检查清单

### 方式 A（Docker Hub 镜像，推荐）

**开发机侧（发布新版本时）：**
- [ ] `docker buildx build --platform linux/amd64,linux/arm64 -t xinzhouw/edubuddy:backend --push .`（在 `backend/` 目录）
- [ ] `docker buildx build --platform linux/amd64,linux/arm64 -t xinzhouw/edubuddy:frontend --push .`（在 `frontend/` 目录）
- [ ] Docker Hub 上可看到更新后的镜像

**新主机侧（初次部署）：**
- [ ] Docker 和 Docker Compose V2 已安装
- [ ] `/opt/edubuddy/docker-compose.yml` 已创建，`image:` 引用 `xinzhouw/edubuddy:backend/frontend`
- [ ] `/opt/edubuddy/.env` 已创建并填写所有必填项
- [ ] `SECRET_KEY` 已更换为强随机值（`openssl rand -hex 32`）
- [ ] `OPENAI_API_KEY` 已填写且有效
- [ ] `CORS_ORIGINS` 已配置为新主机实际访问地址
- [ ] `backend/uploads/` 和 `backend/data/` 目录已存在
- [ ] 旧数据库和上传文件已迁移（如需）
- [ ] `docker compose pull` 执行成功
- [ ] `docker compose up -d` 执行成功
- [ ] `docker compose ps` 显示两个容器均为 `Up`
- [ ] `curl http://localhost:8001/` 返回健康检查响应
- [ ] 浏览器访问前端页面正常
- [ ] 防火墙已开放 80 端口

### 方式 B（离线 tar 包）

- [ ] Docker 和 Docker Compose V2 已安装
- [ ] `docker load -i edubuddy-images.tar` 执行成功，镜像可见
- [ ] 配置文件和数据已解压到 `/opt/edubuddy/`
- [ ] `.env` 已按新主机环境更新
- [ ] `docker compose up -d` 执行成功
- [ ] 验证通过（API 健康、前端可访问）

### 方式 C（源码构建）

- [ ] Docker 和 Docker Compose V2 已安装
- [ ] 源码已克隆/复制到 `/opt/edubuddy`
- [ ] `.env` 已配置
- [ ] `docker compose up -d --build` 执行成功
- [ ] 验证通过

---

*文档版本：V1.3 | 更新日期：2026-06-08*
