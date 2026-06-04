# 高中教材爬取与 RAG 知识库构建

本目录提供「下载高中教材 PDF → 构建向量知识库 → 为 EduBuddy AI 问答提供 RAG 支持」的完整流水线。

## 📦 目录结构

```
agents/textbook_crawler/
├── download_all_hs.py       # 高中全科教材 PDF 批量下载脚本（50本）
├── build_knowledge_base.py  # 知识库构建脚本（PDF→文本→向量库）
├── eval_rag.py              # 检索质量评测脚本
├── requirements.txt         # 依赖
└── cache/pdfs/high_school/  # 下载的 PDF（按学科分目录）
    ├── 数学/  物理/  化学/  生物/
    └── 语文/  英语/  历史/  地理/  政治/
```


## 🚀 使用流程

### 1. 安装依赖

```bash
# 推荐使用 venv
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
# 注：sentence-transformers 体积较大（含 torch），
# 若网络受限可只装 chromadb（自带轻量 ONNX embedding）：
./.venv/bin/pip install requests PyMuPDF chromadb
```

### 2. 下载高中全科教材 PDF（50 本，约 814MB）

```bash
# 下载全部 9 大主科
./.venv/bin/python3 download_all_hs.py

# 只下载某一学科
./.venv/bin/python3 download_all_hs.py --subject 数学

# 预览待下载列表（不实际下载）
./.venv/bin/python3 download_all_hs.py --dry-run
```

教材来源：国家中小学智慧教育平台（basic.smartedu.cn）CDN 直链，**无需登录**。

### 3. 构建向量知识库

```bash
# 【推荐】用 BGE 中文模型（中文检索 SOTA，需 torch）—— 当前后端使用此库
./.venv/bin/python3 build_knowledge_base.py --embedder bge --collection high_school_textbooks_bge --reindex

# 用 ChromaDB 自带 ONNX embedding（轻量无需 torch，但中文检索较差）
./.venv/bin/python3 build_knowledge_base.py --embedder default --reindex

# 用多语言 sentence-transformers 模型
./.venv/bin/python3 build_knowledge_base.py --embedder local --reindex

# 用 OpenAI Embeddings（质量最高，需 OPENAI_API_KEY，消耗 API 额度）
./.venv/bin/python3 build_knowledge_base.py --embedder openai --reindex

# 只生成 curriculum 章节 JSON，不建向量库
./.venv/bin/python3 build_knowledge_base.py --skip-chroma
```

**输出：**
- `backend/data/knowledge_base/chroma/` — ChromaDB 向量库（BGE 库约 15244 条记录）
- `backend/data/curriculum/{subject}.json` — 各学科章节知识点 JSON

### 4. 评测检索质量

```bash
# 评测 BGE 库（当前生产库）
./.venv/bin/python3 eval_rag.py --collection high_school_textbooks_bge --embedder bge --top-k 5

# 评测 ONNX 默认库（基线对比）
./.venv/bin/python3 eval_rag.py --collection high_school_textbooks --embedder auto --top-k 5
```

## 📊 检索质量评测结果（26 个跨学科查询）

| 指标 | ONNX 默认（基线） | BGE 中文 + 噪声过滤（改进后） |
|------|------------------|------------------------------|
| 学科准确率@1   | 100%   | 100%   |
| 关键词召回率@5 | 30.8%  | **100%** ⬆ |
| MRR            | 0.269  | **1.000** ⬆ |
| 平均 top1 相似度 | 0.628 | **0.751** ⬆ |

**改进措施：**
1. **更换中文 embedding 模型**：英文 `all-MiniLM-L6-v2`（ONNX）→ 中文 SOTA 模型 `BAAI/bge-small-zh-v1.5`
2. **噪声过滤**：构建时过滤版权页/页眉页脚/拼音页（`is_noise_chunk()`），并提高最小块大小到 80 字符
3. **学科 + 年级元数据过滤**：检索时按学科精确过滤，避免跨学科误召回


## 📚 教材清单（9 大主科，50 本）

| 学科 | 册数 | 出版社 |
|------|------|--------|
| 数学 | 5（必修2 + 选必3） | 人教A版 |
| 物理 | 6（必修3 + 选必3） | 人教版 |
| 化学 | 5（必修2 + 选必3） | 人教版 |
| 生物 | 5（必修2 + 选必3） | 人教版 |
| 语文 | 5（必修2 + 选必3） | 统编版 |
| 英语 | 7（必修3 + 选必4） | 人教版 |
| 历史 | 5（必修2 + 选必3） | 统编版 |
| 地理 | 5（必修2 + 选必3） | 人教版 |
| 政治 | 7（必修4 + 选必3） | 统编版 |

## ⚠️ 已知限制

- **数学必修第一册（math_a_bi1）等少数 PDF 为扫描版**，PyMuPDF 无法提取文本，
  这些册的内容不会进入向量库（构建时会显示「未提取到文本」）。
  如需处理扫描版，可引入 OCR（如 PaddleOCR / Tesseract），但成本较高。
- 默认 ONNX embedding 是英文模型，中文检索相似度普遍偏低（0.3~0.7），
  靠「学科过滤 + top_k」保证召回相关学科内容。追求更高中文检索质量请用
  `--embedder local`（多语言模型）或 `--embedder openai`。

## 🔗 与后端 RAG 的对接

后端 `backend/app/services/rag_service.py` 会自动加载本目录构建的向量库：
- 加载路径：`backend/data/knowledge_base/chroma/`
- AI 问答（`POST /api/ai/chat`）会自动检索教材内容并注入 prompt
- 知识库状态查询：`GET /api/ai/knowledge-base/stats`
- 检索预览（调试）：`GET /api/ai/knowledge-base/retrieve?query=...&subject=...`

**重要**：后端 venv 也需安装 chromadb（`pip install chromadb`），
且 `rag_service` 使用的 embedding 必须与构建时一致（默认均为 ONNX）。
知识库不存在或 chromadb 未安装时，RAG 自动降级（AI 问答正常工作，只是不注入教材内容）。
