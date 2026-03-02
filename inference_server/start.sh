#!/bin/bash
# AutoDL 启动脚本
# 使用方式: bash start.sh

set -e

echo "=========================================="
echo "  MedGemma 推理服务器 - AutoDL 部署"
echo "=========================================="

# 检查 GPU
echo "[1/4] 检查 GPU..."
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# 安装依赖
echo "[2/4] 安装依赖..."
pip install -r requirements.txt -q

# 登录 HuggingFace（需要提前设置 HF_TOKEN 环境变量）
echo "[3/4] 检查 HuggingFace 认证..."
if [ -z "$HF_TOKEN" ]; then
    echo "警告: 未设置 HF_TOKEN 环境变量"
    echo "请运行: export HF_TOKEN=your_huggingface_token"
    echo "或在 AutoDL 的环境变量中配置"
    exit 1
fi
echo "HF_TOKEN 已设置"

# 启动服务
echo "[4/4] 启动推理服务..."
echo "服务地址: http://0.0.0.0:8080"
echo "健康检查: http://0.0.0.0:8080/health"
echo "API 文档: http://0.0.0.0:8080/docs"
echo "=========================================="

python server.py
