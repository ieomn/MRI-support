# 技术架构详解

## 📐 系统架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                           客户端层                                │
├───────────────────────────┬─────────────────────────────────────┤
│  医生端 (React + Ant D)    │  患者端 (uni-app 小程序/H5)        │
│  - 患者管理               │  - 随访任务列表                     │
│  - 影像标注               │  - 健康问卷填写                     │
│  - AI分析查看             │  - 报告上传                         │
│  - 随访管理               │  - 医患沟通                         │
└───────────────────────────┴─────────────────────────────────────┘
                                   │
                                   │ HTTPS/WSS
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API网关层 (Nginx)                         │
│  - 反向代理              - 负载均衡              - SSL终结      │
│  - 静态资源服务          - Gzip压缩              - 限流保护      │
└─────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
┌─────────────────────────────┐    ┌─────────────────────────────┐
│    FastAPI应用服务层         │    │    Celery异步任务队列        │
│  ┌─────────────────────┐   │    │  - AI模型推理               │
│  │  REST API路由       │   │    │  - 随访提醒                 │
│  │  - /patients        │   │    │  - 数据预处理               │
│  │  - /images          │   │    │  - 报告生成                 │
│  │  - /ai              │   │    └─────────────────────────────┘
│  │  - /followup        │   │
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │  业务逻辑层          │   │
│  │  - PatientService   │   │
│  │  - DicomService     │   │
│  │  - AIService        │   │
│  │  - FollowUpService  │   │
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │  AI模型层           │   │
│  │  - U-Net (PyTorch)  │   │
│  │  - LinearRegression │   │
│  │  - 影像组学特征提取  │   │
│  └─────────────────────┘   │
└─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                          数据访问层                              │
├──────────────┬──────────────────┬────────────────┬──────────────┤
│ PostgreSQL   │ Redis Cache      │ MinIO Storage  │ 消息队列     │
│ - 结构化数据 │ - 热点数据缓存   │ - DICOM影像    │ - RabbitMQ   │
│ - 患者信息   │ - AI结果缓存     │ - 缩略图       │   (可选)     │
│ - 随访记录   │ - 会话管理       │ - 患者报告     │              │
└──────────────┴──────────────────┴────────────────┴──────────────┘
```

## 🎯 关键技术选型理由

### 1. 后端: Python + FastAPI

**选型理由:**
- ✅ **AI生态完善**: PyTorch、TensorFlow、scikit-learn无缝集成
- ✅ **医学影像处理**: pydicom、SimpleITK、nibabel成熟稳定
- ✅ **高性能异步**: 基于Starlette和Pydantic，性能接近Go
- ✅ **自动API文档**: Swagger UI开箱即用，降低前后端对接成本
- ✅ **类型安全**: Type Hints + Pydantic数据验证

**对比其他方案:**
| 技术栈 | 优势 | 劣势 | 适用场景 |
|--------|------|------|----------|
| **Python FastAPI** | AI生态最佳、开发效率高 | 单进程性能中等 | ✅ AI医疗应用 |
| Java Spring | 企业级成熟、并发强 | AI库较少、开发慢 | 传统医疗信息系统 |
| Node.js | 前后端统一、IO高效 | AI支持弱 | 轻量级Web应用 |
| Go | 性能最强、部署简单 | AI生态几乎没有 | 高并发非AI场景 |

### 2. 前端: React + Ant Design + TypeScript

**选型理由:**
- ✅ **组件化开发**: 复杂医疗后台系统模块化管理
- ✅ **UI组件丰富**: Ant Design Pro提供现成的后台模板
- ✅ **类型安全**: TypeScript减少运行时错误
- ✅ **生态成熟**: 影像查看库Cornerstone.js完善

**医学影像查看方案:**
- Cornerstone.js: 专业DICOM查看库
- 支持MPR(多平面重建)、MIP(最大密度投影)
- WebGL加速渲染

### 3. 数据库: PostgreSQL

**选型理由:**
- ✅ **JSON字段**: 灵活存储病理、基因信息
- ✅ **GIS扩展**: PostGIS支持影像坐标查询(未来扩展)
- ✅ **全文检索**: 支持中文分词搜索
- ✅ **事务完整性**: ACID保证数据一致性

**数据模型设计原则:**
- 主表垂直拆分: `patients`, `mri_series`, `annotations`, `followup_tasks`
- JSON字段灵活扩展: `pathology_info`, `radiomics_features`
- 外键约束保证数据完整性

### 4. 缓存: Redis (多级缓存策略)

**三级缓存架构:**

```python
Level 1: 浏览器缓存 (ETag + Cache-Control)
  ↓ 未命中
Level 2: Redis缓存 (L2 Cache)
  ├─ 热点数据 (patient:info:{id}, TTL=1h)
  ├─ 列表数据 (patient:list:page:{n}, TTL=10min)
  ├─ DICOM元数据 (dicom:meta:{uid}, TTL=24h)
  └─ AI结果 (ai:result:{id}, TTL=永久)
  ↓ 未命中
Level 3: PostgreSQL数据库
```

**缓存失效策略:**
- **主动失效**: 数据更新时立即删除相关缓存
- **被动失效**: TTL自动过期
- **LRU淘汰**: 内存不足时淘汰最少使用项

**示例代码:**
```python
async def get_patient(patient_id: int):
    # L2: 检查Redis
    cached = await redis.get(f"patient:info:{patient_id}")
    if cached:
        return cached
    
    # L3: 查询数据库
    patient = await db.query(Patient).filter_by(id=patient_id).first()
    
    # 写回Redis
    await redis.setex(
        f"patient:info:{patient_id}",
        3600,
        patient.to_json()
    )
    return patient
```

### 5. 对象存储: MinIO

**选型理由:**
- ✅ **私有化部署**: 医疗数据不出本地
- ✅ **S3兼容**: 可无缝迁移到阿里云OSS/AWS S3
- ✅ **分布式**: 支持水平扩展
- ✅ **性能优异**: 单节点可达TB/s吞吐

**DICOM存储策略:**
```
Bucket: dicom-images
Path: patients/{patient_id}/series/{series_uid}/slice_{index:04d}.dcm

Bucket: thumbnails
Path: patients/{patient_id}/thumbnails/{series_uid}.png
```

## 🚀 性能优化策略

### 1. 数据库优化

#### 索引设计
```sql
-- 患者编号唯一索引
CREATE UNIQUE INDEX idx_patient_no ON patients(patient_no);

-- 复合索引 (常见查询)
CREATE INDEX idx_patient_hospital_date ON patients(hospital, admission_date);

-- DICOM序列索引
CREATE INDEX idx_series_patient ON mri_series(patient_id, series_uid);
```

#### 连接池配置
```python
# asyncpg连接池
pool_size = 20          # 连接数
max_overflow = 40       # 超出后可创建的连接数
pool_pre_ping = True    # 连接健康检查
```

### 2. API响应优化

#### 分页查询
```python
# 使用LIMIT/OFFSET + 总数缓存
async def list_patients(page: int, size: int):
    # 总数缓存1小时
    total = await redis.get("patient:total") or await db.count()
    
    # 只查询当前页
    items = await db.query(Patient)\
        .offset((page-1) * size)\
        .limit(size)\
        .all()
```

#### 字段裁剪
```python
# 列表只返回必要字段
class PatientListItem(BaseModel):
    id: int
    name: str
    patient_no: str
    # 不包含大字段 (diagnosis, pathology_info)
```

### 3. AI模型优化

#### 模型量化
```python
# PyTorch模型转ONNX (推理速度提升2-3倍)
torch.onnx.export(
    model,
    dummy_input,
    "unet.onnx",
    opset_version=13
)

# 使用ONNX Runtime推理
import onnxruntime as ort
session = ort.InferenceSession("unet.onnx")
output = session.run(None, {"input": image})
```

#### 批处理推理
```python
# 批量处理多个切片
batch_size = 8
for i in range(0, len(slices), batch_size):
    batch = slices[i:i+batch_size]
    results = model(batch)  # GPU并行处理
```

### 4. DICOM加载优化

#### 预签名URL
```python
# 前端直接从MinIO下载，不经过后端
presigned_url = minio.presigned_get_object(
    bucket="dicom-images",
    object_name=path,
    expires=3600  # 1小时有效
)
```

#### 分片传输
```python
# 大文件分片上传
@app.post("/upload-chunk")
async def upload_chunk(
    chunk: UploadFile,
    chunk_index: int,
    total_chunks: int,
    file_id: str
):
    # 保存分片
    await save_chunk(file_id, chunk_index, chunk)
    
    # 最后一片时合并
    if chunk_index == total_chunks - 1:
        await merge_chunks(file_id)
```

## 🔐 安全架构

### 1. 认证授权 (JWT)

```python
# JWT Token结构
{
  "sub": "user_id",
  "role": "doctor",  # doctor/admin/researcher
  "permissions": ["read:patient", "write:patient", "run:ai"],
  "exp": 1234567890
}

# RBAC权限控制
@require_permission("read:patient")
async def get_patient(patient_id: int):
    pass
```

### 2. 数据加密

- **传输加密**: TLS 1.3
- **存储加密**: 
  - 敏感字段AES-256加密 (身份证、电话)
  - MinIO服务端加密 (SSE-S3)

### 3. 数据脱敏

```python
# 用于科研的脱敏数据
def anonymize_patient(patient: Patient) -> dict:
    return {
        "id": hashlib.sha256(patient.id).hexdigest()[:8],
        "age_range": f"{patient.age//10*10}-{patient.age//10*10+9}",
        "region": patient.address[:2],  # 只保留省份
        # 移除所有可识别信息
    }
```

## 📊 监控和可观测性

### 1. 日志系统

```python
# 结构化日志 (Loguru)
logger.info(
    "Patient created",
    patient_id=patient.id,
    hospital=patient.hospital,
    duration_ms=elapsed_time
)
```

### 2. 性能监控

```python
# Prometheus指标
from prometheus_client import Counter, Histogram

api_requests = Counter('api_requests_total', 'Total API requests')
ai_inference_time = Histogram('ai_inference_seconds', 'AI inference time')

@ai_inference_time.time()
async def run_unet_inference(image):
    pass
```

### 3. 健康检查

```python
@app.get("/health")
async def health_check():
    return {
        "database": await check_db_connection(),
        "redis": await check_redis_connection(),
        "minio": await check_minio_connection(),
        "ai_model": model_loaded
    }
```

## 🎯 PRD功能覆盖度

| PRD需求ID | 功能 | 实现状态 | 技术方案 |
|-----------|------|----------|----------|
| F-DM-01 | 创建新病例 | ✅ 已实现 | FastAPI + PostgreSQL |
| F-DM-02 | 结构化信息录入 | ✅ 已实现 | Pydantic验证 + JSON字段 |
| F-DM-03 | 影像数据上传 | ✅ 已实现 | MinIO对象存储 |
| F-DM-04 | AI辅助影像标注 | ✅ 已实现 | U-Net + Cornerstone.js |
| F-DM-05 | 数据质控 | 🔄 部分实现 | 审核工作流待完善 |
| F-AI-01 | U-Net病灶分割 | ✅ 已实现 | PyTorch模型 |
| F-AI-02 | 影像组学特征提取 | 🔄 框架就绪 | PyRadiomics集成 |
| F-AI-03 | 线性回归预后预测 | ✅ 已实现 | scikit-learn |
| F-CD-01 | 患者列表与检索 | ✅ 已实现 | 分页+搜索+缓存 |
| F-CD-02 | 患者360°视图 | ✅ 已实现 | 多Tab页设计 |
| F-CD-03 | AI分析结果可视化 | ✅ 已实现 | ECharts图表 |
| F-FU-01 | 创建随访计划 | ✅ 已实现 | 定时任务生成 |
| F-FU-02 | 任务自动提醒 | ✅ 已实现 | Celery定时任务 |
| F-FU-03 | 患者端应用 | ✅ 已实现 | uni-app小程序 |
| F-FU-04 | 随访数据看板 | ✅ 已实现 | 看板统计API |

## 📈 扩展性设计

### 横向扩展
- FastAPI无状态，支持多实例负载均衡
- PostgreSQL支持主从复制、读写分离
- Redis支持集群模式
- MinIO支持分布式部署

### 纵向扩展
- GPU加速AI推理
- 增加数据库连接池大小
- 提升Redis内存容量

---

**文档版本**: 1.0  
**最后更新**: 2025-11-04

