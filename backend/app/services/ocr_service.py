from typing import List, Dict
import os


class OCRService:
    def __init__(self):
        self.ocr = None
        self._initialized = False
        self._use_tesseract = False

    def _init_ocr(self):
        """延迟初始化OCR（第一次使用时）"""
        if not self._initialized:
            print("正在初始化OCR模型...")

            # 首先尝试 PaddleOCR
            try:
                from paddleocr import PaddleOCR

                os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
                print("尝试初始化 PaddleOCR...")
                self.ocr = PaddleOCR(use_angle_cls=False, lang="ch")
                self._initialized = True
                print("✅ PaddleOCR 初始化成功！")
                return
            except Exception as e:
                print(f"⚠️ PaddleOCR 初始化失败: {str(e)}")
                print("尝试使用 Tesseract 作为备选方案...")

            # 如果 PaddleOCR 失败，使用 Tesseract
            try:
                import pytesseract

                # 检查 tesseract 是否可用
                pytesseract.get_tesseract_version()
                self._use_tesseract = True
                self._initialized = True
                print("✅ Tesseract OCR 初始化成功！")
            except Exception as e:
                print(f"❌ Tesseract 也失败了: {str(e)}")
                raise Exception("无法初始化任何 OCR 引擎")

    def recognize(self, image_path: str) -> List[Dict]:
        """识别图片中的文字"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")

        if not self._initialized:
            self._init_ocr()

        try:
            print(f"开始OCR识别: {image_path}")

            # 检查图片是否可读
            from PIL import Image

            img = Image.open(image_path)
            print(f"图片信息: 格式={img.format}, 尺寸={img.size}, 模式={img.mode}")
            img.close()

            if self._use_tesseract:
                return self._recognize_with_tesseract(image_path)
            else:
                return self._recognize_with_paddleocr(image_path)

        except Exception as e:
            print(f"OCR识别出错: {str(e)}")
            import traceback

            traceback.print_exc()
            return []

    def _recognize_with_paddleocr(self, image_path: str) -> List[Dict]:
        """使用 PaddleOCR 识别"""
        result = self.ocr.ocr(image_path, cls=False)
        print(f"PaddleOCR 原始结果: {result}")

        if not result or not result[0]:
            print("PaddleOCR 未检测到任何文本")
            return []

        text_regions = []
        for idx, line in enumerate(result[0]):
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
                    print(f"检测到文本: {text} (置信度: {confidence:.2f})")
            except Exception as e:
                print(f"解析结果出错: {str(e)}")
                continue

        print(f"共检测到 {len(text_regions)} 个文本区域")
        return text_regions

    def _recognize_with_tesseract(self, image_path: str) -> List[Dict]:
        """使用 Tesseract 识别"""
        import pytesseract
        from PIL import Image
        import cv2
        import numpy as np

        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            print(f"无法读取图片: {image_path}")
            return []

        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 使用 Tesseract 进行 OCR，获取详细信息
        data = pytesseract.image_to_data(
            gray, lang="chi_sim+eng", output_type=pytesseract.Output.DICT
        )

        text_regions = []
        idx = 0

        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])

            # 过滤低置信度和空文本
            if conf > 30 and text:
                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]

                # 创建边界框
                bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
                language = self._detect_language(text)

                text_regions.append(
                    {
                        "id": idx + 1,
                        "bbox": bbox,
                        "text": text,
                        "confidence": conf / 100.0,
                        "language": language,
                        "translated_text": None,
                    }
                )
                idx += 1
                print(f"检测到文本: {text} (置信度: {conf / 100:.2f})")

        print(f"共检测到 {len(text_regions)} 个文本区域")
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
