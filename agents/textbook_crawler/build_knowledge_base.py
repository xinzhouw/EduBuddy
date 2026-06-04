"""
高中教材知识库构建脚本
========================
功能：
  1. 读取 cache/pdfs/high_school/**/*.pdf
  2. 用 PyMuPDF 提取文本（按页/段落分块）
  3. 用 sentence-transformers（或 OpenAI Embeddings）生成向量
  4. 存入 ChromaDB 持久化向量数据库
  5. 同时输出每个学科的 JSON 知识点文件

输出：
  - backend/data/knowledge_base/chroma/     ChromaDB 向量库
  - backend/data/curriculum/{subject}.json  学科知识点 JSON

用法：
    python build_knowledge_base.py
    python build_knowledge_base.py --subject 数学     # 只处理数学
    python build_knowledge_base.py --reindex          # 强制重建（清空已有索引）
    python build_knowledge_base.py --embedder openai  # 用 OpenAI Embeddings
"""

import os
import sys
import json
import logging
import argparse
import re
import hashlib
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
PDF_DIR = BASE_DIR / "cache" / "pdfs" / "high_school"
REPO_ROOT = BASE_DIR / ".." / ".."
KB_DIR = REPO_ROOT / "backend" / "data" / "knowledge_base"
CURRICULUM_DIR = REPO_ROOT / "backend" / "data" / "curriculum"
CHROMA_DIR = KB_DIR / "chroma"

# 文本分块配置
CHUNK_SIZE = 500          # 每块字符数（中文）
CHUNK_OVERLAP = 80        # 相邻块重叠字符数
MIN_CHUNK_SIZE = 80       # 最小块大小，低于此跳过（提高以过滤碎片）

# 噪声页/噪声块过滤规则
NOISE_PATTERNS = [
    "PUTONG GAOZHONG JIAOKESHU",  # 教科书拼音页眉
    "绿色印刷产品",
    "定价：",
    "人民教育出版社",
    "课程教材研究所",
    "ISBN",
    "图书在版编目",
    "未经出版者书面许可",
    "版权所有",
    "盗版必究",
    "电子邮箱",
    "联系方式",
    "印刷",
    "开本",
    "字数",
    "审图号",
]
# 中文字符占比阈值：低于此视为噪声（如纯拼音/英文版权页）
MIN_CN_RATIO = 0.25


# ChromaDB Collection 名称
COLLECTION_NAME = "high_school_textbooks"

# 学科英文映射（用于文件命名）
SUBJECT_MAP = {
    "数学": "math", "物理": "physics", "化学": "chemistry",
    "生物": "biology", "语文": "chinese", "英语": "english",
    "历史": "history", "地理": "geography", "政治": "politics",
}

# 教材文件名到元数据的映射
BOOK_META = {
    # 数学
    "math_a_bi1":  {"subject": "数学", "grade": "高一", "book": "必修第一册"},
    "math_a_bi2":  {"subject": "数学", "grade": "高一", "book": "必修第二册"},
    "math_a_sel1": {"subject": "数学", "grade": "高二", "book": "选择性必修第一册"},
    "math_a_sel2": {"subject": "数学", "grade": "高二", "book": "选择性必修第二册"},
    "math_a_sel3": {"subject": "数学", "grade": "高三", "book": "选择性必修第三册"},
    # 物理
    "physics_bi1": {"subject": "物理", "grade": "高一", "book": "必修第一册"},
    "physics_bi2": {"subject": "物理", "grade": "高一", "book": "必修第二册"},
    "physics_bi3": {"subject": "物理", "grade": "高一", "book": "必修第三册"},
    "physics_sel1": {"subject": "物理", "grade": "高二", "book": "选择性必修第一册"},
    "physics_sel2": {"subject": "物理", "grade": "高二", "book": "选择性必修第二册"},
    "physics_sel3": {"subject": "物理", "grade": "高三", "book": "选择性必修第三册"},
    # 化学
    "chemistry_bi1": {"subject": "化学", "grade": "高一", "book": "必修第一册"},
    "chemistry_bi2": {"subject": "化学", "grade": "高一", "book": "必修第二册"},
    "chemistry_sel1": {"subject": "化学", "grade": "高二", "book": "选择性必修1化学反应原理"},
    "chemistry_sel2": {"subject": "化学", "grade": "高二", "book": "选择性必修2物质结构与性质"},
    "chemistry_sel3": {"subject": "化学", "grade": "高三", "book": "选择性必修3有机化学基础"},
    # 生物
    "biology_bi1": {"subject": "生物", "grade": "高一", "book": "必修1分子与细胞"},
    "biology_bi2": {"subject": "生物", "grade": "高一", "book": "必修2遗传与进化"},
    "biology_sel1": {"subject": "生物", "grade": "高二", "book": "选择性必修1稳态与调节"},
    "biology_sel2": {"subject": "生物", "grade": "高二", "book": "选择性必修2生物与环境"},
    "biology_sel3": {"subject": "生物", "grade": "高三", "book": "选择性必修3生物技术与工程"},
    # 语文
    "chinese_bi_up": {"subject": "语文", "grade": "高一", "book": "必修上册"},
    "chinese_bi_down": {"subject": "语文", "grade": "高一", "book": "必修下册"},
    "chinese_sel_up": {"subject": "语文", "grade": "高二", "book": "选择性必修上册"},
    "chinese_sel_mid": {"subject": "语文", "grade": "高二", "book": "选择性必修中册"},
    "chinese_sel_down": {"subject": "语文", "grade": "高三", "book": "选择性必修下册"},
    # 英语
    "english_bi1": {"subject": "英语", "grade": "高一", "book": "必修第一册"},
    "english_bi2": {"subject": "英语", "grade": "高一", "book": "必修第二册"},
    "english_bi3": {"subject": "英语", "grade": "高一", "book": "必修第三册"},
    "english_sel1": {"subject": "英语", "grade": "高二", "book": "选择性必修第一册"},
    "english_sel2": {"subject": "英语", "grade": "高二", "book": "选择性必修第二册"},
    "english_sel3": {"subject": "英语", "grade": "高三", "book": "选择性必修第三册"},
    "english_sel4": {"subject": "英语", "grade": "高三", "book": "选择性必修第四册"},
    # 历史
    "history_bi_up": {"subject": "历史", "grade": "高一", "book": "必修中外历史纲要上"},
    "history_bi_down": {"subject": "历史", "grade": "高一", "book": "必修中外历史纲要下"},
    "history_sel1": {"subject": "历史", "grade": "高二", "book": "选择性必修1国家制度与社会治理"},
    "history_sel2": {"subject": "历史", "grade": "高二", "book": "选择性必修2经济与社会生活"},
    "history_sel3": {"subject": "历史", "grade": "高三", "book": "选择性必修3文化交流与传播"},
    # 地理
    "geography_bi1": {"subject": "地理", "grade": "高一", "book": "必修第一册"},
    "geography_bi2": {"subject": "地理", "grade": "高一", "book": "必修第二册"},
    "geography_sel1": {"subject": "地理", "grade": "高二", "book": "选择性必修1自然地理基础"},
    "geography_sel2": {"subject": "地理", "grade": "高二", "book": "选择性必修2区域发展"},
    "geography_sel3": {"subject": "地理", "grade": "高三", "book": "选择性必修3资源环境与国家安全"},
    # 政治
    "politics_bi1": {"subject": "政治", "grade": "高一", "book": "必修1中国特色社会主义"},
    "politics_bi2": {"subject": "政治", "grade": "高一", "book": "必修2经济与社会"},
    "politics_bi3": {"subject": "政治", "grade": "高二", "book": "必修3政治与法治"},
    "politics_bi4": {"subject": "政治", "grade": "高二", "book": "必修4哲学与文化"},
    "politics_sel1": {"subject": "政治", "grade": "高二", "book": "选择性必修1当代国际政治与经济"},
    "politics_sel2": {"subject": "政治", "grade": "高三", "book": "选择性必修2法律与生活"},
    "politics_sel3": {"subject": "政治", "grade": "高三", "book": "选择性必修3逻辑与思维"},
}


def extract_text_from_pdf(pdf_path: Path) -> list[dict]:
    """
    用 PyMuPDF 提取 PDF 文本，返回分页文本列表。
    每项：{"page": n, "text": "...", "toc_title": "..."}
    """
    try:
        import fitz
    except ImportError:
        log.error("PyMuPDF 未安装。请运行：pip install PyMuPDF")
        return []

    pages = []
    try:
        doc = fitz.open(str(pdf_path))
        toc = doc.get_toc()  # [(level, title, page), ...]
        # 建立 page_num -> toc_title 映射
        page_to_title = {}
        for level, title, page_num in toc:
            if level <= 2 and page_num not in page_to_title:
                page_to_title[page_num] = title.strip()

        current_title = ""
        for page_num in range(doc.page_count):
            if page_num + 1 in page_to_title:
                current_title = page_to_title[page_num + 1]
            page = doc[page_num]
            text = page.get_text("text").strip()
            if text and len(text) > 30:
                pages.append({
                    "page": page_num + 1,
                    "text": text,
                    "toc_title": current_title,
                })
        doc.close()
    except Exception as e:
        log.error(f"提取 PDF 失败 {pdf_path.name}: {e}")
    return pages


def is_noise_chunk(chunk: str) -> bool:
    """判断文本块是否为噪声（版权页/页眉页脚/拼音/纯符号等）"""
    if len(chunk) < MIN_CHUNK_SIZE:
        return True
    # 命中噪声关键词
    hit = sum(1 for p in NOISE_PATTERNS if p in chunk)
    if hit >= 2:
        return True
    # 中文字符占比过低（纯拼音/英文版权页/纯公式符号），但英语教材除外（靠调用方控制）
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', chunk))
    cn_ratio = cn_chars / max(len(chunk), 1)
    if cn_ratio < MIN_CN_RATIO and hit >= 1:
        return True
    return False


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """将长文本分割成重叠的小块"""

    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()

    if len(text) <= chunk_size:
        return [text] if len(text) >= MIN_CHUNK_SIZE else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunk = text[start:]
        else:
            # 尽量在句子边界切割
            for sep in ['。\n', '。', '！', '？', '\n\n', '\n', '；', '，']:
                pos = text.rfind(sep, start + chunk_size // 2, end)
                if pos != -1:
                    end = pos + len(sep)
                    break
            chunk = text[start:end]

        if len(chunk) >= MIN_CHUNK_SIZE:
            chunks.append(chunk.strip())
        start = end - overlap

    return chunks


def build_chromadb(pdf_files: list[Path], reindex: bool = False, embedder: str = "local") -> bool:
    """构建 ChromaDB 向量知识库"""
    try:
        import chromadb
    except ImportError:
        log.error("chromadb 未安装。请运行：pip install chromadb")
        return False

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    # 创建 ChromaDB 客户端（持久化）
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # 配置 embedding 函数
    if embedder == "openai":
        try:
            from chromadb.utils import embedding_functions
            api_key = os.environ.get("OPENAI_API_KEY", "")
            base_url = os.environ.get("OPENAI_BASE_URL", "")
            if not api_key:
                log.error("使用 OpenAI Embeddings 需要设置 OPENAI_API_KEY 环境变量")
                return False
            ef_kwargs = {"api_key": api_key, "model_name": "text-embedding-3-small"}
            if base_url:
                ef_kwargs["api_base"] = base_url
            embed_fn = embedding_functions.OpenAIEmbeddingFunction(**ef_kwargs)
            log.info("使用 OpenAI text-embedding-3-small")
        except Exception as e:
            log.error(f"OpenAI Embedding 初始化失败: {e}")
            return False
    elif embedder == "bge":
        # 使用 BGE 中文专用模型（中文检索 SOTA，需 torch）
        try:
            from chromadb.utils import embedding_functions
            embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="BAAI/bge-small-zh-v1.5"
            )
            log.info("使用 BAAI/bge-small-zh-v1.5 中文模型")
        except Exception as e:
            log.warning(f"BGE 模型加载失败: {e}")
            log.info("回退到 ChromaDB 默认 embedding")
            embed_fn = None
    elif embedder == "local":
        # 使用 sentence-transformers 多语言模型（需 torch，对中文效果更好）
        try:
            from chromadb.utils import embedding_functions
            embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="paraphrase-multilingual-MiniLM-L12-v2"
            )
            log.info("使用本地 paraphrase-multilingual-MiniLM-L12-v2 模型")
        except Exception as e:
            log.warning(f"sentence-transformers 加载失败: {e}")
            log.info("回退到 ChromaDB 默认 embedding（ONNX all-MiniLM-L6-v2）")
            embed_fn = None
    else:
        # default：使用 ChromaDB 自带的 ONNX embedding（all-MiniLM-L6-v2），轻量无需 torch
        log.info("使用 ChromaDB 默认 embedding（ONNX all-MiniLM-L6-v2，轻量）")
        embed_fn = None


    # 获取或创建 collection
    if reindex:
        try:
            client.delete_collection(COLLECTION_NAME)
            log.info(f"已删除旧 Collection：{COLLECTION_NAME}")
        except Exception:
            pass

    try:
        if embed_fn:
            collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=embed_fn,
                metadata={"hnsw:space": "cosine", "description": "高中教材知识库"}
            )
        else:
            collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine", "description": "高中教材知识库"}
            )
    except Exception as e:
        log.error(f"创建 Collection 失败: {e}")
        return False

    existing_count = collection.count()
    log.info(f"Collection '{COLLECTION_NAME}' 当前已有 {existing_count} 条记录")

    total_chunks = 0
    total_books = 0

    for pdf_path in pdf_files:
        stem = pdf_path.stem
        meta = BOOK_META.get(stem, {})
        subject = meta.get("subject", "未知")
        grade = meta.get("grade", "")
        book_name = meta.get("book", stem)
        full_title = f"普通高中教科书·{subject}{book_name}"

        log.info(f"\n  处理：{pdf_path.name} [{subject} {book_name}]")

        # 提取文本
        pages = extract_text_from_pdf(pdf_path)
        if not pages:
            log.warning(f"  ⚠️ 未提取到文本：{pdf_path.name}")
            continue

        log.info(f"  提取到 {len(pages)} 页文本")

        # 分块
        all_chunks = []
        all_ids = []
        all_metas = []

        skipped_noise = 0
        is_english = subject == "英语"
        for page_data in pages:
            chunks = chunk_text(page_data["text"])
            for ci, chunk in enumerate(chunks):
                # 过滤噪声块（版权页/页眉页脚等）。英语教材本身中文占比低，跳过中文占比检查。
                if not is_english and is_noise_chunk(chunk):
                    skipped_noise += 1
                    continue
                # 生成唯一 ID（基于内容哈希）
                chunk_hash = hashlib.md5(chunk.encode()).hexdigest()[:12]
                chunk_id = f"{stem}_p{page_data['page']:04d}_c{ci:03d}_{chunk_hash}"

                all_chunks.append(chunk)

                all_ids.append(chunk_id)
                all_metas.append({
                    "subject": subject,
                    "grade": grade,
                    "book": book_name,
                    "title": full_title,
                    "page": page_data["page"],
                    "toc_title": page_data.get("toc_title", ""),
                    "source": pdf_path.name,
                })

        if not all_chunks:
            log.warning(f"  ⚠️ 分块后为空：{pdf_path.name}")
            continue

        log.info(f"  生成 {len(all_chunks)} 个文本块")

        # 批量写入 ChromaDB（每批100条）
        batch_size = 100
        added = 0
        for i in range(0, len(all_chunks), batch_size):
            batch_docs = all_chunks[i:i+batch_size]
            batch_ids = all_ids[i:i+batch_size]
            batch_metas = all_metas[i:i+batch_size]
            try:
                collection.upsert(
                    documents=batch_docs,
                    ids=batch_ids,
                    metadatas=batch_metas,
                )
                added += len(batch_docs)
            except Exception as e:
                log.error(f"  写入失败（批次 {i//batch_size+1}）: {e}")

        log.info(f"  ✅ 写入 {added} 条")
        total_chunks += added
        total_books += 1

    final_count = collection.count()
    log.info(f"\n✅ ChromaDB 构建完成")
    log.info(f"   处理教材：{total_books} 本")
    log.info(f"   本次写入：{total_chunks} 条")
    log.info(f"   数据库总计：{final_count} 条")
    log.info(f"   路径：{CHROMA_DIR}")
    return True


def build_curriculum_json(pdf_files: list[Path]) -> dict:
    """
    从 PDF 提取目录结构，生成各学科 curriculum JSON。
    同时更新 backend/data/curriculum/ 下的学科文件。
    """
    try:
        import fitz
    except ImportError:
        log.warning("PyMuPDF 未安装，跳过 curriculum JSON 生成")
        return {}

    curriculum = {}  # {subject: {subject, textbook, grades: {grade: {chapter: [topics]}}}}

    for pdf_path in pdf_files:
        stem = pdf_path.stem
        meta = BOOK_META.get(stem, {})
        subject = meta.get("subject", "未知")
        grade = meta.get("grade", "")
        book_name = meta.get("book", stem)

        log.info(f"  提取目录：{pdf_path.name}")

        try:
            doc = fitz.open(str(pdf_path))
            toc = doc.get_toc()
            doc.close()
        except Exception as e:
            log.warning(f"  打开失败: {e}")
            continue

        if not toc:
            log.warning(f"  无内置目录：{pdf_path.name}")
            continue

        # 解析目录结构
        chapters = {}
        current_ch = None
        skip_titles = {"封面", "目录", "前言", "版权", "索引", "参考文献", "附录", "Contents"}

        for level, title, page in toc:
            title = title.strip()
            if not title or title in skip_titles or len(title) > 80:
                continue
            if level == 1:
                current_ch = title
                if title not in chapters:
                    chapters[title] = []
            elif level == 2 and current_ch:
                chapters[current_ch].append(title)
            elif level >= 3 and current_ch and chapters[current_ch]:
                # 三级标题作为知识点附加到上一条
                last = chapters[current_ch][-1]
                if isinstance(last, str) and not last.startswith("  →"):
                    chapters[current_ch].append(f"  → {title}")

        if not chapters:
            log.warning(f"  目录解析为空：{pdf_path.name}")
            continue

        log.info(f"  提取到 {len(chapters)} 个章节")

        # 合并到 curriculum
        if subject not in curriculum:
            curriculum[subject] = {
                "subject": subject,
                "textbook": "人教版",
                "standard": "2022年版课程标准",
                "source": "official_pdf",
                "grades": {}
            }
        if grade not in curriculum[subject]["grades"]:
            curriculum[subject]["grades"][grade] = {}
        # 合并章节（同年级多册合并）
        curriculum[subject]["grades"][grade].update(chapters)

    # 保存 JSON 文件
    CURRICULUM_DIR.mkdir(parents=True, exist_ok=True)
    for subject, data in curriculum.items():
        fname = SUBJECT_MAP.get(subject, subject)
        out_path = CURRICULUM_DIR / f"{fname}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        ch_count = sum(len(v) for v in data["grades"].values())
        log.info(f"  ✅ 已保存：{out_path.name}（{len(data['grades'])} 年级，{ch_count} 章）")

    return curriculum


def main():
    parser = argparse.ArgumentParser(description="高中教材知识库构建器")
    parser.add_argument("--subject", help="只处理指定学科", default=None)
    parser.add_argument("--reindex", action="store_true", help="强制重建向量库")
    parser.add_argument("--embedder", choices=["local", "openai", "default", "bge"], default="default",
                        help="embedding 方式：default（ChromaDB自带ONNX）/ local（多语言）/ bge（中文BGE，推荐）/ openai")
    parser.add_argument("--collection", default=None, help="自定义 collection 名（默认 high_school_textbooks）")
    parser.add_argument("--skip-chroma", action="store_true", help="跳过 ChromaDB，只生成 JSON")
    args = parser.parse_args()

    global COLLECTION_NAME
    if args.collection:
        COLLECTION_NAME = args.collection


    # 加载 .env
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        env_path = REPO_ROOT / ".env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    if k.strip() and k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip()

    # 查找 PDF 文件
    if not PDF_DIR.exists():
        log.error(f"PDF 目录不存在：{PDF_DIR}")
        log.error("请先运行 python download_all_hs.py 下载教材")
        sys.exit(1)

    pdf_files = sorted(PDF_DIR.rglob("*.pdf"))
    if args.subject:
        subject_pdfs = []
        for stem, meta in BOOK_META.items():
            if meta.get("subject") == args.subject:
                for sub_dir in PDF_DIR.iterdir():
                    pdf_path = sub_dir / f"{stem}.pdf" if sub_dir.is_dir() else PDF_DIR / f"{stem}.pdf"
                    if not pdf_path.exists():
                        pdf_path = PDF_DIR / meta.get("subject", "") / f"{stem}.pdf"
                    if pdf_path.exists():
                        subject_pdfs.append(pdf_path)
        pdf_files = subject_pdfs
        if not pdf_files:
            log.error(f"未找到 {args.subject} 的 PDF 文件")
            sys.exit(1)

    if not pdf_files:
        log.error(f"未找到任何 PDF 文件：{PDF_DIR}")
        log.error("请先运行 python download_all_hs.py 下载教材")
        sys.exit(1)

    log.info("=" * 60)
    log.info("📚 高中教材知识库构建器")
    log.info(f"   找到 {len(pdf_files)} 个 PDF 文件")
    for f in pdf_files:
        size_mb = f.stat().st_size / 1024 / 1024
        log.info(f"   - {f.name} ({size_mb:.1f} MB)")
    log.info("=" * 60)

    # Step 1: 生成 curriculum JSON（目录结构）
    log.info("\n📖 Step 1: 提取目录结构，生成 curriculum JSON...")
    curriculum = build_curriculum_json(pdf_files)
    log.info(f"   处理了 {len(curriculum)} 个学科")

    # Step 2: 构建 ChromaDB 向量库
    if not args.skip_chroma:
        log.info("\n🔍 Step 2: 构建 ChromaDB 向量知识库...")
        log.info("  （首次运行需下载 embedding 模型，约 400MB，请耐心等待）")
        ok = build_chromadb(pdf_files, reindex=args.reindex, embedder=args.embedder)
        if ok:
            log.info("\n🎉 知识库构建完成！")
            log.info(f"   向量库路径：{CHROMA_DIR}")
            log.info("   下一步：启动后端服务，RAG 功能将自动激活")
        else:
            log.error("向量库构建失败，请检查依赖安装")
            sys.exit(1)
    else:
        log.info("\n⏭️  跳过 ChromaDB（--skip-chroma）")
        log.info("🎉 curriculum JSON 生成完成！")


if __name__ == "__main__":
    main()
