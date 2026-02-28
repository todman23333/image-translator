# 图片翻译工具

一个基于Web的图片翻译应用，支持上传图片后自动识别文字、翻译并重新渲染到原图上。

## 功能特性

- 🖼️ **图片上传**：支持拖拽和点击上传，支持 JPG、PNG、WebP 格式
- 🔍 **OCR识别**：使用 PaddleOCR，免费本地运行，支持80+语言
- 🌐 **多语言翻译**：支持10种主流语言互译
- ✨ **智能重绘**：保持原图风格，自动匹配字体、颜色、对齐方式
- 📱 **响应式设计**：支持桌面和移动端访问

## 技术栈

### 后端
- **框架**：FastAPI (Python)
- **OCR**：PaddleOCR（免费开源，无需API Key）
- **翻译**：Alibaba DashScope Qwen API
- **图像处理**：Pillow + OpenCV

### 前端
- **框架**：React 18 + TypeScript
- **UI库**：Ant Design
- **状态管理**：Zustand
- **构建工具**：Vite

## 快速开始

### 环境要求
- Docker
- Docker Compose

### 启动服务

```bash
# 进入项目目录
cd image-translator

# 启动所有服务
docker-compose up -d

# 等待服务启动（首次启动需要下载模型，大约需要3-5分钟）
```
## 使用说明

1. 打开 http://localhost:8000
2. 选择源语言（可选）和目标语言
3. 上传图片或拖拽图片到上传区域
4. 等待处理完成（通常10-30秒）
5. 预览翻译结果并下载

## API接口

### 上传图片并翻译
```bash
curl -X POST "http://localhost:8000/api/v1/translate" \
  -F "image=@example.jpg" \
  -F "target_language=zh"
```

### 查询任务状态
```bash
curl "http://localhost:8000/api/v1/tasks/{task_id}"
```

### 获取支持的语言
```bash
curl "http://localhost:8000/api/v1/languages"
```

## 项目结构

```
image-translator/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由和模型
│   │   ├── services/       # 业务逻辑服务
│   │   │   ├── ocr_service.py         # OCR识别
│   │   │   ├── translation_service.py # 翻译服务
│   │   │   └── image_service.py       # 图像处理
│   │   └── main.py         # 入口文件
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/     # UI组件
│   │   ├── pages/         # 页面组件
│   │   ├── services/      # API服务
│   │   ├── store/         # 状态管理
│   │   └── types/         # TypeScript类型
│   ├── Dockerfile
│   └── package.json
├── uploads/               # 上传图片存储
├── outputs/               # 翻译结果存储
└── docker-compose.yml
```

## 配置说明

### 环境变量

可以在 `docker-compose.yml` 中配置以下环境变量：

- `UPLOAD_DIR`: 上传文件存储目录（默认：/app/uploads）
- `OUTPUT_DIR`: 输出文件存储目录（默认：/app/outputs）
- `FONT_DIR`: 字体文件目录（默认：/app/fonts）

### 字体配置

应用支持以下字体（按优先级）：
1. SourceHanSansCN（思源黑体）
2. NotoSansCJK
3. 微软雅黑
4. Arial
5. DejaVuSans

将字体文件放入 `fonts/` 目录即可自动加载。

## 开发指南

### 本地开发（不使用Docker）

#### 后端开发
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发
```bash
cd frontend
npm install
npm run dev
```

### 添加新功能

1. **添加新语言支持**
   - 在 `backend/app/api/routes.py` 的 `get_languages` 中添加语言
   - 在 `backend/app/api/models.py` 的 `LanguageCode` 枚举中添加

2. **更换翻译引擎**
   - 修改 `backend/app/services/translation_service.py`
   - 实现 `translate` 方法即可

3. **优化图像处理**
   - 修改 `backend/app/services/image_service.py`
   - 调整 `_draw_text_in_region` 方法

## 常见问题

### Q: 为什么OCR识别不准确？
A: PaddleOCR在清晰图片上的准确率很高。如果识别不准确，可以尝试：
- 上传更清晰的图片
- 确保文字与背景对比度足够
- 避免过度压缩的图片

### Q: 翻译质量如何？
A: 使用Google Translate免费API，适合一般用途。如需更高质量，建议：
- 更换为DeepL API
- 使用付费的Google Cloud Translation API

### Q: 支持哪些图片格式？
A: 支持 JPG、JPEG、PNG、WebP、BMP 格式，最大10MB。

### Q: 如何处理失败的任务？
A: 系统会自动重试翻译API调用。如果持续失败，请检查：
- 网络连接
- 图片格式是否正确
- 服务器日志获取详细错误信息

## 性能优化

- 首次启动需要下载OCR模型（约100MB）
- 大图片（>2MB）会自动处理，但耗时较长
- 建议使用SSD存储以加快模型加载速度
- 生产环境建议配置Redis缓存任务状态

## 许可证

MIT License

## 致谢

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR引擎
- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [React](https://react.dev/) - 前端框架
- [Ant Design](https://ant.design/) - UI组件库
