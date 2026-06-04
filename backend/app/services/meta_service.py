"""
应用元信息服务（Meta / Self-Knowledge Service）
================================================
为 AI 问答提供关于"本应用自身"的知识，使得 AI 能够回答诸如：
  - "你都有哪些功能？"
  - "你的知识库中都有哪些科目的教材？"
  - "高一年级数学教材上册中第一章的内容是什么？"

实现方式：
  1. 维护应用功能清单（APP_FEATURES）。
  2. 读取 backend/data/curriculum/*.json 教材目录，生成知识库教材清单与章节目录。
  3. 通过关键词识别"元信息类问题"，并构建注入到 AI System Prompt 的上下文。
"""

import json
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# curriculum JSON 目录
_REPO_ROOT = Path(__file__).parent.parent.parent.parent  # EduBuddy/
CURRICULUM_DIR = _REPO_ROOT / "backend" / "data" / "curriculum"

# 学科英文文件名 -> 中文学科名
SUBJECT_FILE_MAP = {
    "math": "数学", "physics": "物理", "chemistry": "化学",
    "biology": "生物", "chinese": "语文", "english": "英语",
    "history": "历史", "geography": "地理", "politics": "政治",
}

# ---------------------------------------------------------------------------
# 应用功能清单
# ---------------------------------------------------------------------------
APP_FEATURES = [
    {
        "name": "AI 智能问答",
        "desc": "围绕中学各学科进行智能答疑，支持 LaTeX 公式渲染、教材知识库检索（RAG）、配图讲解，"
                "并能回答关于本应用功能与知识库的问题。",
    },
    {
        "name": "作业批改",
        "desc": "上传作业文本或图片（拍照/PDF），AI 自动批改、评分并给出综合评价、错误分析与改进建议。",
    },
    {
        "name": "智能出题 / 练习",
        "desc": "按学科、知识点、难度和题型（单选、多选、填空、判断、简答）自动生成练习题，并支持在线作答与解析。",
    },
    {
        "name": "错题本",
        "desc": "收集来自问答、练习、作业的错题，支持艾宾浩斯遗忘曲线复习提醒与 AI 错题讲解。",
    },
    {
        "name": "学习笔记",
        "desc": "记录与管理学习笔记，支持 AI 总结、提炼知识点、生成知识卡片（Flashcards）。",
    },
    {
        "name": "学习计划",
        "desc": "根据备考学科、考试日期、每日时长和薄弱学科，由 AI 制定个性化的每日学习计划。",
    },
    {
        "name": "学习资料 / 文档分析",
        "desc": "上传学习资料文档，AI 可提取核心知识点、生成摘要或根据资料出题。",
    },
    {
        "name": "学情统计",
        "desc": "可视化展示学习数据，包括练习正确率、错题分布、学科掌握情况等统计信息。",
    },
]


def get_features_text() -> str:
    """返回应用功能清单的文本描述"""
    lines = ["### EduBuddy 应用功能清单"]
    for i, f in enumerate(APP_FEATURES, 1):
        lines.append(f"{i}. **{f['name']}**：{f['desc']}")
    return "\n".join(lines)


class MetaService:
    """应用自身知识服务（懒加载 curriculum JSON）"""

    def __init__(self):
        self._curriculum: Optional[dict] = None  # {subject: data}

    def _load(self) -> dict:
        """加载所有 curriculum JSON 文件"""
        if self._curriculum is not None:
            return self._curriculum

        curriculum = {}
        if CURRICULUM_DIR.exists():
            for json_file in sorted(CURRICULUM_DIR.glob("*.json")):
                # 跳过以 _ 开头的辅助文件（如 _all_textbooks.json）
                if json_file.stem.startswith("_"):
                    continue
                try:
                    with open(json_file, encoding="utf-8") as f:
                        data = json.load(f)
                    subject = data.get("subject") or SUBJECT_FILE_MAP.get(json_file.stem, json_file.stem)
                    curriculum[subject] = data
                except Exception as e:
                    log.warning(f"Meta: 加载 curriculum 文件失败 {json_file.name}: {e}")
        else:
            log.info(f"Meta: curriculum 目录不存在（{CURRICULUM_DIR}）")

        self._curriculum = curriculum
        return curriculum

    def list_subjects(self) -> list[str]:
        """返回知识库中已收录的学科列表"""
        return list(self._load().keys())

    def get_knowledge_base_overview(self) -> str:
        """返回知识库教材总览文本（学科 + 各年级教材册名）"""
        curriculum = self._load()
        if not curriculum:
            return "（当前知识库尚未收录教材目录数据）"

        lines = ["### 教材知识库收录情况"]
        for subject, data in curriculum.items():
            textbook = data.get("textbook", "")
            grades = data.get("grades", {})
            grade_names = "、".join(grades.keys()) if grades else "未知"
            chapter_count = sum(len(ch) for ch in grades.values())
            tb = f"（{textbook}）" if textbook else ""
            lines.append(
                f"- **{subject}**{tb}：覆盖年级 {grade_names}，共约 {chapter_count} 个章节目录"
            )
        return "\n".join(lines)

    def get_curriculum_detail(
        self,
        subject: Optional[str] = None,
        grade: Optional[str] = None,
        max_chars: int = 2500,
    ) -> str:
        """
        返回教材目录详情（章节 + 知识点）。
        可按学科 / 年级过滤；不指定时返回所有已收录学科的目录概览。
        """
        curriculum = self._load()
        if not curriculum:
            return "（当前知识库尚未收录教材目录数据）"

        lines = []
        total = 0
        for subj, data in curriculum.items():
            if subject and subject not in subj and subj not in subject:
                continue
            grades = data.get("grades", {})
            textbook = data.get("textbook", "")
            for g, chapters in grades.items():
                if grade and grade not in g and g not in grade:
                    continue
                header = f"#### {subj}（{textbook}）· {g}"
                lines.append(header)
                total += len(header)
                if not chapters:
                    lines.append("（暂无详细章节目录）")
                    continue
                for chapter, topics in chapters.items():
                    # 过滤无意义的原始文件名章节
                    chapter_line = f"- {chapter}"
                    lines.append(chapter_line)
                    total += len(chapter_line)
                    if topics:
                        for t in topics:
                            topic_line = f"  - {t}"
                            lines.append(topic_line)
                            total += len(topic_line)
                    if total > max_chars:
                        lines.append("……（目录较长，已省略部分内容）")
                        return "\n".join(lines)

        if not lines:
            scope = f"{subject or ''}{grade or ''}".strip()
            return f"（知识库中暂未收录{scope or '相关'}教材的章节目录）"
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 元信息类问题识别
# ---------------------------------------------------------------------------
# 询问应用功能的关键词
_FEATURE_KEYWORDS = [
    "你有哪些功能", "有什么功能", "你能做什么", "你会什么", "你可以做什么",
    "你能干什么", "有哪些功能", "功能有哪些", "你是什么", "你能帮我做什么",
    "怎么用", "如何使用", "使用说明", "介绍一下你", "你叫什么",
]
# 询问知识库 / 教材的关键词
_KB_KEYWORDS = [
    "知识库", "教材", "课本", "有哪些科目", "哪些学科", "哪些教材",
    "收录了", "包含哪些", "目录", "第几章", "第一章", "第二章", "第三章",
    "上册", "下册", "必修", "选择性必修", "章节", "教科书",
]


def detect_meta_intent(question: str) -> dict:
    """
    识别用户问题是否属于"应用元信息"类。
    返回 {"is_feature": bool, "is_kb": bool}
    """
    q = (question or "").strip()
    is_feature = any(k in q for k in _FEATURE_KEYWORDS)
    is_kb = any(k in q for k in _KB_KEYWORDS)
    return {"is_feature": is_feature, "is_kb": is_kb}


def build_meta_context(question: str, subject: Optional[str] = None, grade: Optional[str] = None) -> str:
    """
    根据问题构建注入 AI 的"应用自身知识"上下文。
    若问题不属于元信息类，返回空字符串。
    """
    intent = detect_meta_intent(question)
    if not (intent["is_feature"] or intent["is_kb"]):
        return ""

    parts = []
    if intent["is_feature"]:
        parts.append(get_features_text())

    if intent["is_kb"]:
        # 总览
        parts.append(meta_service.get_knowledge_base_overview())
        # 若问到具体章节/年级，附上目录详情
        detail_triggers = ["第", "章", "目录", "内容是什么", "讲了什么", "包含", "上册", "下册", "必修", "节"]
        if any(t in question for t in detail_triggers):
            detail = meta_service.get_curriculum_detail(subject=subject, grade=grade)
            if detail:
                parts.append("### 相关教材目录详情\n" + detail)

    if not parts:
        return ""

    body = "\n\n".join(parts)
    return (
        "\n\n---\n"
        "## 🧭 关于 EduBuddy 应用自身的信息（用于回答有关本应用功能与知识库的问题）\n\n"
        f"{body}\n"
        "---\n"
        "当用户询问本应用的功能、知识库收录的科目/教材、或教材章节目录时，"
        "请基于以上信息如实、清晰地回答（可用列表整理），不要拒绝这类问题。\n"
    )


# 全局单例
meta_service = MetaService()
