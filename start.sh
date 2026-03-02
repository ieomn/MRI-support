#!/bin/bash

echo "======================================"
echo "青海子宫内膜癌智能诊疗平台 V1.0"
echo "======================================"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未检测到Docker，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: 未检测到Docker Compose，请先安装Docker Compose"
    exit 1
fi

echo "✅ Docker环境检查通过"
echo ""

# 检查.env文件
if [ ! -f "backend/.env" ]; then
    echo "📝 创建后端环境配置文件..."
    cp backend/.env.example backend/.env 2>/dev/null || echo "警告: 未找到.env.example文件"
fi

echo "🚀 启动服务..."
echo ""

# 启动所有服务
docker-compose up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "📊 服务状态:"
docker-compose ps

echo ""
echo "======================================"
echo "✅ 系统启动成功！"
echo "======================================"
echo ""
echo "访问地址:"
echo "  医生端前端: http://localhost:3000"
echo "  API文档:    http://localhost:8000/docs"
echo "  健康检查:   http://localhost:8000/health"
echo "  MinIO控制台: http://localhost:9001"
echo "    账号: minioadmin"
echo "    密码: minioadmin"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f backend"
echo "  停止服务: docker-compose stop"
echo "  重启服务: docker-compose restart"
echo "  完全清理: docker-compose down -v"
echo ""
echo "更多信息请查看 README.md 和 DEPLOY.md"
echo "======================================"

