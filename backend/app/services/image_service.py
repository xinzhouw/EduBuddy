import os
import uuid
import asyncio
import base64
from datetime import datetime
from typing import List, Tuple, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.image import ChatImage
from app.config import settings
from concurrent.futures import ThreadPoolExecutor

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

ALLOWED_TYPES = {"jpg", "jpeg", "png", "pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_MAX_COUNT = 5
UPLOAD_DIR = settings.upload_dir or "./uploads"

# 全局 OCR 实例
_ocr_instance = None
_thread_pool = ThreadPoolExecutor(max_workers=2)


def get_ocr_instance():
    """延迟加载 OCR 实例"""
    global _ocr_instance
    if _ocr_instance is None and PADDLEOCR_AVAILABLE:
        _ocr_instance = PaddleOCR(use_angle_cls=True, lang="ch")
    return _ocr_instance


class ImageService:
    """图片处理服务"""

    async def validate_files(
        self,
        files: List[UploadFile],
        max_count: int = DEFAULT_MAX_COUNT,
        max_size_mb: int = 10,
    ) -> Tuple[bool, Optional[str]]:
        """
        验证上传的文件
        返回：(是否有效, 错误消息)
        """
        if len(files) > max_count:
            return False, f"最多上传 {max_count} 张图片，你上传了 {len(files)} 张"

        max_bytes = max_size_mb * 1024 * 1024
        for file in files:
            # 检查文件名
            if not file.filename:
                return False, "文件名不能为空"

            ext = file.filename.split(".")[-1].lower()
            if ext not in ALLOWED_TYPES:
                return False, f"不支持的文件类型：.{ext}，仅支持 JPG/PNG/PDF"

            # 检查文件大小
            if file.size and file.size > max_bytes:
                size_mb = file.size / (1024 * 1024)
                return False, f"文件过大：{size_mb:.1f}MB，单个文件不超过 {max_size_mb}MB"

        return True, None

    async def save_images(
        self,
        files: List[UploadFile],
        user_id: int,
        session_id: str,
        db: Session,
    ) -> List[str]:
        """
        保存上传的图片到磁盘和数据库
        返回：image_ids 列表
        """
        # 验证
        valid, error = await self.validate_files(files)
        if not valid:
            raise ValueError(error)

        # 创建用户会话目录
        user_session_dir = os.path.join(UPLOAD_DIR, str(user_id), session_id)
        os.makedirs(user_session_dir, exist_ok=True)

        image_ids = []
        timestamp = int(datetime.utcnow().timestamp())

        for idx, file in enumerate(files):
            # 生成唯一的 image_id
            image_id = f"{session_id}_{timestamp}_{idx}"

            # 保存文件到磁盘
            ext = file.filename.split(".")[-1].lower()
            filename = f"{timestamp}_{idx}_{file.filename}"
            file_path = os.path.join(user_session_dir, filename)

            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # 记录到数据库
            relative_path = os.path.join(str(user_id), session_id, filename)
            chat_image = ChatImage(
                id=image_id,
                session_id=session_id,
                user_id=user_id,
                file_path=relative_path,
                original_filename=file.filename,
                file_size=len(content),
                file_type=ext,
                created_at=datetime.utcnow(),
            )
            db.add(chat_image)
            image_ids.append(image_id)

        db.commit()
        return image_ids

    async def extract_with_ocr(self, image_path: str) -> str:
        """
        使用 PaddleOCR 提取图片中的文字

        Args:
            image_path: 图片路径（相对路径）

        Returns:
            提取的文字内容
        """
        if not PADDLEOCR_AVAILABLE:
            return ""

        try:
            # 转为绝对路径
            if not os.path.isabs(image_path):
                image_path = os.path.join(UPLOAD_DIR, image_path)

            if not os.path.exists(image_path):
                return ""

            # 在线程池中执行同步的 OCR 操作
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(_thread_pool, self._run_ocr, image_path)
            return result
        except Exception as e:
            print(f"OCR 失败: {e}")
            return ""

    @staticmethod
    def _run_ocr(image_path: str) -> str:
        """同步的 OCR 执行"""
        try:
            ocr = get_ocr_instance()
            if ocr is None:
                return ""

            result = ocr.ocr(image_path, cls=True)

            # 提取文字（result 是二维列表）
            texts = []
            if result:
                for line in result:
                    for word_info in line:
                        text = word_info[1]
                        texts.append(text)

            return "\n".join(texts) if texts else ""
        except Exception as e:
            print(f"OCR 执行失败: {e}")
            return ""

    async def batch_ocr(self, image_paths: List[str]) -> List[str]:
        """
        并行执行多张图片的 OCR
        """
        tasks = [self.extract_with_ocr(path) for path in image_paths]
        results = await asyncio.gather(*tasks)
        return results

    async def analyze_with_vision(self, image_path: str) -> str:
        """
        使用 GPT-4o Vision API 分析图片

        Args:
            image_path: 图片路径

        Returns:
            图片分析描述
        """
        try:
            from app.services.ai_service import ai_service

            # 转为绝对路径
            if not os.path.isabs(image_path):
                image_path = os.path.join(UPLOAD_DIR, image_path)

            if not os.path.exists(image_path):
                return ""

            # 读取图片并转为 base64
            with open(image_path, "rb") as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")

            # 确定图片类型
            ext = image_path.split(".")[-1].lower()
            mime_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"

            # 调用 Vision API
            response = await ai_service.client.chat.completions.create(
                model=ai_service.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请详细描述这张学科试题图片中的所有内容。包括：题目文字、图表、公式、图像等。要尽可能完整和准确。",
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{image_base64}"},
                            },
                        ],
                    }
                ],
                timeout=30,
            )

            return response.choices[0].message.content
        except asyncio.TimeoutError:
            print("Vision API 超时")
            return ""
        except Exception as e:
            print(f"Vision API 失败: {e}")
            return ""

    async def batch_vision(self, image_paths: List[str]) -> List[str]:
        """
        并行调用 Vision API 分析多张图片
        """
        tasks = [self.analyze_with_vision(path) for path in image_paths]
        results = await asyncio.gather(*tasks)
        return results

    def merge_analysis_results(
        self,
        ocr_results: List[str],
        vision_results: List[str],
    ) -> str:
        """
        融合 OCR 和 Vision API 的结果

        策略：
        1. 如果两者都有，智能合并（优先 Vision，补充 OCR）
        2. 如果仅 OCR 有，使用 OCR
        3. 如果仅 Vision 有，使用 Vision
        4. 都没有，返回空
        """
        merged_parts = []

        for i, (ocr_text, vision_desc) in enumerate(zip(ocr_results, vision_results)):
            ocr_text = ocr_text.strip()
            vision_desc = vision_desc.strip()

            part_number = i + 1

            if vision_desc and ocr_text:
                # 两者都有：Vision 描述为主，OCR 文字为补充
                merged_parts.append(f"【图片 {part_number}】")
                merged_parts.append(f"视觉描述：{vision_desc}")
                merged_parts.append(f"文字内容：{ocr_text}")
            elif vision_desc:
                # 仅 Vision
                merged_parts.append(f"【图片 {part_number}】{vision_desc}")
            elif ocr_text:
                # 仅 OCR
                merged_parts.append(f"【图片 {part_number}】{ocr_text}")

        return "\n\n".join(merged_parts) if merged_parts else ""

    def build_enhanced_prompt(
        self,
        user_question: str,
        merged_analysis: str,
    ) -> str:
        """
        构造增强提示词：原问题 + OCR 文字 + Vision 描述
        """
        enhanced = f"""用户上传了学科试题截图，以下是从截图中提取的内容：

【提取的内容】
{merged_analysis}

【用户的问题】
{user_question}

请根据上述图片内容和用户的问题进行详细解答。
"""
        return enhanced


image_service = ImageService()
