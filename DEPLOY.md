# 部署指南

## 📋 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 内存
- 至少 20GB 磁盘空间

## 🚀 快速部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd tengda
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cd backend
cp .env.example .env

# 编辑配置（可选，使用默认配置即可快速启动）
nano .env
```

### 3. 启动所有服务

```bash
# 返回项目根目录
cd ..

# 启动所有服务（首次启动会自动构建镜像）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

### 4. 初始化数据库

```bash
# 进入后端容器
docker-compose exec backend python -c "
from app.core.database import init_db
import asyncio
asyncio.run(init_db())
"
```

### 5. 访问系统

- **医生端前端**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **MinIO控制台**: http://localhost:9001 (minioadmin/minioadmin)
- **健康检查**: http://localhost:8000/health

## 🔧 服务说明

### 端口映射

| 服务 | 容器内端口 | 宿主机端口 | 说明 |
|------|-----------|-----------|------|
| Nginx | 80 | 80 | 反向代理 |
| 后端API | 8000 | 8000 | FastAPI服务 |
| 医生端前端 | 80 | 3000 | React应用 |
| PostgreSQL | 5432 | 5432 | 数据库 |
| Redis | 6379 | 6379 | 缓存 |
| MinIO | 9000 | 9000 | 对象存储API |
| MinIO控制台 | 9001 | 9001 | 管理界面 |

### 数据卷

```bash
# 查看数据卷
docker volume ls | grep tengda

# 备份数据库
docker-compose exec postgres pg_dump -U postgres endometrial_cancer > backup.sql

# 备份MinIO数据
docker run --rm -v tengda_minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio-backup.tar.gz /data
```

## 🛠️ 常用命令

### 服务管理

```bash
# 停止所有服务
docker-compose stop

# 重启服务
docker-compose restart backend

# 查看日志
docker-compose logs -f backend
docker-compose logs -f --tail=100 backend

# 进入容器
docker-compose exec backend bash
docker-compose exec postgres psql -U postgres
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 仅重启后端
docker-compose up -d --build backend
```

### 清理环境

```bash
# 停止并删除容器
docker-compose down

# 删除容器和数据卷（⚠️ 会丢失所有数据）
docker-compose down -v

# 清理未使用的镜像
docker image prune -a
```

## 📊 性能优化

### 1. 数据库优化

编辑 `docker-compose.yml`，增加PostgreSQL配置：

```yaml
postgres:
  command:
    - "postgres"
    - "-c"
    - "shared_buffers=256MB"
    - "-c"
    - "max_connections=200"
```

### 2. Redis缓存优化

```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### 3. 后端Worker数量

编辑 `backend/Dockerfile`，修改启动命令：

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## 🔒 生产环境配置

### 1. 安全加固

```bash
# 修改默认密码
# 编辑 docker-compose.yml，修改：
POSTGRES_PASSWORD: <strong-password>
MINIO_ROOT_PASSWORD: <strong-password>

# 修改JWT密钥
# 编辑 backend/.env：
SECRET_KEY=<generate-random-string>
```

### 2. HTTPS配置

在 `nginx.conf` 中添加SSL配置：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... 其他配置
}
```

### 3. 监控和日志

```yaml
# docker-compose.yml 添加日志驱动
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🐛 故障排查

### 后端无法连接数据库

```bash
# 检查PostgreSQL是否启动
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 测试连接
docker-compose exec backend python -c "
from app.core.database import engine
import asyncio
async def test():
    async with engine.begin() as conn:
        print('Database connected!')
asyncio.run(test())
"
```

### Redis连接失败

```bash
# 检查Redis状态
docker-compose exec redis redis-cli ping

# 查看Redis日志
docker-compose logs redis
```

### MinIO无法访问

```bash
# 检查MinIO服务
docker-compose logs minio

# 测试MinIO连接
docker-compose exec backend python -c "
from app.services.dicom_service import dicom_service
print(dicom_service.minio_client.bucket_exists('dicom-images'))
"
```

### 前端无法访问后端API

```bash
# 检查Nginx配置
docker-compose exec nginx nginx -t

# 查看Nginx日志
docker-compose logs nginx

# 重启Nginx
docker-compose restart nginx
```

## 📈 监控和维护

### 资源监控

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
docker system df
```

### 定期维护

```bash
# 数据库vacuum（每周）
docker-compose exec postgres psql -U postgres -d endometrial_cancer -c "VACUUM ANALYZE;"

# 清理旧日志（每月）
find ./backend/logs -name "*.log" -mtime +30 -delete

# 清理Docker缓存
docker system prune -a --volumes
```

## 📞 技术支持

如有问题，请联系技术团队或查看项目文档。

