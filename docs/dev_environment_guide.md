# MemoQ工单系统开发环境配置指南

本文档提供了如何设置和运行MemoQ工单系统开发环境的详细说明，包括前后端热重载配置和常见问题解决方案。

## 目录

1. [环境要求](#环境要求)
2. [快速启动](#快速启动)
3. [详细配置说明](#详细配置说明)
   - [Docker环境配置](#docker环境配置)
   - [前端热重载配置](#前端热重载配置)
   - [后端热重载配置](#后端热重载配置)
4. [开发工作流程](#开发工作流程)
5. [常见问题与解决方案](#常见问题与解决方案)

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Git

## 快速启动

1. 克隆代码仓库：

   ```bash
   git clone <repository-url>
   cd memoq-project
   ```
2. 配置环境变量：

   ```bash
   # 后端环境变量
   cp backend/.env.example backend/.env

   # 前端环境变量
   cp frontend/memoq-ticket-frontend/.env.example frontend/memoq-ticket-frontend/.env
   ```
3. 启动开发环境：

   ```bash
   docker-compose up -d
   ```
4. 访问应用：

   - 前端: http://localhost:3000
   - 后端API: http://localhost:8000/api/
   - 管理后台: http://localhost:8000/admin/

## 详细配置说明

### Docker环境配置

项目使用Docker Compose管理多个服务容器，包括：

- **frontend**: Vue.js前端应用，支持热重载
- **backend**: Django后端API，支持热重载
- **db**: PostgreSQL数据库
- **redis**: Redis缓存服务

配置文件位于项目根目录的 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  # PostgreSQL 数据库服务
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=memoq_ticket_system
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports:
      - "5432:5432"
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 缓存服务
  redis:
    image: redis:7
    ports:
      - "6379:6379"
    restart: always
    volumes:
      - redis_data:/data

  # Django 后端服务 - 开发模式
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app  # 挂载整个后端目录，支持代码热重载
      - backend_venv:/app/.venv  # 使用命名卷存储虚拟环境，避免每次重建
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file:
      - ./backend/.env  # 使用环境文件
    restart: always
    # 使用Django开发服务器而不是gunicorn，支持热重载
    command: >
      sh -c ". .venv/bin/activate && 
              python manage.py migrate &&
              python manage.py runserver 0.0.0.0:8000"
    environment:
      - DEBUG=True
      - PYTHONDONTWRITEBYTECODE=1  # 不生成.pyc文件
      - PYTHONUNBUFFERED=1  # 实时输出日志

  # Vue.js 前端服务 - 开发模式
  frontend:
    build: 
      context: ./frontend/memoq-ticket-frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"  # Vite默认端口
    depends_on:
      - backend
    volumes:
      - ./frontend/memoq-ticket-frontend:/app  # 挂载前端代码，支持热重载
      - /app/node_modules  # 避免覆盖容器内的node_modules
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api  # API基础URL
      - CHOKIDAR_USEPOLLING=true  # 在Docker环境中启用polling以正确检测文件变化
    restart: always
    command: npm run dev -- --host 0.0.0.0 --port 3000  # 使用Vite开发服务器

volumes:
  postgres_data:
  redis_data:
  backend_venv:  # 命名卷，用于存储后端虚拟环境
```

### 前端热重载配置

前端使用Vite作为开发服务器，支持热模块替换(HMR)。关键配置包括：

1. **Dockerfile.dev**：

   ```dockerfile
   FROM node:18-alpine

   # 设置工作目录
   WORKDIR /app

   # 设置淘宝npm镜像源以加速依赖安装
   RUN npm config set registry https://registry.npmmirror.com/

   # 复制 package.json、package-lock.json 和 .npmrc
   COPY package*.json ./
   COPY .npmrc ./

   # 安装依赖
   RUN npm install

   # 暴露Vite开发服务器端口
   EXPOSE 3000

   # 设置环境变量，确保热重载正常工作
   ENV HOST=0.0.0.0
   ENV PORT=3000
   ENV CHOKIDAR_USEPOLLING=true

   # 启动开发服务器
   CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
   ```
2. **vite.config.js**：

   ```javascript
   import { defineConfig } from "vite";
   import vue from "@vitejs/plugin-vue";
   import path from "path";

   export default defineConfig({
     plugins: [vue()],
     resolve: {
       alias: {
         "@": path.resolve(__dirname, "./src"),
       },
     },
     server: {
       port: 3000,
       watch: {
         usePolling: true,
         interval: 1000,
       },
       host: '0.0.0.0',
       hmr: {
         clientPort: 3000,
         overlay: true,
       },
       proxy: {
         '/api': {
           target: 'http://backend:8000',
           changeOrigin: true,
         }
       }
     },
     build: {
       sourcemap: true,
       rollupOptions: {
         output: {
           manualChunks: {
             'vendor': ['vue', 'vue-router', 'pinia', 'vuetify'],
             'api': ['axios']
           }
         }
       },
       chunkSizeWarningLimit: 1000
     }
   });
   ```

### 后端热重载配置

后端使用Django的开发服务器，支持代码修改后自动重载：

1. **Dockerfile.dev**：

   ```dockerfile
   FROM python:3.11-slim

   # 设置工作目录
   WORKDIR /app

   # 安装系统依赖
   RUN apt-get update && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       && rm -rf /var/lib/apt/lists/*

   # 创建并激活虚拟环境
   RUN python -m venv .venv
   ENV PATH="/app/.venv/bin:$PATH"

   # 升级pip并安装依赖
   COPY requirements.txt .
   RUN pip install --upgrade pip && \
       pip install -r requirements.txt

   # 暴露Django开发服务器端口
   EXPOSE 8000

   # 启动命令在docker-compose.yml中定义
   ```
2. **Docker Compose命令**：

   ```yaml
   command: >
     sh -c ". .venv/bin/activate && 
             python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"
   ```

## 开发工作流程

1. **启动开发环境**：

   ```bash
   docker-compose up -d
   ```
2. **查看日志**：

   ```bash
   # 查看所有服务日志
   docker-compose logs -f

   # 查看特定服务日志
   docker-compose logs -f frontend
   docker-compose logs -f backend
   ```
3. **前端开发**：

   - 修改 `frontend/memoq-ticket-frontend/src`目录下的文件
   - 保存后，Vite会自动重新编译并刷新浏览器
4. **后端开发**：

   - 修改 `backend`目录下的文件
   - Django开发服务器会自动检测变化并重新加载
5. **数据库操作**：

   ```bash
   # 进入数据库容器
   docker-compose exec db psql -U postgres -d memoq_ticket_system

   # 执行数据库迁移
   docker-compose exec backend python manage.py makemigrations
   docker-compose exec backend python manage.py migrate
   ```
6. **创建超级用户**：

   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```
7. **重启服务**：

   ```bash
   # 重启单个服务
   docker-compose restart frontend
   docker-compose restart backend

   # 重启所有服务
   docker-compose restart
   ```

## 常见问题与解决方案

### 前端热重载不工作

**问题**：修改前端代码后，浏览器不自动刷新
**解决方案**：

1. 确保Docker Compose配置中的卷挂载正确
2. 检查vite.config.js中的HMR配置
3. 尝试清理浏览器缓存
4. 重启前端容器：`docker-compose restart frontend`
5. 检查前端容器日志：`docker-compose logs -f frontend`

### 后端热重载不工作

**问题**：修改后端代码后，服务器不自动重载
**解决方案**：

1. 确保Docker Compose配置中的卷挂载正确
2. 检查Django设置中的DEBUG=True
3. 某些文件（如urls.py）的修改可能需要手动重启
4. 重启后端容器：`docker-compose restart backend`
5. 检查后端容器日志：`docker-compose logs -f backend`

### 数据库连接问题

**问题**：后端无法连接到数据库
**解决方案**：

1. 确保数据库容器正在运行：`docker-compose ps db`
2. 检查后端.env文件中的数据库连接配置
3. 等待数据库完全启动（检查健康检查状态）
4. 重启后端容器：`docker-compose restart backend`

### 前端API请求失败

**问题**：前端无法连接到后端API
**解决方案**：

1. 检查前端.env文件中的API基础URL配置
2. 确保后端服务正在运行：`docker-compose ps backend`
3. 检查浏览器控制台是否有CORS错误
4. 检查vite.config.js中的代理配置
5. 尝试直接访问API端点：http://localhost:8000/api/

### 依赖安装问题

**问题**：容器构建时依赖安装失败
**解决方案**：

1. 检查网络连接
2. 更新package.json或requirements.txt中的依赖版本
3. 清理Docker缓存：`docker-compose build --no-cache`
4. 手动进入容器安装依赖：
   ```bash
   # 前端
   docker-compose exec frontend sh
   npm install

   # 后端
   docker-compose exec backend sh
   pip install -r requirements.txt
   ```

### 登录表单不显示

**问题**：访问/login页面时登录表单不显示
**解决方案**：

1. 检查浏览器控制台是否有JavaScript错误
2. 确认index.html中没有引入冲突的CSS库
3. 确保Vuetify正确安装和配置
4. 清理浏览器缓存或使用隐私模式访问
5. 重建前端容器：
   ```bash
   docker-compose down
   docker-compose up -d --build frontend
   ```
