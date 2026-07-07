"""ImageService 单元测试（不依赖 DB / 网络 / OCR 模型）。

async 方法用 asyncio.run 直接驱动，避免依赖 pytest-asyncio。
"""
import asyncio
from io import BytesIO

from fastapi import UploadFile

from app.services.image_service import ImageService


def make_upload(filename: str, size: int) -> UploadFile:
    """构造一个带指定大小的 UploadFile（内容用零字节填充）。"""
    f = UploadFile(file=BytesIO(b"x" * size), filename=filename)
    # Starlette 的 UploadFile.size 在真实请求中由框架填充，测试里手动设置
    f.size = size
    return f


class TestValidateFiles:
    def setup_method(self):
        self.svc = ImageService()

    def test_too_many_files(self):
        files = [make_upload(f"t{i}.jpg", 100) for i in range(6)]
        valid, error = asyncio.run(self.svc.validate_files(files, max_count=5))
        assert valid is False
        assert error and ("最多" in error or "5" in error)

    def test_file_too_large(self):
        files = [make_upload("big.jpg", 11 * 1024 * 1024)]
        valid, error = asyncio.run(self.svc.validate_files(files, max_size_mb=10))
        assert valid is False
        assert error and "过大" in error

    def test_unsupported_type(self):
        files = [make_upload("x.gif", 100)]
        valid, error = asyncio.run(self.svc.validate_files(files))
        assert valid is False
        assert error and "不支持" in error

    def test_missing_filename(self):
        files = [make_upload("", 100)]
        # 空文件名的扩展名判定应失败
        valid, error = asyncio.run(self.svc.validate_files(files))
        assert valid is False

    def test_valid_files_pass(self):
        files = [make_upload("a.jpg", 1024), make_upload("b.PNG", 2048), make_upload("c.pdf", 4096)]
        valid, error = asyncio.run(self.svc.validate_files(files))
        assert valid is True
        assert error is None


class TestMergeAnalysisResults:
    def setup_method(self):
        self.svc = ImageService()

    def test_both_present(self):
        merged = self.svc.merge_analysis_results(
            ocr_results=["文字A"],
            vision_results=["视觉A"],
        )
        assert "【图片 1】" in merged
        assert "视觉A" in merged
        assert "文字A" in merged

    def test_only_vision(self):
        merged = self.svc.merge_analysis_results(["  "], ["只有视觉"])
        assert "只有视觉" in merged
        assert "文字内容" not in merged

    def test_only_ocr(self):
        merged = self.svc.merge_analysis_results(["只有文字"], [""])
        assert "只有文字" in merged

    def test_both_empty(self):
        merged = self.svc.merge_analysis_results([""], ["   "])
        assert merged == ""

    def test_multiple_images_numbered(self):
        merged = self.svc.merge_analysis_results(
            ocr_results=["f1", "f2"],
            vision_results=["v1", "v2"],
        )
        assert "【图片 1】" in merged
        assert "【图片 2】" in merged


class TestBuildImageParts:
    """PDF 必须被渲染为图片块，而非以 image/pdf 直接下发（Vision 无法读取 PDF）。"""

    def setup_method(self):
        self.svc = ImageService()

    def test_png_single_part(self, tmp_path):
        from PIL import Image
        p = tmp_path / "a.png"
        Image.new("RGB", (10, 10), "white").save(p)
        parts = self.svc._build_image_parts(str(p), "png")
        assert len(parts) == 1
        assert parts[0]["image_url"]["url"].startswith("data:image/png;base64,")

    def test_jpg_uses_jpeg_mime(self, tmp_path):
        from PIL import Image
        p = tmp_path / "a.jpg"
        Image.new("RGB", (10, 10), "white").save(p)
        parts = self.svc._build_image_parts(str(p), "jpg")
        assert parts[0]["image_url"]["url"].startswith("data:image/jpeg;base64,")

    def test_pdf_rendered_to_png_parts(self, tmp_path):
        import fitz
        p = tmp_path / "doc.pdf"
        doc = fitz.open()
        doc.new_page().insert_text((72, 100), "hello pdf", fontsize=12)
        doc.new_page().insert_text((72, 100), "page two", fontsize=12)
        doc.save(str(p))
        doc.close()
        parts = self.svc._build_image_parts(str(p), "pdf")
        # 两页 → 两个 PNG 图片块，绝不出现 image/pdf
        assert len(parts) == 2
        for part in parts:
            assert part["image_url"]["url"].startswith("data:image/png;base64,")


class TestBuildEnhancedPrompt:
    def setup_method(self):
        self.svc = ImageService()

    def test_contains_question_and_analysis(self):
        prompt = self.svc.build_enhanced_prompt(
            user_question="这道题怎么做？",
            merged_analysis="【图片 1】视觉描述：二次函数",
        )
        assert "用户上传了学科试题截图" in prompt
        assert "这道题怎么做？" in prompt
        assert "二次函数" in prompt
