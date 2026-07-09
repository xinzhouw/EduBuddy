"""
国际化消息服务 (Internationalization Message Service)

提供多语言错误和系统消息支持。
默认语言为中文 (zh)，当 key 或语言不存在时，回退到中文，
若中文也不存在则直接返回 key 本身。
"""

from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    "zh": {
        # --- 认证 / Auth ---
        "INVALID_CREDENTIALS": "邮箱或密码错误",
        "EMAIL_NOT_FOUND": "邮箱不存在",
        "EMAIL_ALREADY_EXISTS": "该邮箱已被注册",
        "PASSWORD_MISSING": "密码参数缺失",
        "PASSWORD_POLICY_VIOLATED": "密码不符合要求",
        "PASSWORD_SAME_AS_OLD": "新密码不能与旧密码相同",
        "OLD_PASSWORD_WRONG": "旧密码错误",
        "USER_DISABLED": "用户不存在或已被禁用",
        "TOKEN_MISSING": "未提供认证令牌",
        "TOKEN_INVALID": "Token无效或已过期",
        "REFRESH_TOKEN_INVALID": "刷新令牌无效或已过期",
        "RATE_LIMIT_EXCEEDED": "请求过于频繁，请稍后重试",
        "LOGIN_SUCCESS": "登录成功",
        # --- 权限 / Permissions ---
        "PERMISSION_DENIED": "权限不足",
        "ADMIN_ONLY": "仅管理员可访问",
        "CANNOT_MODIFY_USER": "无法修改此用户",
        "CANNOT_DELETE_USER": "无法删除此用户",
        # --- 用户 / User ---
        "USER_NOT_FOUND": "用户不存在",
        "LANGUAGE_UPDATED": "语言偏好已更新",
        "INVALID_LANGUAGE": "不支持的语言代码，请使用 zh 或 en",
        # --- 文档 / Documents ---
        "DOCUMENT_NOT_FOUND": "文档不存在",
        "DOCUMENT_CONTENT_EMPTY": "文档内容为空或尚未解析完成",
        "UNSUPPORTED_FILE_TYPE_DOC": "不支持的文件类型，仅支持 PDF、DOCX、JPG、PNG",
        "FILE_TOO_LARGE_DOC": "文件大小超过限制",
        # --- 作业 / Homework ---
        "UNSUPPORTED_SUBJECT": "不支持的学科",
        "HOMEWORK_CONTENT_EMPTY": "作业内容不能为空",
        "HOMEWORK_CONTENT_TOO_LONG": "作业内容过长，请控制在10000字以内",
        "UNSUPPORTED_IMAGE_TYPE": "仅支持图片文件（JPG/PNG/GIF/WebP）",
        "UNSUPPORTED_FILE_TYPE_HW": "不支持的文件类型，请上传 PDF、Word、JPG 或 PNG 文件",
        "IMAGE_READ_FAILED": "图片读取失败",
        "IMAGE_RECOGNITION_FAILED": "图片识别失败",
        "FILE_SAVE_FAILED": "文件保存失败",
        "CORRECTION_NOT_FOUND": "批改记录不存在",
        "CORRECTION_NO_FILE": "该记录无上传文件",
        "FILE_DELETED": "文件已被删除或不存在",
        # --- 笔记 / Notes ---
        "NOTE_NOT_FOUND": "笔记不存在",
        "NOTE_CONTENT_EMPTY": "笔记内容为空",
        # --- 错题 / Wrong Book ---
        "WRONG_QUESTION_NOT_FOUND": "错题不存在",
        # --- 关联 / Relations ---
        "ONLY_STUDENT_CAN_GENERATE_CODE": "只有学生才能生成绑定码",
        "ONLY_TEACHER_OR_PARENT_CAN_USE_CODE": "只有教师或家长才能使用绑定码",
        "BINDING_CODE_INVALID": "绑定码无效或已使用",
        "BINDING_CODE_EXPIRED": "绑定码已过期",
        "ALREADY_BOUND": "已绑定该学生",
        "RELATION_NOT_FOUND": "关联不存在",
        "ONLY_TEACHER_CAN_CREATE_CLASS": "只有教师才能创建班级",
        "ONLY_STUDENT_CAN_JOIN_CLASS": "只有学生才能加入班级",
        "CLASS_INVITE_CODE_INVALID": "班级邀请码无效",
        # --- 学习计划 / Study Plan ---
        "NO_STUDY_PLAN": "暂无学习计划",
        "TODAY_OUT_OF_PLAN_RANGE": "今日不在学习计划时间范围内",
        "NO_TASKS_TODAY": "今日暂无学习任务",
        "TASK_NOT_FOUND": "任务不存在",
        "ONLY_TODAY_TASK_MODIFIABLE": "只能修改当日任务的完成状态，历史任务已归档",
        "ONLY_TODAY_TASK_CAN_GENERATE": "只有当日任务可以生成内容，历史任务已归档只读",
        "ONLY_TODAY_TASK_CAN_SUBMIT": "只有当日任务可以提交，历史任务已归档只读",
        "ONLY_TODAY_TASK_CAN_GENERATE_QUIZ": "只有当日任务可以生成练习题，历史任务已归档只读",
        "ONLY_TODAY_TASK_CAN_SUBMIT_QUIZ": "只有当日任务可以提交练习题，历史任务已归档只读",
        "SUBMIT_REQUIRES_CONTENT": "请提供文字说明或上传图片",
        "QUIZ_NOT_GENERATED": "请先生成练习题",
        "DATA_FORMAT_ERROR": "数据格式错误",
        "PLAN_GENERATION_INVALID": "AI 未能生成有效任务，请检查：①考试日期是否至少在1周后；②备考学科是否已选择",
        "PLAN_SAVE_FAILED": "保存计划时发生错误",
        "TASK_WRITE_FAILED": "写入任务时发生错误",
        # --- AI 对话 / AI Chat ---
        "SESSION_NOT_FOUND": "会话不存在",
        "MESSAGE_NOT_FOUND": "消息不存在",
        "QUERY_EMPTY": "查询内容不能为空",
        "IMAGE_SAVE_FAILED": "图片保存失败",
        "IMAGE_NOT_FOUND": "图片不存在",
        "NO_PERMISSION_DELETE_IMAGE": "无权删除他人的图片",
        # --- TTS ---
        "TTS_TEXT_EMPTY": "文本内容不能为空",
        "TTS_TEXT_TOO_LONG": "文本过长，请控制在 50000 字以内",
        "TTS_UNSUPPORTED_FILE_TYPE": "不支持的文件类型，请上传 PDF、Word、JPG、PNG、GIF 或 WebP 文件",
        "TTS_FILE_TOO_LARGE": "文件过大，请控制在 20MB 以内",
        "TTS_FILE_EMPTY": "文件内容为空",
        "TTS_IMAGE_OCR_FAILED": "图片文字识别失败",
        "TTS_IMAGE_NO_TEXT": "图片中未识别到可朗读的文字内容",
        "TTS_PDF_OCR_FAILED": "该 PDF 为扫描/图片型文件，OCR 识别失败",
        "TTS_PDF_OCR_NO_TEXT": "该 PDF 为扫描/图片型文件，OCR 未能识别出任何文字内容",
        "TTS_FILE_EXTRACT_FAILED": "文件文字提取失败",
        # --- 测验 / Quiz ---
        "QUIZ_IMAGE_ONLY": "答案识别仅支持图片格式（JPG、PNG、GIF、WebP）",
        "QUIZ_IMAGE_TOO_LARGE": "图片大小超过限制（最大 10MB）",
        "QUIZ_AI_FAILED": "AI 识别失败",
        "QUIZ_UNSUPPORTED_FILE": "不支持的文件类型，请上传 JPG、PNG、PDF 或 Word 文件",
        "QUIZ_FILE_TOO_LARGE": "文件大小超过限制（最大 10MB）",
        "QUIZ_PDF_OCR_FAILED": "扫描版PDF识别失败",
        "QUIZ_FILE_EXTRACT_FAILED": "文件内容提取失败，请确认文件包含可读文字，或改用图片格式上传",
        "QUIZ_SESSION_NOT_FOUND": "练习会话不存在",
        "QUIZ_ALREADY_SUBMITTED": "练习已提交",
        # --- 建议 / Advice ---
        "ADVICE_NOT_FOUND": "建议不存在",
    },
    "en": {
        # --- 认证 / Auth ---
        "INVALID_CREDENTIALS": "Invalid email or password",
        "EMAIL_NOT_FOUND": "Email not found",
        "EMAIL_ALREADY_EXISTS": "This email is already registered",
        "PASSWORD_MISSING": "Password parameter is missing",
        "PASSWORD_POLICY_VIOLATED": "Password does not meet requirements",
        "PASSWORD_SAME_AS_OLD": "New password cannot be the same as the old password",
        "OLD_PASSWORD_WRONG": "Old password is incorrect",
        "USER_DISABLED": "User does not exist or has been disabled",
        "TOKEN_MISSING": "Authentication token not provided",
        "TOKEN_INVALID": "Token is invalid or has expired",
        "REFRESH_TOKEN_INVALID": "Refresh token is invalid or has expired",
        "RATE_LIMIT_EXCEEDED": "Too many requests, please try again later",
        "LOGIN_SUCCESS": "Login successful",
        # --- 权限 / Permissions ---
        "PERMISSION_DENIED": "Insufficient permissions",
        "ADMIN_ONLY": "Admin access only",
        "CANNOT_MODIFY_USER": "Cannot modify this user",
        "CANNOT_DELETE_USER": "Cannot delete this user",
        # --- 用户 / User ---
        "USER_NOT_FOUND": "User not found",
        "LANGUAGE_UPDATED": "Language preference updated",
        "INVALID_LANGUAGE": "Unsupported language code, please use zh or en",
        # --- 文档 / Documents ---
        "DOCUMENT_NOT_FOUND": "Document not found",
        "DOCUMENT_CONTENT_EMPTY": "Document content is empty or not yet parsed",
        "UNSUPPORTED_FILE_TYPE_DOC": "Unsupported file type; only PDF, DOCX, JPG, PNG are allowed",
        "FILE_TOO_LARGE_DOC": "File size exceeds the limit",
        # --- 作业 / Homework ---
        "UNSUPPORTED_SUBJECT": "Unsupported subject",
        "HOMEWORK_CONTENT_EMPTY": "Homework content cannot be empty",
        "HOMEWORK_CONTENT_TOO_LONG": "Homework content is too long; please keep it under 10000 characters",
        "UNSUPPORTED_IMAGE_TYPE": "Only image files are supported (JPG/PNG/GIF/WebP)",
        "UNSUPPORTED_FILE_TYPE_HW": "Unsupported file type; please upload PDF, Word, JPG, or PNG",
        "IMAGE_READ_FAILED": "Failed to read image",
        "IMAGE_RECOGNITION_FAILED": "Image recognition failed",
        "FILE_SAVE_FAILED": "Failed to save file",
        "CORRECTION_NOT_FOUND": "Correction record not found",
        "CORRECTION_NO_FILE": "No uploaded file for this record",
        "FILE_DELETED": "File has been deleted or does not exist",
        # --- 笔记 / Notes ---
        "NOTE_NOT_FOUND": "Note not found",
        "NOTE_CONTENT_EMPTY": "Note content is empty",
        # --- 错题 / Wrong Book ---
        "WRONG_QUESTION_NOT_FOUND": "Wrong question not found",
        # --- 关联 / Relations ---
        "ONLY_STUDENT_CAN_GENERATE_CODE": "Only students can generate binding codes",
        "ONLY_TEACHER_OR_PARENT_CAN_USE_CODE": "Only teachers or parents can use binding codes",
        "BINDING_CODE_INVALID": "Binding code is invalid or has been used",
        "BINDING_CODE_EXPIRED": "Binding code has expired",
        "ALREADY_BOUND": "Already bound to this student",
        "RELATION_NOT_FOUND": "Relation not found",
        "ONLY_TEACHER_CAN_CREATE_CLASS": "Only teachers can create classes",
        "ONLY_STUDENT_CAN_JOIN_CLASS": "Only students can join classes",
        "CLASS_INVITE_CODE_INVALID": "Class invite code is invalid",
        # --- 学习计划 / Study Plan ---
        "NO_STUDY_PLAN": "No study plan found",
        "TODAY_OUT_OF_PLAN_RANGE": "Today is outside the study plan date range",
        "NO_TASKS_TODAY": "No study tasks for today",
        "TASK_NOT_FOUND": "Task not found",
        "ONLY_TODAY_TASK_MODIFIABLE": "Only today's tasks can be modified; historical tasks are archived",
        "ONLY_TODAY_TASK_CAN_GENERATE": "Only today's tasks can generate content; historical tasks are archived",
        "ONLY_TODAY_TASK_CAN_SUBMIT": "Only today's tasks can be submitted; historical tasks are archived",
        "ONLY_TODAY_TASK_CAN_GENERATE_QUIZ": "Only today's tasks can generate quizzes; historical tasks are archived",
        "ONLY_TODAY_TASK_CAN_SUBMIT_QUIZ": "Only today's tasks can submit quizzes; historical tasks are archived",
        "SUBMIT_REQUIRES_CONTENT": "Please provide a text description or upload an image",
        "QUIZ_NOT_GENERATED": "Please generate a quiz first",
        "DATA_FORMAT_ERROR": "Data format error",
        "PLAN_GENERATION_INVALID": "AI failed to generate valid tasks. Check: ① Is the exam date at least 1 week away? ② Have study subjects been selected?",
        "PLAN_SAVE_FAILED": "An error occurred while saving the plan",
        "TASK_WRITE_FAILED": "An error occurred while writing tasks",
        # --- AI 对话 / AI Chat ---
        "SESSION_NOT_FOUND": "Session not found",
        "MESSAGE_NOT_FOUND": "Message not found",
        "QUERY_EMPTY": "Query content cannot be empty",
        "IMAGE_SAVE_FAILED": "Failed to save image",
        "IMAGE_NOT_FOUND": "Image not found",
        "NO_PERMISSION_DELETE_IMAGE": "No permission to delete another user's image",
        # --- TTS ---
        "TTS_TEXT_EMPTY": "Text content cannot be empty",
        "TTS_TEXT_TOO_LONG": "Text is too long; please keep it under 50000 characters",
        "TTS_UNSUPPORTED_FILE_TYPE": "Unsupported file type; please upload PDF, Word, JPG, PNG, GIF, or WebP",
        "TTS_FILE_TOO_LARGE": "File is too large; please keep it under 20MB",
        "TTS_FILE_EMPTY": "File content is empty",
        "TTS_IMAGE_OCR_FAILED": "Image text recognition failed",
        "TTS_IMAGE_NO_TEXT": "No readable text recognized in the image",
        "TTS_PDF_OCR_FAILED": "This PDF is a scanned/image-based file; OCR recognition failed",
        "TTS_PDF_OCR_NO_TEXT": "This PDF is a scanned/image-based file; OCR found no text",
        "TTS_FILE_EXTRACT_FAILED": "Failed to extract text from file",
        # --- 测验 / Quiz ---
        "QUIZ_IMAGE_ONLY": "Answer recognition only supports image formats (JPG, PNG, GIF, WebP)",
        "QUIZ_IMAGE_TOO_LARGE": "Image size exceeds the limit (max 10MB)",
        "QUIZ_AI_FAILED": "AI recognition failed",
        "QUIZ_UNSUPPORTED_FILE": "Unsupported file type; please upload JPG, PNG, PDF, or Word",
        "QUIZ_FILE_TOO_LARGE": "File size exceeds the limit (max 10MB)",
        "QUIZ_PDF_OCR_FAILED": "Scanned PDF recognition failed",
        "QUIZ_FILE_EXTRACT_FAILED": "Failed to extract file content; please ensure the file contains readable text or use an image format",
        "QUIZ_SESSION_NOT_FOUND": "Quiz session not found",
        "QUIZ_ALREADY_SUBMITTED": "Quiz has already been submitted",
        # --- 建议 / Advice ---
        "ADVICE_NOT_FOUND": "Advice not found",
    },
}


def get_message(key: str, language: str = "zh") -> str:
    """根据 key 和 language 获取本地化消息字符串。

    回退策略：
    1. 尝试 MESSAGES[language][key]
    2. 回退到 MESSAGES['zh'][key]
    3. 直接返回 key 本身

    Args:
        key: 消息键，例如 'INVALID_CREDENTIALS'
        language: 语言代码，例如 'zh' 或 'en'，默认 'zh'

    Returns:
        对应语言的消息字符串，或回退值
    """
    return (
        MESSAGES.get(language, {}).get(key)
        or MESSAGES.get("zh", {}).get(key)
        or key
    )
