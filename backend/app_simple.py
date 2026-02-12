from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import shutil

# 创建必要的目录
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

app = FastAPI(
    title="图片翻译服务",
    description="支持多语言的图片文字翻译服务（演示版）",
    version="1.0.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 数据模型
class Language(BaseModel):
    code: str
    name: str
    native_name: str


class TranslationResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None


class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    result_url: Optional[str] = None
    detected_language: Optional[str] = None
    error_message: Optional[str] = None


# 存储任务状态
tasks = {}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


from fastapi.responses import HTMLResponse


@app.get("/", response_class=HTMLResponse)
async def root():
    """提供前端静态页面"""
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>图片翻译工具</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
        .header { background: white; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 10px; }
        .header h1 { margin: 0; color: #1890ff; font-size: 24px; }
        .container { max-width: 800px; margin: 40px auto; padding: 0 20px; }
        .card { background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .upload-area { border: 2px dashed #d9d9d9; border-radius: 8px; padding: 60px 20px; text-align: center; cursor: pointer; }
        .upload-area:hover { border-color: #1890ff; }
        .form-group { margin-bottom: 20px; }
        select { width: 200px; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 4px; }
        .button { background: #1890ff; color: white; border: none; padding: 10px 24px; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .button:hover { background: #40a9ff; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔄 图片翻译工具</h1>
    </div>
    <div class="container">
        <div class="card">
            <h2>上传图片</h2>
            <form action="/api/v1/translate" method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label>目标语言：</label>
                    <select name="target_language">
                        <option value="zh" selected>中文</option>
                        <option value="en">English</option>
                        <option value="ja">日本語</option>
                        <option value="ko">한국어</option>
                    </select>
                </div>
                <div class="upload-area" onclick="document.getElementById('image').click()">
                    <p style="font-size: 48px;">📁</p>
                    <p>点击选择图片</p>
                    <p style="color: #999; font-size: 14px;">支持 JPG、PNG、WebP，最大 10MB</p>
                    <input type="file" id="image" name="image" accept="image/*" style="display: none;" required>
                </div>
                <br>
                <button type="submit" class="button">开始翻译</button>
            </form>
        </div>
        <div class="card">
            <h3>说明</h3>
            <p>当前运行演示版本。完整版支持真实OCR翻译。</p>
            <p>API文档: <a href="/api/v1/languages">语言列表</a></p>
        </div>
    </div>
</body>
</html>"""
    return html_content


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/v1/languages", response_model=List[Language])
async def get_languages():
    """获取支持的语言列表"""
    return [
        Language(code="zh", name="中文", native_name="中文"),
        Language(code="en", name="English", native_name="English"),
        Language(code="ja", name="Japanese", native_name="日本語"),
        Language(code="ko", name="Korean", native_name="한국어"),
        Language(code="fr", name="French", native_name="Français"),
        Language(code="de", name="German", native_name="Deutsch"),
        Language(code="es", name="Spanish", native_name="Español"),
        Language(code="ru", name="Russian", native_name="Русский"),
    ]


@app.post("/api/v1/translate")
async def translate_image(
    request: Request,
    image: UploadFile = File(...),
    target_language: str = Form(...),
    source_language: Optional[str] = Form(None),
):
    """上传图片并开始翻译任务（演示版）"""

    # 验证文件扩展名
    file_ext = os.path.splitext(image.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持的格式: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 生成任务ID
    task_id = str(uuid.uuid4())

    # 保存上传的文件
    upload_path = f"uploads/{task_id}{file_ext}"
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # 检查文件大小
    file_size = os.path.getsize(upload_path)
    if file_size > MAX_FILE_SIZE:
        os.remove(upload_path)
        raise HTTPException(
            status_code=400,
            detail=f"文件太大。最大允许: {MAX_FILE_SIZE / 1024 / 1024}MB",
        )

    # 演示模式：直接返回原图作为"翻译结果"
    # 实际应用中这里会调用OCR和翻译服务
    output_path = f"outputs/{task_id}.png"

    # 复制原图作为输出（演示用）
    from PIL import Image

    img = Image.open(upload_path)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")
    img.save(output_path, "PNG")

    # 保存任务状态
    tasks[task_id] = {
        "task_id": task_id,
        "status": "completed",
        "progress": 100,
        "output_path": output_path,
        "detected_language": source_language or "auto",
    }

    # 检查是否是表单提交（浏览器）
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        # 返回HTML结果页面
        html_response = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>翻译完成 - 图片翻译工具</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
        .header {{ background: white; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .header h1 {{ margin: 0; color: #1890ff; font-size: 24px; }}
        .container {{ max-width: 800px; margin: 40px auto; padding: 0 20px; }}
        .card {{ background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; text-align: center; }}
        .success-icon {{ font-size: 64px; color: #52c41a; margin-bottom: 20px; }}
        .download-btn {{ display: inline-block; background: #1890ff; color: white; padding: 12px 32px; border-radius: 4px; text-decoration: none; font-size: 16px; margin-top: 20px; }}
        .download-btn:hover {{ background: #40a9ff; }}
        .back-btn {{ display: inline-block; background: white; color: #1890ff; border: 1px solid #1890ff; padding: 12px 32px; border-radius: 4px; text-decoration: none; font-size: 16px; margin-top: 20px; margin-left: 10px; }}
        .image-preview {{ max-width: 100%; max-height: 400px; margin: 20px 0; border: 1px solid #d9d9d9; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔄 图片翻译工具</h1>
    </div>
    <div class="container">
        <div class="card">
            <div class="success-icon">✅</div>
            <h2>翻译完成！</h2>
            <p>任务ID: {task_id}</p>
            <img src="/api/v1/download/{task_id}" alt="翻译结果" class="image-preview">
            <br>
            <a href="/api/v1/download/{task_id}" download class="download-btn">⬇️ 下载翻译结果</a>
            <a href="/" class="back-btn">返回首页</a>
        </div>
    </div>
</body>
</html>"""
        return HTMLResponse(content=html_response)

    # API调用返回JSON
    return TranslationResponse(
        success=True, data={"task_id": task_id, "status": "completed", "progress": 100}
    )


@app.get("/api/v1/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """查询任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    return TaskStatus(
        task_id=task["task_id"],
        status=task["status"],
        progress=task["progress"],
        result_url=f"/api/v1/download/{task_id}"
        if task["status"] == "completed"
        else None,
        detected_language=task.get("detected_language"),
        error_message=task.get("error_message"),
    )


@app.get("/api/v1/download/{task_id}")
async def download_result(task_id: str):
    """下载翻译后的图片"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    output_path = task.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="结果文件不存在")

    return FileResponse(
        output_path, media_type="image/png", filename=f"translated_{task_id}.png"
    )


# 静态文件服务
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

# 添加静态HTML路由
from fastapi.responses import HTMLResponse


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """提供前端静态页面"""
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "static.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>图片翻译服务</h1><p>服务运行正常！</p>"
