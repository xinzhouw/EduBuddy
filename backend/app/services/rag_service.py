"""
RAG 服务（Retrieval-Augmented Generation）
==========================================
基于 ChromaDB 向量库，为 AI 问答提供教材内容检索支持。

工作流程：
  1. 用户提问 → 向量化查询
  2. 在 ChromaDB 中检索最相关的教材段落
  3. 将检索到的上下文注入到 AI System Prompt 中
  4. AI 基于教材内容给出更准确的回答

依赖：
  pip install chromadb sentence-transformers
"""

import os
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# 知识库路径（相对于 backend/）
_REPO_ROOT = Path(__file__).parent.parent.parent.parent  # EduBuddy/
CHROMA_DIR = _REPO_ROOT / "backend" / "data" / "knowledge_base" / "chroma"
# Collection 优先级：BGE 中文模型库 > ONNX 默认库
COLLECTION_NAME = "high_school_textbooks"          # ONNX 默认 embedding 库
COLLECTION_NAME_BGE = "high_school_textbooks_bge"  # BGE 中文 embedding 库（检索质量更高）
BGE_MODEL = "BAAI/bge-small-zh-v1.5"

# 检索配置
DEFAULT_TOP_K = 4           # 默认召回条数
MAX_CONTEXT_CHARS = 2000    # 注入 prompt 的最大字符数



class RAGService:
    """
    教材知识库检索服务。
    懒加载：首次调用 retrieve() 时才初始化向量库，避免影响启动速度。
    """

    def __init__(self):
        self._client = None
        self._collection = None
        self._embed_fn = None
        self._initialized = False
        self._available = False  # 知识库是否可用

    def _init(self) -> bool:
        """懒初始化 ChromaDB"""
        if self._initialized:
            return self._available

        self._initialized = True

        if not CHROMA_DIR.exists():
            log.info(f"RAG: 知识库目录不存在（{CHROMA_DIR}），RAG 功能已禁用")
            log.info("RAG: 请运行 agents/textbook_crawler/build_knowledge_base.py 构建知识库")
            self._available = False
            return False

        try:
            import chromadb
        except ImportError:
            log.warning("RAG: chromadb 未安装，RAG 功能已禁用。可运行 pip install chromadb 启用。")
            self._available = False
            return False

        # 关键：查询用的 embedding 必须与建库时一致。
        # 优先尝试 BGE 中文库（检索质量高），不可用时回退到 ONNX 默认库。
        self._client = chromadb.PersistentClient(path=str(CHROMA_DIR))

        # 1) 优先 BGE 中文 collection
        try:
            from chromadb.utils import embedding_functions
            bge_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=BGE_MODEL)
            self._collection = self._client.get_collection(
                name=COLLECTION_NAME_BGE, embedding_function=bge_fn
            )
            self._embed_fn = bge_fn
            count = self._collection.count()
            log.info(f"RAG: ✅ 使用 BGE 中文知识库（{BGE_MODEL}），共 {count} 条记录")
            self._available = True
            return True
        except Exception as e:
            log.info(f"RAG: BGE 知识库不可用（{e}），尝试 ONNX 默认库")

        # 2) 回退到 ONNX 默认 collection（embedding 函数与建库时一致，不传则用默认 ONNX）
        try:
            self._collection = self._client.get_collection(name=COLLECTION_NAME)
            count = self._collection.count()
            log.info(f"RAG: ✅ 使用 ONNX 默认知识库（all-MiniLM-L6-v2），共 {count} 条记录")
            self._available = True
            return True
        except Exception as e:
            log.warning(f"RAG: 知识库加载失败（{e}），RAG 功能已禁用")
            self._available = False
            return False

    @property
    def is_available(self) -> bool:
        return self._init()

    def retrieve(
        self,
        query: str,
        subject: Optional[str] = None,
        grade: Optional[str] = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[dict]:
        """
        向量检索教材相关内容。

        Args:
            query: 用户问题
            subject: 学科过滤（如"数学"），None 表示不过滤
            grade: 年级过滤（如"高一"），None 表示不过滤
            top_k: 返回条数

        Returns:
            [{"text": "...", "subject": "...", "book": "...", "page": n, "score": 0.xx}, ...]
        """
        if not self._init():
            return []

        try:
            # 构建过滤条件
            where = {}
            if subject and grade:
                where = {"$and": [{"subject": {"$eq": subject}}, {"grade": {"$eq": grade}}]}
            elif subject:
                where = {"subject": {"$eq": subject}}
            elif grade:
                where = {"grade": {"$eq": grade}}

            # 执行检索
            query_kwargs = {
                "query_texts": [query],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                query_kwargs["where"] = where

            results = self._collection.query(**query_kwargs)

            # 格式化结果
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            retrieved = []
            for doc, meta, dist in zip(docs, metas, distances):
                # cosine distance → similarity score
                score = 1.0 - dist
                if score < 0.3:  # 过滤低相关度结果
                    continue
                retrieved.append({
                    "text": doc,
                    "subject": meta.get("subject", ""),
                    "grade": meta.get("grade", ""),
                    "book": meta.get("book", ""),
                    "title": meta.get("title", ""),
                    "page": meta.get("page", 0),
                    "toc_title": meta.get("toc_title", ""),
                    "source": meta.get("source", ""),
                    "score": round(score, 3),
                })

            return retrieved

        except Exception as e:
            log.error(f"RAG 检索失败: {e}")
            return []

    def build_context_prompt(
        self,
        query: str,
        subject: Optional[str] = None,
        grade: Optional[str] = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> str:
        """
        检索教材内容并构建上下文 prompt 段落，直接注入 AI System Prompt。

        Returns:
            上下文字符串（若未检索到则返回空字符串）
        """
        results = self.retrieve(query, subject=subject, grade=grade, top_k=top_k)
        if not results:
            return ""

        # 去重（避免完全相同的文本块）
        seen_texts = set()
        unique_results = []
        for r in results:
            text_key = r["text"][:100]
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_results.append(r)

        # 构建上下文段落
        context_parts = []
        total_chars = 0

        for r in unique_results:
            book_info = f"【{r['subject']} · {r['book']}】"
            if r.get("toc_title"):
                book_info += f"《{r['toc_title']}》"
            text = r["text"]

            part = f"{book_info}\n{text}\n"
            if total_chars + len(part) > MAX_CONTEXT_CHARS:
                # 截断最后一条以适应长度限制
                remaining = MAX_CONTEXT_CHARS - total_chars - len(book_info) - 10
                if remaining > 100:
                    context_parts.append(f"{book_info}\n{text[:remaining]}...\n")
                break
            context_parts.append(part)
            total_chars += len(part)

        if not context_parts:
            return ""

        context = "\n".join(context_parts)
        return (
            "\n\n---\n"
            "## 📚 教材参考内容（来自人教版官方教材）\n\n"
            f"{context}"
            "---\n"
            "请优先基于以上教材内容回答，保持与教材知识体系一致。\n"
        )

    def get_stats(self) -> dict:
        """获取知识库统计信息"""
        if not self._init():
            return {"available": False, "count": 0, "message": "知识库未初始化"}

        try:
            count = self._collection.count()
            # 按学科统计
            subjects_count = {}
            for subject in ["数学", "物理", "化学", "生物", "语文", "英语", "历史", "地理", "政治"]:
                try:
                    r = self._collection.get(where={"subject": {"$eq": subject}}, limit=1)
                    # 粗略统计（ChromaDB 不直接支持 count+where，用 get 替代）
                    subjects_count[subject] = "已加载"
                except Exception:
                    subjects_count[subject] = "无数据"

            return {
                "available": True,
                "count": count,
                "subjects": subjects_count,
                "chroma_dir": str(CHROMA_DIR),
            }
        except Exception as e:
            return {"available": False, "count": 0, "message": str(e)}


# 全局单例
rag_service = RAGService()
