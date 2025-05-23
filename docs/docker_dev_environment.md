# MemoQ工单系统 - Docker开发环境使用指南

本文档详细说明如何使用Docker开发环境进行MemoQ工单系统的本地开发，该环境支持代码热重载功能。

## 开发环境与生产环境的区别

| 特性 | 开发环境 (`docker-compose.dev.yml`) | 生产环境 (`docker-compose.yml`) |
|------|----------------------------------|------------------------------|
| 热重载 | ✅ 支持前后端代码热重载 | ❌ 不支持热重载 |
| 构建过程 | 更快的构建，适合开发迭代 | 完整的生产构建流程 |
| 调试工具 | 启用调试模式和日志 | 禁用调试，优化性能 |
| 服务名称 | `backend-dev`, `frontend-dev` | `backend`, `frontend` |
| 前端服务器 | Vite开发服务器 (端口3000) | Nginx生产服务器 (端口80) |
| 后端服务器 | Django开发服务器 | Gunicorn生产服务器 |
| 数据卷 | 独立的开发数据卷 | 生产数据卷 |

## 使用方法

### 1. 环境准备

确保您的系统已安装：
- Docker
- Docker Compose
- Git

### 2. 配置环境变量

1. 后端环境变量:
   ```bash
   cp backend/.env.example backend/.env
   ```
   根据需要编辑`.env`文件中的配置。

2. 前端环境变量已预配置在`.env.docker-dev`文件中，专为Docker开发环境优化。

### 3. 启动开发环境

```bash
# 构建并启动开发环境容器
docker-compose -f docker-compose.dev.yml up --build
```

首次启动可能需要几分钟时间，因为需要下载镜像和安装依赖。

### 4. 访问应用

- 前端开发服务器: http://localhost:3000
- 后端API: http://localhost:8000/api

### 5. 热重载功能

开发环境已配置支持热重载：

- **前端热重载**: 修改`frontend/memoq-ticket-frontend/src`目录下的任何文件，Vite将自动重新编译并刷新浏览器。
- **后端热重载**: 修改`backend`目录下的Python文件，Django开发服务器将自动重新加载。

### 6. 常用开发命令

```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up

# 在后台启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 停止开发环境
docker-compose -f docker-compose.dev.yml down

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 仅查看前端日志
docker-compose -f docker-compose.dev.yml logs -f frontend-dev

# 仅查看后端日志
docker-compose -f docker-compose.dev.yml logs -f backend-dev

# 重建容器
docker-compose -f docker-compose.dev.yml up --build
```

### 7. 执行后端管理命令

```bash
# 进入后端容器
docker-compose -f docker-compose.dev.yml exec backend-dev bash

# 在容器内执行Django命令
source .venv/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 8. 执行前端命令

```bash
# 进入前端容器
docker-compose -f docker-compose.dev.yml exec frontend-dev sh

# 在容器内执行npm命令
npm install <package-name>
npm run build
```

## 切换到生产环境

当您需要测试生产环境构建时，可以使用原始的docker-compose.yml:

```bash
# 启动生产环境
docker-compose up --build
```

## 注意事项

1. 开发环境和生产环境使用不同的数据卷，因此数据不会共享。
2. 开发环境针对热重载和开发体验进行了优化，不适合用于生产部署。
3. 在Mac M1/M2/M3芯片上，Docker镜像已配置为使用ARM64平台。
4. 如果热重载不工作，可能需要调整vite.config.js中的polling设置。

## 故障排除

### 前端热重载不工作

1. 检查Docker容器日志是否有错误:
   ```bash
   docker-compose -f docker-compose.dev.yml logs frontend-dev
   ```

2. 确认vite.config.js中的hmr配置是否正确。

3. 尝试增加polling间隔:
   ```javascript
   watch: {
     usePolling: true,
     interval: 2000, // 增加到2000ms
   }
   ```

### 后端热重载不工作

1. 检查Docker容器日志是否有错误:
   ```bash
   docker-compose -f docker-compose.dev.yml logs backend-dev
   ```

2. 确保Django设置中DEBUG=True。

3. 某些类型的更改(如添加新文件)可能需要手动重启服务:
   ```bash
   docker-compose -f docker-compose.dev.yml restart backend-dev
   ```

### 数据库连接问题

如果后端无法连接到数据库，请检查:

1. 环境变量配置是否正确
2. 数据库容器是否正常运行
3. 网络连接是否正常

```bash
# 检查数据库容器状态
docker-compose -f docker-compose.dev.yml ps db
```