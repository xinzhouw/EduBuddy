import json
from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """你是 EduBuddy，一名专业的中学学科辅导老师。
你只回答与中学数学、物理、化学、生物、语文、英语、历史、地理、政治相关的学习问题。
解题方法必须在中学教学大纲范围内。
对于非学习相关的问题，礼貌拒绝并引导学生回到学习。

解题时请使用以下结构化格式：
【解题思路】
简要描述解题方向和用到的核心知识点。

【详细步骤】
第一步：...
第二步：...

【最终答案】
明确标注最终结果。

【相关知识点】
- 知识点1
- 知识点2

【易错提醒】
提示学生容易犯的错误。"""


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

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
            model="gpt-4o",
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

请以JSON格式返回，格式如下：
{{
  "questions": [
    {{
      "type": "single_choice",
      "content": "题目内容",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "correct_answer": "A",
      "explanation": "解题步骤说明"
    }}
  ]
}}

对于填空题，options为null；对于判断题，options为["正确", "错误"]；对于简答题，options为null。
correct_answer对于单选题为A/B/C/D，多选题为如"AB"，填空题为具体答案，判断题为"正确"或"错误"。"""

        response = await client.chat.completions.create(
            model="gpt-4o",
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
            model="gpt-4o",
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
            model="gpt-4o",
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
            model="gpt-4o",
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
            model="gpt-4o",
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
            model="gpt-4o",
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
            model="gpt-4o",
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
