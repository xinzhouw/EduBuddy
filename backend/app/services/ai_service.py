import json
import re
from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()

# RAG 服务（懒加载，知识库不存在时自动降级）
try:
    from app.services.rag_service import rag_service as _rag_service
except Exception:
    _rag_service = None

# 几何作图说明：要求 AI 用标准 SVG 矢量代码绘制几何图形，前端会渲染为清晰图形
GEOMETRY_DRAWING_PROMPT = """
**几何/示意图作图规则（最高优先级，必须严格遵守）：**
当题目涉及任何需要配图的内容（三角形、圆、四边形、立体几何、函数图像、坐标系、向量、
力学受力分析、滑轮/斜面/弹簧装置、电路图等），你必须用「标准 SVG 矢量代码」画出规范、
精确、像教科书/试卷一样的专业插图。

⛔ 绝对禁止：使用 ASCII 字符、+ - | / \\ 等符号拼出的"文本图"、用代码块写文字示意图、
   或用「示意如下」之类配上文字符号画图。任何用纯文本/字符画出的图都不允许。
✅ 唯一允许的画图方式：输出一段 ```svg 代码块。

【SVG 质量与规范要求 —— 请像专业制图一样认真画】
1. 画布要足够大、构图要舒展：viewBox 建议 0 0 400 320 或更大，元素之间留足间距，
   不要把图形挤在角落，整体居中、四周留白均匀。
2. 必须含 xmlns、viewBox、width、height（width/height 与 viewBox 比例一致，建议 width≈360）。
3. **所有箭头（坐标轴、力、向量）必须用 <defs><marker> 定义统一的箭头**，再在 <line>/<path>
   上用 marker-end 引用，禁止用两根斜线手画箭头。箭头大小适中。
4. 线条：主体实线 stroke="#222" stroke-width="2"；辅助线/参考线用 stroke="#888" stroke-dasharray="5 4"。
   不同类别的力/对象可用不同颜色（如重力红、拉力绿、支持力蓝），但保持克制专业。
5. 文字标注 font-size="15" fill="#222"，字母/物理量斜体感可用 font-style="italic"；
   **标注要放在对应元素的外侧、不压线、不互相重叠**，与图形保持 6~10px 间距。
6. 几何精度：直角必须真的是 90° 并用小正方形标记；等腰/相似等关系要在坐标上体现；
   圆用 <circle>/<ellipse>；曲线/弧用 <path>。坐标系画带箭头的 x、y 轴、原点 O 和轴标签。
7. 物理受力图：物体用规整的矩形/圆表示，每个力从作用点出发画一条带箭头的有向线段，
   箭头方向与力的真实方向一致，旁边标注力的符号（如 G、F、N、T、f）。
8. 只允许使用 defs/marker/g/line/polyline/polygon/circle/ellipse/rect/path/text 等基础元素；
   禁止 script、image、foreignObject、外部引用和任何 on* 事件属性。
9. 每道题最多画 1~2 幅必要的图，宁可画得简洁准确，也不要堆砌。

【示例 A：直角三角形 + 勾股定理】
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 300" width="320" height="267">
  <polygon points="80,240 280,240 80,90" fill="#eef4ff" stroke="#222" stroke-width="2"/>
  <rect x="80" y="225" width="15" height="15" fill="none" stroke="#222" stroke-width="1.5"/>
  <text x="62" y="80" font-size="16" fill="#222">A</text>
  <text x="286" y="246" font-size="16" fill="#222">B</text>
  <text x="60" y="256" font-size="16" fill="#222">C</text>
  <text x="178" y="262" font-size="15" fill="#555">a</text>
  <text x="55" y="170" font-size="15" fill="#555">b</text>
  <text x="186" y="158" font-size="15" fill="#555">c</text>
</svg>
```

【示例 B：定滑轮 / 受力分析（带 marker 箭头，物理专业画法）】
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 320" width="340" height="286">
  <defs>
    <marker id="ah" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#222"/>
    </marker>
  </defs>
  <!-- 天花板 -->
  <line x1="40" y1="40" x2="340" y2="40" stroke="#222" stroke-width="3"/>
  <path d="M40,40 l8,-10 M70,40 l8,-10 M100,40 l8,-10 M130,40 l8,-10 M160,40 l8,-10 M190,40 l8,-10 M220,40 l8,-10 M250,40 l8,-10 M280,40 l8,-10 M310,40 l8,-10" stroke="#888" stroke-width="1.5"/>
  <!-- 滑轮 -->
  <line x1="190" y1="40" x2="190" y2="90" stroke="#222" stroke-width="2"/>
  <circle cx="190" cy="120" r="30" fill="#f7f7f7" stroke="#222" stroke-width="2"/>
  <circle cx="190" cy="120" r="3" fill="#222"/>
  <!-- 两侧绳与重物 -->
  <line x1="160" y1="120" x2="160" y2="230" stroke="#222" stroke-width="2"/>
  <line x1="220" y1="120" x2="220" y2="190" stroke="#222" stroke-width="2"/>
  <rect x="135" y="230" width="50" height="40" fill="#eef4ff" stroke="#222" stroke-width="2"/>
  <!-- 重力 G（红，向下） -->
  <line x1="160" y1="270" x2="160" y2="300" stroke="#d33" stroke-width="2" marker-end="url(#ah)"/>
  <text x="166" y="292" font-size="15" fill="#d33">G</text>
  <!-- 拉力 F（绿，向下拉绳） -->
  <line x1="220" y1="190" x2="220" y2="220" stroke="#2a9d4a" stroke-width="2" marker-end="url(#ah)"/>
  <text x="226" y="212" font-size="15" fill="#2a9d4a">F</text>
</svg>
```
"""




SYSTEM_PROMPT = """你是 EduBuddy，一名专业的中学学科辅导老师，同时也是「EduBuddy 学习助手」应用本身的智能助理。


你可以回答以下两类问题：
1. **学科学习问题**：与中学数学、物理、化学、生物、语文、英语、历史、地理、政治相关的学习问题。解题方法必须在中学教学大纲范围内。
2. **关于本应用的问题**：当用户询问"你有哪些功能 / 你能做什么"、"知识库里有哪些科目的教材"、"某年级某学科教材某一章的内容是什么"等关于 EduBuddy 应用功能或教材知识库的问题时，请基于系统提供的「关于 EduBuddy 应用自身的信息」如实、清晰地回答（可用列表整理），不要拒绝这类问题。

对于与学习、与本应用都无关的问题，礼貌拒绝并引导用户回到学习。


**输出格式要求（严格遵守）：**
1. 使用 Markdown 格式输出，包括标题（##）、加粗（**...**）、列表（-）等。
2. 所有数学公式必须使用 LaTeX 语法，并严格遵守以下书写规范（极其重要，违反会导致公式无法正确显示）：
   - 行内公式用一对单美元符号包裹，例如：$x^2 + y^2 = r^2$
   - 独立公式块用一对双美元符号包裹，例如：$$\\frac{a+b}{2} \\geq \\sqrt{ab}$$
   - **一条完整公式必须写在一对完整的 $...$ 或 $$...$$ 之内，绝对不能在公式中途插入多余的 $ 或 $$ 把同一条公式拦腰截断**。
     ✗ 错误示例（一条公式被多余的 $$ 断成两半）：`$$(n-2)\\sqrt5\\le a$$ a^2+2a $$`
     ✓ 正确示例（整条公式在一对 $$ 内）：`$$(n-2)\\sqrt5 \\le a^2+2a$$`
   - **$$ 与公式内容必须写在同一行，$$ 内部不要换行**，例如写成 `$$n \\le \\frac{a^2}{\\sqrt5}+2a+1$$`，不要把 `$$`、公式、`$$` 拆成三行。
   - 每个 $ / $$ 都必须成对闭合，数量必须是偶数；公式结尾不要遗留孤立的反斜杠 `\\` 或多余的右花括号 `}`。
   - 不要在中文句子中间用 $$ 块级公式；行文中的变量/短公式一律用行内 $...$。
3. **图片展示（重要）**：当解释需要配合图片才能更直观时（例如：生物结构、物理装置、化学实验、地理地图、历史文物等），必须在回复中插入图片搜索标记，格式如下：
   - `[[IMAGE:英文搜索关键词]]`
   - 关键词必须是英文，简洁精准，例如：`[[IMAGE:DNA double helix structure]]`、`[[IMAGE:mitosis cell division]]`、`[[IMAGE:human heart anatomy]]`
   - 图片标记可以放在解释段落之后，或专门的"📷 参考图片"章节中
   - 对于纯数学计算题不需要图片；对于有明确结构、形态、过程的概念（生物、物理实验、地理、历史）应主动插入图片
4. 解题时使用以下结构：

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
提示学生容易犯的错误。""" + GEOMETRY_DRAWING_PROMPT + """

**专业学科图表工具（在合适时优先使用，比 SVG 更精确美观）：**
1. 化学方程式 / 化学式：用 LaTeX 的 mhchem 语法 `\\ce{...}` 写在 $...$ 内。
   例如：$\\ce{2H2 + O2 -> 2H2O}$、$\\ce{H2SO4}$、$\\ce{CaCO3 ->[\\Delta] CaO + CO2 ^}$。
   配平、状态符号、沉淀↓、气体↑、可逆 <=> 都用 mhchem 写，不要用普通文字拼。
2. 化学分子结构式：用 ```smiles 代码块，里面只写该物质的 SMILES 字符串（前端会画出结构式）。
   例如苯：
   ```smiles
   c1ccccc1
   ```
   例如乙醇：
   ```smiles
   CCO
   ```
3. 数学函数图像 / 函数草图：用 ```funcplot 代码块，里面写 JSON 配置（前端用专业图表库绘制）。
   - 单条曲线：{"fn": "x^2", "xMin": -5, "xMax": 5, "title": "y = x²"}
   - 多条曲线：{"fns": [{"fn": "sin(x)", "label": "sin x"}, {"fn": "cos(x)", "label": "cos x"}], "xMin": -6.28, "xMax": 6.28}
   - 函数表达式里：用 x 作自变量；^ 表示乘方；支持 sin cos tan ln log sqrt abs exp pi 等；
     不要写 "y="，只写右边表达式。
   例如：
   ```funcplot
   {"fn": "x^2 - 2*x - 3", "xMin": -3, "xMax": 5, "title": "二次函数图像"}
   ```
   仅当需要展示函数形状/交点/单调性等图像信息时才用 funcplot；纯计算不需要。
"""


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
        # 部分模型网关（Claude/Bedrock 等）不接受 temperature 参数
        self.use_temperature = settings.openai_use_temperature

    def _get_client(self) -> AsyncOpenAI:
        if not self.client:
            raise ValueError("OpenAI API Key 未配置，请在 .env 中设置 OPENAI_API_KEY")
        return self.client

    def _temp(self, value: float) -> dict:
        """按配置决定是否携带 temperature 参数（兼容不支持该参数的模型）"""
        return {"temperature": value} if self.use_temperature else {}


    async def chat_stream(
        self,
        question: str,
        subject: str,
        grade: str,
        history: list = None,
        rag_context: str = "",
    ) -> AsyncGenerator[str, None]:
        """流式 AI 问答（支持 RAG 教材上下文注入）"""
        client = self._get_client()
        # 若有 RAG 上下文，追加到 System Prompt 末尾
        system_content = SYSTEM_PROMPT
        if rag_context:
            system_content = SYSTEM_PROMPT + rag_context
        messages = [{"role": "system", "content": system_content}]
        if history:
            messages.extend(history)
        messages.append({
            "role": "user",
            "content": f"[学科：{subject}，年级：{grade}]\n{question}"
        })

        # 使用带「自动续写」的流式输出，避免长回答（含公式/SVG）被 max_tokens 截断
        async for delta in self._stream_with_continuation(
            messages, max_tokens=4000, temperature=0.3
        ):
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
            **self._temp(0.5),
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("questions", [])

    async def _stream_with_continuation(
        self,
        messages: list,
        max_tokens: int = 4000,
        temperature: float = 0.3,
        max_rounds: int = 3,
    ) -> AsyncGenerator[str, None]:
        """
        流式输出，并在因 max_tokens 截断（finish_reason == 'length'）时自动续写，
        直到模型自然结束或达到 max_rounds 轮，避免讲解中途中断。
        """
        client = self._get_client()
        # 拷贝一份消息列表，续写时会把已生成内容追加为 assistant 消息
        msgs = list(messages)
        rounds = 0
        while rounds < max_rounds:
            rounds += 1
            finish_reason = None
            round_text = []
            # 标记本轮 stream 是否因异常（网络中断、网关超时等）提前结束，
            # 以便像 length 截断一样自动续写，避免回答中途丢失
            stream_error = False
            try:
                stream = await client.chat.completions.create(
                    model=self.model,
                    messages=msgs,
                    stream=True,
                    max_tokens=max_tokens,
                    **self._temp(temperature),
                )
                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    choice = chunk.choices[0]
                    delta = choice.delta.content
                    if delta:
                        round_text.append(delta)
                        yield delta
                    if choice.finish_reason:
                        finish_reason = choice.finish_reason
            except Exception:
                # 流式过程中途异常：保留已生成内容，标记为需要续写
                stream_error = True

            generated = "".join(round_text)
            # 正常结束（既不是长度截断，也没有异常）则停止
            if finish_reason != "length" and not stream_error:
                break
            # 若本轮异常发生在尚未产出任何内容时，直接结束避免空转
            if stream_error and not generated:
                break
            # 因长度截断或中途异常：把已生成内容作为上下文，要求模型从断点处无缝继续
            msgs = list(messages) + [
                {"role": "assistant", "content": generated},
                {"role": "user", "content": "请从你上一段被截断的位置继续输出，不要重复已经写过的内容，直接接着写完剩下的部分。"},
            ]


    async def explain_wrong_answer(
        self,
        question: str,
        correct_answer: str,
        wrong_answer: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """错题 AI 讲解（流式，自动续写防中断）"""
        prompt = f"""请详细讲解以下题目：

题目：{question}
正确答案：{correct_answer}"""
        if wrong_answer:
            prompt += f"\n学生错误答案：{wrong_answer}\n\n请分析错误原因并给出详细讲解。"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        async for delta in self._stream_with_continuation(
            messages, max_tokens=4000, temperature=0.3
        ):
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
            **self._temp(0.3),
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
            **self._temp(0.4),
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
            **self._temp(0.4),
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
            **self._temp(0.3),
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
            **self._temp(0.2),
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
            **self._temp(0.2),
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
            **self._temp(0.1),
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
            **self._temp(0.2),
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
            **self._temp(0.2),
        )
        return json.loads(response.choices[0].message.content)

    async def ocr_image_for_reading(
        self,
        image_base64: str,
        mime_type: str = "image/jpeg",
    ) -> dict:
        """使用 Vision API 从图片中识别文字，用于读书郎朗读（返回纯文本，不含LaTeX）"""
        client = self._get_client()

        prompt = """请仔细、完整地识别这张图片中的所有文字内容。

要求：
1. 按照图片中文字的顺序和段落结构，逐段输出所有文字
2. 手写文字尽量准确识别
3. 数学公式和符号用普通文字/汉字描述（例如：x的平方、根号2、分之、等于），不要输出LaTeX代码
4. 保留原有的段落和换行结构
5. 直接输出识别到的文字内容，不要添加任何解释或说明
6. 如果图片中包含图表，用简要文字描述其内容
7. 如果图片模糊无法识别，只输出：[图片模糊，无法识别]"""

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
            **self._temp(0.1),
        )
        text = (response.choices[0].message.content or "").strip()
        return {"text": text}

    async def follow_up_stream(
        self,
        question: str,
        context: str,
        history: list = None,
    ) -> AsyncGenerator[str, None]:
        """追问 AI（流式，自动续写防中断）"""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "assistant", "content": context})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": question})

        async for delta in self._stream_with_continuation(
            messages, max_tokens=3000, temperature=0.3
        ):
            yield delta



ai_service = AIService()
