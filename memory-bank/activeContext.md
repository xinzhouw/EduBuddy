# EduBuddy 活跃上下文

## 当前工作焦点
**日期**：2026-06-10  
**阶段**：V1.0 开发阶段 — Bug 修复

## 最新完成的工作（本次）

- **修复学习计划"练习题"内容 LaTeX 未渲染问题**（`frontend/src/views/plan/StudyPlanView.vue`）：
  - **根因**：`StudyPlanView.vue` 练习题面板（`activePanel === 'quiz'`）中，题目内容 `q.question` 和选项 `opt` 使用了 `{{ }}` 纯文本插值，`$...$` LaTeX 语法完全不经过渲染函数处理，直接显示原始文本（如 `$f(x)=\sqrt{x-2}+\dfrac{1}{x-3}$`）。
  - **修复**：
    1. 在 `<script setup>` 中新增 `import { renderLatexOnly } from '@/utils/markdown'`
    2. 题目标题 `{{ q.id }}. {{ q.question }}` → `v-html="\`${q.id}. \` + renderLatexOnly(q.question)"` 并添加 `.latex-content` class
    3. 选项 `{{ opt }}` → `<span class="latex-content" v-html="renderLatexOnly(opt)"></span>`（`<label>` 改为 flex 布局，radio input 保持不变）
  - **影响范围**：仅 `StudyPlanView.vue` 练习题面板的题目和选项渲染，不影响其他功能。
  - **验证**：`vue-tsc --noEmit` 编译 exit code 0；`npm run build` 成功（2.17s）；`docker cp` 热部署到运行中的 `edubuddy-frontend-1` 容器。

- **修复学习计划"AI生成学习内容"的 LaTeX 渲染问题**（`frontend/src/views/plan/StudyPlanView.vue`）：
  - **根因**：`StudyPlanView.vue` 中的 `renderMd` 函数直接使用了 `new MarkdownIt(...)` 简单实例，只能渲染基础 Markdown，**不支持 LaTeX 公式**（`$...$`、`$$...$$`）渲染。
  - **修复**：移除文件内自定义的 `MarkdownIt` 实例和 `renderMd` 函数，改为从 `@/utils/markdown` 导入 `renderMessage`，该函数完整支持 Markdown + KaTeX LaTeX 渲染（含块级 `$$...$$`、行内 `$...$`、公式清洗、SVG 图形等）。
  - **影响范围**：学习内容面板（AI 生成内容展示、流式生成中预览）+ 评判结果面板（评判报告渲染）均通过 `renderMd = renderMessage` 正确渲染 LaTeX。
  - **验证**：`vue-tsc --noEmit` 编译 exit code 0。

## 最新测试结果（2026-06-09）

**`test_new_features.sh` 修复后运行结果：✅ 19/19 全部通过**

| # | 测试项 | 结果 |
|---|--------|------|
| 1 | API 健康检查 | ✅ PASS |
| 2 | 获取用户信息（含grade字段） | ✅ PASS |
| 3 | 更新用户Profile | ✅ PASS |
| 4 | TTS 纯文本提取（中文古诗） | ✅ PASS |
| 4b | TTS 空文本返回错误 | ✅ PASS |
| 4c | TTS 超长文本截断/接受 | ✅ PASS |
| 5 | TTS 文件上传 - 不支持类型返回400 | ✅ PASS |
| 6 | TTS PNG图片OCR返回200 | ✅ PASS |
| 7 | TTS 未登录被拒绝（Not authenticated） | ✅ PASS |
| 8 | 文档列表查询（items/total结构） | ✅ PASS |
| 9 | 作业批改SSE流式响应 | ✅ PASS |
| 10 | 练习题主题识别接口 | ✅ PASS |
| 11 | 学习统计概览 | ✅ PASS |
| 12 | 前端页面HTTP 200 | ✅ PASS |
| 13 | Swagger UI可访问 | ✅ PASS |
| 14 | TTS路由已注册 | ✅ PASS |
| 15a | Advice/today接口 | ✅ PASS |
| 15b | Relations/observers接口 | ✅ PASS |
| 15c | Monitor/students接口（权限控制正常） | ✅ PASS |

> 原脚本4个误判均已修正：7（grep未匹配"Not authenticated"）、8（Python断言逻辑）、15a/b（访问了无子路径的根路由）
> 测试脚本 `test_new_features.sh` 已在测试完成后删除（连同 `/tmp/test_tts.txt`、`/tmp/test_image.png`）

## 最新完成的工作

- **为"AI问答"页面（语文/英语学科）新增语音朗读功能**（`frontend/src/views/ai/AIChatView.vue`）：
  - **触发条件**：仅当当前对话学科为"语文"或"英语"时，AI回复消息的操作按钮区域才显示语音朗读控件（`isTtsSubject` computed）
  - **技术方案**：使用浏览器原生 **Web Speech API（`SpeechSynthesis`）**，无需任何后端改动
  - **新增响应式状态**：
    - `ttsState`（`'idle' | 'playing' | 'paused'`）：当前播放状态
    - `ttsActiveMsgId`：当前正在朗读的消息 id
  - **新增核心函数**：
    - `pickVoice(lang)`：按学科选取语音 —— 语文优先 zh-CN > zh-TW > zh，英语优先 en-US > en-GB > en
    - `msgToPlainText(content)`：将 AI 回复从 Markdown/LaTeX 转为适合朗读的纯文本（块级 `$$...$$` → "数学公式"，行内 `$...$` → "数学公式"，去除 `#` 标题符/加粗斜体/代码块/图片标记等）
    - `startSpeech(msg)`：停止旧朗读 → 纯文本转换 → 创建 `SpeechSynthesisUtterance` → 按学科设置 lang/rate → 绑定 onstart/onpause/onresume/onend/onerror → 开始播放
    - `togglePauseSpeech()`：playing 中暂停 / paused 中继续
    - `stopSpeech()`：停止并重置状态
  - **模板控件**（每条 AI 消息操作栏，`isTtsSubject` 为 true 时渲染）：
    - idle 或非当前消息：`🔊 朗读` 按钮（灰色/靛蓝 hover）
    - playing（当前消息）：4 格动态音频波形（`.tts-wave-bar`）+ `⏸ 暂停`（琥珀色）+ `⏹ 停止`
    - paused（当前消息）：`▶ 继续`（绿色）+ `⏹ 停止` + "⏸ 已暂停" 文字
  - **CSS 动画**：`.tts-wave-bar` + `@keyframes tts-wave`，4 根高度不同、延迟不同的靛蓝色竖条
  - **生命周期**：`onMounted` 中调用 `getVoices()` 预热 + 注册 `voiceschanged` 事件；`onUnmounted` 中调用 `cancel()` 防止资源泄漏
  - `vue-tsc --noEmit` 编译验证通过（exit code 0）

## 最近完成的工作

- **🟡 修复 AI 回答 Markdown/LaTeX 渲染异常**（`frontend/src/utils/markdown.ts`）：
  - **根因3（畸形 `$$` 连锁错位，最终根治）**：从数据库取真实消息（id=53）发现 AI 输出含**奇数个 `$$`（187 个）**和畸形片段 `(n-2)\sqrt5\le a$$\na^2+2a.\n$$`（`$$` 紧贴文字）。朴素逐字符配对发生**连锁角色错位**，把中文段落、甚至已生成的占位符吞进公式，导致**占位符 `\uFFFD…` 泄漏到页面（192 处）**、`a^2+2a` 等裸文本残留、标题/分隔线粘连。**根治方案**（第 1 步重写）：① `1a` 规范化把紧贴文字的 `$$` 前后补换行（`a$$`→`a\n$$`）；② `looksLikeFormula` 加强：含占位符 / 含中文 / 跨空行段落一律拒绝；③ 逐字符配对时若内容不像公式则**整体跳过 2 个 `$`**（而非 1 个），避免畸形 `$$` 被拆成游离单 `$` 污染行内提取；④ 行内 `$...$` 提取限定 `[^$\n\uFFFD]`，绝不吞换行/占位符。**验证**：真实 id=53 消息（含 92 块级 + 43 行内公式）预处理后**占位符泄漏 0、katex-error 0、8 处关键文本全部保留**。
  - **根因2（$$ 配对错位）**：AI 混用行内 `$...$` 与块级 `$$...$$`，奇数个 `$$` 会发生角色错位把中文段落误吞成公式（已被根因3 方案一并根治）。
  - **`cleanFormula` 增强**：除去除孤立反斜杠外，新增 ① 删除公式内残留的 `$`（块级/行内公式内部出现 `$` 必是 AI 畸形输出，如 `(n-2)\sqrt5\le a $ a^2+2a.`，替换为空格后 KaTeX 即可正常渲染）；② 「平衡花括号」兜底——AI 偶尔多写未配对 `}`（如 `\frac1r}.`），从右删除多余 `}` 防止整条公式渲染失败。
  - **`wrapBareLatex` 整行判断放宽**：不含中文且「主要由数字/运算符/上下标构成」的纯数学行（如被 `$$` 拦腰截断后留在公式外的 `a^2+2a.`）也包成 `$$块级`，避免裸文本残留。
  - **`cleanFormula` 处理公式内残留 `$`**：块级/行内公式内部出现的 `$`（AI 把一条公式用多余 `$`/`$$` 拦腰断开，如 `(n-2)\sqrt5\le a $ a^2+2a.`）替换为 LaTeX 中等间隔 `\;`，保留完整内容、用可见间距提示歧义，避免渲染成误导性的粘连 `aa^2`。
  - **🟢 从源头治本：强化后端 `SYSTEM_PROMPT` 公式格式规范**（`backend/app/services/ai_service.py`）：在「输出格式要求」第 2 条中明确：① 一条完整公式必须在一对完整 `$...$`/`$$...$$` 内，禁止中途插入多余 `$`/`$$` 拦腰截断（给出正反示例）；② `$$` 与公式内容同行、内部不换行；③ `$`/`$$` 必须成对偶数闭合，结尾不留孤立 `\` 或多余 `}`；④ 中文句中只用行内 `$...$`。`py_compile` 通过。
  - **本质说明**：截图中的 `aa^2` 等错误根源是 **AI 生成的原始数据本身畸形**（多余 `$$`、重复字符），渲染层只能尽力降级（不崩溃/不泄漏源码/不误导），无法 100% 还原本意；故同步从 prompt 源头约束 AI 规范输出。



  - **根因1（公式内孤立反斜杠）**：从数据库取真实历史消息发现，AI 输出的块级公式里常多写一个**单独成行的孤立反斜杠 `\`**（LaTeX 换行符），如：

    ```
    $$
    \max(b_1-a_1,\; b_2-a_2)\ge \frac{(b_1-a_1)+(b_2-a_2)}{2}
    \
    $$
    ```
    提取 `$$` 时内部换行被压成空格后残留 `...{2} \`，导致 KaTeX 渲染异常、整条公式原样显示（红色）。
  - **新增** `cleanFormula()`：KaTeX 渲染前去除末尾孤立反斜杠 `\\+\s*$` 及夹在空白间的孤立 `\`；`renderFormula()` 统一调用。
  - **新增** `wrapBareLatex()`：对忘记加 `$` 的裸 LaTeX（含整行 `\max(...)\ge\frac{...}`、逗号/分号/末尾反斜杠）自动补 `$...$`/`$$...$$`；逐行处理：不含中文整行→`$$块级`，中英混排→行内片段；遇中文/占位符边界停止。
  - **新增** `normalizeBlockBreaks()`：把挤在行中间的 `## 标题`、` --- ` 分隔线补成独立段落。
  - **接入 `renderMessage()`**：提取 `$$`/`$` → `wrapBareLatex` → 再提取新 `$$`（先块级后行内，避免 `$$` 被行内正则拆分）→ `normalizeBlockBreaks` → markdown-it。
  - **验证**：用 `chat_messages` 真实消息（含孤立 `\`）测试，`cleanFormula` 清理后 KaTeX 渲染成功（7667 字符 HTML，无 error）；多组裸公式/中英混排/挤行用例输出正确；`npm run build` 通过；docker 已重建部署。


- **AI 问答支持"应用元信息"问题（功能/知识库/教材目录）**：

  - **问题**：原 `SYSTEM_PROMPT` 限制 AI 只答学科题，且 RAG 仅检索教材正文向量库，导致"你有哪些功能""知识库有哪些科目教材""高一数学第一章内容"等问题被拒答或答不准。
  - **新增** `backend/app/services/meta_service.py`：
    - `APP_FEATURES` 应用功能清单 + `get_features_text()`
    - `MetaService` 懒加载 `backend/data/curriculum/*.json`（跳过 `_` 前缀辅助文件），提供 `list_subjects()`/`get_knowledge_base_overview()`/`get_curriculum_detail(subject,grade)`
    - `detect_meta_intent(question)` 关键词识别（功能类 / 知识库类）+ `build_meta_context()` 构建注入上下文（非元信息类返回空字符串）
  - **修改** `ai_service.py` 的 `SYSTEM_PROMPT`：明确 AI 可回答"本应用功能/知识库/教材目录"问题，不再拒答
  - **修改** `routers/ai.py` 的 `chat()`：新增 `build_meta_context()` 调用，与 `rag_context` 合并为 `combined_context` 注入；元信息优先
  - **验证**：3 类样例问题均正确注入功能清单/教材总览/章节目录，普通学科题不受影响（上下文为空）；`py_compile` 语法校验通过

- **代码整理（剔除冗余）+ 全功能测试**（详见 `docs/TEST_REPORT.md`）：
  - **删除冗余文件**：`frontend/src/components/HelloWorld.vue` 及其 assets（hero.png/vue.svg/vite.svg）、`public/icons.svg`（脚手架残留）；`backend/app/services/image_search_service.py`（前端已改用 `utils/imageSearch.ts` 浏览器直连，后端服务无调用）；agents 旧版脚本 `download_pdfs.py`/`parse_local_pdfs.py`/`config.py`/`fetch_cdn.py`/`crawler.log`/`cookies.json`；空虚拟环境 `backend/.venv/`（保留有依赖的 `backend/venv/`）
  - **删除死代码**：`ai.py` 的 `/api/ai/search-images` 端点、`wrong_book.py` 的占位 `/api/wrong-book/ocr` 端点、`api/ai.ts` 的 `searchImages()` 和空函数 `createChatStream()`
  - **现代化重构**：`main.py` 弃用的 `@app.on_event("startup")` → `lifespan`；`requirements.txt` 移除未用的 `alembic`、移除有 bug 的 `passlib`
  - **🔴 修复严重 Bug（认证全部 500）**：`bcrypt 5.0.0` 与 `passlib 1.7.4` 不兼容（detect_wrap_bug 抛 ValueError）。新增 `backend/app/security.py` 直接用 bcrypt 实现 `hash_password`/`verify_password`，`auth.py` 改用之，彻底弃用 passlib
  - **🟡 修复 temperature 兼容性**：部分模型网关（Claude/Bedrock via litellm）不接受 temperature 参数返回 400。新增配置 `OPENAI_USE_TEMPERATURE`（默认 true），`ai_service._temp()` 辅助方法按配置决定是否携带，13 处调用全部改用 `**self._temp(x)`
  - **测试结果**：认证 9 用例 ✅、业务 CRUD（笔记/卡片/错题本含艾宾浩斯算法/统计/计划）✅、AI 功能（问答SSE/出题/答题判分/笔记总结/计划生成/作业批改）✅、前端 `vue-tsc` + `npm run build` ✅ 全部通过



- **新增「高中教材 RAG 知识库」完整流水线**（下载教材PDF → 构建向量库 → AI问答RAG增强）：
  - **教材下载** `agents/textbook_crawler/download_all_hs.py`：
    - 从国家中小学智慧教育平台 CDN 直链（`c1.ykt.cbern.com.cn`，**无需登录**）批量下载
    - 覆盖高中 9 大主科（数学/物理/化学/生物/语文/英语/历史/地理/政治），共 **50 本**教材（约 814MB）
    - 按学科分目录存放：`agents/textbook_crawler/cache/pdfs/high_school/{学科}/`
    - 支持 `--subject` 单科下载、`--dry-run` 预览
  - **知识库构建** `agents/textbook_crawler/build_knowledge_base.py`：
    - PyMuPDF 提取 PDF 文本 → 500字符分块（50字符重叠，句子边界切割）→ ChromaDB 向量化存储
    - 支持 3 种 embedding：`default`（ChromaDB自带ONNX all-MiniLM-L6-v2，轻量无需torch）/ `local`（多语言sentence-transformers）/ `openai`
    - 同时从 PDF 内置目录生成 `backend/data/curriculum/{subject}.json` 章节知识点
    - **成果**：14933 条向量记录，存于 `backend/data/knowledge_base/chroma/`（约58MB）
  - **后端 RAG 服务** `backend/app/services/rag_service.py`（新建）：
    - `RAGService` 单例，懒加载 ChromaDB（知识库/chromadb 不存在时优雅降级，不影响后端启动）
    - 核心方法：`retrieve()`（向量检索+学科/年级过滤+相似度阈值0.3）、`build_context_prompt()`（生成注入prompt的教材上下文）、`get_stats()`
    - **关键约定**：embedding 必须与构建时一致（均用默认 ONNX），否则检索错乱
  - **AI 服务集成** `backend/app/services/ai_service.py`：`chat_stream()` 新增 `rag_context` 参数，注入到 System Prompt 末尾
  - **AI 路由集成** `backend/app/routers/ai.py`：
    - `POST /api/ai/chat` 自动调用 `rag_service.build_context_prompt()` 检索教材并注入
    - 新增 `GET /api/ai/knowledge-base/stats`（知识库状态）、`GET /api/ai/knowledge-base/retrieve`（检索预览）
  - **依赖**：`backend/requirements.txt` + `agents/textbook_crawler/requirements.txt` 添加 `chromadb>=0.5.0`、`sentence-transformers>=2.7.0`
  - **.gitignore**：排除 PDF 缓存与 chroma 向量库（体积大）
  - **已知限制**：数学必修第一册等少数 PDF 为扫描版，PyMuPDF 无法提取文本（构建时跳过）；默认 ONNX 是英文模型，中文检索精度有限，可升级 `--embedder local/openai`


- **为"AI批改作业"页面新增语音朗读功能**（`frontend/src/views/homework/HomeworkGradingView.vue`）：
  - 技术方案：使用浏览器原生 **Web Speech API（`SpeechSynthesis`）**，无需任何后端改动
  - **新增响应式状态**：`ttsState`（`'idle' | 'playing' | 'paused'`）
  - **新增核心函数**：
    - `pickChineseVoice()`：从浏览器语音列表中优先选取 zh-CN > zh-TW > zh 语音
    - `reportToPlainText(md)`：将批改报告从 Markdown/LaTeX 格式转为纯文本（去除 `$...$`、`##`、`**`、`` ` `` 等标记，LaTeX 公式替换为"数学公式"口播词）
    - `startSpeech()`：停止旧朗读 → 文本转换 → 创建 `SpeechSynthesisUtterance` → 设置 zh-CN 语音 → 绑定 onstart/onpause/onresume/onend/onerror 回调 → 开始播放
    - `togglePauseSpeech()`：播放中暂停 / 暂停中继续
    - `stopSpeech()`：停止朗读并重置状态
  - **模板改动**：批改报告完成后（`v-else-if="gradingReport"`），在报告内容上方新增"语音朗读工具栏"：
    - idle 状态：`▶ 开始朗读` 按钮（靛蓝色）
    - playing 状态：`⏸ 暂停` 按钮（琥珀色）+ `⏹ 停止` 按钮 + 4 格动态音频波形动画
    - paused 状态：`▶ 继续` 按钮（绿色）+ `⏹ 停止` 按钮 + "⏸ 已暂停" 文字
  - **CSS 动画**：`.tts-bar` + `@keyframes tts-wave`，四个高度不同延迟的竖条模拟音频波形
  - **生命周期**：`onMounted` 中注册 `voiceschanged` 事件缓存中文语音；`onUnmounted` 中调用 `cancel()` 防止资源泄漏
  - TypeScript 编译验证通过（`tsc --noEmit` exit 0）


- **修复页面切换后显示空白问题**（`frontend/src/App.vue`）：
  - **根因**：`App.vue` 使用了 `<Transition name="fade" mode="out-in">` 包装 `<RouterView>`
  - `HomeworkGradingView.vue` 引入了 `import 'mathlive'`（注册 `<math-field>` Web Component）
  - 当用户执行「批改作业 → 导出 PDF（`window.open` 打开新窗口）→ 切换页面」时，mathlive Web Component 在 `disconnectedCallback` 触发额外 DOM 操作，干扰了 Vue `<Transition out-in>` 的 `transitionend` 状态机，导致新页面组件卡在 `opacity: 0`（`fade-enter-from`）状态，视觉上表现为空白页
  - **修复**：移除 `<Transition>` 包装，改用 `<RouterView :key="route.fullPath" />`
  - 使用 `:key="route.fullPath"` 的好处：每次路由变化强制 Vue 完整卸载/重建组件，避免任何过渡动画竞态问题；同时保证带参数路由（如 `/wrong-book/:id`）在参数变化时也能正确刷新
  - TypeScript 编译验证通过（`tsc --noEmit` exit 0）

- **新增题目练习扫描图片/文档输入功能**：
  - **背景**：当题目中含有复杂公式时，手动输入知识点非常困难
  - **后端 `backend/app/services/ai_service.py`**：
    - 新增 `extract_quiz_topic_from_image(image_base64, mime_type)` 方法：将图片 base64 传给 OpenAI Vision API，返回学科、知识点、识别文字、题目数量（JSON）
    - 新增 `extract_quiz_topic_from_pdf(text)` 方法：对 PDF/DOCX 提取的文字调用 AI 分析，返回相同结构
  - **后端 `backend/app/routers/quiz.py`**：
    - 新增 `POST /api/quiz/extract-topic` 接口（`UploadFile`），接受 JPG/PNG/GIF/WebP/PDF/DOCX
    - 图片直接 base64 编码调用 Vision API；PDF/DOCX 先用 `extract_text()` 提取文字再调用 AI
    - 返回 `{ subject, topic, recognized_text, question_count }`
  - **前端 `frontend/src/api/quiz.ts`**：新增 `extractTopicFromFile(file)` 方法（multipart/form-data）
  - **前端 `frontend/src/views/quiz/QuizSetupView.vue`**：
    - 在表单顶部增加「扫描图片/文档」拖拽上传区域
    - 支持点击选择文件和拖拽放入，有识别中动画
    - 识别成功后展示识别到的题目文字、学科、知识点，并自动填入下方表单
    - 支持「重新上传」和「应用到表单」操作

- **修复练习题评判错误 + 新增数学符号输入工具栏**（`frontend/src/views/quiz/QuizSessionView.vue`）：
  - **Bug1 根因**：`selectAnswer()` 原来将完整选项文本（如 `"B. π"`）存入 `answers`，但后端 `correct_answer` 只存字母 `"B"`，导致字符串比较永远不等而判错。
  - **修复**：新增 `extractOptionKey(opt)` 函数，用正则从 `"A. xxx"` / `"A、xxx"` 格式中提取字母；`selectAnswer`、`toggleMultiAnswer`、`isMultiSelected` 及选项高亮 `:class` 均改用此函数，保证前后端答案格式一致。
  - **Bug2 根因**：填空/简答题只有普通 textarea，无法输入数学符号（π、√、²、≥ 等）。
  - **修复**：在 textarea 上方增加「数学符号快捷输入工具栏」，包含 20 个常用符号按钮；点击时通过 `selectionStart/End` 将符号插入光标处，并恢复光标位置。

- **新增 AI 批改作业功能**：
  - 新增数据模型 `backend/app/models/homework.py`（`HomeworkGrading` 表）
  - 在 `backend/app/services/ai_service.py` 新增 `grade_homework()`（流式批改）和 `extract_score_from_report()`（正则提取分数）方法
  - 新增后端路由 `backend/app/routers/homework.py`：
    - `POST /api/homework/grade/text`：文本作业批改（SSE 流式）
    - `POST /api/homework/grade/file`：文件上传批改（PDF/DOCX/图片，SSE 流式）
    - `GET /api/homework/history`：批改历史列表
    - `GET /api/homework/history/{id}`：批改详情
    - `DELETE /api/homework/history/{id}`：删除记录
  - 注册路由到 `backend/app/main.py`，更新 `backend/app/database.py` init_db
  - 前端新增 `frontend/src/api/homework.ts`（REST API + SSE 流式工具函数）
  - 前端新增 `frontend/src/views/homework/HomeworkGradingView.vue`（完整提交+批改报告UI）
  - 前端路由 `/homework` 已注册，侧边栏已添加「✍️ AI 批改作业」入口

- **修复 AI 聊天界面题目显示与 AI 回答格式问题**：
  - 前端安装 `markdown-it`、`@types/markdown-it`、`katex`、`@vscode/markdown-it-katex` 依赖
  - 新建 `frontend/src/utils/markdown.ts`：封装 `renderMessage()` 函数，支持 Markdown + LaTeX（行内 `$...$`、独立块 `$$...$$`）渲染
  - 修改 `frontend/src/views/ai/AIChatView.vue`：
    - AI 回复消息改用 `v-html="renderMessage(msg.content)"` 富文本渲染（原为纯文本 `{{ msg.content }}`）
    - 添加完整的 `.markdown-body` CSS 样式（段落、标题、列表、代码块、引用、KaTeX 公式等）
    - 用户消息保持纯文本 `whitespace-pre-wrap` 显示
  - 修改 `backend/app/services/ai_service.py` 的 `SYSTEM_PROMPT`：
    - 要求 AI 使用 Markdown 格式输出（标题 `##`、加粗、列表）
    - 要求所有数学公式使用 LaTeX 语法（行内 `$...$`、块级 `$$...$$`）
    - 将原【】括号式纯文本结构改为 Markdown 标题结构

## 最近完成的工作（历史）
- 初始化 Memory Bank，创建所有 6 个核心文档文件
- 全面梳理了项目文档（PRD、架构、数据库设计）
- 确认了项目基础架构已搭建完成（前后端脚手架、所有文件骨架）
- **新增 OpenAI 兼容模式支持**：
  - `backend/app/config.py` 新增 `openai_base_url`、`openai_model` 两个配置项
  - `backend/app/services/ai_service.py` 初始化时按需传入 `base_url`，所有 API 调用改用 `self.model`（不再硬编码 `gpt-4o`）
  - `.env` 与 `backend/.env.example` 增加 `OPENAI_BASE_URL`、`OPENAI_MODEL` 示例配置
- **修复 Tailwind CSS v4 样式不生效问题**：
  - 安装 `@tailwindcss/vite` 插件并配置到 `vite.config.ts`
  - 将 `src/style.css` 从 v3 语法（`@tailwind base/components/utilities`）改为 v4 语法（`@import "tailwindcss"`）
  - 将 `tailwind.config.js` 的自定义主题迁移为 `@theme {}` 块写入 CSS
  - 在 `AppSidebar.vue` 和 `DashboardView.vue` 的 `<style scoped>` 块开头加 `@reference` 指令
- **修复 AI 聊天接口 DetachedInstanceError**：
  - `backend/app/routers/ai.py` 的 `chat()` 中，`StreamingResponse` 返回后 SQLAlchemy Session 已关闭
  - 在 `generate()` 调用前提前读取 `user_id = current_user.id` 和 `user_grade = current_user.grade`
  - `generate()` 内部改用这两个局部变量，不再访问 `current_user` 对象
- **修复 docker-compose 找不到根目录 .env 的问题**：
  - `docker-compose.yml` 的 `env_file` 引用了根目录 `.env`，但配置实际在 `backend/.env`
  - 将 `backend/.env` 复制到项目根目录 `.env`

## 项目当前状态摘要

**✅ 环境已成功重建并运行（2026-06-05 验证）**

### Docker 部署状态
- **前端容器**（`edubuddy-frontend:latest`）：✅ 运行中，端口 `:80`，HTTP 200
- **后端容器**（`edubuddy-backend:latest`）：✅ 运行中，端口 `:8001`，HTTP 200
- **API 健康检查**：`GET /` → `{"message":"EduBuddy API is running","version":"1.0.0"}` ✅
- **注册接口**：`POST /api/auth/register` 正常，返回用户信息 ✅
- **登录接口**：`POST /api/auth/login` 正常，返回 JWT Token ✅

### 环境配置
- AI 服务：IBM watsonx.ai 兼容层（Claude claude-opus-4-8，`OPENAI_USE_TEMPERATURE=false`）
- 数据库：SQLite，`backend/data/edubuddy.db`
- Docker 镜像：后端 9.77GB（含 chromadb/sentence-transformers），前端 100MB

### 注意事项
- **企业代理环境**：系统配置了 `http_proxy=http://proxy.us.ibm.com:8080`，curl 访问 localhost 需加 `no_proxy="localhost,127.0.0.1"` 绕过代理；浏览器通常默认不走代理直接访问 localhost
- **注册接口字段**：注册用 `nickname`（不是 `username`），字段为 `{email, password, nickname, grade}`

### 已确认存在的文件
- 后端：所有路由文件、服务文件、ORM 模型、Schema 已创建并运行
- 前端：所有视图页面、API 封装、路由配置、auth store 已创建并构建
- 数据库文件：`backend/data/edubuddy.db` 存在，表结构由 `init_db()` 在启动时自动创建

## 下一步建议

### 优先级 1：核查后端实现
1. 查看 `backend/app/routers/auth.py` — 确认注册/登录接口是否完整
2. 查看 `backend/app/services/ai_service.py` — 确认 OpenAI 调用是否实现
3. 查看 `backend/app/routers/ai.py` — 确认 SSE 流式接口是否实现

### 优先级 2：核查前端实现
1. 查看 `frontend/src/views/auth/LoginView.vue` — 登录页面 UI 是否完整
2. 查看 `frontend/src/views/ai/AIChatView.vue` — AI 问答页面是否实现
3. 查看 `frontend/vite.config.ts` — 确认 API 代理是否配置

### 优先级 3：启动验证
- 尝试启动 Docker Compose 或本地开发环境，验证项目可运行

## 重要模式与偏好

### 代码约定
- 后端 Python 异步优先（`async def`）
- 前端使用 `<script setup lang="ts">` Composition API 语法
- API 统一前缀 `/api/`
- 错误响应统一格式：`{ "code": 400, "message": "...", "data": null }`

### 关键路径
- AI 流式输出：后端 `StreamingResponse` → 前端 `fetch + ReadableStream`
- 用户认证：登录 → JWT Token → localStorage → Axios 请求头
- 错题复习：答题答错 → `wrong_items` 表 → `review_service` 计算下次复习时间

## 活跃决策与注意事项

1. **数据库 `init_db()` vs Alembic**：当前 `main.py` 在 startup 事件调用 `init_db()`，可能是直接 `create_all()` 建表，不需要 Alembic 也能运行
2. **Tailwind CSS v4**：`tailwind.config.js` 存在但 v4 的配置方式可能有变化，样式问题时优先检查此处
3. **后端端口**：Docker 生产环境后端映射到 8001，本地开发是 8000，前端代理配置需要注意区分
4. **SQLite 数据库路径**：Docker 中是 `sqlite:///./data/edubuddy.db`，本地开发路径由 `.env` 决定

## 学到的项目洞察

- 项目文档非常完整和详细，是理解业务逻辑的最佳参考
- 数据库文件 `edubuddy.db` 已存在，说明数据库初始化逻辑可用
- 所有前端视图文件都已存在，需要进一步核查每个文件的完成度
