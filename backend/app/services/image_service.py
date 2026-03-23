from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import os
import re


class ImageService:
    def __init__(self):
        self.font_dir = os.environ.get("FONT_DIR", "./fonts")
        self.default_font_size = 20

        # 修复4: 专业术语词典 - 扩展版
        self.terminology_dict = {
            # 光伏/电力领域
            "photovoltaic": "光伏",
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
            "discharge": "放电",
            "standby": "待机",
            "grid input power": "电网输入功率",
            "sell to the grid": "卖给电网",
            "electricity": "电能",
            "curve": "曲线",
            "period": "时段",
            "charging period": "充电时段",
            "discharge period": "放电时段",
            "non-charging and non-discharging period": "非充非放时段",
            # 新增术语
            "load": "负载",
            "pool": "电池包",
            "take-off": "取电",
            "draws": "取",
            "generates": "产生",
            "sells": "出售",
            "from": "从",
            "pv": "光伏",
            "battery": "电池",
            "pack": "包",
            "grid": "电网",
            "input": "输入",
            "output": "输出",
        }

        # 反向词典用于修正翻译
        self.reverse_terminology = {v: k for k, v in self.terminology_dict.items()}

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
        is_legend = self._detect_legend_region(
            img_array.shape[1], img_array.shape[0], x1, x2, y1, y2
        )

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
        self, img_width: int, img_height: int, x1: int, x2: int, y1: int, y2: int
    ) -> bool:
        """检测是否为图例区域（右侧或顶部）"""
        # 图例通常在右侧边缘或顶部
        right_margin = (img_width - x2) / img_width
        is_right_edge = right_margin < 0.15  # 右侧边缘

        # 顶部图例（如标题栏）
        top_margin = y1 / img_height
        is_top_area = top_margin < 0.15  # 顶部15%区域

        return is_right_edge or is_top_area

    def redraw_image(
        self, image_path: str, regions_with_style: List[Dict], output_path: str
    ):
        """重绘图片 - 全面改进版V3（添加重叠检测）"""
        print(f"🎨 开始重绘图片: {image_path}")
        print(f"   共 {len(regions_with_style)} 个文字区域")

        image = Image.open(image_path)
        original_mode = image.mode
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # 修复2: 使用矩形填充替代Inpainting，效果更好
        result_img = image.copy()
        draw = ImageDraw.Draw(result_img)

        # 修复7: 检测重叠区域并排序处理
        regions_with_style = self._sort_regions_by_priority(
            regions_with_style, image.height
        )
        drawn_regions = []  # 记录已绘制的区域

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
            margin = 5  # 增大边距
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

            # 如果没有翻译结果，使用原文（处理数字、时间等不需要翻译的内容）
            if not translated_text:
                translated_text = original_text

            print(
                f"   区域 {i + 1}: '{original_text[:30]}...' → '{translated_text[:30]}...'"
            )

            # 检查区域位置和类型
            y_coords = [p[1] for p in region["bbox"]]
            y1 = min(y_coords)
            is_bottom = y1 > image.height * 0.75
            is_legend = style.get("is_legend", False)
            is_chart_area = 0.15 < (y1 / image.height) < 0.75 and not is_legend
            is_top_area = (y1 / image.height) < 0.15

            # 检查是否与已绘制区域重叠
            # 大幅放宽重叠阈值，避免丢失文字
            overlap_threshold = 0.6 if is_bottom else 0.5
            if self._check_overlap(region["bbox"], drawn_regions, overlap_threshold):
                print(f"   ⚠️  检测到严重重叠，尝试偏移绘制")
                # 不再跳过，而是尝试偏移绘制
                # continue

            self._draw_text_in_region_v2(
                draw,
                result_img,
                region["bbox"],
                translated_text,
                style,
                image.height,
                is_legend,
                is_chart_area,
                is_top_area,
                image.width,  # 添加图片宽度参数
            )
            drawn_regions.append(region["bbox"])

        # 转换回原始模式
        if original_mode != "RGBA":
            result_img = result_img.convert(original_mode)

        result_img.save(output_path, quality=95)
        print(f"✅ 重绘完成: {output_path}")

    def _sort_regions_by_priority(
        self, regions_with_style: List[Dict], img_height: int
    ) -> List[Dict]:
        """按优先级排序区域（图例优先，大的区域优先，底部区域靠后）"""

        def get_priority(item):
            style = item["style"]
            bbox = item["region"]["bbox"]
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            x1, x2 = min(x_coords), max(x_coords)
            y1, y2 = min(y_coords), max(y_coords)
            area = (x2 - x1) * (y2 - y1)

            # 检测区域类型
            is_legend = style.get("is_legend", False)
            is_bottom = y1 > img_height * 0.75  # 底部区域
            is_chart_area = (y1 / img_height) < 0.75  # 图表区域（顶部+中间）

            # 优先级：图例 > 顶部标题 > 图表区域 > 底部区域
            # 底部区域应该分散绘制，避免重叠
            priority = 0
            if is_legend:
                priority = 0
            elif y1 < img_height * 0.15:
                priority = 1  # 顶部
            elif is_chart_area:
                priority = 2  # 中部图表
            elif is_bottom:
                priority = 3  # 底部

            return (priority, -area)  # 优先级小的在前，同优先级大面积在前

        return sorted(regions_with_style, key=get_priority)

    def _check_overlap(
        self,
        bbox: List[List[int]],
        drawn_regions: List[List[List[int]]],
        threshold: float = 0.5,
    ) -> bool:
        """检查是否与已绘制区域重叠 - 改进版（更宽松）"""
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)

        area = (x2 - x1) * (y2 - y1)
        if area == 0:
            return False

        # 减少边距，避免误判
        margin = 1
        x1 -= margin
        x2 += margin
        y1 -= margin
        y2 += margin

        for drawn_bbox in drawn_regions:
            dx_coords = [p[0] for p in drawn_bbox]
            dy_coords = [p[1] for p in drawn_bbox]
            dx1, dx2 = min(dx_coords), max(dx_coords)
            dy1, dy2 = min(dy_coords), max(dy_coords)

            # 计算重叠面积（不扩大已绘制区域）
            overlap_x = max(0, min(x2, dx2) - max(x1, dx1))
            overlap_y = max(0, min(y2, dy2) - max(y1, dy1))
            overlap_area = overlap_x * overlap_y

            if overlap_area > 0:
                overlap_ratio = overlap_area / area
                # 只有重叠比例超过阈值才认为是严重重叠
                if overlap_ratio > threshold:
                    return True

        return False

    def _draw_text_in_region_v2(
        self,
        draw: ImageDraw.ImageDraw,
        image: Image.Image,
        bbox: List[List[int]],
        text: str,
        style: Dict,
        img_height: Optional[int] = None,
        is_legend: bool = False,
        is_chart_area: bool = False,
        is_top_area: bool = False,
        img_width: Optional[int] = None,  # 新增图片宽度参数
    ):
        """在指定区域绘制文字 - 全面改进版V4（添加高级排版功能）"""
        # 计算边界框
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)

        # 计算可用宽度：从文本区域左边缘到图片右边缘
        # 这样文本可以利用右侧的空白区域
        if img_width:
            available_width = img_width - x1  # 从x1到图片右边缘的宽度
            # 但不要超过原始区域宽度的2倍，避免过度拉伸
            region_width = x2 - x1
            max_allowed_width = region_width * 2
            region_width = min(available_width, max_allowed_width)
        else:
            region_width = x2 - x1

        region_height = y2 - y1

        # 检测区域类型
        is_bottom_region = bool(img_height and y1 > img_height * 0.75)
        is_chart_area = bool(
            img_height and 0.15 < (y1 / img_height) < 0.75 and not is_legend
        )
        is_top_area = bool(img_height and (y1 / img_height) < 0.15)

        # 获取字体大小和换行
        font_size, lines = self._calculate_optimal_font_and_lines(
            text,
            region_width,
            region_height,
            style["font_size"],
            is_bottom_region,
            is_legend,
            is_chart_area,
        )

        if not lines or (len(lines) == 1 and not lines[0].strip()):
            lines = [text] if text else []
            if not lines:
                return

        # 使用多语言字体回退
        detected_lang = style.get("language", "zh")
        font = self._get_font_with_fallback(
            font_size, detected_lang, style.get("is_bold", False)
        )

        # 自适应行距和字距
        char_spacing, line_spacing_mult = self._calculate_adaptive_spacing(
            text, region_width, font_size, detected_lang
        )

        # 使用自适应行高
        line_height = font_size * line_spacing_mult
        total_text_height = len(lines) * line_height

        # 垂直居中，但确保不超出边界
        start_y = max(y1, y1 + (region_height - total_text_height) / 2)

        # 优化文字颜色对比度
        text_color = self._optimize_text_color(
            style["font_color"], style["background_color"]
        )
        text_color = tuple(text_color)
        bg_color = tuple(style["background_color"])

        # 检测是否需要添加阴影效果（深色背景上使用阴影）
        bg_luminance = sum(bg_color) / (3 * 255)
        add_shadow = bg_luminance > 0.7  # 浅色背景添加阴影

        # 逐行绘制
        for i, line in enumerate(lines):
            bbox_line = draw.textbbox((0, 0), line, font=font)
            line_width = bbox_line[2] - bbox_line[0]

            # 检测溢出
            overflow_info = self._detect_text_overflow(
                line, region_width, region_height, font
            )

            # 根据对齐方式计算x位置
            if is_chart_area:
                x = x1
            elif is_top_area:
                x = x1
            elif style["alignment"] == "center":
                x = x1 + (region_width - line_width) / 2
            elif style["alignment"] == "right":
                x = x2 - line_width
            else:  # left
                x = x1

            y = start_y + i * line_height

            # 使用增强的文字渲染
            self._render_text_with_enhanced_style(
                draw,
                x,
                y,
                line,
                font,
                text_color,
                bg_color,
                add_shadow=add_shadow,
                add_outline=False,
            )

    def _calculate_optimal_font_and_lines(
        self,
        text: str,
        region_width: int,
        region_height: int,
        original_font_size: int,
        is_bottom_region: bool = False,
        is_legend: bool = False,
        is_chart_area: bool = False,
        is_top_area: bool = False,
    ) -> Tuple[int, List[str]]:
        """修复1: 计算最优字体大小和自动换行 - 改进版V7（图例和图表区统一字号）"""

        # 修复术语翻译问题
        text = self._fix_translation_terms(text)

        # 顶部区域（图例）：使用统一的字体大小（16px），不换行
        if is_legend or is_top_area:
            legend_font_size = 16
            font = self._get_font(legend_font_size)
            # 顶部区域不换行
            lines = [text]
            return legend_font_size, lines

        # 图表中间区域：使用换行而不是缩小字体
        if is_chart_area:
            # 使用12px作为最小字体，允许换行
            font_size = 18  # 增大起始字号
            min_font_size = 12  # 增大最小字号

            best_font_size = min_font_size
            best_lines = [text]

            for fs in range(font_size, min_font_size - 1, -1):
                font = self._get_font(fs)
                # 积极换行：使用区域宽度限制
                lines = self._wrap_text_to_lines(text, region_width, font)

                # 检查每行是否都在边界内
                all_fit = True
                for line in lines:
                    line_bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox(
                        (0, 0), line, font=font
                    )
                    if line_bbox[2] > region_width:
                        all_fit = False
                        break

                if all_fit:
                    best_font_size = fs
                    best_lines = lines
                    break
                else:
                    # 保存当前尝试的结果
                    best_font_size = fs
                    best_lines = lines

            return best_font_size, best_lines

        # 底部区域使用更紧凑的设置
        if is_bottom_region:
            # 底部区域：使用实际区域大小，不扩大
            adjusted_width = int(region_width * 1.0)  # 不溢出
            adjusted_height = int(region_height * 1.0)  # 不扩大
            min_font_size = 8  # 增大最小字号
            max_font_size = min(original_font_size, 16)  # 增大最大字号
            line_height_mult = 1.2  # 更紧凑的行高
        else:
            adjusted_width = int(region_width * 1.8)
            adjusted_height = int(region_height * 1.3)
            min_font_size = 10  # 增大最小字号
            max_font_size = max(original_font_size, 20)  # 增大最大字号
            line_height_mult = 1.4

        # 查找最优字体大小
        best_font_size = min_font_size
        best_lines = [text]
        found_fit = False

        for font_size in range(max_font_size, min_font_size - 1, -1):
            font = self._get_font(font_size)
            lines = self._wrap_text_to_lines(text, adjusted_width, font)

            line_height = font_size * line_height_mult
            total_height = len(lines) * line_height

            # 检查是否所有行都能放下
            all_lines_fit = all(
                ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox(
                    (0, 0), line, font=font
                )[2]
                <= adjusted_width
                for line in lines
            )

            if total_height <= adjusted_height and all_lines_fit:
                best_font_size = font_size
                best_lines = lines
                found_fit = True
                break

        # 如果没找到合适的大小，使用最小字体并强制适应
        if not found_fit and is_bottom_region:
            font = self._get_font(min_font_size)
            # 尝试进一步缩写
            short_text = self._abbreviate_text(text, True)
            if short_text != text:
                lines = self._wrap_text_to_lines(short_text, adjusted_width, font)
            else:
                lines = [text]
            best_font_size = min_font_size
            best_lines = lines

        return best_font_size, best_lines

    def _fix_translation_terms(self, text: str) -> str:
        """修复翻译中的术语错误"""
        # 修正常见错误翻译
        corrections = {
            "electricity Pool": "battery pack",
            "power take-off": "power draw",
            "Pool power": "battery pack power",
            "from electricity": "from the battery",
            "and from": "and",
            "Load from": "The load draws power from",
        }

        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)

        return text

    def _abbreviate_text(
        self, text: str, is_bottom: bool = False, is_chart: bool = False
    ) -> str:
        """智能缩写长文本"""
        if not is_bottom and not is_chart:
            return text

        # 通用缩写规则（更激进 - 图表区域优先处理）
        if is_chart:
            # 图表区域强制缩写 - 英文缩写（最终手段）
            # 这是在翻译之后应用的，所以不管翻译API返回什么，我们都会缩写
            text = text.replace("The load draws power from the battery", "Load bat")
            text = text.replace("the load draws power from the battery", "Load bat")
            text = text.replace("draws power from the battery", "from battery")
            text = text.replace(
                "The load draws power from the grid and the battery", "Load grid+bat"
            )
            text = text.replace(
                "draws power from the grid and the battery", "from grid+bat"
            )
            text = text.replace("The load draws power from the grid", "Load grid")
            text = text.replace(
                "The load purchases electricity from the grid", "Load grid"
            )
            text = text.replace("purchases electricity from the grid", "from grid")
            text = text.replace("PV charges the battery", "PV bat")
            text = text.replace(
                "PV generates electricity to sell to the grid", "PV grid"
            )
            text = text.replace(
                "generates electricity and sells it to the grid", "sells to grid"
            )

        replacements = [
            ("draws power from", "from"),
            ("purchases electricity from", "from"),
            ("the battery pack", "battery"),
            ("the power grid", "grid"),
            ("generates electricity and sells it to", "sells to"),
            ("generates electricity to sell to", "sells to"),
            ("sells electricity to", "sells to"),
            ("Electricity consumption curve of household appliances", "Household load"),
            ("Photovoltaic power generation curve", "PV curve"),
            ("Charging Period", "Charging"),
            ("Discharge period", "Discharge"),
            ("Non-charging and non-discharging period", "Standby"),
            ("and the battery pack", ""),
            ("and from the", "from"),
        ]

        for old, new in replacements:
            text = text.replace(old, new)

        return text

    def _wrap_text_to_lines(self, text: str, max_width: int, font) -> List[str]:
        """智能文本换行 - 支持 CJK 字符级换行"""
        if not text:
            return [""]

        # 检测是否包含 CJK 字符
        def is_cjk(char):
            return any(
                [
                    "\u4e00" <= char <= "\u9fff",  # 中文
                    "\u3040" <= char <= "\u309f",  # 日文平假名
                    "\u30a0" <= char <= "\u30ff",  # 日文片假名
                    "\uac00" <= char <= "\ud7af",  # 韩文
                ]
            )

        has_cjk = any(is_cjk(c) for c in text)

        if has_cjk:
            # CJK 模式：逐字符换行
            return self._wrap_cjk_text(text, max_width, font)
        else:
            # 西文模式：按单词换行
            return self._wrap_latin_text(text, max_width, font)

    def _wrap_cjk_text(self, text: str, max_width: int, font) -> List[str]:
        """CJK 文本逐字符换行"""
        lines = []
        current_line = ""

        # 标点符号（不允许在行首）
        no_start = set("，。！？）】》、；：,.!?:;)]}>")
        # 标点符号（不允许在行尾）
        no_end = set("（【《({<")

        for i, char in enumerate(text):
            test_line = current_line + char

            # 检查宽度
            bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox(
                (0, 0), test_line, font=font
            )
            line_width = bbox[2] - bbox[0]

            if line_width > max_width and current_line:
                # 需要换行
                # 检查行尾标点
                if current_line[-1] in no_end and i + 1 < len(text):
                    # 行尾是开括号，把开括号移到下一行
                    lines.append(current_line[:-1])
                    current_line = current_line[-1] + char
                elif char in no_start and i > 0:
                    # 当前字符是闭标点，不应在行首
                    lines.append(current_line)
                    current_line = char
                else:
                    lines.append(current_line)
                    current_line = char
            else:
                current_line = test_line

        if current_line:
            lines.append(current_line)

        return lines if lines else [text]

    def _wrap_latin_text(self, text: str, max_width: int, font) -> List[str]:
        """西文文本按单词换行（原有逻辑）"""
        words = text.split()
        if not words:
            return [text]

        lines = []
        current_line = words[0]

        for word in words[1:]:
            test_line = current_line + " " + word
            bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox(
                (0, 0), test_line, font=font
            )
            test_width = bbox[2] - bbox[0]

            if test_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines if lines else [text]

    def _optimize_text_color(
        self, text_color: List[int], bg_color: List[int]
    ) -> List[int]:
        """优化文字颜色以确保在背景上有足够的对比度"""
        text_rgb = np.array(text_color)
        bg_rgb = np.array(bg_color)

        # 计算相对亮度 (基于人眼对不同颜色的敏感度)
        def get_luminance(rgb):
            r, g, b = rgb / 255.0
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        text_lum = get_luminance(text_rgb)
        bg_lum = get_luminance(bg_rgb)

        # 计算对比度
        contrast = (max(text_lum, bg_lum) + 0.05) / (min(text_lum, bg_lum) + 0.05)

        # 如果对比度不够，调整文字颜色
        if contrast < 4.5:  # WCAG AA 标准
            if bg_lum > 0.5:
                # 背景较亮，使用深色文字
                return [0, 0, 0]
            else:
                # 背景较暗，使用白色文字
                return [255, 255, 255]

        return text_color

    def _calculate_adaptive_spacing(
        self, text: str, region_width: int, font_size: int, target_lang: str = "zh"
    ) -> Tuple[float, float]:
        """
        自适应计算行距和字距
        - 英文→中文：文本通常变短，增加字距
        - 中文→英文：文本通常变长，减小字距
        """
        ascii_ratio = sum(1 for c in text if ord(c) < 128) / max(len(text), 1)

        if target_lang in ["zh", "ja", "ko"]:
            if ascii_ratio > 0.5:
                return 1.1, 1.3
            else:
                return 1.0, 1.2
        else:
            if ascii_ratio < 0.5:
                return 0.9, 1.1
            else:
                return 1.0, 1.2

    def _detect_text_overflow(
        self, text: str, region_width: int, region_height: int, font
    ) -> Dict:
        """检测文本是否超出区域边界"""
        bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox(
            (0, 0), text, font=font
        )
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        overflow_x = text_width > region_width
        overflow_y = text_height > region_height

        scale_x = region_width / text_width if text_width > 0 else 1.0
        scale_y = region_height / text_height if text_height > 0 else 1.0
        scale_factor = min(scale_x, scale_y, 1.0)

        return {
            "overflow_x": overflow_x,
            "overflow_y": overflow_y,
            "text_width": text_width,
            "text_height": text_height,
            "scale_factor": scale_factor,
        }

    def _get_font_with_fallback(
        self, size: int, language: str = "zh", is_bold: bool = False
    ):
        """多语言字体 fallback 支持"""
        import glob as glob_module

        font_priority = {
            "zh": ["NotoSansCJK", "NotoSansSC", "SimHei", "Microsoft YaHei", "SimSun"],
            "ja": ["NotoSansCJK", "NotoSansJP", "MS Gothic", "Hiragino Sans"],
            "ko": ["NotoSansCJK", "NotoSansKR", "Malgun Gothic"],
            "en": ["Arial", "DejaVuSans", "NotoSans"],
            "default": ["NotoSansCJK", "DejaVuSans", "Arial"],
        }

        font_names = font_priority.get(language, font_priority["default"])

        for font_name in font_names:
            patterns = [
                os.path.join(self.font_dir, f"*{font_name}*.ttc"),
                os.path.join(self.font_dir, f"*{font_name}*.otf"),
                os.path.join(self.font_dir, f"*{font_name}*.ttf"),
            ]
            for pattern in patterns:
                for font_path in glob_module.glob(pattern):
                    try:
                        return ImageFont.truetype(font_path, size)
                    except Exception:
                        continue

        system_fonts = {
            "zh": [
                "C:\\Windows\\Fonts\\msyh.ttc",
                "C:\\Windows\\Fonts\\simhei.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            ],
            "ja": [
                "C:\\Windows\\Fonts\\msgothic.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            ],
            "ko": [
                "C:\\Windows\\Fonts\\malgun.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            ],
            "en": [
                "C:\\Windows\\Fonts\\arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ],
        }

        for font_path in system_fonts.get(language, system_fonts["en"]):
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue

        return self._get_font(size, is_bold)

    def _optimize_paragraph_layout(
        self, text: str, max_width: int, font, min_line_length: int = 10
    ) -> List[str]:
        """优化段落布局"""
        paragraphs = text.split("\n\n")
        if len(paragraphs) == 1:
            paragraphs = text.split("\n")

        optimized_lines = []

        for para in paragraphs:
            if not para.strip():
                optimized_lines.append("")
                continue

            lines = self._wrap_text_to_lines(para.strip(), max_width, font)

            merged_lines = []
            for i, line in enumerate(lines):
                if len(line) < min_line_length and i < len(lines) - 1:
                    next_line = lines[i + 1] if i + 1 < len(lines) else ""
                    merged = line + " " + next_line
                    merged_bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox(
                        (0, 0), merged, font=font
                    )
                    if merged_bbox[2] <= max_width:
                        lines[i + 1] = merged
                        continue
                merged_lines.append(line)

            optimized_lines.extend(merged_lines)
            optimized_lines.append("")

        while optimized_lines and not optimized_lines[-1]:
            optimized_lines.pop()

        return optimized_lines if optimized_lines else [text]

    def _render_text_with_enhanced_style(
        self,
        draw: ImageDraw.ImageDraw,
        x: float,
        y: float,
        text: str,
        font,
        text_color: tuple,
        bg_color: tuple,
        add_shadow: bool = False,
        add_outline: bool = False,
    ):
        """增强的文字渲染"""
        if add_shadow:
            shadow_color = (
                max(0, text_color[0] - 100),
                max(0, text_color[1] - 100),
                max(0, text_color[2] - 100),
            )
            draw.text((x + 1, y + 1), text, font=font, fill=shadow_color)

        if add_outline:
            outline_color = (
                255 - text_color[0],
                255 - text_color[1],
                255 - text_color[2],
            )
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)

        draw.text((x, y), text, font=font, fill=text_color)

    def _get_font(self, size: int, is_bold: bool = False):
        """获取字体 - 优先从配置目录加载"""
        import glob as glob_module

        # 1. 优先从 font_dir 加载
        font_patterns = [
            os.path.join(self.font_dir, "*.ttc"),
            os.path.join(self.font_dir, "*.otf"),
            os.path.join(self.font_dir, "*.ttf"),
        ]

        for pattern in font_patterns:
            for font_path in glob_module.glob(pattern):
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception:
                    continue

        # 2. 回退到系统路径（跨平台）
        system_paths = []
        if os.name == "nt":  # Windows
            system_paths = [
                "C:\\Windows\\Fonts\\msyh.ttc",  # 微软雅黑
                "C:\\Windows\\Fonts\\simsun.ttc",  # 宋体
                "C:\\Windows\\Fonts\\arial.ttf",
            ]
        else:  # Linux/Mac
            system_paths = [
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]

        for font_path in system_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue

        # 3. 最后回退
        return ImageFont.load_default()
