FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（PyMuPDF 需要 libmupdf，Pillow 需要图像库）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 先安装核心依赖（不含 RAG 重型依赖）
RUN pip install --no-cache-dir \
    fastapi==0.110.0 \
    uvicorn[standard]==0.27.1 \
    sqlalchemy==2.0.28 \
    "pydantic[email]==2.6.3" \
    pydantic-settings==2.2.1 \
    email-validator==2.1.1 \
    "python-jose[cryptography]==3.3.0" \
    "bcrypt>=4.0.1" \
    python-multipart==0.0.9 \
    openai==1.14.0 \
    PyMuPDF==1.24.0 \
    python-docx==1.1.0 \
    Pillow==10.2.0 \
    aiofiles==23.2.1 \
    python-dotenv==1.0.1 \
    httpx==0.27.0

# 安装 chromadb（不含 sentence-transformers / torch，使用内置 ONNX embedding）
RUN pip install --no-cache-dir "chromadb>=0.5.0"

COPY . .

RUN mkdir -p uploads data

EXPOSE 8000

# 启动脚本：先运行迁移，再启动应用
COPY scripts/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
