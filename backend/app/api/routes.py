from typing import Optional
import os
import uuid
import shutil
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    BackgroundTasks,
    Request,
)
from fastapi.responses import FileResponse, HTMLResponse

from app.api.models import (
    TranslationResponse,
    TaskStatus,
    Language,
    LanguageCode,
)
from app.services.ocr_service import OCRService
from app.services.translation_service import TranslationService
from app.services.image_service import ImageService

router = APIRouter()

# 存储任务状态
tasks = {}

# 初始化服务
ocr_service = OCRService()
translation_service = TranslationService()
image_service = ImageService()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.get("/languages", response_model=list[Language])
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


@router.post("/translate")
async def translate_image(
    request: Request,
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    target_language: str = Form(...),
    source_language: Optional[str] = Form(None),
):
    """上传图片并开始翻译任务"""

    if not image.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    file_ext = os.path.splitext(image.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持的格式: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    task_id = str(uuid.uuid4())
    upload_path = f"uploads/{task_id}{file_ext}"

    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    file_size = os.path.getsize(upload_path)
    if file_size > MAX_FILE_SIZE:
        os.remove(upload_path)
        raise HTTPException(
            status_code=400,
            detail=f"文件太大。最大允许: {MAX_FILE_SIZE / 1024 / 1024}MB",
        )

    tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "upload_path": upload_path,
        "target_language": target_language,
        "source_language": source_language,
        "result_url": None,
        "detected_language": None,
        "text_regions": None,
        "error_message": None,
    }

    background_tasks.add_task(
        process_translation_task,
        task_id,
        upload_path,
        target_language,
        source_language,
    )

    # 检查是否是浏览器表单提交
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        html_response = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>处理中 - 图片翻译工具</title>
    <meta http-equiv="refresh" content="3;url=/api/v1/tasks/{task_id}">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 100px auto; padding: 40px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; }}
        .loading {{ font-size: 48px; margin-bottom: 20px; }}
        .progress-bar {{ width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; margin: 20px 0; }}
        .progress-fill {{ height: 100%; background: #1890ff; width: 30%; animation: progress 2s infinite; }}
        @keyframes progress {{ 0% {{ width: 30%; }} 50% {{ width: 70%; }} 100% {{ width: 30%; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="loading">⏳</div>
        <h2>正在处理中...</h2>
        <p>正在识别文字并翻译，请稍候</p>
        <p style="color: #999; font-size: 14px;">首次使用需下载OCR模型（约2-3分钟）</p>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        <p style="margin-top: 20px; font-size: 12px; color: #999;">任务ID: {task_id}</p>
    </div>
</body>
</html>"""
        return HTMLResponse(content=html_response)

    return TranslationResponse(
        success=True,
        data={"task_id": task_id, "status": "processing", "progress": 0},
    )


@router.get("/tasks/{task_id}")
async def get_task_status(request: Request, task_id: str):
    """查询任务状态"""
    if task_id not in tasks:
        if "text/html" in request.headers.get("accept", ""):
            return HTMLResponse(
                content="<h1>错误</h1><p>任务不存在</p><a href='/'>返回首页</a>",
                status_code=404,
            )
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]

    # 浏览器访问返回HTML页面
    if "text/html" in request.headers.get("accept", ""):
        if task["status"] == "completed":
            html_content = f"""<!DOCTYPE html>
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
            return HTMLResponse(content=html_content)
        elif task["status"] == "failed":
            error_msg = task.get("error_message", "未知错误")
            return HTMLResponse(
                content=f"<h1>处理失败</h1><p>{error_msg}</p><a href='/'>返回</a>"
            )
        else:
            progress = task.get("progress", 0)
            html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>处理中 - 图片翻译工具</title>
    <meta http-equiv="refresh" content="3;url=/api/v1/tasks/{task_id}">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 100px auto; padding: 40px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; }}
        .loading {{ font-size: 48px; margin-bottom: 20px; }}
        .progress-bar {{ width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; margin: 20px 0; }}
        .progress-fill {{ height: 100%; background: #1890ff; width: {progress}%; transition: width 0.5s; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="loading">⏳</div>
        <h2>正在处理中...</h2>
        <p>进度: {progress}%</p>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        <p style="color: #999; font-size: 14px;">{"识别中..." if progress < 50 else "翻译中..."}</p>
        <p style="margin-top: 20px; font-size: 12px; color: #999;">任务ID: {task_id}</p>
    </div>
</body>
</html>"""
            return HTMLResponse(content=html_content)

    # API调用返回JSON
    return TaskStatus(
        task_id=task["task_id"],
        status=task["status"],
        progress=task["progress"],
        result_url=f"/api/v1/download/{task_id}"
        if task["status"] == "completed"
        else None,
        detected_language=task.get("detected_language"),
        text_regions=task.get("text_regions"),
        error_message=task.get("error_message"),
    )


@router.get("/download/{task_id}")
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
        output_path,
        media_type="image/png",
        filename=f"translated_{task_id}.png",
    )


async def process_translation_task(
    task_id: str,
    upload_path: str,
    target_language: str,
    source_language: Optional[str],
):
    """后台处理翻译任务"""
    try:
        task = tasks[task_id]

        # 1. OCR识别
        task["status"] = "processing"
        task["progress"] = 20
        text_regions = ocr_service.recognize(upload_path)

        if not text_regions:
            task["status"] = "completed"
            task["progress"] = 100
            task["output_path"] = upload_path
            return

        # 2. 提取样式
        task["progress"] = 40
        regions_with_style = image_service.extract_styles(upload_path, text_regions)

        # 3. 翻译
        task["progress"] = 60
        texts = [r["text"] for r in text_regions]
        translations = translation_service.translate(
            texts, target_language, source_language
        )

        # 更新翻译结果
        for i, region in enumerate(regions_with_style):
            region["region"]["translated_text"] = translations[i]

        task["text_regions"] = [r["region"] for r in regions_with_style]
        task["detected_language"] = text_regions[0].get("language", "unknown")

        # 4. 重绘图片
        task["progress"] = 80
        output_path = f"outputs/{task_id}.png"
        image_service.redraw_image(upload_path, regions_with_style, output_path)

        task["status"] = "completed"
        task["progress"] = 100
        task["output_path"] = output_path

    except Exception as e:
        task["status"] = "failed"
        task["error_message"] = str(e)
        print(f"任务 {task_id} 处理失败: {str(e)}")
