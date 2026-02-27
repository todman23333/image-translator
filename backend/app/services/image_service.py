from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from typing import List, Dict, Tuple
import os
import re


class ImageService:
    def __init__(self):
        self.font_dir = os.environ.get("FONT_DIR", "./fonts")
        self.default_font_size = 20

        # 修复4: 专业术语词典
        self.terminology_dict = {
            # 光伏/电力领域
            " photovoltaic": "光伏",
            "power generation": "发电",
            "power generation curve": "发电曲线",
            "household appliance": "家用电器",
            "power consumption": "耗电量",
            "power consumption curve": "耗电曲线",
            "the load": "负载",
            "draws power": "取电",
            "draws power from": "从...取电",
            "battery pack": "电池包",
            "power grid": "电网",
            "purchases electricity": "买电",
            "purchases electricity from": "从...买电",
            "charges": "充电",
            "charging": "充电中",
            "discharging": "放电中",
            "standby": "待机",
            "grid input power": "电网输入功率",
            "sell to the grid": "卖给电网",
            "electricity": "电能",
            "curve": "曲线",
            "period": "时段",
            "charging period": "充电时段",
            "discharge period": "放电时段",
            "non-charging and non-discharging period": "非充非放时段",
        }

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
        img_array = np.array(image)

        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)

        margin = 3
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(img_array.shape[1], x2 + margin)
        y2 = min(img_array.shape[0], y2 + margin)

        region_img = img_array[y1:y2, x1:x2]

        bg_color = self._extract_background_color(region_img)
        text_color = self._extract_text_color(region_img, bg_color)
        font_size = self._estimate_font_size(y2 - y1, text)

        # 修复3: 改进对齐检测
        alignment = self._detect_alignment_v2(
            img_array.shape[1], img_array.shape[0], x1, x2, y1, y2, text
        )

        # 修复5: 检测是否为图例区域
        is_legend = self._detect_legend_region(img_array.shape[1], x1, x2, y1, y2)

        return {
            "font_color": text_color,
            "background_color": bg_color,
            "font_size": font_size,
            "font_weight": "normal",
            "alignment": alignment,
            "is_vertical": False,
            "is_legend": is_legend,
            "bbox": [x1, y1, x2, y2],
        }

    def _extract_background_color(self, region_img: np.ndarray) -> List[int]:
        """提取背景色 - 改进版"""
        if region_img.size == 0:
            return [255, 255, 255]

        h, w = region_img.shape[:2]

        # 修复2: 使用更大范围的边缘采样
        edge_pixels = []

        # 上下边缘（采样更多点）
        if w > 0:
            for i in range(0, w, max(1, w // 20)):  # 采样20个点
                edge_pixels.append(region_img[0, i, :].tolist())
                edge_pixels.append(region_img[-1, i, :].tolist())

        # 左右边缘
        if h > 2:
            for i in range(0, h, max(1, h // 10)):
                edge_pixels.append(region_img[i, 0, :].tolist())
                edge_pixels.append(region_img[i, -1, :].tolist())

        if not edge_pixels:
            return [255, 255, 255]

        # 使用聚类找出主要背景色
        edge_pixels_array = np.array(edge_pixels)

        # 简单的众数计算
        unique_colors, counts = np.unique(edge_pixels_array, axis=0, return_counts=True)
        dominant_color = unique_colors[np.argmax(counts)]

        return dominant_color.tolist()

    def _extract_text_color(
        self, region_img: np.ndarray, bg_color: List[int]
    ) -> List[int]:
        """提取文字颜色"""
        if region_img.size == 0:
            return [0, 0, 0]

        h, w = region_img.shape[:2]
        center_y, center_x = h // 2, w // 2

        # 取中心区域
        center_region = region_img[
            max(0, center_y - 3) : min(h, center_y + 3),
            max(0, center_x - 10) : min(w, center_x + 10),
        ]

        if center_region.size == 0:
            return [0, 0, 0]

        pixels = center_region.reshape(-1, 3)
        bg_array = np.array(bg_color)

        # 找出与背景色差异最大的颜色
        distances = np.linalg.norm(pixels - bg_array, axis=1)

        # 过滤掉背景色（距离太小的）
        text_pixels = pixels[distances > 30]

        if len(text_pixels) > 0:
            # 取平均文字颜色
            text_color = np.mean(text_pixels, axis=0).astype(int)
            return text_color.tolist()

        return [0, 0, 0]

    def _estimate_font_size(self, region_height: int, text: str) -> int:
        """估算字体大小 - 改进版"""
        # 根据区域高度估算字体大小
        font_size = max(8, int(region_height * 0.8))
        return font_size

    def _detect_alignment_v2(
        self,
        img_width: int,
        img_height: int,
        x1: int,
        x2: int,
        y1: int,
        y2: int,
        text: str,
    ) -> str:
        """检测文字对齐方式 - 改进版V2"""
        region_width = x2 - x1
        region_center_x = (x1 + x2) / 2
        img_center_x = img_width / 2

        left_margin = x1 / img_width
        right_margin = (img_width - x2) / img_width

        # 检测是否为右侧图例（右对齐）
        if right_margin < 0.05 and left_margin > 0.7:
            return "right"

        # 检测是否为左侧文字（左对齐）
        if left_margin < 0.05:
            return "left"

        # 中间区域文字
        center_offset = abs(region_center_x - img_center_x) / img_width
        if center_offset < 0.15:
            return "center"
        elif region_center_x < img_center_x:
            return "left"
        else:
            # 右侧区域但非边缘，通常是左对齐（段落文字）
            return "left"

    def _detect_legend_region(
        self, img_width: int, x1: int, x2: int, y1: int, y2: int
    ) -> bool:
        """检测是否为图例区域"""
        # 图例通常在右侧边缘
        right_margin = (img_width - x2) / img_width
        return right_margin < 0.1

    def redraw_image(
        self, image_path: str, regions_with_style: List[Dict], output_path: str
    ):
        """重绘图片 - 全面改进版"""
        print(f"🎨 开始重绘图片: {image_path}")
        print(f"   共 {len(regions_with_style)} 个文字区域")

        image = Image.open(image_path)
        original_mode = image.mode
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # 修复2: 使用矩形填充替代Inpainting，效果更好
        result_img = image.copy()
        draw = ImageDraw.Draw(result_img)

        # 首先清除所有文字区域（使用背景色填充）
        for item in regions_with_style:
            bbox = item["region"]["bbox"]
            style = item["style"]

            # 计算矩形区域
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            x1, x2 = min(x_coords), max(x_coords)
            y1, y2 = min(y_coords), max(y_coords)

            # 稍微扩大清除区域
            margin = 2
            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)
            x2 = min(image.width, x2 + margin)
            y2 = min(image.height, y2 + margin)

            # 使用背景色填充矩形
            bg_color = tuple(style["background_color"])
            draw.rectangle([x1, y1, x2, y2], fill=bg_color)

        # 绘制翻译后的文字
        for i, item in enumerate(regions_with_style):
            region = item["region"]
            style = item["style"]
            original_text = region["text"]
            translated_text = region.get("translated_text")

            if translated_text and translated_text != original_text:
                print(
                    f"   区域 {i + 1}: '{original_text[:30]}...' → '{translated_text[:30]}...'"
                )
                self._draw_text_in_region_v2(
                    draw, result_img, region["bbox"], translated_text, style
                )

        # 转换回原始模式
        if original_mode != "RGBA":
            result_img = result_img.convert(original_mode)

        result_img.save(output_path, quality=95)
        print(f"✅ 重绘完成: {output_path}")

    def _draw_text_in_region_v2(
        self,
        draw: ImageDraw.ImageDraw,
        image: Image.Image,
        bbox: List[List[int]],
        text: str,
        style: Dict,
    ):
        """在指定区域绘制文字 - 全面改进版V2"""
        # 计算边界框
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)

        region_width = x2 - x1
        region_height = y2 - y1

        # 修复1&6: 智能字体大小调整和自动换行
        font_size, lines = self._calculate_optimal_font_and_lines(
            text, region_width, region_height, style["font_size"]
        )

        if not lines:
            return

        font = self._get_font(font_size, style.get("is_bold", False))

        # 计算总高度
        line_height = font_size * 1.2
        total_text_height = len(lines) * line_height

        # 垂直居中
        start_y = y1 + (region_height - total_text_height) / 2

        text_color = tuple(style["font_color"])

        # 逐行绘制
        for i, line in enumerate(lines):
            bbox_line = draw.textbbox((0, 0), line, font=font)
            line_width = bbox_line[2] - bbox_line[0]

            # 根据对齐方式计算x位置
            if style["alignment"] == "center":
                x = x1 + (region_width - line_width) / 2
            elif style["alignment"] == "right":
                x = x2 - line_width
            else:  # left
                x = x1

            y = start_y + i * line_height

            # 绘制文字
            draw.text((x, y), line, font=font, fill=text_color)

    def _calculate_optimal_font_and_lines(
        self, text: str, region_width: int, region_height: int, original_font_size: int
    ) -> Tuple[int, List[str]]:
        """修复1: 计算最优字体大小和自动换行"""

        # 尝试不换行，减小字体
        font_size = original_font_size
        min_font_size = 6

        while font_size >= min_font_size:
            font = self._get_font(font_size)
            bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox(
                (0, 0), text, font=font
            )
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 如果不换行能放下
            if text_width <= region_width and text_height <= region_height:
                return font_size, [text]

            # 如果字体已经很小了，尝试换行
            if font_size <= 10:
                break

            font_size -= 1

        # 修复1: 自动换行处理
        font = self._get_font(font_size)
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox(
                (0, 0), test_line, font=font
            )
            test_width = bbox[2] - bbox[0]

            if test_width <= region_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # 如果换行后行数太多，继续减小字体
        line_height = font_size * 1.3
        total_height = len(lines) * line_height

        while total_height > region_height and font_size > min_font_size:
            font_size -= 1
            font = self._get_font(font_size)
            line_height = font_size * 1.3
            total_height = len(lines) * line_height

        return font_size, lines if lines else [text]

    def _get_font(self, size: int, is_bold: bool = False):
        """获取字体"""
        system_fonts = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
            if is_bold
            else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

        for font_path in system_fonts:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue

        return ImageFont.load_default()
