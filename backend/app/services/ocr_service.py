from paddleocr import PaddleOCR
from typing import List, Dict
import os


class OCRService:
    def __init__(self):
        self.ocr = None
        self._initialized = False

    def _init_ocr(self):
        """延迟初始化OCR（第一次使用时）"""
        if not self._initialized:
            print("正在初始化OCR模型...")
            try:
                # 使用最基本的配置
                self.ocr = PaddleOCR(lang="ch")
                self._initialized = True
                print("✅ OCR模型初始化成功！")
            except Exception as e:
                print(f"❌ OCR模型初始化失败: {str(e)}")
                raise

    def recognize(self, image_path: str) -> List[Dict]:
        """识别图片中的文字"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")

        if not self._initialized:
            self._init_ocr()

        try:
            # 执行OCR识别
            result = self.ocr.ocr(image_path)
        except Exception as e:
            print(f"OCR识别出错: {str(e)}")
            return []

        if not result:
            return []

        # 解析结果
        text_regions = []

        # PaddleOCR返回的是列表的列表
        for idx, line in enumerate(result[0] if result else []):
            try:
                if len(line) >= 2:
                    bbox = line[0]
                    text_info = line[1]
                    text = text_info[0]
                    confidence = text_info[1]

                    bbox_int = [[int(x), int(y)] for x, y in bbox]
                    language = self._detect_language(text)

                    text_regions.append(
                        {
                            "id": idx + 1,
                            "bbox": bbox_int,
                            "text": text,
                            "confidence": float(confidence),
                            "language": language,
                            "translated_text": None,
                        }
                    )
            except Exception as e:
                continue

        return text_regions

    def _detect_language(self, text: str) -> str:
        """简单检测文字语言"""
        has_chinese = any("\u4e00" <= char <= "\u9fff" for char in text)
        has_japanese = any(
            "\u3040" <= char <= "\u309f" or "\u30a0" <= char <= "\u30ff"
            for char in text
        )
        has_korean = any("\uac00" <= char <= "\ud7af" for char in text)

        if has_chinese:
            return "zh"
        elif has_japanese:
            return "ja"
        elif has_korean:
            return "ko"
        else:
            return "en"
