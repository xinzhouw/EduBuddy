"""
RAG 检索质量评测脚本
=====================
对教材知识库的检索效果进行量化评测，计算以下指标：
  - Subject Accuracy@k：返回结果中学科正确的比例
  - Recall@k：期望关键词命中的查询占比（命中=top_k 任一结果含关键词）
  - MRR（Mean Reciprocal Rank）：第一个命中结果排名倒数的平均
  - 平均相似度

用法：
    python eval_rag.py                          # 用默认 collection 评测
    python eval_rag.py --collection high_school_textbooks_v2
    python eval_rag.py --top-k 5
"""

import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.WARNING)

BASE_DIR = Path(__file__).parent
CHROMA_DIR = BASE_DIR / ".." / ".." / "backend" / "data" / "knowledge_base" / "chroma"

# ==================== 评测集 ====================
# 每条：(查询, 期望学科, [期望命中的关键词（任一出现即算命中）])
EVAL_SET = [
    # 生物
    ("细胞膜的结构和功能", "生物", ["细胞膜", "磷脂", "流动镶嵌", "蛋白质"]),
    ("DNA的双螺旋结构", "生物", ["DNA", "双螺旋", "碱基", "脱氧核糖"]),
    ("光合作用的过程", "生物", ["光合作用", "光反应", "暗反应", "叶绿体", "ATP"]),
    ("有丝分裂的分裂期", "生物", ["有丝分裂", "染色体", "纺锤体", "分裂"]),
    ("基因的自由组合定律", "生物", ["自由组合", "等位基因", "孟德尔", "遗传"]),
    # 物理
    ("牛顿第二定律的内容", "物理", ["牛顿第二定律", "加速度", "合外力", "F=ma", "质量"]),
    ("动量守恒定律", "物理", ["动量", "守恒", "碰撞"]),
    ("电场强度的定义", "物理", ["电场强度", "电场", "电荷"]),
    ("简谐运动的特点", "物理", ["简谐", "振动", "周期", "回复力"]),
    ("万有引力定律", "物理", ["万有引力", "引力", "天体"]),
    # 化学
    ("元素周期律", "化学", ["元素周期", "周期表", "原子序数", "电子"]),
    ("化学反应速率的影响因素", "化学", ["反应速率", "催化剂", "浓度", "温度"]),
    ("化学平衡移动原理", "化学", ["化学平衡", "平衡移动", "勒夏特列"]),
    ("氧化还原反应", "化学", ["氧化", "还原", "电子", "化合价"]),
    ("有机物的官能团", "化学", ["官能团", "有机", "羟基", "羧基"]),
    # 历史
    ("鸦片战争的影响", "历史", ["鸦片战争", "条约", "通商", "主权"]),
    ("辛亥革命的意义", "历史", ["辛亥革命", "孙中山", "清", "共和"]),
    ("新中国成立", "历史", ["新中国", "中华人民共和国", "1949"]),
    # 地理
    ("大气环流的形成", "地理", ["大气环流", "气压", "气流", "风带"]),
    ("板块构造学说", "地理", ["板块", "地壳", "地震", "构造"]),
    # 政治
    ("我国的根本政治制度", "政治", ["人民代表大会", "根本政治制度", "人大"]),
    ("社会主义市场经济", "政治", ["市场经济", "社会主义", "市场"]),
    # 语文
    ("议论文的论证方法", "语文", ["论证", "论点", "论据"]),
    ("文言文虚词的用法", "语文", ["虚词", "之", "而", "以"]),
    # 英语
    ("现在完成时的用法", "英语", ["present perfect", "have", "完成"]),
    ("定语从句", "英语", ["which", "that", "who", "relative"]),
]


def evaluate(collection_name: str, top_k: int = 5, embedder: str = "auto"):
    import chromadb
    from chromadb.utils import embedding_functions

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    embed_fn = None
    if embedder == "st":
        embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
    elif embedder == "bge":
        embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-small-zh-v1.5"
        )

    if embed_fn:
        col = client.get_collection(name=collection_name, embedding_function=embed_fn)
    else:
        col = client.get_collection(name=collection_name)

    total = len(EVAL_SET)
    subject_hits = 0          # top1 学科正确数
    subject_hits_topk = 0     # top_k 任一学科正确数
    keyword_recall = 0        # top_k 命中关键词的查询数
    rr_sum = 0.0              # reciprocal rank 累加
    sim_sum = 0.0
    sim_count = 0

    detail_lines = []

    for query, exp_subject, keywords in EVAL_SET:
        r = col.query(
            query_texts=[query],
            n_results=top_k,
            where={"subject": {"$eq": exp_subject}},
            include=["documents", "metadatas", "distances"],
        )
        docs = r["documents"][0]
        metas = r["metadatas"][0]
        dists = r["distances"][0]

        if not docs:
            detail_lines.append(f"  ✗ [{exp_subject}] {query} -> 无召回")
            continue

        # top1 学科
        if metas[0].get("subject") == exp_subject:
            subject_hits += 1
        if any(m.get("subject") == exp_subject for m in metas):
            subject_hits_topk += 1

        # 关键词命中 + 排名
        hit_rank = 0
        for idx, doc in enumerate(docs):
            if any(kw.lower() in doc.lower() for kw in keywords):
                hit_rank = idx + 1
                break
        if hit_rank > 0:
            keyword_recall += 1
            rr_sum += 1.0 / hit_rank

        # 平均相似度（top1）
        sim_sum += (1.0 - dists[0])
        sim_count += 1

        status = "✓" if hit_rank > 0 else "✗"
        detail_lines.append(
            f"  {status} [{exp_subject}] {query[:20]:20s} "
            f"命中rank={hit_rank if hit_rank else '-'} "
            f"top1相似度={1-dists[0]:.2f} "
            f"-> {metas[0].get('book','')[:18]} p{metas[0].get('page')}"
        )

    print("=" * 70)
    print(f"📊 RAG 检索质量评测  collection={collection_name}  top_k={top_k}  embedder={embedder}")
    print("=" * 70)
    for line in detail_lines:
        print(line)
    print("-" * 70)
    print(f"评测查询数:            {total}")
    print(f"学科准确率@1:          {subject_hits/total*100:.1f}%  ({subject_hits}/{total})")
    print(f"学科准确率@{top_k}:          {subject_hits_topk/total*100:.1f}%  ({subject_hits_topk}/{total})")
    print(f"关键词召回率@{top_k}:        {keyword_recall/total*100:.1f}%  ({keyword_recall}/{total})")
    print(f"MRR（平均倒数排名）:    {rr_sum/total:.3f}")
    print(f"平均 top1 相似度:      {sim_sum/sim_count:.3f}" if sim_count else "N/A")
    print("=" * 70)

    return {
        "subject_acc@1": subject_hits / total,
        "subject_acc@k": subject_hits_topk / total,
        "keyword_recall@k": keyword_recall / total,
        "mrr": rr_sum / total,
        "avg_sim": sim_sum / sim_count if sim_count else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="RAG 检索质量评测")
    parser.add_argument("--collection", default="high_school_textbooks")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--embedder", choices=["auto", "st", "bge"], default="auto",
                        help="auto=默认ONNX / st=多语言 / bge=中文BGE")
    args = parser.parse_args()

    evaluate(args.collection, top_k=args.top_k, embedder=args.embedder)


if __name__ == "__main__":
    main()
