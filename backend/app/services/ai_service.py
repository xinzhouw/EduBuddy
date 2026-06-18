import json
import re
import time
import asyncio
from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from httpx import Timeout
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
            # 添加客户端超时配置（连接30s，读取60s，写入10s）
            kwargs["timeout"] = Timeout(timeout=60.0, connect=30.0, read=60.0, write=10.0)
            self.client = AsyncOpenAI(**kwargs)
        else:
            self.client = None
        # 使用配置的模型名，默认 gpt-4o
        self.model = settings.openai_model or "gpt-4o"
        # 部分模型网关（Claude/Bedrock 等）不接受 temperature 参数
        self.use_temperature = settings.openai_use_temperature

        # 简单的速率限制：记录最后一次请求的时间戳
        # 用于防止突发请求导致 API 配额耗尽
        self._last_request_time = 0
        self._min_interval_seconds = 0.1  # 最小请求间隔 100ms

    def _get_client(self) -> AsyncOpenAI:
        if not self.client:
            raise ValueError("OpenAI API Key 未配置，请在 .env 中设置 OPENAI_API_KEY")
        return self.client

    def _temp(self, value: float) -> dict:
        """按配置决定是否携带 temperature 参数（兼容不支持该参数的模型）"""
        return {"temperature": value} if self.use_temperature else {}

    async def _apply_rate_limit(self):
        """简单的速率限制：确保请求之间的最小间隔，防止 API 配额耗尽"""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval_seconds:
            await asyncio.sleep(self._min_interval_seconds - elapsed)
        self._last_request_time = time.time()


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
                # 应用速率限制，防止 API 配额被耗尽
                await self._apply_rate_limit()
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
        import math
        from datetime import date as _date
        client = self._get_client()

        # 计算计划天数，限制每天任务条数，避免输出过长被截断
        try:
            total_days = (_date.fromisoformat(exam_date) - _date.fromisoformat(start_date)).days + 1
        except Exception:
            total_days = 30
        # 每天最多安排的任务数 = 可学习时长 / 每个任务0.75小时，但不超过4条
        tasks_per_day = min(4, max(1, math.floor(daily_hours / 0.75)))
        # 当学科数量多时，建议每天安排2~3个学科交替
        subjects_count = len(subjects)

        prompt = f"""请制定一个从{start_date}到{exam_date}（共{total_days}天）的学习计划。

备考学科（共{subjects_count}科）：{', '.join(subjects)}
每天可学习时长：{daily_hours}小时
薄弱学科（需要重点加强）：{', '.join(weak_subjects) if weak_subjects else '无'}

请以JSON格式返回每天的学习任务：
{{
  "tasks": [
    {{
      "date": "YYYY-MM-DD",
      "subject": "学科名称（必须从备考学科列表中选取，所有{subjects_count}个学科都要覆盖到）",
      "topic": "具体知识点",
      "task_type": "study/practice/review",
      "duration_minutes": 60
    }}
  ]
}}

严格要求：
1. **所有{subjects_count}个学科（{', '.join(subjects)}）都必须出现在计划中，不能遗漏任何一科**
2. 每天安排 {tasks_per_day} 个任务，每个任务 {int(daily_hours * 60 / tasks_per_day)} 分钟左右
3. 轮换安排各学科，确保每个学科在计划期间都有充分的覆盖
4. 薄弱学科多安排练习和复习（task_type 用 practice 或 review）
5. 考试前一周安排综合复习（task_type 用 review）
6. 每天总时长不超过 {int(daily_hours * 60)} 分钟
7. 循序渐进，先基础（study）后提高（practice），再复习（review）
8. 只输出 JSON，不要附加任何说明文字"""

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一名专业的学习规划师，擅长制定备考计划。请严格按照用户要求，确保所有学科都被覆盖到计划中。只输出合法JSON，不要加任何说明文字，不要用代码块包裹。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=8000,
            **self._temp(0.4),
        )
        raw = response.choices[0].message.content or ""
        # 兼容模型在 JSON 外包裹 markdown 代码块的情况
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            raw = raw.strip()
        # 尝试提取第一个完整 JSON 对象（处理模型输出多余前缀的情况）
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            raw = match.group(0)
        try:
            data = json.loads(raw)
        except Exception:
            data = {}
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
            max_tokens=2000,
            **self._temp(0.2),
        )
        raw = (response.choices[0].message.content or "").strip()
        # 兼容模型在 JSON 外包裹 markdown 代码块的情况
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            raw = raw.strip()
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            raw = match.group(0)
        try:
            return json.loads(raw)
        except Exception:
            return {}

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
                {"role": "system", "content": "你是一名专业的中学学科教师，擅长识别题目类型和知识点。只输出合法JSON，不要加任何说明文字，不要用代码块包裹。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            **self._temp(0.2),
        )
        raw = (response.choices[0].message.content or "").strip()
        # 兼容模型在 JSON 外包裹 markdown 代码块的情况
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            raw = raw.strip()
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            raw = match.group(0)
        try:
            return json.loads(raw)
        except Exception:
            return {}

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

    async def generate_daily_advice(self, context: dict) -> list:
        """根据学生学习数据生成每日个性化建议，返回建议列表（3~5条）"""
        client = self._get_client()

        student_info = context.get("student_info", {})
        recent_stats = context.get("recent_stats", {})
        due_reviews = context.get("due_reviews", [])
        prev_outcomes = context.get("previous_advice_outcomes", [])

        prompt = f"""你是一位专业的学习顾问，需要根据学生的学习数据生成今日个性化学习建议。

## 学生信息
- 昵称：{student_info.get('nickname', '同学')}
- 年级：{student_info.get('grade', '未知')}

## 最近学习状况
- 连续打卡天数：{recent_stats.get('streak_days', 0)} 天
- 今日计划完成率：{int(recent_stats.get('today_plan_completion', 0) * 100)}%
- 近3天正确率趋势：{recent_stats.get('recent_accuracy_trend', [])}
- 薄弱学科：{recent_stats.get('weak_subjects', [])}

## 今日到期复习项
{json.dumps(due_reviews, ensure_ascii=False, indent=2) if due_reviews else '无'}

## 昨日建议执行情况
{json.dumps(prev_outcomes, ensure_ascii=False, indent=2) if prev_outcomes else '无历史记录'}

请生成 3~5 条今日学习建议。每条建议必须：
1. 有明确的类型（review_reminder/practice_suggestion/plan_adjustment/achievement/general）
2. 引用具体的教育心理学理论作为依据
3. 措辞积极正向，具体可行

请以 JSON 格式返回：
{{
  "advices": [
    {{
      "id": "adv-001",
      "type": "review_reminder",
      "priority": 1,
      "icon": "📚",
      "title": "建议标题（10字以内）",
      "content": "具体建议内容（50字以内）",
      "action": {{
        "label": "去复习",
        "route": "/wrong-book",
        "params": {{"subject": "数学"}}
      }},
      "theory_basis": "艾宾浩斯遗忘曲线：该知识点距上次学习已7天，正处于遗忘临界期，此时复习效率最高。"
    }}
  ]
}}

建议类型说明：
- review_reminder：有到达复习节点的错题（用艾宾浩斯遗忘曲线理论）
- practice_suggestion：学习时长充足但正确率低（用测试效应理论）
- plan_adjustment：计划完成率持续偏低（用认知负荷理论）
- achievement：连续打卡或正确率提升等正向事件（用自我效能感理论）
- general：通用学习建议（用间隔效应理论）

注意：action 字段可为 null（对于 achievement 类型）"""

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一位专业的教育心理学顾问，精通艾宾浩斯遗忘曲线、间隔效应、测试效应、认知负荷理论和自我效能感理论。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,
            **self._temp(0.5),
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("advices", [])

    async def generate_study_report(
        self,
        student_info: dict,
        stats_30d: dict,
    ) -> AsyncGenerator[str, None]:
        """生成30天学习分析报告（流式输出）"""
        client = self._get_client()

        prompt = f"""请为以下学生生成一份详细的学习分析报告（约500~800字）。

## 学生信息
- 昵称：{student_info.get('nickname', '同学')}
- 年级：{student_info.get('grade', '未知')}

## 近30天学习数据
- 总学习天数：{stats_30d.get('total_study_days', 0)} 天
- 总学习时长：{stats_30d.get('total_study_minutes', 0)} 分钟
- 总答题数：{stats_30d.get('total_questions', 0)} 道
- 平均正确率：{int(stats_30d.get('average_accuracy', 0) * 100)}%
- 各学科正确率：{json.dumps(stats_30d.get('accuracy_by_subject', []), ensure_ascii=False)}
- 各学科学习时长（分钟）：{json.dumps(stats_30d.get('time_by_subject', []), ensure_ascii=False)}
- 错题总数：{stats_30d.get('wrong_book_count', 0)} 道
- 已掌握错题：{stats_30d.get('mastered_count', 0)} 道
- 连续打卡天数：{stats_30d.get('streak_days', 0)} 天
- 番茄钟完成数：{stats_30d.get('pomodoro_count', 0)} 个

请按以下结构输出 Markdown 格式报告：

## 📊 总体评价
（基于数据的整体评估，含量化亮点）

## 🌟 优势学科
（正确率和时长双高的学科，结合布鲁姆教育目标分类说明掌握层次）

## ⚠️ 薄弱环节
（错题集中的知识点分析，结合艾宾浩斯遗忘曲线和测试效应给出改善建议）

## 🔍 学习行为洞察
（专注度、学习时段分布、间隔效应应用情况分析）

## 🎯 未来7天行动建议
（3条具体、可执行的学习建议，每条引用教育心理学理论依据）"""

        stream = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一位专业的教育数据分析师，精通教育心理学理论，擅长用数据洞察学生学习规律并给出有说服力的改进建议。"},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            max_tokens=2000,
            **self._temp(0.4),
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def generate_task_content(
        self,
        subject: str,
        topic: str,
        task_type: str,
        duration_minutes: int,
        grade: str = "高中",
    ) -> AsyncGenerator[str, None]:
        """为学习计划任务 AI 生成学习内容（流式），Markdown 格式"""
        type_names = {"study": "学习", "practice": "练习", "review": "复习"}
        type_label = type_names.get(task_type, "学习")

        prompt = f"""请为{grade}学生生成一份关于「{subject} - {topic}」的{type_label}内容，预计用时 {duration_minutes} 分钟。

要求：
1. 内容结构清晰，使用 Markdown 格式（标题、列表、加粗等）
2. 根据任务类型调整侧重点：
   - study（学习）：系统讲解知识点，包含定义、原理、例题讲解
   - practice（练习）：提供 3~5 道有代表性的练习题，含详细解析
   - review（复习）：知识点梳理回顾 + 易错点总结 + 巩固练习
3. 数学公式使用 LaTeX（行内 $...$，块级 $$...$$）
4. 内容难度符合{grade}水平，时长控制在 {duration_minutes} 分钟内可以完成
5. 最后附上「✅ 学习检验」板块：提出 1~2 个思考问题，供学生自测是否掌握"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        async for delta in self._stream_with_continuation(
            messages, max_tokens=3000, temperature=0.4
        ):
            yield delta

    async def evaluate_submission(
        self,
        subject: str,
        topic: str,
        task_type: str,
        submission_text: str = "",
        image_base64: str = "",
        mime_type: str = "image/jpeg",
    ) -> AsyncGenerator[str, None]:
        """AI 评判用户提交的学习成果（流式），输出结构化 Markdown 评判报告"""
        type_names = {"study": "学习笔记", "practice": "练习作答", "review": "复习成果"}
        type_label = type_names.get(task_type, "学习成果")

        system_prompt = f"""你是一位专业的{subject}学科教师，正在评判学生提交的{type_label}（知识点：{topic}）。
请对提交的内容进行认真、专业的评判，严格按照以下 Markdown 格式输出评判报告。

**数学公式格式要求：** 行内 $...$，块级 $$...$$，$$ 与内容同行不换行。

## 📊 评判结果

**综合得分：xx / 100 分**（掌握程度评定）

| 评判维度 | 得分 | 满分 | 说明 |
|---------|------|------|------|
| 知识点覆盖 | xx | 40 | ... |
| 理解准确性 | xx | 40 | ... |
| 表达清晰度 | xx | 20 | ... |

---

## ✅ 掌握良好
（列出学生正确理解并表达的知识点）

---

## ❌ 需要改进
（指出理解偏差或遗漏的知识点，给出正确说明）

---

## 💡 学习建议
（基于此次提交，给出针对性的下一步学习建议）

---

注意：语气要鼓励，评判要客观，得分要真实反映掌握程度。"""

        if image_base64:
            user_message: dict = {
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
                        "text": f"请评判图片中的{subject}学习成果（知识点：{topic}）。" + (f"\n\n学生还附带了文字说明：\n{submission_text}" if submission_text else ""),
                    },
                ],
            }
        else:
            user_message = {
                "role": "user",
                "content": f"请评判以下{subject}{type_label}（知识点：{topic}）：\n\n{submission_text}",
            }

        client = self._get_client()
        stream = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                user_message,
            ],
            stream=True,
            max_tokens=3000,
            **self._temp(0.2),
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def generate_task_quiz(
        self,
        subject: str,
        topic: str,
        task_type: str,
        grade: str = "高中",
        count: int = 5,
    ) -> AsyncGenerator[str, None]:
        """为学习计划任务 AI 生成练习题（流式），输出 JSON 数组格式"""
        type_names = {"study": "学习", "practice": "练习", "review": "复习"}
        type_label = type_names.get(task_type, "练习")

        prompt = f"""请为{grade}学生生成 {count} 道关于「{subject} - {topic}」的{type_label}练习题。

要求：
1. 题型多样：包含选择题（单选）、填空题、简答题，选择题占 60%
2. 难度适中，符合{grade}水平
3. 数学公式使用 LaTeX（行内 $...$，块级 $$...$$）
4. **必须严格按照以下 JSON 格式输出，不要有任何其他文字，不要有 Markdown 代码块包裹**：

[
  {{
    "id": 1,
    "type": "choice",
    "question": "题目内容",
    "options": ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"],
    "answer": "A",
    "explanation": "解析内容"
  }},
  {{
    "id": 2,
    "type": "fill",
    "question": "题目内容，答案填在___处",
    "answer": "正确答案",
    "explanation": "解析内容"
  }},
  {{
    "id": 3,
    "type": "short",
    "question": "简答题题目",
    "answer": "参考答案",
    "explanation": "评分要点"
  }}
]

type 字段只能是 "choice"（单选）、"fill"（填空）、"short"（简答）之一。
只输出 JSON 数组，不要任何额外说明。"""

        messages = [
            {"role": "system", "content": "你是一位专业的中学学科教师，擅长出题。请严格按照用户要求的 JSON 格式输出练习题，不要有任何额外文字。"},
            {"role": "user", "content": prompt},
        ]
        async for delta in self._stream_with_continuation(
            messages, max_tokens=3000, temperature=0.5
        ):
            yield delta

    async def evaluate_task_quiz(
        self,
        subject: str,
        topic: str,
        questions: list,
        student_answers: dict,
        per_score: float = None,
        obj_scores: dict = None,
    ) -> AsyncGenerator[str, None]:
        """AI 评判学生的练习题答案（流式），输出结构化 Markdown 评判报告"""
        total_q = len(questions) if questions else 1
        # 若调用方未传入 per_score，则自动计算
        if per_score is None:
            per_score = 100.0 / total_q
        if obj_scores is None:
            obj_scores = {}

        # 构建题目和答案对照表，客观题注明已知得分，简答题注明满分供 AI 按要点评分
        qa_lines = []
        for q in questions:
            qid = str(q.get("id", ""))
            qtype = q.get("type", "")
            qtext = q.get("question", "")
            correct = q.get("answer", "")
            student_ans = student_answers.get(qid, "（未作答）")
            type_label = {"choice": "选择题", "fill": "填空题", "short": "简答题"}.get(qtype, "题目")
            score_hint = ""
            if qtype in ("choice", "fill"):
                got = obj_scores.get(qid, 0.0)
                score_hint = f"\n程序化判分：{got:.0f} / {per_score:.0f} 分（已由系统确认，请在表格中如实填写此分数）"
            else:
                score_hint = f"\n满分：{per_score:.0f} 分（请按要点给分，不得超过此满分）"
            qa_lines.append(
                f"【第{qid}题 {type_label}】\n"
                f"题目：{qtext}\n"
                f"参考答案：{correct}\n"
                f"学生答案：{student_ans}\n"
                f"解析提示：{q.get('explanation', '')}"
                f"{score_hint}"
            )

        qa_text = "\n\n".join(qa_lines)

        # 生成表格示例行（帮助 AI 理解格式）
        example_rows = ""
        for q in questions:
            qid = str(q.get("id", ""))
            qtype = q.get("type", "")
            type_label = {"choice": "选择题", "fill": "填空题", "short": "简答题"}.get(qtype, "题目")
            if qtype in ("choice", "fill"):
                got = obj_scores.get(qid, 0.0)
                example_rows += f"| {qid} | {type_label} | {got:.0f} | {per_score:.0f} | 正确/错误 |\n"
            else:
                example_rows += f"| {qid} | {type_label} | （你给的分，≤{per_score:.0f}） | {per_score:.0f} | 部分正确/错误 |\n"

        system_prompt = f"""你是一位专业的{subject}学科教师，正在批改学生的练习题（知识点：{topic}）。
请仔细对比学生答案与参考答案，给出详细评判报告。

**评分规则（必须严格遵守）：**
- 本次共 {total_q} 道题，每题满分 {per_score:.0f} 分，总满分 100 分
- 选择题/填空题：系统已程序化判分，请在表格中原样填写"程序化判分"中的数字，不得修改
- 简答题：按要点给分，给分不得超过该题满分 {per_score:.0f} 分
- 综合得分 = 所有题目得分之和，必须与表格数字完全一致，不得自行重新计算

**数学公式格式要求：** 行内 $...$，块级 $$...$$，$$ 与内容同行不换行。

**输出格式（严格遵守 Markdown，综合得分必须等于表格各题得分之和）：**

## 📊 总体得分

**综合得分：xx / 100 分**

| 题号 | 题型 | 得分 | 满分 | 评价 |
|------|------|------|------|------|
{example_rows}
---

## 📝 逐题解析

### 第1题
- **学生答案**：...
- **参考答案**：...
- **是否正确**：✅ 正确 / ❌ 错误
- **解析**：...

（对每道题重复上述结构）

---

## 💡 总结建议

（根据错题分布，给出针对性的学习建议，不超过3条）

---

注意：综合得分必须严格等于表格各题得分之和，简答题语气鼓励，评判客观。"""

        user_message = {
            "role": "user",
            "content": f"请评判以下{subject}练习题的学生作答情况（知识点：{topic}）：\n\n{qa_text}",
        }

        client = self._get_client()
        stream = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                user_message,
            ],
            stream=True,
            max_tokens=3000,
            **self._temp(0.2),
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
