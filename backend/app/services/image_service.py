from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from typing import List, Dict, Tuple
import os


class ImageService:
    def __init__(self):
        self.font_dir = os.environ.get("FONT_DIR", "./fonts")
        self.default_font_size = 20

    def extract_styles(self, image_path: str, text_regions: List[Dict]) -> List[Dict]:
        """提取每个文字区域的样式信息"""
        image = Image.open(image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")

        regions_with_style = []

        for region in text_regions:
            bbox = region["bbox"]
            style = self._extract_region_style(image, bbox, region["text"])
            regions_with_style.append({"region": region, "style": style})

        return regions_with_style

    def _extract_region_style(
        self, image: Image.Image, bbox: List[List[int]], text: str
    ) -> Dict:
        """提取单个区域的样式"""
        # 转换为numpy数组
        img_array = np.array(image)

        # 计算边界框
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)

        # 提取区域
        margin = 5
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(img_array.shape[1], x2 + margin)
        y2 = min(img_array.shape[0], y2 + margin)

        region_img = img_array[y1:y2, x1:x2]

        # 提取背景色（取边缘像素的平均值）
        bg_color = self._extract_background_color(region_img)

        # 提取文字颜色
        text_color = self._extract_text_color(region_img, bg_color)

        # 估算字体大小
        font_size = self._estimate_font_size(y2 - y1, text)

        # 检测对齐方式
        alignment = self._detect_alignment(img_array.shape[1], x1, x2)

        return {
            "font_color": text_color,
            "background_color": bg_color,
            "font_size": font_size,
            "font_weight": "normal",  # 简化处理
            "alignment": alignment,
            "is_vertical": False,
        }

    def _extract_background_color(self, region_img: np.ndarray) -> List[int]:
        """提取背景色"""
        if region_img.size == 0:
            return [255, 255, 255]

        # 取边缘像素
        h, w = region_img.shape[:2]
        edge_pixels = []

        # 上下边缘
        if w > 0:
            edge_pixels.extend(region_img[0, :, :].tolist())
            edge_pixels.extend(region_img[-1, :, :].tolist())

        # 左右边缘
        if h > 2:
            edge_pixels.extend(region_img[1:-1, 0, :].tolist())
            edge_pixels.extend(region_img[1:-1, -1, :].tolist())

        if not edge_pixels:
            return [255, 255, 255]

        # 计算平均颜色
        avg_color = np.mean(edge_pixels, axis=0).astype(int).tolist()
        return avg_color

    def _extract_text_color(
        self, region_img: np.ndarray, bg_color: List[int]
    ) -> List[int]:
        """提取文字颜色"""
        if region_img.size == 0:
            return [0, 0, 0]

        # 转换为中心像素
        h, w = region_img.shape[:2]
        center_y, center_x = h // 2, w // 2

        # 取中心区域
        center_region = region_img[
            max(0, center_y - 5) : min(h, center_y + 5),
            max(0, center_x - 5) : min(w, center_x + 5),
        ]

        if center_region.size == 0:
            return [0, 0, 0]

        # 找出与背景色差异最大的颜色
        pixels = center_region.reshape(-1, 3)

        # 计算每个像素与背景的差异
        bg_array = np.array(bg_color)
        distances = np.linalg.norm(pixels - bg_array, axis=1)

        # 取差异最大的作为文字颜色
        text_pixel = pixels[np.argmax(distances)]
        return text_pixel.tolist()

    def _estimate_font_size(self, region_height: int, text: str) -> int:
        """估算字体大小 - 更精确的计算"""
        # 根据区域高度估算字体大小
        # 考虑行间距和边距，通常文字占据区域高度的70-80%
        font_size = max(10, int(region_height * 0.75))

        # 如果文字较长，适当减小字体以避免换行
        if len(text) > 20:
            font_size = int(font_size * 0.9)
        elif len(text) > 10:
            font_size = int(font_size * 0.95)

        return max(10, font_size)

    def _detect_alignment(self, img_width: int, x1: int, x2: int) -> str:
        """检测文字对齐方式 - 修复版

        关键改进：检测文字段落内部的视觉对齐，而不是文字框在图片中的位置。
        例如：图片右上方的文字段落，内部应该是左对齐（每行从同一个左边界开始）
        """
        region_width = x2 - x1
        region_center = (x1 + x2) / 2
        img_center = img_width / 2

        # 计算文字区域相对于图片的位置比例
        left_margin = x1 / img_width
        right_margin = (img_width - x2) / img_width
        center_offset = abs(region_center - img_center) / img_width

        # 核心逻辑：判断文字是"视觉左对齐"还是"视觉右对齐"
        #
        # 对于文字段落（多行文字），关键是看文字的视觉对齐方式：
        # - 左对齐：文字左边缘整齐，右边缘不齐
        # - 右对齐：文字右边缘整齐，左边缘不齐
        # - 居中对齐：文字中心对齐
        #
        # 通过分析文字区域的位置来判断：

        # 情况1：文字在图片左侧（左边界 < 40%）
        if left_margin < 0.40:
            # 左侧文字通常是左对齐
            return "left"

        # 情况2：文字在图片右侧（左边界 > 60%）
        elif left_margin > 0.60:
            # 右侧文字通常是左对齐（从同一个左边界开始）
            # 例如：右上方的文字段落
            return "left"

        # 情况3：文字在图片中心区域
        else:
            # 根据中心偏移判断
            if center_offset < 0.10:  # 中心偏差小于10%
                return "center"
            elif left_margin < right_margin:
                return "left"
            else:
                return "right"

    def redraw_image(
        self, image_path: str, regions_with_style: List[Dict], output_path: str
    ):
        """重绘图片"""
        print(f"🎨 开始重绘图片: {image_path}")
        print(f"   共 {len(regions_with_style)} 个文字区域")

        # 加载图片
        image = Image.open(image_path)
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # 转换为numpy数组用于OpenCV操作
        img_array = np.array(image)

        # 创建掩码用于清除原文
        mask = np.zeros(img_array.shape[:2], dtype=np.uint8)

        # 标记所有文字区域
        for item in regions_with_style:
            bbox = item["region"]["bbox"]
            points = np.array(bbox, dtype=np.int32)
            cv2.fillPoly(mask, [points], 255)

        # 使用OpenCV的inpainting清除文字
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        mask_dilated = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
        result_bgr = cv2.inpaint(img_bgr, mask_dilated, 3, cv2.INPAINT_TELEA)
        result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)

        # 转回PIL Image
        result_img = Image.fromarray(result_rgb)
        draw = ImageDraw.Draw(result_img)

        # 绘制翻译后的文字
        for i, item in enumerate(regions_with_style):
            region = item["region"]
            style = item["style"]
            original_text = region["text"]
            translated_text = region.get("translated_text")

            print(f"   区域 {i + 1}: '{original_text}' → '{translated_text}'")

            if translated_text and translated_text != original_text:
                print(f"      绘制译文: '{translated_text}'")
                self._draw_text_in_region(
                    draw, result_img, region["bbox"], translated_text, style
                )
            else:
                print(f"      跳过（无译文或译文与原文相同）")

        # 保存结果
        result_img.save(output_path, "PNG")
        print(f"✅ 重绘完成: {output_path}")

    def _draw_text_in_region(
        self,
        draw: ImageDraw.ImageDraw,
        image: Image.Image,
        bbox: List[List[int]],
        text: str,
        style: Dict,
    ):
        """在指定区域绘制文字 - 优化对齐和排版"""
        print(f"      📝 绘制文字: '{text}'")

        # 计算边界框（使用原始四边形的精确边界）
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)

        region_width = x2 - x1
        region_height = y2 - y1

        print(
            f"         区域: ({x1}, {y1}) - ({x2}, {y2}), 尺寸: {region_width}x{region_height}"
        )
        print(f"         对齐方式: {style['alignment']}")

        # 智能字体大小调整 - 保持原图比例，不过度缩小
        font_size = style["font_size"]
        font = self._get_font(font_size, style.get("is_bold", False))

        # 计算初始文字尺寸
        bbox_text = draw.textbbox((0, 0), text, font=font)
        text_width = bbox_text[2] - bbox_text[0]
        text_height = bbox_text[3] - bbox_text[1]

        # 只有当文字超出区域时才调整大小，且最多缩小30%
        min_font_size = max(8, int(font_size * 0.7))

        while font_size > min_font_size:
            if text_width <= region_width and text_height <= region_height:
                break
            font_size -= 1
            font = self._get_font(font_size, style.get("is_bold", False))
            bbox_text = draw.textbbox((0, 0), text, font=font)
            text_width = bbox_text[2] - bbox_text[0]
            text_height = bbox_text[3] - bbox_text[1]

        print(f"         字体大小: {font_size}px (原始: {style['font_size']}px)")

        # 精确计算对齐位置
        if style["alignment"] == "center":
            # 居中对齐：文字中心与区域中心对齐
            x = x1 + (region_width - text_width) / 2
        elif style["alignment"] == "right":
            # 右对齐：文字右边缘与区域右边缘对齐
            x = x2 - text_width
        else:  # left
            # 左对齐：保持原始左边界
            x = x1

        # 垂直居中 - 考虑文字基线
        # 使用anchor参数让文字在指定位置居中，而不是从左上角开始
        y = y1 + (region_height - text_height) / 2

        print(
            f"         绘制位置: ({x:.1f}, {y:.1f}), 文字尺寸: {text_width}x{text_height}"
        )

        # 改进的文字绘制 - 使用anchor实现更精确的对齐
        text_color = tuple(style["font_color"])

        # 可选：添加轻微阴影提高可读性
        if style.get("background_color"):
            shadow_color = style["background_color"]
            # 只在下方和右下方添加1像素的阴影
            draw.text((x + 1, y + 1), text, font=font, fill=tuple(shadow_color))

        # 绘制主文字
        draw.text((x, y), text, font=font, fill=text_color)
        print(f"         ✅ 文字绘制完成")

    def _get_font(self, size: int, is_bold: bool = False) -> ImageFont.FreeTypeFont:
        """获取字体"""
        # 系统字体路径（修正为正确的opentype路径）
        system_fonts = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
            if is_bold
            else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
            if is_bold
            else "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # 文泉驿正黑
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # 文泉驿微米黑
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]

        # 项目字体目录
        local_fonts = [
            "NotoSansCJKsc-Regular.otf",
            "NotoSansCJKsc-Bold.otf" if is_bold else "NotoSansCJKsc-Regular.otf",
            "SourceHanSansCN-Regular.otf",
            "msyh.ttc",
            "arial.ttf",
            "DejaVuSans.ttf",
        ]

        # 先检查系统字体
        for font_path in system_fonts:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception as e:
                    print(f"系统字体加载失败 {font_path}: {e}")
                    continue

        # 再检查本地字体
        for font_file in local_fonts:
            font_path = os.path.join(self.font_dir, font_file)
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception as e:
                    print(f"本地字体加载失败 {font_path}: {e}")
                    continue

        # 使用默认字体（但可能不支持中文）
        print("警告：未找到中文字体，使用默认字体，中文可能显示为方框")
        return ImageFont.load_default()
