import json
import re
from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """你是 EduBuddy，一名专业的中学学科辅导老师。
你只回答与中学数学、物理、化学、生物、语文、英语、历史、地理、政治相关的学习问题。
解题方法必须在中学教学大纲范围内。
对于非学习相关的问题，礼貌拒绝并引导学生回到学习。

**输出格式要求（严格遵守）：**
1. 使用 Markdown 格式输出，包括标题（##）、加粗（**...**）、列表（-）等。
2. 所有数学公式必须使用 LaTeX 语法：
   - 行内公式用单美元符号包裹，例如：$x^2 + y^2 = r^2$
   - 独立公式块用双美元符号包裹，例如：$$\\frac{a+b}{2} \\geq \\sqrt{ab}$$
3. 解题时使用以下结构：

## 解题思路
简要描述解题方向和核心知识点。

## 详细步骤
**第一步：** ...

**第二步：** ...

## 最终答案
$$答案的LaTeX公式或文字说明$$

## 相关知识点
- 知识点1
- 知识点2

## 易错提醒
提示学生容易犯的错误。"""


class AIService:
    def __init__(self):
        if settings.openai_api_key:
            kwargs = {"api_key": settings.openai_api_key}
            # 若配置了兼容接口地址则使用，否则使用 OpenAI 官方地址
            if settings.openai_base_url:
                kwargs["base_url"] = settings.openai_base_url
            self.client = AsyncOpenAI(**kwargs)
        else:
            self.client = None
        # 使用配置的模型名，默认 gpt-4o
        self.model = settings.openai_model or "gpt-4o"

    def _get_client(self) -> AsyncOpenAI:
        if not self.client:
            raise ValueError("OpenAI API Key 未配置，请在 .env 中设置 OPENAI_API_KEY")
        return self.client

    async def chat_stream(
        self,
        question: str,
        subject: str,
        grade: str,
        history: list = None,
    ) -> AsyncGenerator[str, None]:
        """流式 AI 问答"""
        client = self._get_client()
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({
            "role": "user",
            "content": f"[学科：{subject}，年级：{grade}]\n{question}"
        })

        stream = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            max_tokens=2000,
            temperature=0.3,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def generate_quiz(
        self,
        subject: str,
        topic: str,
        difficulty: int,
        question_types: list,
        count: int,
        grade: str = "高一",
    ) -> list:
        """生成练习题，返回题目列表"""
        client = self._get_client()
        difficulty_names = {1: "基础", 2: "中等", 3: "困难", 4: "挑战"}
        type_names = {
            "single_choice": "单选题（4个选项A/B/C/D）",
            "multiple_choice": "多选题（4个选项，多个正确答案）",
            "fill_blank": "填空题",
            "true_false": '判断题（答案为"正确"或"错误"）',
            "subjective": "简答/计算题",
        }
        types_str = "、".join([type_names.get(t, t) for t in question_types])

        prompt = f"""请为{grade}学生生成{count}道{subject}学科关于"{topic}"的练习题。
难度：{difficulty_names.get(difficulty, "中等")}
题型：{types_str}

【重要格式要求】
1. 所有数学公式、符号、表达式必须用 LaTeX 语法，并用美元符号包裹：
   - 行内公式：$公式$，例如 $z + \\overline{{z}} = 4$、$\\sin\\theta = \\frac{{3}}{{5}}$
   - 独立公式块：$$公式$$
   - 禁止裸写 LaTeX 命令（如 \\overline{{z}}），必须包在 $...$ 内
2. 选项文本中的数学内容同样必须用 $...$ 包裹，例如 "A. $\\frac{{7}}{{25}}$"

请以JSON格式返回，格式如下：
{{
  "questions": [
    {{
      "type": "single_choice",
      "content": "已知复数 $z$ 满足 $z + \\overline{{z}} = 4$，且 $z\\overline{{z}} = 13$，则 $z = $",
      "options": ["A. $2+3i$", "B. $2-3i$", "C. $3+2i$", "D. $3-2i$"],
      "correct_answer": "A",
      "explanation": "解题步骤说明，公式也用 $...$ 包裹"
    }}
  ]
}}

对于填空题，options为null；对于判断题，options为["正确", "错误"]；对于简答题，options为null。
correct_answer对于单选题为A/B/C/D，多选题为如"AB"，填空题为具体答案，判断题为"正确"或"错误"。"""

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一名专业的中学出题老师，请严格按照JSON格式输出题目。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("questions", [])

    async def explain_wrong_answer(
        self,
        question: str,
        correct_answer: str,
        wrong_answer: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """错题 AI 讲解（流式）"""
        client = self._get_client()
        prompt = f"""请详细讲解以下题目：

题目：{question}
正确答案：{correct_answer}"""
        if wrong_answer:
            prompt += f"\n学生错误答案：{wrong_answer}\n\n请分析错误原因并给出详细讲解。"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        stream = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            max_tokens=1500,
            temperature=0.3,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def summarize_note(self, content: str) -> dict:
        """笔记 AI 总结"""
        client = self._get_client()
        prompt = f"""请对以下笔记内容进行总结，提炼核心知识点：

{content}

请以JSON格式返回：
{{
  "summary": "结构化摘要内容",
  "key_points": ["知识点1", "知识点2", ...]
}}"""
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一名专业的学科教师，擅长提炼知识点。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content)

    async def generate_flashcards(self, content: str, subject: str) -> list:
        """从笔记生成知识卡片"""
        client = self._get_client()
        prompt = f"""请从以下{subject}笔记中提取关键概念，生成5-10张知识卡片：

{content}

请以JSON格式返回：
{{
  "flashcards": [
    {{
      "front": "概念/问题",
      "back": "解释/答案",
      "tags": ["标签1", "标签2"]
    }}
  ]
}}"""
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一名专业的学科教师，擅长制作知识卡片。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("flashcards", [])

    async def generate_study_plan(
        self,
        subjects: list,
        exam_date: str,
        daily_hours: float,
        weak_subjects: list,
        start_date: str,
    ) -> list:
        """生成学习计划，返回按天任务列表"""
        client = self._get_client()
        prompt = f"""请制定一个从{start_date}到{exam_date}的学习计划。

备考学科：{', '.join(subjects)}
每天可学习时长：{daily_hours}小时
薄弱学科（需要重点加强）：{', '.join(weak_subjects) if weak_subjects else '无'}

请以JSON格式返回每天的学习任务：
{{
  "tasks": [
    {{
      "date": "YYYY-MM-DD",
      "subject": "学科",
      "topic": "具体知识点",
      "task_type": "study/practice/review",
      "duration_minutes": 60
    }}
  ]
}}

要求：
1. 合理分配各学科学习时间
2. 薄弱学科多安排练习和复习
3. 考试前一周安排综合复习
4. 每天总时长不超过设定时长
5. 循序渐进，先基础后提高"""

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一名专业的学习规划师，擅长制定备考计划。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("tasks", [])

    async def analyze_document(
        self, text: str, task: str
    ) -> AsyncGenerator[str, None]:
        """文档 AI 分析（流式）"""
        client = self._get_client()
        task_prompts = {
            "extract_key_points": f"请从以下文档中提取核心知识点，以结构化列表形式展示：\n\n{text[:3000]}",
            "summarize": f"请对以下文档生成简洁摘要，包含主要内容和重点：\n\n{text[:3000]}",
            "generate_quiz": f"请根据以下文档内容生成5道练习题（包含答案和解析）：\n\n{text[:3000]}",
        }
        prompt = task_prompts.get(task, task_prompts["summarize"])

        stream = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一名专业的中学学科教师，擅长分析学习资料。"},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            max_tokens=1500,
            temperature=0.3,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def _homework_grading_system_prompt(self, subject: str, grade_level: str) -> str:
        """生成作业批改的系统提示词"""
        grade_context = f"（{grade_level}）" if grade_level else ""
        return f"""你是一位经验丰富的{subject}学科教师，正在批改学生的{subject}作业{grade_context}。
请对提交的作业内容进行全面、专业的批改，严格按照以下 Markdown 格式输出批改报告。

**数学公式格式要求（严格遵守）：**
- 行内公式使用 $...$，例如：$\\sin B = \\frac{{\\sqrt{{21}}}}{{7}}$
- 块级公式使用 $$...$$，且 $$ 必须和公式内容在同一行，例如：$$\\cos B = \\frac{{2\\sqrt{{7}}}}{{7}}$$
- 多步推导每步单独一行，每步用行内公式 $...$ 表示，不要将多步推导放在一个 $$ 块内
- 禁止在 $$ 和 $$ 之间使用换行符

## 📊 综合评分

| 评分维度 | 得分 | 满分 | 说明 |
|---------|------|------|------|
| 知识掌握 | xx | 30 | ... |
| 解题过程 | xx | 30 | ... |
| 答案准确性 | xx | 25 | ... |
| 书写规范 | xx | 15 | ... |

**最终得分：xx / 100 分**

---

## 💬 总体评价

（对整份作业的整体评价，肯定优点，指出主要问题，语气要鼓励性）

---

## ✅ 正确之处

（列出做得好的地方，具体到题目或知识点）

---

## ❌ 错误分析

（逐题或逐点分析错误，给出正确解法）

---

## 📈 改进建议

（提供具体、可操作的学习建议，帮助学生提升）

---

## 🎯 知识点总结

（总结本次作业涉及的核心知识点，以及需要重点复习的内容）

---

注意：
1. 评分要客观公正，符合中学教学评分标准
2. 批改意见要具体、有建设性
3. 数学公式使用 LaTeX 语法（行内 $...$，块级 $$...$$）
4. 语气要鼓励学生，不要打击积极性"""

    async def grade_homework(
        self,
        subject: str,
        grade_level: str,
        content: str,
        file_description: str = "",
    ) -> AsyncGenerator[str, None]:
        """AI 批改作业（文本，流式输出），输出结构化 Markdown 批改报告"""
        client = self._get_client()

        file_ctx = f"\n\n[附件描述/识别内容]：{file_description}" if file_description else ""
        user_content = f"请批改以下{subject}作业：\n\n{content}{file_ctx}"

        stream = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._homework_grading_system_prompt(subject, grade_level)},
                {"role": "user", "content": user_content},
            ],
            stream=True,
            max_tokens=6000,
            temperature=0.2,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def grade_homework_image(
        self,
        subject: str,
        grade_level: str,
        image_base64: str,
        mime_type: str = "image/jpeg",
    ) -> AsyncGenerator[str, None]:
        """AI 批改作业（图片，Vision API，流式输出）"""
        client = self._get_client()

        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_base64}",
                        "detail": "high",
                    },
                },
                {
                    "type": "text",
                    "text": f"请批改图片中的{subject}作业，仔细阅读图片里的所有题目和学生的作答内容，然后给出完整的批改报告。",
                },
            ],
        }

        stream = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._homework_grading_system_prompt(subject, grade_level)},
                user_message,
            ],
            stream=True,
            max_tokens=6000,
            temperature=0.2,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def extract_score_from_report(self, report: str) -> float:
        """从批改报告中提取最终得分（正则解析，无需额外API调用）"""
        # 尝试从 "最终得分：xx / 100 分" 格式中提取
        match = re.search(r'最终得分[：:]\s*(\d+(?:\.\d+)?)\s*/\s*100', report)
        if match:
            score = float(match.group(1))
            return min(100.0, max(0.0, score))
        # 尝试从 "xx/100" 格式中提取
        match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*100\s*分', report)
        if match:
            score = float(match.group(1))
            return min(100.0, max(0.0, score))
        return 0.0

    async def extract_answer_from_image(
        self,
        image_base64: str,
        mime_type: str = "image/jpeg",
        question_content: str = "",
    ) -> dict:
        """使用 Vision API 从图片中识别手写/打印的答案内容，直接返回纯文本（非流式）"""
        client = self._get_client()

        question_ctx = f"\n\n对应的题目内容是：{question_content}" if question_content else ""

        prompt = f"""请仔细、完整地识别这张图片中的所有文字内容。{question_ctx}

要求：
1. 按照图片中文字的顺序和结构，逐行输出所有文字
2. 手写文字尽量准确识别
3. 数学公式和符号用 LaTeX 格式表示（行内用 $...$，独立公式用 $$...$$）
4. 保留原有的段落和换行结构
5. 直接输出识别到的文字内容，不要添加任何解释或说明
6. 如果图片模糊无法识别，只输出：[图片模糊，无法识别]"""

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}",
                                "detail": "high",
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            max_tokens=4000,
            temperature=0.1,
        )
        text = (response.choices[0].message.content or "").strip()
        # 根据文本长度和内容判断置信度
        if not text or text == "[图片模糊，无法识别]":
            confidence = "low"
        elif len(text) < 20:
            confidence = "medium"
        else:
            confidence = "high"
        return {"answer": text, "confidence": confidence}

    async def extract_quiz_topic_from_image(
        self,
        image_base64: str,
        mime_type: str = "image/jpeg",
    ) -> dict:
        """使用 Vision API 从图片中识别题目，提取学科和知识点信息（非流式）"""
        client = self._get_client()

        prompt = """请仔细分析这张图片中的题目或文字内容，完成以下任务：

1. 识别图片中所有文字内容（包括数学公式、符号等）
2. 判断题目所属学科
3. 提取核心知识点

请以 JSON 格式返回：
{
  "subject": "学科名称（从数学/物理/化学/生物/语文/英语/历史/地理/政治中选择最匹配的）",
  "topic": "核心知识点（简洁描述，20字以内）",
  "recognized_text": "图片中识别到的完整文字内容（包含数学公式，用LaTeX格式 $...$）",
  "question_count": 题目数量（整数）
}

注意：
- 数学公式、符号请用 LaTeX 格式书写，如 $x^2$、$\\frac{a}{b}$
- recognized_text 要尽量完整保留题目原文"""

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}",
                                "detail": "high",
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,
            temperature=0.2,
        )
        return json.loads(response.choices[0].message.content)

    async def extract_quiz_topic_from_pdf(
        self,
        text: str,
    ) -> dict:
        """从 PDF/DOCX 提取的文本中识别学科和知识点（非流式）"""
        client = self._get_client()

        prompt = f"""请分析以下从文档中提取的文字内容，完成以下任务：

1. 判断题目所属学科
2. 提取核心知识点
3. 整理题目文字（去除多余空白，保持数学公式格式）

文字内容：
{text[:3000]}

请以 JSON 格式返回：
{{
  "subject": "学科名称（从数学/物理/化学/生物/语文/英语/历史/地理/政治中选择最匹配的）",
  "topic": "核心知识点（简洁描述，20字以内）",
  "recognized_text": "整理后的题目文字内容（数学公式用LaTeX格式 $...$）",
  "question_count": 题目数量（整数）
}}

注意：数学公式、符号请用 LaTeX 格式书写"""

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一名专业的中学学科教师，擅长识别题目类型和知识点。"},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,
            temperature=0.2,
        )
        return json.loads(response.choices[0].message.content)

    async def follow_up_stream(
        self,
        question: str,
        context: str,
        history: list = None,
    ) -> AsyncGenerator[str, None]:
        """追问 AI（流式）"""
        client = self._get_client()
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "assistant", "content": context})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": question})

        stream = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            max_tokens=1000,
            temperature=0.3,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


ai_service = AIService()
