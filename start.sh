#!/bin/bash

# 图片翻译工具启动脚本

echo "=========================================="
echo "   图片翻译工具 - 启动脚本"
echo "=========================================="
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误：Docker未安装"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误：Docker Compose未安装"
    echo "请先安装Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker环境检查通过"
echo ""

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p uploads outputs fonts
echo "✅ 目录创建完成"
echo ""

# 检查是否已经有容器在运行
if docker-compose ps | grep -q "image-translator"; then
    echo "⚠️  发现已有服务在运行"
    read -p "是否重新启动服务？(y/n): " restart
    if [ "$restart" = "y" ] || [ "$restart" = "Y" ]; then
        echo "🔄 停止现有服务..."
        docker-compose down
        echo ""
    else
        echo "✅ 使用现有服务"
        echo ""
        echo "📋 服务访问地址："
        echo "   前端界面: http://localhost:3000"
        echo "   后端API:  http://localhost:8000"
        echo "   API文档:  http://localhost:8000/docs"
        echo ""
        exit 0
    fi
fi

# 启动服务
echo "🚀 启动服务..."
echo "（首次启动需要下载模型，大约需要3-5分钟）"
echo ""

docker-compose up -d --build

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 服务启动失败"
    echo "请检查错误信息并修复问题"
    exit 1
fi

echo ""
echo "✅ 服务启动成功！"
echo ""
echo "📋 服务访问地址："
echo "   前端界面: http://localhost:3000"
echo "   后端API:  http://localhost:8000"
echo "   API文档:  http://localhost:8000/docs"
echo ""
echo "📊 查看日志："
echo "   docker-compose logs -f"
echo ""
echo "🛑 停止服务："
echo "   docker-compose down"
echo ""
echo "=========================================="
