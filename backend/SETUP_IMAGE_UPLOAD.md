# AI 问答图片上传功能 — 部署指南

支持用户上传学科试题截图（JPG/PNG/PDF），后端并行执行 OCR + GPT-4o Vision
分析，融合结果后由 AI 解答。

## 1. 环境要求

- Python >= 3.8（已有环境为 3.12）
- SQLite（现有 `data/edubuddy.db`）
- 已配置可用的 OpenAI/兼容 Vision 模型（`OPENAI_MODEL` 需支持图像输入，如 `gpt-4o`）

## 2. 依赖安装

核心依赖（`python-multipart`、`Pillow`）已在 `requirements.txt` 中。

OCR 为**可选增强**——不安装时 `ImageService` 自动降级为仅使用 Vision API，
功能仍完整可用（融合逻辑会跳过空的 OCR 结果）：

```bash
cd backend
# 仅在需要 OCR 文字提取增强时安装（体积较大）
pip install "paddleocr>=2.8.0" "pdf2image>=1.16.0"
```

## 3. 数据库迁移

`chat_images` 表与 `chat_messages` 新增字段（`image_ids` / `image_ocr_text` /
`image_vision_desc`）会在应用启动时由 `init_db()` 的 `create_all` 自动创建
（`ChatImage` 已注册到 `init_db`）。**无需手动操作**——重启后端即可。

如需手动执行（例如生产环境审计），可运行幂等迁移脚本：

```bash
cd backend
./venv/bin/python -c "
import importlib.util
from app.database import engine
spec = importlib.util.spec_from_file_location('m', 'migrations/001_add_chat_images_table.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.migrate_up(engine)
print('migration done')
"
```

> 注：`create_all` 只创建缺失的表，不会重复建表；已存在时安全跳过。

## 4. 文件存储

上传的图片保存在 `UPLOAD_DIR`（默认 `./uploads`），按
`{user_id}/{session_id}/{timestamp}_{index}_{filename}` 组织，并通过
`main.py` 已有的 `app.mount("/uploads", StaticFiles(...))` 静态托管，
前端以 `/uploads/{file_path}` 访问回显。

```bash
mkdir -p backend/uploads   # 若不存在
```

## 5. 启动验证

```bash
cd backend
./venv/bin/uvicorn app.main:app --reload --port 8000
```

首次安装 PaddleOCR 时，首个含图片的请求会触发模型下载（10–50MB，约 2–3 分钟）；
之后常驻内存。未安装 PaddleOCR 时无此延迟。

## 6. 测试

```bash
cd backend
./venv/bin/python -m pytest tests/test_image_service.py tests/test_ai_routes_with_images.py -v
```

预期 16 个用例全部通过（11 单元 + 5 集成）。

## 7. 限制与降级策略

| 场景 | 行为 |
|------|------|
| 未安装 PaddleOCR | 仅用 Vision API，OCR 结果为空，融合自动跳过 |
| OCR 超时/异常 | 记录日志，返回空字符串，不影响 Vision |
| Vision API 超时（30s）/异常 | 记录日志，返回空字符串，回退到 OCR 结果 |
| 两者皆失败 | 降级为用原始问题文本进行普通对话 |
| 上传校验失败 | 返回 400，前端展示错误（数量/大小/格式） |

## 8. 约束

- 每条消息最多 **5 张**图片，单张 ≤ **10MB**，格式 **JPG/PNG/PDF**
- 用户仅能查询/删除**自己**会话的图片（后端属主校验）
- 删除为软删除（`deleted_at`）并移除磁盘文件

## 9. 定期清理（建议）

图片随会话级联删除（`ChatImage.session` 配置了 `cascade="all, delete-orphan"`）。
如需按时间清理磁盘上的过期文件，可加定时任务：

```bash
find backend/uploads -type f -mtime +30 -delete
```
