# 青海子宫内膜癌智能诊疗平台 - 完整操作手册

> 本手册覆盖从零配置到完成一次 MedGemma 推理的全流程，适用于 Windows 本地开发环境。

---

## 目录

- [一、环境要求](#一环境要求)
- [二、基础设施启动（PostgreSQL / Redis / MinIO）](#二基础设施启动)
- [三、MedGemma 推理服务部署（AutoDL 云 GPU）](#三medgemma-推理服务部署)
- [四、后端启动（FastAPI）](#四后端启动)
- [五、前端启动（React 医生端）](#五前端启动)
- [六、端到端验证](#六端到端验证)
- [七、API 接口速查](#七api-接口速查)
- [八、常见问题排查](#八常见问题排查)

---

## 一、环境要求

### 本地机器（你的 Windows 电脑）

| 软件 | 版本要求 | 用途 |
|------|----------|------|
| Python | 3.9+ | 后端运行 |
| Node.js | 18+ | 前端运行 |
| Docker Desktop | 最新版 | 运行 PostgreSQL / Redis / MinIO |
| Git | 最新版 | 代码管理 |

### 云端（AutoDL）

| 资源 | 要求 | 用途 |
|------|------|------|
| GPU | A100 40GB（推荐）或 A800 | 运行 MedGemma 27B |
| 系统镜像 | PyTorch 2.1+ / CUDA 12.x | 推理框架 |
| HuggingFace Token | 需提前申请 | 下载 MedGemma 模型权重 |

---

## 二、基础设施启动

> 使用 Docker Compose 一键启动数据库、缓存和对象存储。

### 2.1 启动服务

在项目根目录打开终端：

```powershell
# 仅启动基础设施（不启动 backend 和 frontend 容器，我们用本地运行）
docker compose up -d postgres redis minio
```

### 2.2 验证服务状态

```powershell
docker compose ps
```

应看到三个容器均为 `running (healthy)` 状态：

| 服务 | 端口 | 访问地址 |
|------|------|----------|
| PostgreSQL | 5432 | `localhost:5432` |
| Redis | 6379 | `localhost:6379` |
| MinIO | 9000 / 9001 | API: `localhost:9000`，控制台: `http://localhost:9001` |

### 2.3 MinIO 初始化（首次）

1. 浏览器打开 `http://localhost:9001`
2. 登录：用户名 `minioadmin`，密码 `minioadmin`
3. 创建两个 Bucket：
   - `dicom-images`（存储 DICOM 影像）
   - `patient-reports`（存储患者报告）

---

## 三、MedGemma 推理服务部署

> 在 AutoDL 租用 A100 GPU 实例，部署 MedGemma 27B 推理服务器。

### 3.1 准备 HuggingFace Token

1. 注册 HuggingFace 账号：https://huggingface.co/join
2. 访问 MedGemma 模型页面，接受使用条款：https://huggingface.co/google/medgemma-27b-it
3. 生成 Access Token：https://huggingface.co/settings/tokens（选择 `Read` 权限）
4. 记下 Token，后续会用到

### 3.2 AutoDL 实例创建

1. 登录 AutoDL（https://www.autodl.com）
2. 创建实例：
   - **GPU**：选择 `A100-40GB` 或 `A100-80GB`
   - **镜像**：选择 `PyTorch 2.1.0` + `Python 3.10` + `CUDA 12.1`
   - **数据盘**：建议 50GB+（模型权重约 15-20GB，量化后更小）
3. 启动实例，通过 JupyterLab 或 SSH 连接

### 3.3 上传推理服务代码

将 `inference_server/` 目录上传到 AutoDL 实例。可以通过 JupyterLab 上传，或用 SCP：

```bash
# 从本地 Windows 用 SCP 上传（替换为你的实例信息）
scp -P <端口> -r inference_server/ root@<AutoDL地址>:/root/
```

### 3.4 配置环境变量

SSH 连接到 AutoDL 实例后：

```bash
# 设置 HuggingFace 国内镜像（AutoDL 必须，否则无法连接 huggingface.co）
export HF_ENDPOINT=https://hf-mirror.com

# 设置 HuggingFace Token（替换为你的实际 Token）
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 写入 bashrc 使其持久化
echo 'export HF_ENDPOINT=https://hf-mirror.com' >> ~/.bashrc
echo 'export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"' >> ~/.bashrc
```

> **关键**：`HF_ENDPOINT` 是解决国内服务器无法访问 HuggingFace 的核心配置。
> `start.sh` 脚本会自动设置此变量，但手动写入 `~/.bashrc` 可确保持久化。

### 3.5 启动推理服务

```bash
cd /root/inference_server
bash start.sh
```

脚本会自动：
- 配置 HuggingFace 国内镜像
- 测试镜像连通性（不通则自动切换备用镜像）
- 根据 GPU 显存自动决定是否启用量化（>=60GB 不量化，<60GB 开启 4-bit 量化）

首次启动会下载模型权重（约 15-50GB），请耐心等待。下载完成后会看到：

```
MedGemma 模型加载完成 (GPU 显存占用: xx.x GB)
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### 3.6 验证推理服务

在 AutoDL 实例内验证：

```bash
curl http://localhost:8080/health
```

应返回：

```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_id": "google/medgemma-27b-it",
  "gpu": "NVIDIA A100-SXM4-40GB",
  "gpu_memory_allocated": "18.3 GB"
}
```

### 3.7 获取公网访问地址

AutoDL 提供两种公网访问方式：

**方式一：自定义服务端口映射（推荐）**

1. 在 AutoDL 控制台 → 实例详情 → 自定义服务
2. 添加端口 `8080` 的映射
3. 获得公网 URL，格式类似：`https://u-xxxxx-8080.westb.seetacloud.com`

**方式二：SSH 端口转发（临时调试用）**

```powershell
# 在本地 Windows 终端执行
ssh -L 8080:localhost:8080 -p <端口> root@<AutoDL地址>
```

此时本地 `localhost:8080` 会转发到 AutoDL 的推理服务。

### 3.8 记下推理服务地址

后续配置需要用到，例如：
- SSH 转发模式：`http://localhost:8080`
- AutoDL 自定义服务：`https://u-xxxxx-8080.westb.seetacloud.com`

---

## 四、后端启动

### 4.1 创建 Python 虚拟环境

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4.2 安装依赖

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4.3 创建 .env 配置文件

在 `backend/` 目录下创建 `.env` 文件：

```ini
# ===== 基础配置 =====
DEBUG=True
HOST=0.0.0.0
PORT=8000

# ===== 数据库（Docker 中的 PostgreSQL）=====
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/endometrial_cancer

# ===== Redis 缓存 =====
REDIS_HOST=localhost
REDIS_PORT=6379

# ===== MinIO 对象存储 =====
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# ===== MedGemma 远程推理（关键！填写你的推理服务地址）=====
MEDGEMMA_API_URL=http://localhost:8080
MEDGEMMA_API_TIMEOUT=120
MEDGEMMA_MODEL_ID=google/medgemma-27b-it

# ===== CORS（允许前端访问）=====
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]

# ===== JWT =====
SECRET_KEY=your-dev-secret-key-change-in-production

# ===== 日志 =====
LOG_LEVEL=DEBUG
```

> **重要**：将 `MEDGEMMA_API_URL` 改为你在步骤 3.7 获得的实际地址。
> 如果使用 AutoDL 自定义服务，格式为 `https://u-xxxxx-8080.westb.seetacloud.com`。
> 如果使用 SSH 端口转发，保持 `http://localhost:8080`。

### 4.4 创建日志目录

```powershell
mkdir logs
```

### 4.5 初始化数据库

数据库表会在应用启动时通过 SQLAlchemy 自动创建。如需手动创建数据库：

```powershell
# 连接 Docker 中的 PostgreSQL
docker exec -it tengda-postgres psql -U postgres

# 在 psql 中执行
CREATE DATABASE endometrial_cancer;
\q
```

### 4.6 启动后端

```powershell
# 确保虚拟环境已激活
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

成功启动后会看到类似输出：

```
2026-03-02 12:00:00 | INFO     | 🚀 应用启动中...
2026-03-02 12:00:01 | INFO     | ✓ 数据库初始化完成
2026-03-02 12:00:01 | INFO     | ✓ Redis缓存连接成功
2026-03-02 12:00:02 | INFO     | ✓ MedGemma 推理服务连接成功 (GPU: NVIDIA A100-SXM4-40GB)
2026-03-02 12:00:02 | INFO     | 🎉 青海子宫内膜癌智能诊疗平台 v1.0.0 启动成功!
```

> 如果 MedGemma 服务未启动，会显示警告但**不影响**其他功能。

### 4.7 验证后端

- Swagger 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- MedGemma 状态：http://localhost:8000/api/v1/ai/medgemma/health

---

## 五、前端启动

### 5.1 安装依赖

打开新终端：

```powershell
cd frontend-doctor
npm install
```

### 5.2 创建环境变量文件

在 `frontend-doctor/` 目录下创建 `.env.local` 文件：

```ini
# API 地址 - 使用相对路径，通过 Vite 代理转发到后端
VITE_API_BASE_URL=/api/v1
```

> **说明**：`vite.config.ts` 已配置将 `/api` 开头的请求代理到 `http://localhost:8000`，
> 所以前端使用 `/api/v1` 相对路径即可，无需写完整地址。

### 5.3 启动开发服务器

```powershell
npm start
```

成功启动后会看到：

```
  VITE v5.0.4  ready in 1234 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.x.x:3000/
```

### 5.4 访问前端

浏览器打开 http://localhost:3000

---

## 六、端到端验证

### 6.1 架构总览

确认所有服务都在运行：

```
┌─────────────────────────────────────────────────────┐
│  你的 Windows 电脑                                   │
│                                                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────┐ │
│  │ 前端     │──→│ 后端     │──→│ Docker           │ │
│  │ :3000    │   │ :8000    │   │ PostgreSQL :5432  │ │
│  │ (React)  │   │ (FastAPI)│   │ Redis      :6379  │ │
│  └──────────┘   └────┬─────┘   │ MinIO  :9000/9001│ │
│                      │         └──────────────────┘ │
└──────────────────────┼──────────────────────────────┘
                       │ HTTP
                       ▼
              ┌──────────────────┐
              │  AutoDL 云 GPU    │
              │  MedGemma 27B    │
              │  :8080           │
              │  (A100 GPU)      │
              └──────────────────┘
```

### 6.2 逐步验证

**第 1 步：验证基础设施**

```powershell
# PostgreSQL
docker exec -it tengda-postgres pg_isready -U postgres
# 应返回: accepting connections

# Redis
docker exec -it tengda-redis redis-cli ping
# 应返回: PONG

# MinIO
curl http://localhost:9000/minio/health/live
# 或浏览器访问 http://localhost:9001
```

**第 2 步：验证后端 API**

```powershell
# 健康检查
curl http://localhost:8000/health

# 应返回:
# {"status":"healthy","database":"connected","cache":"connected"}
```

**第 3 步：验证 MedGemma 连接**

```powershell
curl http://localhost:8000/api/v1/ai/medgemma/health
```

应返回推理服务器的详细状态（GPU 型号、显存占用等）。

**第 4 步：测试完整推理流程**

使用 Swagger UI（http://localhost:8000/docs）或 curl 测试：

```powershell
# 1. 创建一个测试患者
curl -X POST http://localhost:8000/api/v1/patients/ ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"测试患者\",\"gender\":\"female\",\"hospital\":\"青海大学附属医院\"}"
```

记下返回的 `patient_id`（假设为 1）。

```powershell
# 2. 测试 MedGemma 预后分析（纯文本，无需影像）
curl -X POST http://localhost:8000/api/v1/ai/medgemma/analyze-prognosis ^
  -H "Content-Type: application/json" ^
  -d "{\"patient_id\":1,\"clinical_data\":{\"age\":55,\"stage\":\"II\",\"grade\":2,\"tumor_size\":3.5,\"lymph_node_positive\":0,\"bmi\":24.5}}"
```

应返回 MedGemma 生成的结构化预后评估报告。

```powershell
# 3. 测试 MedGemma 自由问答
curl -X POST http://localhost:8000/api/v1/ai/medgemma/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"子宫内膜癌FIGO IB期，高分化，推荐的标准治疗方案是什么？\"}"
```

**第 5 步：测试前端页面**

1. 浏览器打开 http://localhost:3000
2. 应能看到患者列表页面
3. 创建患者 → 查看详情 → AI 分析功能

---

## 七、API 接口速查

### 原有接口（保留）

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | `/api/v1/ai/segment` | U-Net MRI 分割 |
| POST | `/api/v1/ai/predict-prognosis` | 线性回归预后预测 |
| GET | `/api/v1/ai/results/patient/{id}` | 获取患者全部 AI 结果 |

### MedGemma 新增接口

| 方法 | 端点 | 功能 | 说明 |
|------|------|------|------|
| GET | `/api/v1/ai/medgemma/health` | 推理服务状态 | 检查 GPU、模型加载状态 |
| POST | `/api/v1/ai/medgemma/analyze-image` | 影像分析报告 | 输入 series_id，输出子宫内膜癌 MRI 结构化报告 |
| POST | `/api/v1/ai/medgemma/analyze-prognosis` | LLM 预后评估 | 输入临床数据，输出风险评估+治疗建议 |
| POST | `/api/v1/ai/medgemma/ask` | 自由医学问答 | 支持纯文本或附带影像的问答 |

### 请求示例

**影像分析**：
```json
POST /api/v1/ai/medgemma/analyze-image
{
    "series_id": 1,
    "patient_id": 1,
    "clinical_context": "55岁女性，绝经后阴道出血2月，CA125轻度升高"
}
```

**预后分析**：
```json
POST /api/v1/ai/medgemma/analyze-prognosis
{
    "patient_id": 1,
    "clinical_data": {
        "age": 55,
        "bmi": 24.5,
        "stage": "II",
        "grade": 2,
        "tumor_size": 3.5,
        "lymph_node_positive": 0,
        "histology": "子宫内膜样腺癌",
        "myometrial_invasion": ">=50%",
        "lvsi": false
    }
}
```

**自由问答**：
```json
POST /api/v1/ai/medgemma/ask
{
    "question": "子宫内膜癌术后辅助治疗的指征有哪些？"
}
```

---

## 八、常见问题排查

### 8.1 后端启动报错

| 错误 | 原因 | 解决 |
|------|------|------|
| `connection refused :5432` | PostgreSQL 未启动 | `docker compose up -d postgres` |
| `connection refused :6379` | Redis 未启动 | `docker compose up -d redis` |
| `MedGemma 推理服务不可用` | 推理服务未启动或网络不通 | 检查 AutoDL 实例状态和 `MEDGEMMA_API_URL` 配置 |
| `No module named 'app'` | 运行目录不对 | 确保在 `backend/` 目录下运行 |

### 8.2 MedGemma 推理服务问题

| 错误 | 原因 | 解决 |
|------|------|------|
| `Network is unreachable` / 连接超时 | 国内服务器无法访问 huggingface.co | 设置 `export HF_ENDPOINT=https://hf-mirror.com`（start.sh 已自动处理） |
| `OutOfMemoryError` | GPU 显存不足 | 设置 `export USE_QUANTIZATION=true` 启用 4-bit 量化 |
| `401 Unauthorized` | HuggingFace Token 无效 | 检查 `HF_TOKEN` 环境变量，确认已在 HF 页面接受模型使用条款 |
| `RuntimeError: client has been closed` | HF 库网络重试失败 | 确认 `HF_ENDPOINT` 已设置为镜像地址 |
| 模型下载慢 | 镜像速度波动 | 首次下载 27B 约需 10-30 分钟，耐心等待 |
| `CUDA out of memory` | 推理时显存溢出 | 减少 `max_new_tokens`，或限制输入图片数量 |

### 8.3 前端问题

| 错误 | 原因 | 解决 |
|------|------|------|
| API 请求 404 | API 地址配置错误 | 确认 `.env.local` 中 `VITE_API_BASE_URL=/api/v1` |
| CORS 错误 | 后端未允许前端域名 | 检查后端 `.env` 中 `CORS_ORIGINS` 包含 `http://localhost:3000` |
| 页面空白 | Node.js 版本过低 | 升级到 Node.js 18+ |

### 8.4 性能参考

| 操作 | 预期耗时 | 说明 |
|------|----------|------|
| 首次模型下载 | 10-30 分钟 | 取决于网络速度，约 15-20GB |
| 模型加载 | 2-5 分钟 | 启动时一次性加载到 GPU |
| 单张影像分析 | 15-60 秒 | 取决于 prompt 长度和 max_new_tokens |
| 纯文本问答 | 5-30 秒 | 文本推理通常更快 |
| 多图序列分析 | 30-120 秒 | 图片越多越慢 |

---

## 附录：快速启动清单

按顺序执行，从零到完整运行：

```
□ 1. 安装 Docker Desktop、Python 3.9+、Node.js 18+
□ 2. docker compose up -d postgres redis minio
□ 3. 在 MinIO 控制台创建 dicom-images 和 patient-reports Bucket
□ 4. 在 AutoDL 创建 A100 实例并上传 inference_server/ 代码
□ 5. AutoDL 设置 HF_TOKEN，运行 bash start.sh
□ 6. 获取 AutoDL 推理服务公网地址
□ 7. 在 backend/ 创建 .env，配置 MEDGEMMA_API_URL
□ 8. cd backend && python -m venv venv && .\venv\Scripts\Activate.ps1
□ 9. pip install -r requirements.txt
□ 10. python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
□ 11. 新终端：cd frontend-doctor && npm install
□ 12. 创建 .env.local，写入 VITE_API_BASE_URL=/api/v1
□ 13. npm start
□ 14. 浏览器打开 http://localhost:3000
□ 15. 在 Swagger (http://localhost:8000/docs) 测试 MedGemma 接口
```
