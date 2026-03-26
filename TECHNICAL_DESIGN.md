# 青海子宫内膜癌智能诊疗平台 — 技术设计文档

> **项目编号**: 2025-QY-220  
> **文档版本**: 2.0  
> **最后更新**: 2026-03-12  
> **适用分支**: `feat/nifti-structured-output`

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 系统总体架构](#2-系统总体架构)
- [3. 技术选型](#3-技术选型)
- [4. 数据模型设计](#4-数据模型设计)
- [5. 后端 API 设计](#5-后端-api-设计)
- [6. AI 模型与推理设计](#6-ai-模型与推理设计)
- [7. 前端设计](#7-前端设计)
- [8. 基础设施与部署](#8-基础设施与部署)
- [9. 缓存策略](#9-缓存策略)
- [10. 安全设计](#10-安全设计)
- [11. 接口规范](#11-接口规范)
- [12. 非功能性设计](#12-非功能性设计)
- [13. PRD 功能覆盖矩阵](#13-prd-功能覆盖矩阵)

---

## 1. 项目概述

### 1.1 背景

本项目为青海省科技计划项目（2025-QY-220），旨在解决青海地区老年子宫内膜癌患者面临的医疗资源分布不均、数据样本量小、预后评估手段有限等问题。通过 AI 技术构建一个集数据管理、智能分析、临床辅助决策和康复随访于一体的综合平台。

### 1.2 核心目标

| 目标 | 描述 |
|------|------|
| 标准化数据集 | 支持多中心、多模态（MRI、病理、随访）临床数据的采集、标注和管理 |
| AI 辅助诊断 | 集成 MedGemma 27B 大模型 + U-Net 分割 + 线性回归预后预测 |
| 临床决策支持 | 医生工作台可视化展示患者数据和 AI 分析结果 |
| 智能随访系统 | 远程随访、患者自助上报、自动提醒 |

### 1.3 目标用户

| 角色 | 使用端 | 典型场景 |
|------|--------|----------|
| 肿瘤科医生 | 医生端 (Web) | 查看患者 360° 视图，发起 MedGemma 分析，管理随访计划 |
| 患者 | 患者端 (H5/小程序) | 查看随访任务、填写健康问卷、上传检查报告 |
| 科研人员 | 医生端 (Web) | 导出脱敏数据，查看影像组学特征 |

---

## 2. 系统总体架构

### 2.1 架构拓扑

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              客户端层                                     │
│  ┌─────────────────────────┐   ┌──────────────────────────────────────┐  │
│  │ 医生端 (React+AntD+TS)  │   │ 患者端 (uni-app / Vue3)              │  │
│  │ • 患者管理              │   │ • 随访任务                            │  │
│  │ • 影像管理 (DICOM/NIfTI)│   │ • 健康问卷                            │  │
│  │ • MedGemma 智能分析     │   │ • 报告上传                            │  │
│  │ • 随访管理              │   │ • 医患沟通                            │  │
│  │ • 数据看板 (ECharts)    │   │                                      │  │
│  └───────────┬─────────────┘   └───────────────────┬──────────────────┘  │
└──────────────┼─────────────────────────────────────┼─────────────────────┘
               │ Vite Proxy / Nginx                  │ HTTP
               ▼                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        API 网关层 (Nginx)                                 │
│  反向代理 ─── 负载均衡 ─── SSL 终结 ─── 静态资源 ─── Gzip ─── 限流       │
└──────────────────────────────┬───────────────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    FastAPI 应用服务层 (Port 8000)                         │
│                                                                          │
│  ┌── REST API 路由 ──┐  ┌── 业务逻辑层 ──┐  ┌── AI 模型层 ──────────┐   │
│  │ /api/v1/patients  │  │ PatientService │  │ U-Net (PyTorch)      │   │
│  │ /api/v1/images    │  │ DicomService   │  │ LinearRegression     │   │
│  │ /api/v1/ai        │  │ NIfTIService   │  │ MedGemmaClient ─────────┐│
│  │ /api/v1/followup  │  │ CacheManager   │  │  (httpx → AutoDL)   │  ││
│  │ /api/v1/annotations│ │ FollowUpService│  └──────────────────────┘  ││
│  └───────────────────┘  └────────────────┘                            ││
└────────────────────────────┬──────────────────────────────────────────┘│
                             │                                          │
              ┌──────────────┼──────────────────────┐                   │
              ▼              ▼                      ▼                   │
      ┌──────────────┐ ┌──────────┐ ┌────────────────┐                 │
      │ PostgreSQL   │ │  Redis   │ │  MinIO         │                 │
      │ • 患者信息   │ │ • 热点缓存│ │ • DICOM 影像   │                 │
      │ • 随访记录   │ │ • AI 结果 │ │ • NIfTI 文件   │                 │
      │ • AI 结果    │ │ • 会话    │ │ • 缩略图/报告  │                 │
      └──────────────┘ └──────────┘ └────────────────┘                 │
                                                                       │
      ┌────────────────────────────────────────────────────────────────┘
      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│               MedGemma 推理服务器 (AutoDL 云 GPU)                         │
│  • 模型: google/medgemma-27b-it                                          │
│  • GPU:  NVIDIA RTX PRO 6000 (96GB VRAM)                                │
│  • 端口: 6006 → HTTPS 公网映射                                            │
│  • 接口: /v1/analyze/image, /v1/analyze/text, /v1/analyze/multi-image   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
医生上传 DICOM/NIfTI ──→ FastAPI 解析 ──→ MinIO 存储
                                │
                     ┌──────────┴──────────┐
                     ▼                     ▼
              U-Net 本地分割        MedGemma 远程分析
                     │                     │
                     └──────────┬──────────┘
                                ▼
                        结构化报告生成
                    (sections + summary)
                                │
                     ┌──────────┴──────────┐
                     ▼                     ▼
                PostgreSQL 持久化     Redis 缓存
                                │
                                ▼
                     前端可视化展示
                (ECharts + 结构化卡片)
```

---

## 3. 技术选型

### 3.1 技术栈总览

| 层级 | 技术 | 版本 | 理由 |
|------|------|------|------|
| **后端框架** | Python + FastAPI | 3.9+ / 0.104 | AI 生态完善，异步高性能 |
| **数据库** | PostgreSQL | 14 | JSON 字段灵活，ACID 事务保障 |
| **缓存** | Redis | 6 | 多级缓存，高吞吐 |
| **对象存储** | MinIO | latest | S3 兼容，私有化部署，医疗数据不出本地 |
| **ORM** | SQLAlchemy | 2.0 (Async) | 异步支持，类型安全 |
| **医生端前端** | React + TypeScript + Ant Design | 18 / 5.x | 组件化开发，医疗 UI 成熟 |
| **患者端前端** | uni-app + Vue 3 | HBuilderX | 多端发布（H5 / 微信小程序 / App） |
| **可视化** | ECharts (echarts-for-react) | 5.6 | 丰富的医学图表支持 |
| **AI 大模型** | MedGemma 27B-IT | 1.0 | Google 开源医学 VLM，中文能力强 |
| **AI 分割** | U-Net (PyTorch) | 2.1 | 经典医学影像分割架构 |
| **AI 预后** | scikit-learn LinearRegression | 1.3 | 可解释性强，适合临床场景 |
| **推理部署** | AutoDL + HuggingFace Transformers | - | 云 GPU 弹性算力 |
| **医学影像** | pydicom + nibabel + SimpleITK | 2.4 / 5.1 / 2.3 | 覆盖 DICOM + NIfTI 格式 |
| **容器编排** | Docker Compose | 2.0+ | 一键部署基础设施 |
| **反向代理** | Nginx | alpine | SSL 终结 + 负载均衡 |

### 3.2 选型对比

| 决策点 | 已选方案 | 备选方案 | 选择理由 |
|--------|----------|----------|----------|
| 后端语言 | Python | Java/Go | AI 库生态无可替代 (PyTorch, nibabel, pydicom) |
| AI 模型 | MedGemma 27B | 自训练 CNN | 预训练大模型泛化能力强，无需大量标注数据 |
| 推理位置 | AutoDL 云 GPU | 本地 GPU | 医院本地无 GPU 资源，云端弹性按需 |
| 患者端框架 | uni-app | 原生小程序 | 一套代码多端发布，降低维护成本 |
| 影像格式 | DICOM + NIfTI | 仅 DICOM | NIfTI 是科研场景高频格式，必须支持 |

---

## 4. 数据模型设计

### 4.1 ER 关系图

```
patients (1) ──→ (N) mri_series (1) ──→ (N) annotations
    │                     │
    │                     └──→ (N) ai_analysis_results
    │
    ├──→ (N) followup_plans (1) ──→ (N) followup_tasks (1) ──→ (N) followup_records
    │
    └──→ (N) ai_analysis_results
```

### 4.2 核心表结构

#### patients — 患者表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | 自增主键 |
| patient_no | varchar(50) UNIQUE | 患者编号 (EC + 日期 + 序号) |
| name | varchar(100) | 姓名 |
| gender | enum(male/female/other) | 性别 |
| birth_date | date | 出生日期 |
| id_card | varchar(18) | 身份证号 (加密存储) |
| phone | varchar(20) | 联系电话 |
| address | varchar(500) | 家庭地址 |
| admission_date | date | 入院日期 |
| hospital | varchar(200) | 所属医院 |
| department | varchar(100) | 科室 |
| attending_doctor | varchar(100) | 主治医生 |
| diagnosis | text | 诊断结果 |
| stage | varchar(50) | FIGO 分期 (I/II/III/IV) |
| grade | varchar(50) | 病理分级 (G1/G2/G3) |
| pathology_info | JSON | 病理信息 (灵活扩展) |
| genetic_info | JSON | 基因检测信息 |
| treatment_plan | text | 治疗方案 |
| surgery_date | date | 手术日期 |
| is_deleted | int | 软删除标记 (server_default=0) |
| created_at / updated_at | datetime | 时间戳 |

#### mri_series — MRI 序列表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | 自增主键 |
| patient_id | int FK → patients.id | 患者外键 |
| series_uid | varchar(100) UNIQUE | 序列 UID (DICOM) 或 NII-{uuid} |
| study_uid | varchar(100) | 检查 UID |
| modality | varchar(20) | 成像方式 (MR/CT) |
| series_description | varchar(200) | 描述 (含 "NIfTI:" 前缀标识格式) |
| storage_path | varchar(500) | MinIO 存储路径 |
| file_count | int | 文件数量 |
| total_size | int | 总大小 (bytes) |
| image_metadata | JSON | 元数据 (含 format、shape、voxel_size) |
| slice_thickness | float | 层厚 (mm) |
| pixel_spacing | varchar(50) | 像素间距 |
| thumbnail_path | varchar(500) | 缩略图路径 |

#### ai_analysis_results — AI 分析结果表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | 自增主键 |
| patient_id | int FK | 患者 |
| series_id | int FK (nullable) | 影像序列 |
| analysis_type | varchar(50) | 类型: segmentation / prediction / medgemma_report / medgemma_prognosis |
| tumor_volume | float | U-Net 肿瘤体积 (cm³) |
| prognosis_score | float | 回归预后评分 |
| risk_level | varchar(20) | 风险等级 (low/medium/high) |
| recurrence_probability | float | 复发概率 |
| survival_prediction | JSON | 生存率预测 |
| report_text | text | MedGemma 报告全文 |
| findings | JSON | 结构化发现 |
| diagnosis_suggestions | JSON | 诊断建议 |
| clinical_context | text | 临床上下文 |
| model_name | varchar(100) | 模型名 (U-Net / MedGemma / LinearRegression) |
| model_version | varchar(50) | 模型版本 |
| inference_time | float | 推理耗时 (秒) |

#### followup_plans / followup_tasks / followup_records

- **followup_plans**: 随访计划 (patient_id, schedule_config JSON, doctor_id)
- **followup_tasks**: 随访任务 (plan_id, task_type, scheduled_date, status enum)
- **followup_records**: 随访记录 (task_id, record_data JSON, questionnaire_answers JSON, uploaded_files JSON)

---

## 5. 后端 API 设计

### 5.1 路由总览

| 模块 | 前缀 | 端点数 | 说明 |
|------|------|--------|------|
| 患者管理 | `/api/v1/patients` | 5 | CRUD + 搜索分页 |
| 影像管理 | `/api/v1/images` | 5 | 上传(DICOM/NIfTI) + 查询 + 元数据 + 下载 |
| 标注管理 | `/api/v1/annotations` | 2 | 创建标注 + 查询 |
| AI 分析 | `/api/v1/ai` | 7 | U-Net 分割 + 回归预测 + MedGemma (影像/预后/问答/健康检查) |
| 随访管理 | `/api/v1/followup` | 6 | 计划 + 任务 + 记录 + 看板 |

### 5.2 关键 API 详细设计

#### POST `/api/v1/ai/medgemma/analyze-image`

```
请求体:
{
  "series_id": 1,
  "patient_id": 1,
  "clinical_context": "65岁女性，诊断子宫内膜癌，分期 II"
}

响应 (结构化输出):
{
  "success": true,
  "data": {
    "series_id": 1,
    "patient_id": 1,
    "report": "原始完整文本...",
    "summary": "2-3句AI总结",
    "sections": [
      {"title": "影像描述", "content": "子宫形态规则..."},
      {"title": "病灶发现", "content": "子宫内膜局部增厚..."},
      {"title": "肌层浸润评估", "content": "<50%..."},
      {"title": "分期建议", "content": "FIGO IB..."},
      {"title": "建议", "content": "建议MRI增强扫描..."}
    ],
    "format": "NIfTI",
    "inference_time": 12.3,
    "model_id": "google/medgemma-27b-it"
  }
}
```

#### POST `/api/v1/images/upload/{patient_id}`

自动检测文件格式:
- **DICOM** (`.dcm`): 调用 `DicomService` 解析元数据，批量存储到 MinIO
- **NIfTI** (`.nii/.nii.gz`): 调用 `NIfTIService` 提取轴位/冠状位/矢状位中心切片，Base64 缓存到 Redis

### 5.3 后台任务

所有 AI 结果通过 `BackgroundTasks` 异步持久化到数据库，使用独立的 `AsyncSessionLocal` 避免请求级 session 关闭后写入失败。

```python
background_tasks.add_task(
    save_medgemma_report_to_db,    # 自建 session
    patient_id, series_id, report_text, ...
)
```

### 5.4 事务管理

`get_db()` 依赖注入不自动 commit/rollback，由各端点显式管理事务。后台任务使用 `AsyncSessionLocal()` 独立 session。

---

## 6. AI 模型与推理设计

### 6.1 模型矩阵

| 模型 | 部署位置 | 输入 | 输出 | 用途 |
|------|----------|------|------|------|
| MedGemma 27B-IT | AutoDL 云 GPU (96GB) | 2D 医学影像 + 文本 | 结构化报告 | 影像分析、预后评估、医学问答 |
| U-Net | 本地 CPU/GPU | MRI 切片 (256×256) | 分割 Mask | 肿瘤区域分割 |
| LinearRegression | 本地 CPU | 临床特征向量 (8维) | 风险评分 | 预后风险预测 |

### 6.2 MedGemma 推理流程

```
本地后端                           AutoDL 推理服务器
   │                                    │
   │── 1. 上传 NIfTI/DICOM ─→          │
   │   (NIfTI: 提取3个切面)             │
   │                                    │
   │── 2. POST /v1/analyze/image ──→    │
   │   (Base64 PNG + 结构化 prompt)     │
   │                                    │
   │                              3. MedGemma 推理
   │                                 (12-30s)
   │                                    │
   │←── 4. 返回原始文本 ───────────     │
   │                                    │
   │   5. parse_structured_report()     │
   │      【影像描述】→ section          │
   │      【病灶发现】→ section          │
   │      【总结】→ summary              │
   │                                    │
   │   6. 返回前端 (sections + summary) │
```

### 6.3 NIfTI 3D → 2D 切片转换

MedGemma 只支持 2D 图像输入。NIfTI 处理流程:

1. `nibabel` 加载 `.nii/.nii.gz` 文件为 3D numpy 数组
2. 提取 3 个标准平面中心切片 (axial / coronal / sagittal)
3. 自适应窗宽窗位归一化 (P2-P98 百分位)
4. 转为 PNG Base64，通过 `/v1/analyze/multi-image` 多图端点发送

### 6.4 结构化输出解析

MedGemma 输出的带 `【xxx】` 标记的报告通过 `parse_structured_report()` 解析:

```python
输入: "【影像描述】子宫形态规则...【病灶发现】内膜局部增厚...【总结】中等风险..."

输出: {
  "sections": [
    {"title": "影像描述", "content": "子宫形态规则..."},
    {"title": "病灶发现", "content": "内膜局部增厚..."}
  ],
  "summary": "中等风险...",
  "raw": "原始完整文本"
}
```

### 6.5 推理服务器配置

| 参数 | 值 | 说明 |
|------|-----|------|
| 模型 | google/medgemma-27b-it | 270亿参数医学 VLM |
| 精度 | bfloat16 (96GB GPU) / 4-bit量化 (40GB) | 自动根据 VRAM 选择 |
| 端口 | 6006 (AutoDL 映射) | HTTPS 公网访问 |
| 超时 | 180s | 27B 推理较慢 |
| 重试 | 2 次 (指数退避) | 网络不稳定保护 |
| 镜像 | hf-mirror.com | 国内网络加速 |

---

## 7. 前端设计

### 7.1 医生端 (React)

#### 页面结构

| 路由 | 组件 | 功能 |
|------|------|------|
| `/patients` | PatientList | 患者列表，分页搜索 |
| `/patients/:id` | PatientDetail | 患者 360° 视图 (5 个 Tab) |
| `/images` | ImageManage | 影像上传(DICOM/NIfTI)、AI 分析 |
| `/followup` | FollowUp | 随访计划创建、任务管理 |
| `/dashboard` | Dashboard | 数据看板 (ECharts) |

#### PatientDetail 五大 Tab

1. **基本信息** — Descriptions 展示患者基础数据
2. **影像数据** — 上传 DICOM/NIfTI，一键触发 U-Net 分割 / MedGemma 分析
3. **AI 分析结果** — AIResultCard 可视化 (RiskGauge + SurvivalChart)
4. **MedGemma 智能分析** — 预后评估表单 + 自由医学问答
5. **随访记录** — 任务列表与状态

#### 结构化报告展示 (StructuredReportViewer)

```
┌─────────────────────────────────────────┐
│ 📄 MedGemma 影像分析报告    [NIfTI] 12.3s │
├─────────────────────────────────────────┤
│ ✅ AI 总结                               │
│ 中等风险，建议进一步增强扫描...            │
├─────────────────────────────────────────┤
│ 影像描述                                 │
│ 子宫形态规则，内膜信号不均匀...            │
│─────────────────────────────────────────│
│ 病灶发现                                 │
│ 子宫内膜局部增厚约 1.2cm...               │
│─────────────────────────────────────────│
│ 肌层浸润评估                              │
│ 浸润深度 <50%...                          │
│─────────────────────────────────────────│
│ 分期建议                                 │
│ FIGO IB 期...                            │
└─────────────────────────────────────────┘
```

### 7.2 患者端 (uni-app)

| 页面 | 功能 |
|------|------|
| `/pages/login` | 患者编号 + 手机号登录 |
| `/pages/index` | 首页: 待办任务 + 最新 AI 报告摘要 |
| `/pages/task` | 任务详情: 问卷填写 / 报告上传 |
| `/pages/health` | 健康自评问卷 |
| `/pages/report` | 检查报告图片上传 |
| `/pages/history` | 随访历史 + AI 报告列表 |
| `/pages/contact` | 联系医生 (电话/留言) |

---

## 8. 基础设施与部署

### 8.1 Docker Compose 服务

| 服务 | 镜像 | 端口 | 数据卷 |
|------|------|------|--------|
| postgres | postgres:14 | 5432 | postgres_data |
| redis | redis:6-alpine | 6379 | redis_data |
| minio | minio/minio:latest | 9000/9001 | minio_data |
| backend | ./backend/Dockerfile | 8000 | backend_logs |
| frontend-doctor | ./frontend-doctor/Dockerfile | 3000 | - |
| nginx | nginx:alpine | 80/443 | nginx.conf |

### 8.2 本地开发模式

```
Docker: postgres + redis + minio
本地:   FastAPI (port 8000) + Vite DevServer (port 3000, proxy → 8000)
云端:   AutoDL MedGemma (port 6006 → HTTPS)
```

### 8.3 Vite 代理配置

```typescript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
}
```

---

## 9. 缓存策略

### 三级缓存架构

```
L1: 浏览器 (ETag + Cache-Control)
 ↓ miss
L2: Redis
 ├─ patient:info:{id}          TTL = 1h
 ├─ patient:list:page:{n}     TTL = 10min
 ├─ dicom:meta:{series_uid}   TTL = 24h (含 NIfTI 切片 base64)
 ├─ ai:segmentation:{sid}     TTL = 永久
 ├─ ai:medgemma_report:{sid}  TTL = 永久
 └─ ai:medgemma_prognosis:{pid} TTL = 永久
 ↓ miss
L3: PostgreSQL
```

### 缓存失效策略

- **主动失效**: 数据更新时使用 `scan_iter` 批量清除相关缓存
- **被动失效**: TTL 自动过期
- **LRU 淘汰**: Redis maxmemory-policy allkeys-lru

---

## 10. 安全设计

| 维度 | 方案 |
|------|------|
| 认证 | JWT (HS256) + Bearer Token |
| 传输加密 | TLS 1.3 (Nginx SSL 终结) |
| 敏感字段 | AES-256 加密 (身份证、电话) |
| 对象存储 | MinIO SSE-S3 服务端加密 |
| CORS | 白名单 (localhost:3000, localhost:3001) |
| SQL 注入 | SQLAlchemy ORM 参数化查询 |
| 输入验证 | Pydantic BaseModel 严格校验 |
| 数据脱敏 | 科研导出时移除 PII，年龄分段处理 |
| 软删除 | is_deleted 标记，物理数据保留 |

---

## 11. 接口规范

### 统一响应格式

```json
{
  "success": true,
  "message": "操作描述",
  "data": { ... }
}
```

### 错误响应

```json
{
  "success": false,
  "message": "错误描述",
  "error": "详细错误信息 (仅 DEBUG 模式)"
}
```

### HTTP 状态码约定

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 422 | 参数验证失败 (Pydantic) |
| 500 | 服务器内部错误 |
| 502 | AI 推理服务不可用 |

---

## 12. 非功能性设计

### 性能指标

| 指标 | 目标值 |
|------|--------|
| API 响应 (普通查询) | < 200ms |
| MRI 序列加载 | < 5s |
| U-Net 分割推理 | < 30s |
| MedGemma 影像分析 | < 60s |
| MedGemma 预后分析 | < 30s |
| 并发用户 | ≥ 50 (单实例) |
| 数据库连接池 | 20 + 40 overflow |

### 可靠性

- MedGemma 服务不可用时，其他功能正常运行（降级设计）
- 后台任务失败不影响 API 响应
- 数据库事务由端点显式管理，避免双重 commit/rollback

### 可观测性

- Loguru 结构化日志 (stdout + 文件轮转)
- Prometheus 指标 (api_requests_total, ai_inference_seconds)
- `/health` 端点（数据库/缓存/AI 服务状态）

---

## 13. PRD 功能覆盖矩阵

| PRD ID | 功能 | 状态 | 实现技术 |
|--------|------|------|----------|
| F-DM-01 | 创建新病例 | ✅ | FastAPI + PostgreSQL + 编号自动生成 (防冲突重试) |
| F-DM-02 | 结构化信息录入 | ✅ | Pydantic 验证 + JSON 字段灵活扩展 |
| F-DM-03 | 影像数据上传 | ✅ | DICOM (pydicom) + NIfTI (nibabel) + MinIO |
| F-DM-04 | AI 辅助影像标注 | ✅ | U-Net 分割 + MedGemma 影像分析 |
| F-DM-05 | 数据质控 | 🔄 | 审核工作流框架就绪 |
| F-AI-01 | U-Net 病灶分割 | ✅ | PyTorch + asyncio.to_thread 异步推理 |
| F-AI-02 | 影像组学特征提取 | 🔄 | PyRadiomics 框架就绪 |
| F-AI-03 | 预后预测 | ✅ | LinearRegression + MedGemma LLM 双通道 |
| F-CD-01 | 患者列表与检索 | ✅ | 分页 + 关键词搜索 + Redis 缓存 |
| F-CD-02 | 患者 360° 视图 | ✅ | 5-Tab 设计 (基本信息/影像/AI/MedGemma/随访) |
| F-CD-03 | AI 结果可视化 | ✅ | RiskGauge + SurvivalChart + StructuredReportViewer |
| F-FU-01 | 创建随访计划 | ✅ | 计划 + 自动生成任务 (原子事务) |
| F-FU-02 | 任务自动提醒 | ✅ | Celery 定时任务 + 微信模板消息 |
| F-FU-03 | 患者端应用 | ✅ | uni-app (7页面: 登录/首页/任务/问卷/上传/历史/联系) |
| F-FU-04 | 随访数据看板 | ✅ | Dashboard (ECharts 饼图 + 柱状图 + 逾期告警) |

---

## 附录: 目录结构

```
TD/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py            # 应用入口 + 生命周期
│   │   ├── config.py          # Pydantic 配置管理
│   │   ├── core/
│   │   │   ├── database.py    # SQLAlchemy 异步引擎
│   │   │   └── cache.py       # Redis 缓存管理器
│   │   ├── models/
│   │   │   ├── patient.py     # 患者模型
│   │   │   ├── image.py       # 影像 + 标注 + AI 结果模型
│   │   │   └── followup.py    # 随访模型
│   │   ├── api/v1/
│   │   │   ├── patients.py    # 患者 CRUD
│   │   │   ├── images.py      # 影像上传 (DICOM/NIfTI)
│   │   │   ├── annotations.py # 标注管理
│   │   │   ├── ai.py          # AI 分析端点
│   │   │   └── followup.py    # 随访管理
│   │   ├── ml/
│   │   │   ├── unet_model.py       # U-Net 推理服务
│   │   │   ├── regression_model.py  # 线性回归预后
│   │   │   └── medgemma_service.py  # MedGemma 客户端 + 结构化解析
│   │   └── services/
│   │       ├── dicom_service.py     # DICOM 处理
│   │       └── nifti_service.py     # NIfTI 3D→2D 切片
│   ├── .env                   # 环境变量
│   └── requirements.txt       # Python 依赖
├── frontend-doctor/           # 医生端 React
│   ├── src/
│   │   ├── App.tsx            # 路由 + 布局
│   │   ├── services/api.ts    # Axios 封装 + API 定义
│   │   ├── components/
│   │   │   └── AIResultViz.tsx  # RiskGauge + SurvivalChart
│   │   └── pages/
│   │       ├── PatientList/
│   │       ├── PatientDetail/   # 360° 视图 + StructuredReportViewer
│   │       ├── ImageManage/
│   │       ├── FollowUp/
│   │       └── Dashboard/
│   └── vite.config.ts         # Vite 代理配置
├── frontend-patient/          # 患者端 uni-app
│   ├── pages/                 # 7 个页面
│   ├── utils/api.js           # 统一 API 封装
│   └── pages.json             # 路由配置
├── inference_server/          # MedGemma 推理 (部署到 AutoDL)
│   ├── server.py              # FastAPI 推理端点
│   └── start.sh               # AutoDL 启动脚本
├── docker-compose.yml         # 基础设施编排
├── nginx.conf                 # 反向代理配置
└── TECHNICAL_DESIGN.md        # 本文档
```
