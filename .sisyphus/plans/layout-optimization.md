# 译文排版全面优化计划

## TL;DR
> **Summary**: 实现译文排版的全面优化，包括自适应布局、字体回退、段落优化等
> **Deliverables**: 优化后的 image_service.py 和 routes.py
> **Effort**: Medium
> **Parallel**: NO - 单文件修改
> **Critical Path**: Task 1 → Task 2 → Task 3

---

## 优化项

### Task 1: 添加高级排版方法到 image_service.py

**文件**: `backend/app/services/image_service.py`

**新增方法**:

#### 1.1 `_calculate_adaptive_spacing()`
自适应计算行距和字距：
- 英文→中文：文本变短，增加字距（1.1倍）
- 中文→英文：文本变长，减小字距（0.9倍）
- CJK→CJK：保持原有字距（1.0倍）

**代码位置**: 在 `_optimize_text_color()` 方法后添加

#### 1.2 `_detect_text_overflow()`
检测文本是否超出区域边界：
- 返回 overflow_x, overflow_y 状态
- 计算 text_width, text_height
- 返回建议的 scale_factor

**代码位置**: 在 `_calculate_adaptive_spacing()` 方法后添加

#### 1.3 `_get_font_with_fallback()`
多语言字体 fallback 支持：
- 根据语言自动选择合适的字体
- 支持 zh/ja/ko/en 语言
- 优先级：font_dir → 系统路径 → 默认字体

**代码位置**: 在 `_detect_text_overflow()` 方法后添加

#### 1.4 `_optimize_paragraph_layout()`
优化段落布局：
- 检测段落分隔（双换行）
- 避免过短的行（孤行）
- 保持段落结构

**代码位置**: 在 `_get_font_with_fallback()` 方法后添加

#### 1.5 `_render_text_with_enhanced_style()`
增强的文字渲染：
- 可选阴影效果
- 可选描边效果
- 更好的对比度

**代码位置**: 在 `_optimize_paragraph_layout()` 方法后添加

---

### Task 2: 更新 `_draw_text_in_region_v2()` 方法

**文件**: `backend/app/services/image_service.py`
**方法**: `_draw_text_in_region_v2()` (lines 417-502)

**修改内容**:
1. 使用 `_calculate_adaptive_spacing()` 计算自适应行距
2. 使用 `_get_font_with_fallback()` 获取字体
3. 使用 `_detect_text_overflow()` 检测溢出
4. 使用 `_render_text_with_enhanced_style()` 渲染文字

---

### Task 3: 更新前端显示对比图

**文件**: `backend/app/main.py` (HTML 响应)
**修改内容**:
1. 在翻译完成页面添加原图和译文对比显示
2. 添加移动端响应式适配
3. 添加下载按钮

---

## 实现细节

### 1. 行距自适应算法

```python
def _calculate_adaptive_spacing(self, text, region_width, font_size, target_lang):
    # 估算ASCII字符比例
    ascii_ratio = sum(1 for c in text if ord(c) < 128) / max(len(text), 1)
    
    if target_lang in ["zh", "ja", "ko"]:
        if ascii_ratio > 0.5:  # 英文→中文
            return 1.1, 1.3  # char_spacing, line_spacing
        else:
            return 1.0, 1.2
    else:  # 目标是西方语言
        if ascii_ratio < 0.5:  # 中文→英文
            return 0.9, 1.1
        else:
            return 1.0, 1.2
```

### 2. 溢出检测算法

```python
def _detect_text_overflow(self, text, region_width, region_height, font):
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
```

### 3. 字体回退算法

```python
def _get_font_with_fallback(self, size, language="zh", is_bold=False):
    font_priority = {
        "zh": ["NotoSansCJK", "SimHei", "Microsoft YaHei"],
        "ja": ["NotoSansCJK", "MS Gothic"],
        "ko": ["NotoSansCJK", "Malgun Gothic"],
        "en": ["Arial", "DejaVuSans"],
    }
    
    for font_name in font_priority.get(language, ["NotoSansCJK"]):
        # 从 font_dir 和系统路径查找
        ...
    
    return self._get_font(size, is_bold)
```

---

## 验证标准

### Task 1 验证
- [ ] 所有新方法已添加到 image_service.py
- [ ] 方法签名和返回值符合设计

### Task 2 验证
- [ ] `_draw_text_in_region_v2()` 使用了新方法
- [ ] 行距自适应生效
- [ ] 溢出检测生效

### Task 3 验证
- [ ] 前端显示原图和译文对比
- [ ] 移动端响应式适配

---

## 依赖关系

```
Task 1 (添加方法)
    ↓
Task 2 (更新渲染逻辑)
    ↓
Task 3 (更新前端)
```

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 字体文件缺失 | 中等 | 使用默认字体回退 |
| 行距计算错误 | 低 | 添加边界检查 |
| 溢出检测误判 | 低 | 添加调试日志 |
