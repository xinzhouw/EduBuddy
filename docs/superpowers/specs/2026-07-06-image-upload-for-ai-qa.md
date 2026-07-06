# AI 问答图片上传功能设计规范

**文档版本**：1.0  
**创建日期**：2026-07-06  
**状态**：待实现  
**相关功能**：AI 问答（/api/ai/chat）

---

## 1. 功能概述

### 需求背景
EduBuddy 的 AI 问答功能面向学科学习，涉及大量复杂公式、图表、图片等内容。用户无法通过纯文本输入复杂的数学题、物理实验装置图、化学结构式等，因此需要支持**图片上传**功能，让 AI 能够识别并解答试题。

### 核心功能
1. **用户体验**：图片预览 + 编辑问题 + 提交（两步流）
2. **多图支持**：单条消息支持最多 5 张图片
3. **智能分析**：融合 OCR 和 Vision API 的双重识别
4. **文件管理**：本地磁盘存储，聊天记录保留时图片也保留

---

## 2. 用户流程

### 前端交互流程

```
┌─────────────────────────────────────────────┐
│         用户进入 AI 问答页面                  │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│      图片上传区（拖拽或点击上传）             │
│   ├─ 选择图片文件（JPG/PNG/PDF）             │
│   ├─ 实时验证（数量≤5, 单个≤10MB）          │
│   └─ 显示错误提示（格式/大小/数量）          │
└────────────────┬────────────────────────────┘
                 │
                 ▼ (验证通过)
┌─────────────────────────────────────────────┐
│      图片预览网格（最多 5 张缩略图）         │
│   ├─ 网格展示，支持删除单张图片              │
│   ├─ 显示原始文件名和大小                    │
│   └─ 拖拽排序（可选）                       │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    输入问题文本（与图片绑定）                │
│   ├─ 占位符："请输入你的问题..."             │
│   ├─ 支持换行和格式                         │
│   └─ 文本不为空时，发送按钮启用              │
└────────────────┬────────────────────────────┘
                 │
                 ▼ (点击发送)
┌─────────────────────────────────────────────┐
│   上传：multipart/form-data                  │
│   ├─ session_id: UUID                       │
│   ├─ question: 文本                         │
│   ├─ subject: 学科                          │
│   └─ images[]: 文件数组（≤5个）             │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│       后端处理（见第 3 节）                   │
└────────────────┬────────────────────────────┘
                 │
                 ▼ (流式响应)
┌─────────────────────────────────────────────┐
│    聊天气泡显示                              │
│   ├─ 用户消息：文本 + 图片缩略图（网格）     │
│   ├─ AI 回复：流式展示，支持公式/表格/图表  │
│   └─ 支持图片放大查看                       │
└─────────────────────────────────────────────┘
```

### 后端处理流程

```
请求到达 POST /api/ai/chat
    │
    ▼
┌─────────────────────────────────┐
│  1. 文件验证                     │
│  ├─ 检查数量（≤5）              │
│  ├─ 检查单个大小（≤10MB）       │
│  ├─ 检查文件类型（JPG/PNG/PDF） │
│  └─ 返回错误或继续              │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  2. 文件保存                     │
│  ├─ 路径: uploads/{user_id}/    │
│  │         {session_id}/        │
│  │         {timestamp}_{name}   │
│  ├─ 数据库: ChatImage 表记录    │
│  └─ 返回 image_ids[]            │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  3. 并行分析                     │
│  ├─ OCR: PaddleOCR 提取文字     │
│  ├─ Vision: GPT-4o 分析图片    │
│  └─ 等待两个结果都完成          │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  4. 结果融合                     │
│  ├─ 智能去重（相同内容合并）    │
│  ├─ 补充优化（文字 + 图形混合）│
│  └─ 返回 merged_analysis        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  5. 构造增强提示词               │
│  ├─ 原问题 +                    │
│  ├─ OCR 文字 +                  │
│  ├─ Vision 描述                 │
│  └─ RAG 教材上下文（如有）      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  6. AI 流式对话                  │
│  ├─ 调用 chat_stream()          │
│  ├─ 返回 SSE 流式响应           │
│  └─ 前端实时显示                │
└─────────────────────────────────┘
```

---

## 3. 数据模型

### 3.1 数据库扩展

#### ChatMessage 表（扩展）

```sql
ALTER TABLE chat_messages ADD COLUMN image_ids TEXT;  
-- 格式：JSON 数组 ["img_001", "img_002"]，为空时为 NULL

ALTER TABLE chat_messages ADD COLUMN image_ocr_text TEXT;  
-- OCR 提取的文字，多张图片的结果合并

ALTER TABLE chat_messages ADD COLUMN image_vision_desc TEXT;  
-- Vision API 返回的描述，多张图片的结果合并

-- 索引（已存在）
-- CREATE INDEX idx_chat_message_session ON chat_messages(session_id, created_at);
```

#### 新建 ChatImage 表

```sql
CREATE TABLE chat_images (
  id TEXT PRIMARY KEY,                          -- 格式：{session_id}_{timestamp}_{index}
  session_id TEXT NOT NULL,                     -- FK: chat_sessions.id
  user_id INTEGER NOT NULL,                     -- FK: users.id
  file_path TEXT NOT NULL,                      -- 相对路径：uploads/{user_id}/{session_id}/filename
  original_filename TEXT NOT NULL,              -- 原始文件名，用于展示
  file_size INTEGER NOT NULL,                   -- 字节数，用于验证
  file_type TEXT NOT NULL,                      -- jpg/png/pdf
  ocr_text TEXT,                                -- PaddleOCR 提取的文字
  vision_description TEXT,                      -- Vision API 的描述
  created_at TIMESTAMP NOT NULL,                -- 上传时间
  deleted_at TIMESTAMP,                         -- 软删除（可选）
  
  FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_session_user (session_id, user_id),
  INDEX idx_created_at (created_at)
);
```

### 3.2 Pydantic Schema（新增）

```python
# backend/app/schemas/image.py

class ImageUploadRequest(BaseModel):
    """图片上传请求"""
    session_id: Optional[str] = None
    question: str                    # 问题文本
    subject: str = "数学"
    # images: List[UploadFile]       # FastAPI 自动处理 multipart

class ImageResponse(BaseModel):
    """图片信息响应"""
    id: str
    file_path: str
    original_filename: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChatImageModel(BaseModel):
    """聊天消息中的图片信息"""
    image_ids: Optional[List[str]] = None
    ocr_text: Optional[str] = None
    vision_description: Optional[str] = None
```

---

## 4. API 端点

### 4.1 POST /api/ai/chat（修改）

**请求格式**（multipart/form-data）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `session_id` | string | 否 | 现有会话 ID，不填则创建新会话 |
| `question` | string | 是 | 问题文本 |
| `subject` | string | 否 | 学科，默认"数学" |
| `images` | File[] | 否 | 最多 5 张图片，每张 ≤10MB |

**响应格式**（SSE 流式）

```
data: {"content": "根据你上传的图片，这是一道二次函数题..."}
data: {"content": "$y = ax^2 + bx + c$"}
data: {"content": "..."}
```

**错误处理**

| HTTP 状态 | 错误码 | 说明 |
|----------|-------|------|
| 400 | `INVALID_FILE_COUNT` | 图片超过 5 张 |
| 400 | `FILE_TOO_LARGE` | 单个文件超过 10MB |
| 400 | `INVALID_FILE_TYPE` | 文件类型不支持 |
| 400 | `EMPTY_QUESTION` | 问题文本为空 |
| 401 | `UNAUTHORIZED` | 未认证 |
| 404 | `SESSION_NOT_FOUND` | 会话不存在 |
| 500 | `AI_SERVICE_ERROR` | AI 服务错误（降级处理） |

### 4.2 GET /api/ai/chat/{session_id}/images（新增）

**说明**：获取会话中的所有图片

**响应格式**

```json
{
  "code": 200,
  "data": [
    {
      "id": "uuid_001",
      "file_path": "uploads/user_123/session_abc/1720275000_题目.jpg",
      "original_filename": "题目.jpg",
      "file_size": 2048576,
      "created_at": "2026-07-06T10:30:00Z"
    }
  ]
}
```

### 4.3 DELETE /api/ai/chat/images/{image_id}（新增）

**说明**：删除单个图片，需权限检查（只能删除自己的）

**响应格式**

```json
{
  "code": 200,
  "message": "图片已删除"
}
```

---

## 5. 后端实现细节

### 5.1 新建 ImageService（backend/app/services/image_service.py）

#### 职责
- 文件验证（类型、大小、数量）
- 文件保存和数据库记录
- OCR 文字提取
- Vision API 图片分析
- 结果融合和提示词构造

#### 核心方法

```python
class ImageService:
    # 文件验证
    async def validate_files(
        self,
        files: List[UploadFile],
        max_count: int = 5,
        max_size_mb: int = 10
    ) -> Tuple[bool, Optional[str]]
    
    # 保存文件
    async def save_images(
        self,
        files: List[UploadFile],
        user_id: int,
        session_id: str,
        db: Session
    ) -> List[str]  # 返回 image_ids
    
    # OCR 提取（支持 JPG/PNG）
    async def extract_with_ocr(self, image_path: str) -> str
    
    # Vision API 分析
    async def analyze_with_vision(self, image_base64: str) -> str
    
    # 批量 OCR（并行）
    async def batch_ocr(self, image_paths: List[str]) -> List[str]
    
    # 批量 Vision（并行）
    async def batch_vision(self, image_base64s: List[str]) -> List[str]
    
    # 融合结果
    def merge_analysis_results(
        self,
        ocr_results: List[str],
        vision_results: List[str]
    ) -> str  # 合并后的描述
    
    # 构造增强提示词
    def build_enhanced_prompt(
        self,
        user_question: str,
        merged_analysis: str
    ) -> str  # 增强后的提示词
```

### 5.2 修改 AIService（backend/app/services/ai_service.py）

#### 新增方法

```python
async def chat_stream_with_images(
    self,
    messages: List[Dict],
    images: List[ChatImage],
    context: Optional[str] = None,
    **kwargs
):
    """
    流式对话（带图片支持）
    
    流程：
    1. 并行执行 OCR + Vision API
    2. 融合结果
    3. 构造增强提示词
    4. 调用 chat_stream()
    """
```

### 5.3 修改 AI 路由（backend/app/routers/ai.py）

#### 关键改动

```python
@router.post("/chat")
async def chat(
    data: ImageUploadRequest = None,
    files: List[UploadFile] = File(default=[]),  # 添加文件参数
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 验证文件
    # 2. 保存文件和数据库记录
    # 3. 创建或获取会话
    # 4. 保存用户消息（含 image_ids）
    # 5. 调用 ai_service.chat_stream_with_images()
    # 6. 返回 SSE 流式响应
```

---

## 6. 前端实现细节

### 6.1 新建 ImageUploadArea.vue 组件

#### 功能
- 拖拽上传 + 点击上传
- 实时预览（网格展示）
- 单张删除
- 文件验证提示

#### Props

```typescript
interface Props {
  maxCount: number = 5;
  maxSizeMB: number = 10;
  onImagesSelected: (files: File[]) => void;
  selectedFiles: File[];
}
```

### 6.2 修改 AIChatView.vue

#### 关键改动
1. 集成 ImageUploadArea 组件
2. 聊天气泡显示图片缩略图
3. 点击图片放大查看
4. 问题输入 + 图片绑定提交

#### 流程

```typescript
// 选择图片
onImagesSelected(files: File[]) {
  selectedImages.value = files;
}

// 提交消息
async sendMessage() {
  const formData = new FormData();
  formData.append('session_id', currentSessionId.value);
  formData.append('question', userInput.value);
  formData.append('subject', currentSubject.value);
  
  selectedImages.value.forEach((file, idx) => {
    formData.append('images', file);
  });
  
  // 调用 /api/ai/chat（multipart/form-data）
  // 处理 SSE 流式响应
}
```

---

## 7. 错误处理与降级

### 7.1 错误处理矩阵

| 场景 | 处理方案 |
|------|--------|
| 上传文件验证失败 | 清晰的错误提示，用户可重新选择 |
| 文件保存失败 | 返回 500 错误，提示联系管理员 |
| OCR 超时或失败 | 仅使用 Vision API 结果，记录日志 |
| Vision API 失败 | 仅使用 OCR 结果，记录日志 |
| 两个都失败 | 使用原问题文本，降级为纯文本对话 |
| 网络中断 | 保留已选择的图片，支持重新上传 |

### 7.2 超时设置

- OCR 调用超时：10 秒
- Vision API 超时：30 秒
- 整个图片处理超时：45 秒（OCR 10s + Vision 30s + 余量 5s）

---

## 8. 性能考虑

### 8.1 并发处理

- OCR 和 Vision API **并行执行**，不串行
- 使用 `asyncio.gather()` 等待两个结果
- 预估耗时：max(OCR 10s, Vision 30s) ≈ 30-35 秒

### 8.2 文件存储

- 路径结构：`uploads/{user_id}/{session_id}/{timestamp}_{filename}`
- 支持按用户/会话快速清理
- 建议添加定时任务删除 30 天前的文件

### 8.3 数据库查询优化

- ChatImage 表建立索引：(session_id, user_id)、created_at
- 查询历史消息时 JOIN ChatImage，一次查询获取消息+图片

### 8.4 Token 成本优化

- Vision API：每张图片 ~500-1000 tokens
- 5 张图片：~2500-5000 tokens
- 可选：限制每个用户每小时的图片分析次数（需求确认）

---

## 9. 新增依赖

### 后端 requirements.txt

```
paddleocr>=2.8.0              # OCR 识别（中文优化）
pdf2image>=1.16.0             # PDF → 图片转换
pillow>=10.0.0                # 图片处理和压缩
python-multipart>=0.0.6       # FastAPI 文件上传支持
```

### 版本要求

- FastAPI >= 0.95.0（已有）
- SQLAlchemy >= 2.0（已有）
- AsyncOpenAI >= 1.3.0（已有）

---

## 10. 测试策略

### 10.1 后端单元测试

```
test_image_service.py
  ├─ validate_files()
  │   ├─ 测试文件数量超限
  │   ├─ 测试单个文件过大
  │   └─ 测试不支持的文件类型
  ├─ save_images()
  │   ├─ 测试文件保存路径
  │   └─ 测试数据库记录
  ├─ extract_with_ocr()
  │   └─ 测试 OCR 提取结果
  ├─ analyze_with_vision()
  │   └─ 测试 Vision API 调用
  └─ merge_analysis_results()
      └─ 测试去重和融合逻辑

test_ai_routes.py
  ├─ POST /api/ai/chat (with images)
  │   ├─ 测试单张图片
  │   ├─ 测试多张图片
  │   ├─ 测试文件验证失败
  │   └─ 测试流式响应
  ├─ GET /api/ai/chat/{session_id}/images
  ├─ DELETE /api/ai/chat/images/{image_id}
```

### 10.2 集成测试

- 完整流程：上传 → OCR + Vision → 流式回答
- 降级测试：OCR 失败、Vision 失败、都失败

### 10.3 前端测试

- ImageUploadArea 组件测试
- 图片拖拽/点击上传
- 文件验证提示
- 聊天气泡图片展示

---

## 11. 部署清单

### 11.1 数据库迁移

```sql
-- 1. 修改 chat_messages 表
ALTER TABLE chat_messages 
  ADD COLUMN image_ids TEXT,
  ADD COLUMN image_ocr_text TEXT,
  ADD COLUMN image_vision_desc TEXT;

-- 2. 创建 chat_images 表
CREATE TABLE chat_images (
  ... (见第 3.1 节)
);

-- 3. 创建目录
mkdir -p backend/uploads
chmod 755 backend/uploads
```

### 11.2 依赖安装

```bash
cd backend
pip install --upgrade -r requirements.txt
```

### 11.3 环境变量（可选）

```env
# 如需配置上传目录
UPLOAD_DIR=./uploads

# 如需限制上传
MAX_IMAGE_COUNT=5
MAX_IMAGE_SIZE_MB=10
```

### 11.4 启动验证

```bash
# 1. 启动后端
uvicorn app.main:app --reload

# 2. 检查 OCR 模型加载
# 首次启动时会下载 PaddleOCR 模型（10-50MB），预期耗时 2-3 分钟

# 3. 测试 /api/ai/chat 端点（带图片）
curl -X POST http://localhost:8000/api/ai/chat \
  -F "session_id=test" \
  -F "question=这道题怎么做？" \
  -F "subject=数学" \
  -F "images=@sample.jpg"
```

---

## 12. 里程碑和交付

### Phase 1：核心实现（≈ 2-3 天）
- [ ] ImageService 基础实现
- [ ] 数据库模型和迁移
- [ ] 文件上传和验证
- [ ] ImageUploadArea 组件

### Phase 2：AI 集成（≈ 1-2 天）
- [ ] PaddleOCR 集成
- [ ] Vision API 集成
- [ ] 结果融合逻辑
- [ ] 增强提示词构造

### Phase 3：测试和优化（≈ 1-2 天）
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能测试（并发、响应时间）
- [ ] 用户体验优化

### Phase 4：部署（≈ 0.5 天）
- [ ] 数据库迁移
- [ ] 依赖安装
- [ ] 部署验证
- [ ] 监控告警配置

---

## 13. 风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|--------|
| PaddleOCR 首次加载慢 | 首次请求延迟 2-3s | 启动时预加载模型 |
| Vision API 速率限制 | 高并发时失败 | 添加队列机制 + 重试 |
| 磁盘空间爆满 | 文件保存失败 | 定期清理过期文件 + 告警 |
| 图片识别准确度低 | AI 回答不准确 | 融合 OCR+Vision，降级处理 |

---

## 14. 附录：系统提示词补充

**原 SYSTEM_PROMPT 补充内容：**

```
## 处理上传的试题图片
当用户上传了图片试题时：
1. 我已经为你提取了图片中的文字（OCR）和内容描述（Vision API）
2. 你可以同时参考：
   - 用户输入的问题文本
   - OCR 提取的文字
   - 图片的视觉描述
3. 对于数学公式，保持 LaTeX 格式：$...$ 或 $$...$$
4. 对于化学结构，使用 SMILES 或 mhchem 格式
5. 如果识别结果有冲突，优先相信 Vision API 的描述
```

---

## 15. 参考资源

- PaddleOCR 文档：https://github.com/PaddlePaddle/PaddleOCR
- OpenAI Vision API：https://platform.openai.com/docs/guides/vision
- FastAPI 文件上传：https://fastapi.tiangolo.com/tutorial/request-files/
- SQLAlchemy 级联删除：https://docs.sqlalchemy.org/en/20/orm/cascades.html

