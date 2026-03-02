#!/bin/bash
# AutoDL 启动脚本
# 使用方式: bash start.sh

set -e

echo "=========================================="
echo "  MedGemma 推理服务器 - AutoDL 部署"
echo "=========================================="

# 检查 GPU
echo "[1/5] 检查 GPU..."
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# 配置 HuggingFace 国内镜像（AutoDL 等国内服务器必须）
echo "[2/5] 配置 HuggingFace 镜像..."
export HF_ENDPOINT=https://hf-mirror.com
echo "已设置 HF_ENDPOINT=$HF_ENDPOINT"

# 安装依赖
echo "[3/5] 安装依赖..."
pip install -r requirements.txt -q

# 检查 HuggingFace 认证
echo "[4/5] 检查 HuggingFace 认证..."
if [ -z "$HF_TOKEN" ]; then
    echo "======================================="
    echo "  错误: 未设置 HF_TOKEN 环境变量"
    echo "  请运行: export HF_TOKEN=hf_xxxxxxxxx"
    echo "======================================="
    exit 1
fi
echo "HF_TOKEN 已设置"

# 测试镜像连通性
echo "测试镜像连通性..."
if curl -s --max-time 10 https://hf-mirror.com > /dev/null 2>&1; then
    echo "hf-mirror.com 连通正常"
else
    echo "警告: hf-mirror.com 连接超时，尝试备用方案..."
    # 备用镜像
    export HF_ENDPOINT=https://huggingface.sukaka.top
    echo "已切换到备用镜像: $HF_ENDPOINT"
fi

# 启动服务
echo "[5/5] 启动推理服务..."
echo "=========================================="
echo "  服务地址: http://0.0.0.0:8080"
echo "  健康检查: http://0.0.0.0:8080/health"
echo "  API 文档: http://0.0.0.0:8080/docs"
echo "=========================================="

python server.py
