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

# 配置 HuggingFace 国内镜像 + 缓存路径
echo "[2/5] 配置 HuggingFace..."
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf_cache
export HF_HUB_DISABLE_XET=1
export HF_HUB_DOWNLOAD_TIMEOUT=1800
mkdir -p "$HF_HOME"
echo "  镜像:  $HF_ENDPOINT"
echo "  缓存:  $HF_HOME (数据盘)"
echo "  XET:   已禁用 (避免 CDN 403)"
echo "  超时:  1800s"

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

# 启动服务（AutoDL 仅映射 6006 和 6008 端口到公网）
PORT=${INFERENCE_PORT:-6006}
echo "[5/5] 启动推理服务..."
echo "=========================================="
echo "  本地地址: http://0.0.0.0:${PORT}"
echo "  健康检查: http://0.0.0.0:${PORT}/health"
echo "  API 文档: http://0.0.0.0:${PORT}/docs"
echo "=========================================="

python server.py --port $PORT
