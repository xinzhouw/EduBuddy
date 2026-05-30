from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class HomeworkGrading(Base):
    """AI 批改作业记录"""
    __tablename__ = "homework_gradings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 作业基本信息
    title = Column(String(300), nullable=False, default="我的作业")
    subject = Column(String(20), nullable=False)          # 数学/物理/化学/...
    grade_level = Column(String(20), nullable=True)       # 年级（可选）

    # 提交内容
    content_type = Column(String(20), nullable=False)     # 'text'/'image'/'pdf'/'docx'/'audio'
    content_text = Column(Text, nullable=True)            # 文本内容或OCR提取结果
    file_path = Column(String(500), nullable=True)        # 上传文件路径
    file_name = Column(String(300), nullable=True)        # 原始文件名

    # AI 批改结果
    status = Column(String(20), nullable=False, default="pending")  # pending/processing/done/error
    score = Column(Float, nullable=True)                  # 最终分数（0-100）
    score_breakdown = Column(Text, nullable=True)         # JSON: 各维度分数
    overall_comment = Column(Text, nullable=True)         # 总体评价
    detailed_feedback = Column(Text, nullable=True)       # 详细批改意见（Markdown）
    improvement_suggestions = Column(Text, nullable=True) # 改进建议（Markdown）
    error_analysis = Column(Text, nullable=True)          # 错误分析（Markdown）

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    graded_at = Column(DateTime, nullable=True)
