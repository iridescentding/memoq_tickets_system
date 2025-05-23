# Docker 环境清理指南

本文档提供了如何清理旧的Docker镜像和卷的步骤，以便在更新Docker配置后重新构建环境。

## 停止并删除容器

首先，停止并删除所有与项目相关的容器：

```bash
# 停止所有容器
docker-compose down

# 或者使用开发环境配置
docker-compose -f docker-compose.dev.yml down
```

## 删除Docker镜像

删除与项目相关的Docker镜像：

```bash
# 列出所有镜像
docker images

# 删除特定镜像
docker rmi memoq-ticket-system_backend
docker rmi memoq-ticket-system_frontend

# 或者使用镜像ID删除
docker rmi <image_id>

# 删除所有未使用的镜像（谨慎使用）
docker image prune -a
```

## 删除Docker卷

删除项目使用的Docker卷：

```bash
# 列出所有卷
docker volume ls

# 删除特定卷
docker volume rm memoq-ticket-system_postgres_data
docker volume rm memoq-ticket-system_redis_data
docker volume rm memoq-ticket-system_static_volume
docker volume rm memoq-ticket-system_media_volume
docker volume rm memoq-ticket-system_backend_venv

# 删除所有未使用的卷（谨慎使用）
docker volume prune
```

## 完全清理（谨慎使用）

如果需要完全清理所有Docker资源：

```bash
# 停止所有容器
docker stop $(docker ps -a -q)

# 删除所有容器
docker rm $(docker ps -a -q)

# 删除所有镜像
docker rmi $(docker images -q)

# 删除所有卷
docker volume prune -f

# 删除所有网络
docker network prune -f

# 完全系统清理
docker system prune -a --volumes
```

**注意**：完全清理命令会删除所有未使用的容器、网络、镜像和卷。请确保您了解这些命令的影响再执行。

## 重新构建环境

清理完成后，可以重新构建环境：

```bash
# 开发环境
docker-compose -f docker-compose.dev.yml up --build

# 生产环境
docker-compose up --build
```
