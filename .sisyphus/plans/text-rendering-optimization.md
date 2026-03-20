# 图像文本渲染优化计划

## TL;DR
> **Summary**: 修复字体加载 Bug 和 CJK 文本换行问题
> **Deliverables**: 优化后的 image_service.py
> **Effort**: Short
> **Parallel**: NO - 单文件修改
> **Critical Path**: Task 1 → Task 2

## Context
### Original Request
优化图片翻译工具中译文的排版，重点是 CJK 文本换行和字体加载。

### 关键发现
1. **字体加载 Bug**: `_get_font()` 方法忽略 `self.font_dir`，使用硬编码 Linux 路径
2. **CJK 换行失效**: `_wrap_text_to_lines()` 只按空格分词，对中日韩语言无效

---

## Work Objectives
### Core Objective
1. 修复 `_get_font()` 使用配置的 `font_dir`
2. 实现 CJK 字符级换行算法

### Definition of Done
- [ ] 字体加载优先使用 `self.font_dir` 目录
- [ ] CJK 文本支持逐字符换行
- [ ] 英文文本仍按单词换行
- [ ] 中日韩混合文本正确处理

---

## TODOs

### Task 1: 修复字体加载 Bug
**文件**: `backend/app/services/image_service.py`
**方法**: `_get_font()` (lines 752-772)

**问题**: 当前硬编码 Linux 路径，忽略 `self.font_dir`

**修改方案**:
```python
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
    if os.name == 'nt':  # Windows
        system_paths = [
            "C:\\Windows\\Fonts\\msyh.ttc",      # 微软雅黑
            "C:\\Windows\\Fonts\\simsun.ttc",     # 宋体
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
```

**Acceptance Criteria**:
- [ ] 优先从 `self.font_dir` 加载字体
- [ ] 支持 .ttc, .otf, .ttf 格式
- [ ] Windows/Linux/Mac 路径兼容

---

### Task 2: 实现 CJK 文本换行
**文件**: `backend/app/services/image_service.py`
**方法**: `_wrap_text_to_lines()` (lines 693-718)

**问题**: 只按空格分词，CJK 语言词间无空格导致整个文本变成一个 "word"

**修改方案**:
```python
def _wrap_text_to_lines(self, text: str, max_width: int, font) -> List[str]:
    """智能文本换行 - 支持 CJK 字符级换行"""
    if not text:
        return [""]
    
    # 检测是否包含 CJK 字符
    def is_cjk(char):
        return any([
            '\u4e00' <= char <= '\u9fff',   # 中文
            '\u3040' <= char <= '\u309f',   # 日文平假名
            '\u30a0' <= char <= '\u30ff',   # 日文片假名
            '\uac00' <= char <= '\ud7af',   # 韩文
        ])
    
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
    no_start = set('，。！？）】》、；：,.!?:;)]}>')
    # 标点符号（不允许在行尾）
    no_end = set('（【《({<')
    
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
```

**Acceptance Criteria**:
- [ ] CJK 文本支持逐字符换行
- [ ] 标点符号正确处理（不在行首/行尾）
- [ ] 西文文本仍按单词换行
- [ ] 中日韩混合文本正确处理

---

## Final Verification
- [ ] 使用中文图片测试换行效果
- [ ] 使用英文图片测试换行效果
- [ ] 使用混合语言图片测试
- [ ] 验证字体加载在 Docker 环境中工作
