#!/usr/bin/env python3
"""
图片翻译工具 - 完整启动脚本
"""

import subprocess
import sys
import os
import time


def start_backend():
    """启动后端服务"""
    print("🚀 启动图片翻译服务...")
    print("")

    # 切换到backend目录
    backend_dir = "/home/admin/image-translator/backend"
    os.chdir(backend_dir)

    # 设置Python路径
    sys.path.insert(0, backend_dir)

    # 启动服务
    try:
        import uvicorn
        from app_simple import app

        print("📡 服务地址:")
        print("   网页界面: http://localhost:8000")
        print("   API文档:  http://localhost:8000/docs")
        print("   语言列表: http://localhost:8000/api/v1/languages")
        print("")
        print("⚠️  当前为演示版本，会返回原图（无真实OCR翻译）")
        print("💡 按 Ctrl+C 停止服务")
        print("")
        print("=" * 50)

        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_backend()
