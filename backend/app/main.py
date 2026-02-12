from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from app.api.routes import router

# 创建必要的目录
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

app = FastAPI(
    title="图片翻译服务", description="支持多语言的图片文字翻译服务", version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix="/api/v1")

# 静态文件服务
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


@app.get("/", response_class=HTMLResponse)
async def root():
    """提供前端HTML界面"""
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>图片翻译工具（完整版）</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
        .header { background: white; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 10px; }
        .header h1 { margin: 0; color: #1890ff; font-size: 24px; }
        .container { max-width: 800px; margin: 40px auto; padding: 0 20px; }
        .card { background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .upload-area { border: 2px dashed #d9d9d9; border-radius: 8px; padding: 40px 20px; text-align: center; cursor: pointer; transition: all 0.3s; background: #fafafa; }
        .upload-area:hover { border-color: #1890ff; background: #f0f7ff; }
        .upload-area.has-file { border-color: #52c41a; background: #f6ffed; }
        .form-group { margin-bottom: 20px; }
        select { width: 200px; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 14px; }
        .button { background: #1890ff; color: white; border: none; padding: 12px 32px; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .button:hover { background: #40a9ff; }
        .loading { display: none; text-align: center; padding: 20px; }
        .loading.show { display: block; }
        .progress-bar { width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; margin-top: 10px; }
        .progress-fill { height: 100%; background: #1890ff; width: 0%; transition: width 0.3s; }
        .badge { display: inline-block; background: #52c41a; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔄 图片翻译工具</h1>
        <span class="badge">完整版</span>
    </div>
    <div class="container">
        <div class="card">
            <h2>上传图片进行翻译</h2>
            <p style="color: #666; margin-bottom: 20px;">支持中文、英文、日文、韩文等多种语言互译</p>
            
            <form id="uploadForm" action="/api/v1/translate" method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label>源语言（可选）：</label>
                    <select name="source_language">
                        <option value="">自动检测</option>
                        <option value="zh">中文</option>
                        <option value="en">English</option>
                        <option value="ja">日本語</option>
                        <option value="ko">한국어</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>目标语言：</label>
                    <select name="target_language">
                        <option value="zh" selected>中文</option>
                        <option value="en">English</option>
                        <option value="ja">日本語</option>
                        <option value="ko">한국어</option>
                        <option value="fr">Français</option>
                        <option value="de">Deutsch</option>
                        <option value="es">Español</option>
                        <option value="ru">Русский</option>
                    </select>
                </div>
                
                <div class="upload-area" id="uploadArea" onclick="document.getElementById('image').click()">
                    <div id="uploadPlaceholder">
                        <p style="font-size: 48px; margin: 0;">📁</p>
                        <p>点击选择图片</p>
                        <p style="color: #999; font-size: 14px;">支持 JPG、PNG、WebP 格式，最大 10MB</p>
                    </div>
                    <div id="fileInfo" style="display: none;">
                        <p style="font-size: 48px; margin: 0;">✅</p>
                        <p id="fileName" style="font-weight: bold; color: #1890ff; margin: 10px 0;"></p>
                        <p id="fileSize" style="color: #666; font-size: 14px;"></p>
                        <img id="imagePreview" style="max-width: 300px; max-height: 200px; margin-top: 15px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: none;">
                        <p style="color: #999; font-size: 12px; margin-top: 10px;">点击重新选择图片</p>
                    </div>
                    <input type="file" id="image" name="image" accept="image/*" style="display: none;" required>
                </div>
                
                <div class="loading" id="loading">
                    <p>⏳ 正在处理，请稍候...</p>
                    <p style="font-size: 12px; color: #666;">首次使用需下载OCR模型（约2-3分钟）</p>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                </div>
                
                <br>
                <button type="submit" class="button" id="submitBtn">开始翻译</button>
            </form>
        </div>
        
        <div class="card">
            <h3>功能特点</h3>
            <ul>
                <li>🎯 自动识别图片中的文字位置和内容</li>
                <li>🌐 支持10种语言互译</li>
                <li>🎨 保持原图样式和排版</li>
                <li>⚡ 本地处理，无需上传云端</li>
            </ul>
        </div>
    </div>
    
    <script>
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            document.getElementById('loading').classList.add('show');
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('submitBtn').textContent = '处理中...';
            
            // 模拟进度条
            let progress = 0;
            const interval = setInterval(function() {
                progress += 5;
                if (progress > 90) clearInterval(interval);
                document.getElementById('progressFill').style.width = progress + '%';
            }, 1000);
        });
        
        document.getElementById('image').addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                if (file.size > 10 * 1024 * 1024) {
                    alert('文件太大！最大支持10MB');
                    e.target.value = '';
                    return;
                }
                
                // 显示文件信息
                document.getElementById('uploadPlaceholder').style.display = 'none';
                document.getElementById('fileInfo').style.display = 'block';
                document.getElementById('uploadArea').classList.add('has-file');
                document.getElementById('fileName').textContent = file.name;
                
                // 格式化文件大小
                let size = file.size;
                let unit = 'B';
                if (size > 1024) { size /= 1024; unit = 'KB'; }
                if (size > 1024) { size /= 1024; unit = 'MB'; }
                document.getElementById('fileSize').textContent = size.toFixed(2) + ' ' + unit;
                
                // 显示图片预览
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.getElementById('imagePreview');
                    img.src = e.target.result;
                    img.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    </script>
</body>
</html>"""
    return html_content


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
