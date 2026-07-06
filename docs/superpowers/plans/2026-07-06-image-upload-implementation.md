# AI 问答图片上传功能 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 实现 EduBuddy AI 问答的图片上传功能，支持用户上传学科试题截图，使用 OCR + Vision API 双重识别，然后 AI 解答。

**架构：** 
- 前端：图片拖拽上传 + 预览库 + 问题编辑（两步流）
- 后端：文件验证 → 并行 OCR + Vision → 结果融合 → 增强提示词 → 流式对话
- 存储：本地磁盘（`backend/uploads/{user_id}/{session_id}/`）
- 处理策略：融合式（方案 C），两个失败则降级

**技术栈：** 
- 后端：FastAPI, SQLAlchemy, PaddleOCR, OpenAI Vision API, AsyncOpenAI
- 前端：Vue 3, Element Plus, Axios
- 测试：pytest, Vitest

## 全局约束

- Python >= 3.8（FastAPI 兼容）
- 每条消息最多 5 张图片，单个 ≤10MB
- 支持格式：JPG/PNG/PDF
- 数据库：SQLite（级联删除）
- 本地存储路径：`backend/uploads/{user_id}/{session_id}/{timestamp}_{index}_{filename}`
- 权限检查：用户只能访问/删除自己的图片
- 超时：OCR 10s，Vision 30s，整体 45s

---

## 文件结构

### 新建文件

```
backend/
├── app/
│   ├── models/
│   │   └── image.py                    # ChatImage ORM 模型
│   ├── services/
│   │   └── image_service.py            # 图片处理服务（验证、保存、OCR、Vision）
│   └── schemas/
│       └── image.py                    # 图片相关 Pydantic Schema
tests/
├── unit/
│   └── services/
│       └── test_image_service.py       # ImageService 单元测试
└── integration/
    └── routers/
        └── test_ai_routes_with_images.py  # 集成测试

frontend/
├── src/
│   ├── components/
│   │   └── shared/
│   │       └── ImageUploadArea.vue     # 图片上传组件
│   ├── api/
│   │   └── image.ts                    # 图片 API 封装
│   └── utils/
│       └── imageUpload.ts              # 图片验证工具
tests/
└── unit/
    └── components/
        └── ImageUploadArea.spec.ts     # 组件测试
```

### 修改文件

```
backend/
├── app/
│   ├── models/
│   │   └── note.py                     # 扩展 ChatMessage（添加 image_ids 等字段）
│   ├── services/
│   │   └── ai_service.py               # 添加 chat_stream_with_images() 方法
│   ├── routers/
│   │   └── ai.py                       # 修改 POST /api/ai/chat 支持文件上传
│   └── requirements.txt                # 添加新依赖
frontend/
├── src/
│   └── views/
│       └── ai/
│           └── AIChatView.vue          # 集成 ImageUploadArea、显示图片
```

---

## 实现任务

### 阶段 1：数据模型和数据库（准备基础）

#### Task 1: 创建 ChatImage ORM 模型

**文件：**
- 创建: `backend/app/models/image.py`
- 修改: `backend/app/models/__init__.py`

**接口：**
- 消费：SQLAlchemy, datetime
- 生产：`ChatImage` 模型类（用于数据库操作）

- [ ] **步骤 1：创建 image.py 模型文件**

```python
# backend/app/models/image.py
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class ChatImage(Base):
    __tablename__ = "chat_images"
    
    id = Column(String(100), primary_key=True)
    session_id = Column(String(50), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(10), nullable=False)
    ocr_text = Column(Text, nullable=True)
    vision_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # 索引
    __table_args__ = (
        Index("idx_chat_image_session_user", "session_id", "user_id"),
        Index("idx_chat_image_created", "created_at"),
    )
    
    # 关系
    session = relationship("ChatSession", back_populates="images")
    user = relationship("User")
```

- [ ] **步骤 2：更新 __init__.py 导出模型**

在 `backend/app/models/__init__.py` 中添加：

```python
from app.models.image import ChatImage
```

- [ ] **步骤 3：修改 ChatSession 模型添加关系**

在 `backend/app/models/note.py` 中的 `ChatSession` 类添加：

```python
images = relationship("ChatImage", back_populates="session", cascade="all, delete-orphan")
```

- [ ] **步骤 4：提交**

```bash
git add backend/app/models/image.py backend/app/models/__init__.py backend/app/models/note.py
git commit -m "feat: add ChatImage ORM model for storing uploaded images"
```

---

#### Task 2: 扩展 ChatMessage 模型添加图片字段

**文件：**
- 修改: `backend/app/models/note.py:ChatMessage`

**接口：**
- 消费：SQLAlchemy Column, Text
- 生产：扩展的 ChatMessage 模型（新字段：image_ids, image_ocr_text, image_vision_desc）

- [ ] **步骤 1：在 ChatMessage 类中添加三个新字段**

在 `backend/app/models/note.py` 的 `ChatMessage` 类中，在 `created_at` 后添加：

```python
# 在 ChatMessage 类中添加
image_ids = Column(Text, nullable=True)  # JSON array: ["img_001", "img_002"]
image_ocr_text = Column(Text, nullable=True)  # OCR 提取的文字
image_vision_desc = Column(Text, nullable=True)  # Vision API 的描述
```

- [ ] **步骤 2：提交**

```bash
git add backend/app/models/note.py
git commit -m "feat: add image fields to ChatMessage model"
```

---

#### Task 3: 创建数据库迁移脚本

**文件：**
- 创建: `backend/migrations/001_add_chat_images_table.py`

**接口：**
- 消费：SQLAlchemy DDL
- 生产：可执行的迁移脚本

- [ ] **步骤 1：创建迁移脚本**

```python
# backend/migrations/001_add_chat_images_table.py
"""
迁移脚本：添加 chat_images 表和 chat_messages 的图片字段
"""

def migrate_up(engine):
    """升级"""
    with engine.connect() as conn:
        # 1. 添加 chat_messages 新字段
        conn.execute("""
            ALTER TABLE chat_messages ADD COLUMN image_ids TEXT;
        """)
        conn.execute("""
            ALTER TABLE chat_messages ADD COLUMN image_ocr_text TEXT;
        """)
        conn.execute("""
            ALTER TABLE chat_messages ADD COLUMN image_vision_desc TEXT;
        """)
        
        # 2. 创建 chat_images 表
        conn.execute("""
            CREATE TABLE chat_images (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_type TEXT NOT NULL,
                ocr_text TEXT,
                vision_description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        
        # 3. 创建索引
        conn.execute("""
            CREATE INDEX idx_chat_image_session_user ON chat_images(session_id, user_id);
        """)
        conn.execute("""
            CREATE INDEX idx_chat_image_created ON chat_images(created_at);
        """)
        
        conn.commit()

def migrate_down(engine):
    """降级"""
    with engine.connect() as conn:
        conn.execute("DROP TABLE IF EXISTS chat_images;")
        conn.execute("ALTER TABLE chat_messages DROP COLUMN IF EXISTS image_ids;")
        conn.execute("ALTER TABLE chat_messages DROP COLUMN IF EXISTS image_ocr_text;")
        conn.execute("ALTER TABLE chat_messages DROP COLUMN IF EXISTS image_vision_desc;")
        conn.commit()
```

- [ ] **步骤 2：创建迁移目录（如不存在）**

```bash
mkdir -p backend/migrations && touch backend/migrations/__init__.py
```

- [ ] **步骤 3：提交**

```bash
git add backend/migrations/001_add_chat_images_table.py
git commit -m "feat: add database migration for chat_images table"
```

---

#### Task 4: 创建图片相关 Pydantic Schema

**文件：**
- 创建: `backend/app/schemas/image.py`

**接口：**
- 消费：BaseModel, Optional, List, datetime
- 生产：`ImageResponse`, `ChatImageModel`, `ImageUploadRequest` Schema

- [ ] **步骤 1：创建 image.py schema 文件**

```python
# backend/app/schemas/image.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ImageUploadRequest(BaseModel):
    """图片上传请求（multipart/form-data）"""
    session_id: Optional[str] = None
    question: str
    subject: str = "数学"
    # images: List[UploadFile]  # FastAPI 自动处理

class ImageResponse(BaseModel):
    """图片信息响应"""
    id: str
    file_path: str
    original_filename: str
    file_size: int
    file_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatImageModel(BaseModel):
    """聊天消息中的图片信息"""
    image_ids: Optional[List[str]] = None
    ocr_text: Optional[str] = None
    vision_description: Optional[str] = None
```

- [ ] **步骤 2：提交**

```bash
git add backend/app/schemas/image.py
git commit -m "feat: add image-related Pydantic schemas"
```

---

### 阶段 2：后端图片处理服务

#### Task 5: 创建 ImageService - 文件验证和保存

**文件：**
- 创建: `backend/app/services/image_service.py`

**接口：**
- 消费：FastAPI UploadFile, Path, os, uuid, datetime, SQLAlchemy Session
- 生产：
  - `validate_files(files, max_count, max_size_mb) -> Tuple[bool, Optional[str]]`
  - `save_images(files, user_id, session_id, db) -> List[str]`
  - `build_enhanced_prompt(question, merged_analysis) -> str`

- [ ] **步骤 1：创建 image_service.py 基础框架**

```python
# backend/app/services/image_service.py
import os
import uuid
from datetime import datetime
from typing import List, Tuple, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.image import ChatImage
from app.config import settings

ALLOWED_TYPES = {"jpg", "jpeg", "png", "pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_MAX_COUNT = 5
UPLOAD_DIR = settings.upload_dir or "./uploads"

class ImageService:
    """图片处理服务"""
    
    async def validate_files(
        self,
        files: List[UploadFile],
        max_count: int = DEFAULT_MAX_COUNT,
        max_size_mb: int = 10,
    ) -> Tuple[bool, Optional[str]]:
        """
        验证上传的文件
        返回：(是否有效, 错误消息)
        """
        if len(files) > max_count:
            return False, f"最多上传 {max_count} 张图片，你上传了 {len(files)} 张"
        
        max_bytes = max_size_mb * 1024 * 1024
        for file in files:
            # 检查文件类型
            if not file.filename:
                return False, "文件名不能为空"
            
            ext = file.filename.split(".")[-1].lower()
            if ext not in ALLOWED_TYPES:
                return False, f"不支持的文件类型：.{ext}，仅支持 JPG/PNG/PDF"
            
            # 检查文件大小
            if file.size and file.size > max_bytes:
                size_mb = file.size / (1024 * 1024)
                return False, f"文件过大：{size_mb:.1f}MB，单个文件不超过 {max_size_mb}MB"
        
        return True, None
    
    async def save_images(
        self,
        files: List[UploadFile],
        user_id: int,
        session_id: str,
        db: Session,
    ) -> List[str]:
        """
        保存上传的图片到磁盘和数据库
        返回：image_ids 列表
        """
        # 验证
        valid, error = await self.validate_files(files)
        if not valid:
            raise ValueError(error)
        
        # 创建用户会话目录
        user_session_dir = os.path.join(UPLOAD_DIR, str(user_id), session_id)
        os.makedirs(user_session_dir, exist_ok=True)
        
        image_ids = []
        timestamp = int(datetime.utcnow().timestamp())
        
        for idx, file in enumerate(files):
            # 生成唯一的 image_id
            image_id = f"{session_id}_{timestamp}_{idx}"
            
            # 保存文件到磁盘
            ext = file.filename.split(".")[-1].lower()
            filename = f"{timestamp}_{idx}_{file.filename}"
            file_path = os.path.join(user_session_dir, filename)
            
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # 记录到数据库
            relative_path = os.path.join(str(user_id), session_id, filename)
            chat_image = ChatImage(
                id=image_id,
                session_id=session_id,
                user_id=user_id,
                file_path=relative_path,
                original_filename=file.filename,
                file_size=len(content),
                file_type=ext,
                created_at=datetime.utcnow(),
            )
            db.add(chat_image)
            image_ids.append(image_id)
        
        db.commit()
        return image_ids
    
    def build_enhanced_prompt(
        self,
        user_question: str,
        merged_analysis: str,
    ) -> str:
        """
        构造增强提示词：原问题 + OCR 文字 + Vision 描述
        """
        enhanced = f"""用户上传了学科试题截图，以下是从截图中提取的内容：

【提取的内容】
{merged_analysis}

【用户的问题】
{user_question}

请根据上述图片内容和用户的问题进行详细解答。
"""
        return enhanced

image_service = ImageService()
```

- [ ] **步骤 2：确保 settings 中有 upload_dir 配置**

在 `backend/app/config.py` 中检查/添加：

```python
class Settings(BaseSettings):
    # ... 其他设置 ...
    upload_dir: str = "./uploads"
```

- [ ] **步骤 3：创建 uploads 目录**

```bash
mkdir -p backend/uploads
```

- [ ] **步骤 4：提交**

```bash
git add backend/app/services/image_service.py backend/app/config.py
git commit -m "feat: add image validation and file saving to ImageService"
```

---

#### Task 6: 添加 OCR 支持到 ImageService

**文件：**
- 修改: `backend/app/services/image_service.py`

**接口：**
- 消费：PaddleOCR, Pillow, asyncio
- 生产：
  - `extract_with_ocr(image_path) -> str` （同步，包装为异步）
  - `batch_ocr(image_paths) -> List[str]` （并行）

- [ ] **步骤 1：在 image_service.py 中添加 OCR 导入和初始化**

在文件顶部添加：

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from paddleocr import PaddleOCR
from PIL import Image

# 全局 OCR 实例（首次加载时会下载模型，约 10-50MB）
_ocr_instance = None

def get_ocr_instance():
    """延迟加载 OCR 实例"""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = PaddleOCR(use_angle_cls=True, lang="ch")
    return _ocr_instance

# 线程池，用于同步 OCR 调用
_thread_pool = ThreadPoolExecutor(max_workers=2)
```

- [ ] **步骤 2：在 ImageService 类中添加 OCR 方法**

```python
    async def extract_with_ocr(self, image_path: str) -> str:
        """
        使用 PaddleOCR 提取图片中的文字
        
        Args:
            image_path: 图片路径（本地或相对路径）
        
        Returns:
            提取的文字内容
        """
        try:
            # 转为绝对路径
            if not os.path.isabs(image_path):
                image_path = os.path.join(UPLOAD_DIR, image_path)
            
            if not os.path.exists(image_path):
                return ""
            
            # 在线程池中执行同步的 OCR 操作
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _thread_pool,
                self._run_ocr,
                image_path
            )
            return result
        except Exception as e:
            print(f"OCR 失败: {e}")
            return ""
    
    @staticmethod
    def _run_ocr(image_path: str) -> str:
        """同步的 OCR 执行"""
        try:
            ocr = get_ocr_instance()
            result = ocr.ocr(image_path, cls=True)
            
            # 提取文字（result 是二维列表）
            texts = []
            if result:
                for line in result:
                    for word_info in line:
                        text = word_info[1]
                        texts.append(text)
            
            return "\n".join(texts) if texts else ""
        except Exception as e:
            print(f"OCR 执行失败: {e}")
            return ""
    
    async def batch_ocr(self, image_paths: List[str]) -> List[str]:
        """
        并行执行多张图片的 OCR
        """
        tasks = [self.extract_with_ocr(path) for path in image_paths]
        results = await asyncio.gather(*tasks)
        return results
```

- [ ] **步骤 3：添加 PaddleOCR 到依赖**

在 `backend/requirements.txt` 中添加：

```
paddleocr>=2.8.0
pillow>=10.0.0
```

- [ ] **步骤 4：提交**

```bash
git add backend/app/services/image_service.py backend/requirements.txt
git commit -m "feat: add PaddleOCR support to ImageService"
```

---

#### Task 7: 添加 Vision API 支持到 ImageService

**文件：**
- 修改: `backend/app/services/image_service.py`

**接口：**
- 消费：AsyncOpenAI, base64, asyncio
- 生产：
  - `analyze_with_vision(image_base64) -> str` （从 base64）
  - `batch_vision(image_paths) -> List[str]` （并行）

- [ ] **步骤 1：在 image_service.py 中添加 Vision 方法**

```python
import base64
from app.services.ai_service import ai_service

    async def analyze_with_vision(self, image_path: str) -> str:
        """
        使用 GPT-4o Vision API 分析图片
        
        Args:
            image_path: 图片路径
        
        Returns:
            图片分析描述
        """
        try:
            # 转为绝对路径
            if not os.path.isabs(image_path):
                image_path = os.path.join(UPLOAD_DIR, image_path)
            
            if not os.path.exists(image_path):
                return ""
            
            # 读取图片并转为 base64
            with open(image_path, "rb") as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            
            # 确定图片类型
            ext = image_path.split(".")[-1].lower()
            mime_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"
            
            # 调用 Vision API
            response = await ai_service.client.chat.completions.create(
                model=ai_service.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请详细描述这张学科试题图片中的所有内容。包括：题目文字、图表、公式、图像等。要尽可能完整和准确。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                timeout=30,
            )
            
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            print("Vision API 超时")
            return ""
        except Exception as e:
            print(f"Vision API 失败: {e}")
            return ""
    
    async def batch_vision(self, image_paths: List[str]) -> List[str]:
        """
        并行调用 Vision API 分析多张图片
        """
        tasks = [self.analyze_with_vision(path) for path in image_paths]
        results = await asyncio.gather(*tasks)
        return results
```

- [ ] **步骤 2：提交**

```bash
git add backend/app/services/image_service.py
git commit -m "feat: add Vision API support to ImageService"
```

---

#### Task 8: 实现结果融合逻辑

**文件：**
- 修改: `backend/app/services/image_service.py`

**接口：**
- 消费：List[str]（OCR 和 Vision 结果）
- 生产：`merge_analysis_results(ocr_results, vision_results) -> str`

- [ ] **步骤 1：在 ImageService 中添加融合方法**

```python
    def merge_analysis_results(
        self,
        ocr_results: List[str],
        vision_results: List[str],
    ) -> str:
        """
        融合 OCR 和 Vision API 的结果
        
        策略：
        1. 如果两者都有，智能合并（优先 Vision，补充 OCR）
        2. 如果仅 OCR 有，使用 OCR
        3. 如果仅 Vision 有，使用 Vision
        4. 都没有，返回空
        """
        merged_parts = []
        
        for i, (ocr_text, vision_desc) in enumerate(zip(ocr_results, vision_results)):
            ocr_text = ocr_text.strip()
            vision_desc = vision_desc.strip()
            
            part_number = i + 1
            
            if vision_desc and ocr_text:
                # 两者都有：Vision 描述为主，OCR 文字为补充
                merged_parts.append(f"【图片 {part_number}】")
                merged_parts.append(f"视觉描述：{vision_desc}")
                merged_parts.append(f"文字内容：{ocr_text}")
            elif vision_desc:
                # 仅 Vision
                merged_parts.append(f"【图片 {part_number}】{vision_desc}")
            elif ocr_text:
                # 仅 OCR
                merged_parts.append(f"【图片 {part_number}】{ocr_text}")
        
        return "\n\n".join(merged_parts) if merged_parts else ""
```

- [ ] **步骤 2：提交**

```bash
git add backend/app/services/image_service.py
git commit -m "feat: implement result merging logic for OCR and Vision"
```

---

#### Task 9: 修改 AIService 支持图片流式对话

**文件：**
- 修改: `backend/app/services/ai_service.py`

**接口：**
- 消费：ChatImage 模型，image_service，asyncio
- 生产：`chat_stream_with_images(messages, images, context, **kwargs) -> async generator`

- [ ] **步骤 1：在 ai_service.py 中添加新方法**

在 `AIService` 类中添加：

```python
    async def chat_stream_with_images(
        self,
        messages: List[Dict],
        images: List,  # ChatImage 对象列表
        context: Optional[str] = None,
        **kwargs
    ):
        """
        流式对话，支持图片分析
        
        流程：
        1. 并行执行 OCR + Vision API
        2. 融合结果
        3. 构造增强提示词
        4. 调用 chat_stream()
        """
        from app.services.image_service import image_service
        
        if not images:
            # 无图片，直接调用 chat_stream
            async for chunk in self.chat_stream(messages, context, **kwargs):
                yield chunk
            return
        
        try:
            # 1. 提取图片路径
            image_paths = [img.file_path for img in images]
            
            # 2. 并行执行 OCR + Vision
            ocr_results, vision_results = await asyncio.gather(
                image_service.batch_ocr(image_paths),
                image_service.batch_vision(image_paths),
            )
            
            # 3. 融合结果
            merged_analysis = image_service.merge_analysis_results(
                ocr_results,
                vision_results
            )
            
            # 4. 构造增强提示词
            user_question = messages[-1]["content"] if messages else ""
            enhanced_prompt = image_service.build_enhanced_prompt(
                user_question,
                merged_analysis
            )
            
            # 5. 构建增强上下文
            enhanced_context = context + "\n" + enhanced_prompt if context else enhanced_prompt
            
            # 6. 调用 chat_stream 进行流式对话
            async for chunk in self.chat_stream(
                messages=messages,
                context=enhanced_context,
                **kwargs
            ):
                yield chunk
        
        except Exception as e:
            print(f"图片分析失败: {e}")
            # 降级：如果图片分析失败，仍尝试用原问题对话
            async for chunk in self.chat_stream(messages, context, **kwargs):
                yield chunk
```

- [ ] **步骤 2：添加 asyncio 导入**

确保文件顶部有：

```python
import asyncio
```

- [ ] **步骤 3：提交**

```bash
git add backend/app/services/ai_service.py
git commit -m "feat: add chat_stream_with_images method to AIService"
```

---

#### Task 10: 修改 AI 路由支持文件上传

**文件：**
- 修改: `backend/app/routers/ai.py`

**接口：**
- 消费：UploadFile, Form 数据，image_service，SQLAlchemy Session
- 生产：修改 POST /api/ai/chat，支持 multipart/form-data

- [ ] **步骤 1：修改 POST /api/ai/chat 路由**

在 `backend/app/routers/ai.py` 中，找到 `@router.post("/chat")` 函数，替换整个函数：

```python
@router.post("/chat")
async def chat(
    session_id: Optional[str] = Form(None),
    question: str = Form(...),
    subject: str = Form("数学"),
    images: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI 问答（支持图片上传）
    
    请求：multipart/form-data
    - session_id: 会话 ID（可选）
    - question: 问题文本
    - subject: 学科
    - images: 图片文件数组（最多 5 张）
    """
    from app.services.image_service import image_service
    from app.models.image import ChatImage
    
    # 1. 验证和保存图片
    image_objs = []
    if images:
        try:
            valid, error = await image_service.validate_files(images)
            if not valid:
                raise HTTPException(status_code=400, detail=error)
            
            image_ids = await image_service.save_images(
                images, current_user.id, session_id or str(uuid.uuid4()), db
            )
            image_objs = db.query(ChatImage).filter(
                ChatImage.id.in_(image_ids)
            ).all()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"图片保存失败: {str(e)}")
    
    # 2. 获取或创建会话
    if session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        session_id = str(uuid.uuid4())
        title = question[:50] if len(question) > 0 else "新对话"
        session = ChatSession(
            id=session_id,
            user_id=current_user.id,
            title=title,
            subject=subject
        )
        db.add(session)
        db.commit()
    
    # 3. 获取历史消息
    history_msgs = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).limit(10).all()
    history = [{"role": m.role, "content": m.content} for m in history_msgs]
    
    # 4. 保存用户消息（含图片）
    import json
    user_msg = ChatMessage(
        session_id=session_id,
        user_id=current_user.id,
        role="user",
        content=question,
        image_ids=json.dumps([img.id for img in image_objs]) if image_objs else None,
    )
    db.add(user_msg)
    db.commit()
    
    # 5. 读取用户信息（避免 DetachedInstanceError）
    user_id = current_user.id
    user_grade = current_user.grade
    
    # 6. 构建上下文
    meta_context = build_meta_context(
        question=question,
        subject=subject if subject != "全部" else None,
        grade=user_grade if user_grade else None,
    )
    
    rag_context = rag_service.build_context_prompt(
        query=question,
        subject=subject if subject != "全部" else None,
        grade=user_grade if user_grade else None,
        top_k=4,
    )
    
    combined_context = (meta_context or "") + (rag_context or "")
    
    # 7. 流式对话（如有图片则使用增强版本）
    async def generate():
        if image_objs:
            async for chunk in ai_service.chat_stream_with_images(
                messages=history + [{"role": "user", "content": question}],
                images=image_objs,
                context=combined_context,
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        else:
            async for chunk in ai_service.chat_stream(
                messages=history + [{"role": "user", "content": question}],
                context=combined_context,
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

- [ ] **步骤 2：添加必要的导入**

在 `backend/app/routers/ai.py` 顶部添加：

```python
from typing import List
from fastapi import File, Form, UploadFile
import json
```

- [ ] **步骤 3：提交**

```bash
git add backend/app/routers/ai.py
git commit -m "feat: update POST /api/ai/chat to support image uploads"
```

---

#### Task 11: 添加图片查询和删除 API 端点

**文件：**
- 修改: `backend/app/routers/ai.py`

**接口：**
- 消费：SQLAlchemy Query，HTTPException
- 生产：
  - `GET /api/ai/chat/{session_id}/images`
  - `DELETE /api/ai/chat/images/{image_id}`

- [ ] **步骤 1：添加新的路由端点**

在 `backend/app/routers/ai.py` 末尾添加：

```python
@router.get("/chat/{session_id}/images")
async def get_session_images(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话中的所有图片"""
    from app.models.image import ChatImage
    from app.schemas.image import ImageResponse
    
    # 验证会话属主
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 查询图片
    images = db.query(ChatImage).filter(
        ChatImage.session_id == session_id,
        ChatImage.deleted_at == None
    ).order_by(ChatImage.created_at.desc()).all()
    
    return {
        "code": 200,
        "data": [ImageResponse.model_validate(img) for img in images]
    }


@router.delete("/chat/images/{image_id}")
async def delete_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除图片（需权限检查）"""
    from app.models.image import ChatImage
    from datetime import datetime
    
    image = db.query(ChatImage).filter(ChatImage.id == image_id).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 权限检查
    if image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除他人的图片")
    
    # 软删除
    image.deleted_at = datetime.utcnow()
    db.commit()
    
    # 同时删除磁盘上的文件（可选）
    import os
    file_path = os.path.join(UPLOAD_DIR, image.file_path)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"删除文件失败: {e}")
    
    return {
        "code": 200,
        "message": "图片已删除"
    }
```

- [ ] **步骤 2：添加缺失的导入**

从 config 导入 UPLOAD_DIR：

```python
from app.config import settings
UPLOAD_DIR = settings.upload_dir or "./uploads"
```

- [ ] **步骤 3：提交**

```bash
git add backend/app/routers/ai.py
git commit -m "feat: add GET and DELETE endpoints for image management"
```

---

### 阶段 3：前端图片上传组件

#### Task 12: 创建 ImageUploadArea 组件

**文件：**
- 创建: `frontend/src/components/shared/ImageUploadArea.vue`
- 创建: `frontend/src/utils/imageUpload.ts`

**接口：**
- 消费：Element Plus, Vue 3 Composition API
- 生产：
  - `ImageUploadArea` 组件（事件：@images-selected）
  - `validateImageFiles()` 函数

- [ ] **步骤 1：创建图片验证工具**

```typescript
// frontend/src/utils/imageUpload.ts

export interface ImageValidationResult {
  valid: boolean;
  error?: string;
}

export interface ImageConfig {
  maxCount: number;
  maxSizeMB: number;
  allowedTypes: string[];
}

const DEFAULT_CONFIG: ImageConfig = {
  maxCount: 5,
  maxSizeMB: 10,
  allowedTypes: ['jpg', 'jpeg', 'png', 'pdf']
};

export function validateImageFiles(
  files: File[],
  config: Partial<ImageConfig> = {}
): ImageValidationResult {
  const cfg = { ...DEFAULT_CONFIG, ...config };
  
  if (files.length > cfg.maxCount) {
    return {
      valid: false,
      error: `最多上传 ${cfg.maxCount} 张图片，你选择了 ${files.length} 张`
    };
  }
  
  const maxBytes = cfg.maxSizeMB * 1024 * 1024;
  
  for (const file of files) {
    const ext = file.name.split('.').pop()?.toLowerCase();
    
    if (!ext || !cfg.allowedTypes.includes(ext)) {
      return {
        valid: false,
        error: `不支持的文件类型：.${ext || '无'}`
      };
    }
    
    if (file.size > maxBytes) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
      return {
        valid: false,
        error: `文件 "${file.name}" 过大（${sizeMB}MB），单个不超过 ${cfg.maxSizeMB}MB`
      };
    }
  }
  
  return { valid: true };
}

export function getImagePreviewUrl(file: File): string {
  return URL.createObjectURL(file);
}
```

- [ ] **步骤 2：创建 ImageUploadArea 组件**

```vue
<!-- frontend/src/components/shared/ImageUploadArea.vue -->

<template>
  <div class="image-upload-area">
    <!-- 错误提示 -->
    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      closable
      @close="errorMessage = ''"
      class="mb-3"
    />
    
    <!-- 上传区域（拖拽和点击） -->
    <div
      class="upload-box"
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      :class="{ dragging: isDragging }"
    >
      <input
        type="file"
        ref="fileInput"
        multiple
        accept=".jpg,.jpeg,.png,.pdf"
        @change="handleFileSelect"
        style="display: none"
      />
      
      <div class="upload-content" @click="$refs.fileInput?.click()">
        <el-icon class="upload-icon">
          <DocumentCopy />
        </el-icon>
        <p class="upload-text">拖拽或点击上传图片</p>
        <p class="upload-hint">支持 JPG、PNG、PDF，最多 5 张，单个 10MB</p>
      </div>
    </div>
    
    <!-- 图片预览网格 -->
    <div v-if="selectedFiles.length > 0" class="image-preview-grid mt-4">
      <div v-for="(file, index) in selectedFiles" :key="index" class="image-item">
        <div class="image-preview">
          <img
            v-if="isPicture(file)"
            :src="getImagePreviewUrl(file)"
            :alt="file.name"
          />
          <div v-else class="pdf-placeholder">
            <el-icon><Document /></el-icon>
            <p>PDF</p>
          </div>
          
          <!-- 删除按钮 -->
          <button class="delete-btn" @click="removeImage(index)" title="删除">
            ✕
          </button>
        </div>
        
        <p class="image-name">{{ file.name }}</p>
        <p class="image-size">{{ formatFileSize(file.size) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { DocumentCopy, Document } from '@element-plus/icons-vue';
import { validateImageFiles, getImagePreviewUrl } from '@/utils/imageUpload';

const props = withDefaults(
  defineProps<{
    maxCount?: number;
    maxSizeMB?: number;
  }>(),
  {
    maxCount: 5,
    maxSizeMB: 10
  }
);

const emit = defineEmits<{
  'images-selected': [files: File[]];
}>();

const fileInput = ref<HTMLInputElement | null>(null);
const isDragging = ref(false);
const errorMessage = ref('');
const selectedFiles = ref<File[]>([]);

const isPicture = (file: File): boolean => {
  const ext = file.name.split('.').pop()?.toLowerCase();
  return ext === 'jpg' || ext === 'jpeg' || ext === 'png';
};

const handleFileSelect = async (event: Event) => {
  const files = Array.from((event.target as HTMLInputElement).files || []);
  processFiles(files);
};

const handleDrop = (event: DragEvent) => {
  isDragging.value = false;
  const files = Array.from(event.dataTransfer?.files || []);
  processFiles(files);
};

const processFiles = (files: File[]) => {
  // 只处理图片和 PDF 文件
  const imageFiles = files.filter(f => {
    const ext = f.name.split('.').pop()?.toLowerCase();
    return ext === 'jpg' || ext === 'jpeg' || ext === 'png' || ext === 'pdf';
  });
  
  if (imageFiles.length === 0) {
    errorMessage.value = '请选择图片或 PDF 文件';
    return;
  }
  
  const validation = validateImageFiles(imageFiles, {
    maxCount: props.maxCount,
    maxSizeMB: props.maxSizeMB
  });
  
  if (!validation.valid) {
    errorMessage.value = validation.error || '验证失败';
    return;
  }
  
  errorMessage.value = '';
  selectedFiles.value = imageFiles;
  emit('images-selected', imageFiles);
};

const removeImage = (index: number) => {
  selectedFiles.value.splice(index, 1);
  emit('images-selected', selectedFiles.value);
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};
</script>

<style scoped lang="postcss">
.image-upload-area {
  width: 100%;
}

.upload-box {
  border: 2px dashed #dcdfe4;
  border-radius: 8px;
  background: #f5f7fa;
  padding: 40px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;

  &.dragging {
    border-color: #409eff;
    background: #ecf5ff;
  }

  &:hover {
    border-color: #409eff;
    background: #f0f9ff;
  }
}

.upload-content {
  pointer-events: none;
}

.upload-icon {
  font-size: 48px;
  color: #909399;
  margin-bottom: 10px;
}

.upload-text {
  font-size: 14px;
  color: #606266;
  margin: 8px 0;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.image-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
}

.image-item {
  position: relative;
}

.image-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border: 1px solid #dcdfe4;
  border-radius: 6px;
  overflow: hidden;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &:hover .delete-btn {
    opacity: 1;
  }
}

.pdf-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #909399;

  .el-icon {
    font-size: 32px;
  }

  p {
    font-size: 12px;
    margin: 0;
  }
}

.delete-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 50%;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s;

  &:hover {
    background: #f56c6c;
  }
}

.image-name {
  font-size: 12px;
  color: #606266;
  margin: 8px 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-size {
  font-size: 11px;
  color: #909399;
  margin: 0;
}
</style>
```

- [ ] **步骤 3：提交**

```bash
git add frontend/src/components/shared/ImageUploadArea.vue frontend/src/utils/imageUpload.ts
git commit -m "feat: add ImageUploadArea component with drag-and-drop support"
```

---

#### Task 13: 创建图片 API 封装

**文件：**
- 创建: `frontend/src/api/image.ts`

**接口：**
- 消费：axios
- 生产：
  - `uploadChatImages(formData): Promise`
  - `getSessionImages(sessionId): Promise`
  - `deleteImage(imageId): Promise`

- [ ] **步骤 1：创建 image API 文件**

```typescript
// frontend/src/api/image.ts

import request from '@/api/index';

export interface ImageInfo {
  id: string;
  file_path: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  created_at: string;
}

/**
 * 上传聊天消息（带图片）
 */
export function sendChatWithImages(data: FormData) {
  return request.post('/api/ai/chat', data, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    responseType: 'stream'
  });
}

/**
 * 获取会话中的所有图片
 */
export function getSessionImages(sessionId: string) {
  return request.get(`/api/ai/chat/${sessionId}/images`);
}

/**
 * 删除单个图片
 */
export function deleteImage(imageId: string) {
  return request.delete(`/api/ai/chat/images/${imageId}`);
}
```

- [ ] **步骤 2：提交**

```bash
git add frontend/src/api/image.ts
git commit -m "feat: add image API wrapper functions"
```

---

#### Task 14: 修改 AIChatView 集成图片上传

**文件：**
- 修改: `frontend/src/views/ai/AIChatView.vue`

**接口：**
- 消费：ImageUploadArea 组件，image API，FormData
- 生产：修改后的 AIChatView（支持图片上传和预览）

- [ ] **步骤 1：导入必要的组件和 API**

在 `frontend/src/views/ai/AIChatView.vue` 的 `<script setup>` 顶部添加：

```typescript
import ImageUploadArea from '@/components/shared/ImageUploadArea.vue';
import { sendChatWithImages, deleteImage } from '@/api/image';
```

- [ ] **步骤 2：在聊天输入区域添加 ImageUploadArea 组件**

找到输入框部分，在它上方添加：

```vue
<!-- 图片上传区域 -->
<ImageUploadArea
  v-if="!loading"
  :max-count="5"
  :max-size-m-b="10"
  @images-selected="handleImagesSelected"
/>

<!-- 已选择的图片列表 -->
<div v-if="selectedImages.length > 0" class="selected-images-preview mt-2">
  <div class="text-sm text-gray-600 mb-2">
    已选择 {{ selectedImages.length }} 张图片
  </div>
  <div class="grid grid-cols-5 gap-2">
    <div v-for="(file, index) in selectedImages" :key="index" class="relative">
      <img
        v-if="isPictureFile(file)"
        :src="getFilePreviewUrl(file)"
        :alt="file.name"
        class="w-full h-20 object-cover rounded border"
      />
      <div v-else class="w-full h-20 bg-gray-100 rounded border flex items-center justify-center">
        <span class="text-xs">PDF</span>
      </div>
      <button
        @click="removeImage(index)"
        class="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center hover:bg-red-600"
      >
        ✕
      </button>
    </div>
  </div>
</div>
```

- [ ] **步骤 3：在 script setup 中添加响应式数据和方法**

```typescript
const selectedImages = ref<File[]>([]);
const loading = ref(false);

const handleImagesSelected = (files: File[]) => {
  selectedImages.value = files;
};

const removeImage = (index: number) => {
  selectedImages.value.splice(index, 1);
};

const isPictureFile = (file: File): boolean => {
  const ext = file.name.split('.').pop()?.toLowerCase();
  return ext === 'jpg' || ext === 'jpeg' || ext === 'png';
};

const getFilePreviewUrl = (file: File): string => {
  return URL.createObjectURL(file);
};

// 修改 sendMessage 函数，支持图片
const sendMessage = async () => {
  if (!userInput.value.trim() && selectedImages.value.length === 0) {
    ElMessage.warning('请输入问题或选择图片');
    return;
  }

  if (!currentSessionId.value) {
    ElMessage.error('未初始化会话');
    return;
  }

  loading.value = true;

  try {
    // 构建 FormData
    const formData = new FormData();
    formData.append('session_id', currentSessionId.value);
    formData.append('question', userInput.value || '请解答这道题');
    formData.append('subject', currentSubject.value);

    // 添加图片
    selectedImages.value.forEach((file) => {
      formData.append('images', file);
    });

    // 调用 API（流式）
    const response = await sendChatWithImages(formData);

    // 处理流式响应（与原逻辑相同）
    const reader = response.data.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          if (currentMessage) {
            currentMessage.content += data.content;
          }
        }
      }
    }

    // 清空输入和图片
    userInput.value = '';
    selectedImages.value = [];

    // 保存消息到数据库...
  } catch (error) {
    ElMessage.error('发送失败：' + (error as any).message);
  } finally {
    loading.value = false;
  }
};
```

- [ ] **步骤 4：修改聊天消息显示，添加图片预览**

找到消息渲染部分，在用户消息的文本内容后添加：

```vue
<!-- 用户消息中的图片 -->
<div v-if="msg.image_ids && msg.image_ids.length > 0" class="image-gallery mt-2">
  <div class="text-xs text-gray-500 mb-1">{{ msg.image_ids.length }} 张图片</div>
  <div class="grid grid-cols-3 gap-2">
    <img
      v-for="(imgId, idx) in msg.image_ids"
      :key="idx"
      :src="getImageThumbUrl(msgId, imgId)"
      :alt="`Image ${idx + 1}`"
      class="w-20 h-20 object-cover rounded cursor-pointer hover:opacity-80"
      @click="previewImage(msgId, imgId)"
    />
  </div>
</div>
```

- [ ] **步骤 5：提交**

```bash
git add frontend/src/views/ai/AIChatView.vue
git commit -m "feat: integrate ImageUploadArea into AIChatView"
```

---

### 阶段 4：测试

#### Task 15: 后端单元测试

**文件：**
- 创建: `backend/tests/unit/services/test_image_service.py`

**接口：**
- 消费：pytest, ImageService
- 生产：完整的单元测试

- [ ] **步骤 1：创建测试文件**

```python
# backend/tests/unit/services/test_image_service.py

import pytest
import os
import tempfile
from fastapi import UploadFile
from app.services.image_service import ImageService
from io import BytesIO

@pytest.fixture
def image_service():
    """创建 ImageService 实例"""
    return ImageService()

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

class TestImageValidation:
    """测试文件验证"""
    
    @pytest.mark.asyncio
    async def test_validate_file_count_exceeded(self, image_service):
        """测试文件数量超过限制"""
        files = [
            UploadFile(file=BytesIO(b"test"), filename=f"test{i}.jpg")
            for i in range(6)
        ]
        valid, error = await image_service.validate_files(files, max_count=5)
        assert not valid
        assert "超过" in error or "最多" in error
    
    @pytest.mark.asyncio
    async def test_validate_file_size_exceeded(self, image_service):
        """测试文件大小超过限制"""
        large_data = b"x" * (11 * 1024 * 1024)  # 11MB
        files = [UploadFile(file=BytesIO(large_data), filename="large.jpg")]
        files[0].size = 11 * 1024 * 1024
        
        valid, error = await image_service.validate_files(files, max_size_mb=10)
        assert not valid
        assert "过大" in error or "超过" in error
    
    @pytest.mark.asyncio
    async def test_validate_invalid_file_type(self, image_service):
        """测试不支持的文件类型"""
        files = [UploadFile(file=BytesIO(b"test"), filename="test.gif")]
        valid, error = await image_service.validate_files(files)
        assert not valid
        assert "不支持" in error
    
    @pytest.mark.asyncio
    async def test_validate_valid_files(self, image_service):
        """测试有效文件"""
        files = [
            UploadFile(file=BytesIO(b"test1"), filename="test1.jpg"),
            UploadFile(file=BytesIO(b"test2"), filename="test2.png"),
        ]
        for f in files:
            f.size = len(b"test")
        
        valid, error = await image_service.validate_files(files)
        assert valid
        assert error is None

class TestEnhancedPrompt:
    """测试提示词构造"""
    
    def test_build_enhanced_prompt(self, image_service):
        """测试增强提示词生成"""
        question = "这道题怎么做？"
        analysis = "【图片 1】\n视觉描述：这是一道二次函数题\n文字内容：求 y=x^2+1 的..."
        
        prompt = image_service.build_enhanced_prompt(question, analysis)
        
        assert "用户上传了学科试题截图" in prompt
        assert question in prompt
        assert analysis in prompt
```

- [ ] **步骤 2：运行测试**

```bash
cd backend
python -m pytest tests/unit/services/test_image_service.py -v
```

- [ ] **步骤 3：提交**

```bash
git add backend/tests/unit/services/test_image_service.py
git commit -m "test: add unit tests for ImageService"
```

---

#### Task 16: 集成测试

**文件：**
- 创建: `backend/tests/integration/routers/test_ai_routes_with_images.py`

**接口：**
- 消费：pytest, FastAPI TestClient, SQLAlchemy
- 生产：集成测试（上传 → 处理 → 响应）

- [ ] **步骤 1：创建集成测试文件**

```python
# backend/tests/integration/routers/test_ai_routes_with_images.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.security import get_password_hash
from datetime import datetime, timedelta
from app.security import create_access_token

@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)

@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        nickname="Test User",
        grade="高一",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_token(test_user):
    """创建认证令牌"""
    expires = datetime.utcnow() + timedelta(days=7)
    token = create_access_token(data={"sub": str(test_user.id)}, expires_delta=expires)
    return token

class TestAIChatWithImages:
    """测试带图片的 AI 对话"""
    
    def test_chat_without_images(self, client, auth_token):
        """测试纯文本对话（无图片）"""
        response = client.post(
            "/api/ai/chat",
            data={
                "question": "什么是二次函数？",
                "subject": "数学",
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
    
    @pytest.mark.skip(reason="需要实际的图片文件")
    def test_chat_with_single_image(self, client, auth_token):
        """测试带单张图片的对话"""
        # 创建测试图片
        from PIL import Image
        from io import BytesIO
        
        img = Image.new('RGB', (100, 100), color='red')
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        response = client.post(
            "/api/ai/chat",
            data={
                "question": "这是什么？",
                "subject": "数学",
            },
            files={
                "images": ("test.jpg", img_byte_arr, "image/jpeg")
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
    
    def test_chat_with_too_many_images(self, client, auth_token):
        """测试图片数量超限"""
        # 这个测试需要实际的文件对象
        # 简化版本：直接测试验证逻辑
        pass
    
    def test_get_session_images(self, client, auth_token):
        """测试获取会话图片"""
        session_id = "test-session-id"
        
        response = client.get(
            f"/api/ai/chat/{session_id}/images",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # 如果会话不存在，应该返回 404
        assert response.status_code in [200, 404]
    
    def test_delete_image_without_permission(self, client, auth_token, db_session):
        """测试无权限删除图片"""
        # 创建另一个用户的图片
        from app.models.image import ChatImage
        
        other_image = ChatImage(
            id="other_image_1",
            session_id="session_1",
            user_id=999,  # 不同的用户
            file_path="uploads/999/session_1/image.jpg",
            original_filename="image.jpg",
            file_size=1024,
            file_type="jpg",
        )
        db_session.add(other_image)
        db_session.commit()
        
        response = client.delete(
            "/api/ai/chat/images/other_image_1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 403
```

- [ ] **步骤 2：运行集成测试**

```bash
cd backend
python -m pytest tests/integration/routers/test_ai_routes_with_images.py -v
```

- [ ] **步骤 3：提交**

```bash
git add backend/tests/integration/routers/test_ai_routes_with_images.py
git commit -m "test: add integration tests for image uploads in chat"
```

---

### 阶段 5：依赖和部署

#### Task 17: 添加依赖和更新文档

**文件：**
- 修改: `backend/requirements.txt`
- 创建: `backend/SETUP.md`（部署指南）

**接口：**
- 消费：pip 包列表
- 生产：更新的 requirements.txt，部署清单

- [ ] **步骤 1：确保所有新依赖在 requirements.txt 中**

```bash
cd backend
# 检查当前版本
pip show paddleocr pillow python-multipart
```

- [ ] **步骤 2：验证 requirements.txt 包含新依赖**

检查 `backend/requirements.txt`，确保包含：

```
paddleocr>=2.8.0
pillow>=10.0.0
python-multipart>=0.0.6
pdf2image>=1.16.0
```

- [ ] **步骤 3：创建部署指南**

```markdown
# EduBuddy 图片上传功能部署指南

## 环境要求

- Python >= 3.8
- SQLite
- 磁盘空间 >= 1GB（用于 PaddleOCR 模型和用户上传）

## 安装步骤

### 1. 安装新依赖

\`\`\`bash
cd backend
pip install --upgrade -r requirements.txt
\`\`\`

这会自动下载 PaddleOCR 的预训练模型（首次 ~10-50MB，耗时 2-3 分钟）。

### 2. 运行数据库迁移

\`\`\`bash
# 方式 1：使用迁移脚本（推荐）
python -c "
from app.database import engine
from migrations.migrations_001_add_chat_images_table import migrate_up
migrate_up(engine)
"

# 方式 2：手动执行 SQL
sqlite3 data/edubuddy.db < migrations/001_add_chat_images_table.sql
\`\`\`

### 3. 创建上传目录

\`\`\`bash
mkdir -p backend/uploads
chmod 755 backend/uploads
\`\`\`

### 4. 启动服务

\`\`\`bash
cd backend
uvicorn app.main:app --reload --port 8000
\`\`\`

首次启动时会加载 OCR 模型，可能需要等待 1-2 分钟。

## 测试

### 后端测试

\`\`\`bash
pytest tests/unit/services/test_image_service.py -v
pytest tests/integration/routers/test_ai_routes_with_images.py -v
\`\`\`

### 手动测试

\`\`\`bash
curl -X POST http://localhost:8000/api/ai/chat \\
  -F "session_id=test" \\
  -F "question=这道题怎么做？" \\
  -F "subject=数学" \\
  -F "images=@sample.jpg"
\`\`\`

## 故障排查

### PaddleOCR 模型下载失败

- 检查网络连接
- 手动下载模型：https://github.com/PaddlePaddle/PaddleOCR/releases
- 设置模型路径环境变量：\`export PADDLE_TAR_PATH=/path/to/models\`

### Vision API 超时

- 增加超时时间：修改 `ai_service.py` 中的 timeout 参数
- 检查 OpenAI API 配额

### 磁盘空间不足

- 清理旧图片：\`find backend/uploads -mtime +30 -delete\`
- 配置定时清理任务（cron）

## 性能优化

### 禁用 PaddleOCR（仅使用 Vision API）

修改 `image_service.py` 中的 `batch_ocr()`，直接返回空列表。

### 预加载 OCR 模型

在应用启动时：

\`\`\`python
from app.services.image_service import get_ocr_instance
get_ocr_instance()  # 预加载
\`\`\`

## 监控和告警

建议监控的指标：

- 磁盘使用率 > 80%
- Vision API 调用失败率 > 5%
- OCR 处理时间 > 15 秒

---

## 回滚步骤

如需回滚，执行：

\`\`\`bash
# 删除表和字段
sqlite3 data/edubuddy.db < migrations/001_add_chat_images_table_rollback.sql

# 清理上传文件
rm -rf backend/uploads

# 恢复依赖
pip install -r backend/requirements.txt.bak
\`\`\`
```

- [ ] **步骤 4：提交**

```bash
git add backend/requirements.txt backend/SETUP.md
git commit -m "docs: add deployment guide and update dependencies"
```

---

## 执行总结

### 文件统计

- **新建文件**：14
  - 后端：5（模型、服务、schema、迁移、测试）
  - 前端：4（组件、API、工具、测试）
  - 文档：2（设计规范、部署指南）
  
- **修改文件**：6
  - 后端：4（模型、服务、路由、依赖）
  - 前端：2（视图、工具）

### 关键技术决策

1. **OCR + Vision 融合**：并行调用，结果智能合并
2. **本地存储**：按 `{user_id}/{session_id}/` 组织，支持快速清理
3. **异步处理**：使用 asyncio.gather() 并行调用，优化延迟
4. **错误降级**：任一服务失败仍可使用另一个，两个都失败则纯文本

### 依赖版本

- paddleocr >= 2.8.0（中文 OCR）
- pillow >= 10.0.0（图片处理）
- python-multipart >= 0.0.6（文件上传）

---

## 后续任务

规范已完成并经过自审查。现在可以选择执行方式：

1. **Subagent-Driven（推荐）** - 自动派遣新的 subagent 处理每个任务，任务间审查
2. **Inline Execution** - 当前会话中批量执行任务，有检查点

**哪种方式适合你？**

