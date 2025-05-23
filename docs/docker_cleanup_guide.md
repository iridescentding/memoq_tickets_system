# Docker 环境清理指南

本文档提供了如何清理旧的Docker镜像和卷的步骤，以便在更新Docker配置后重新构建环境。

## 停止并删除容器

首先，停止并删除所有与项目相关的容器：

```bash
# 停止所有容器
docker-compose down

# 或者使用开发环境配置
docker-compose -f docker-compose.dev.yml down