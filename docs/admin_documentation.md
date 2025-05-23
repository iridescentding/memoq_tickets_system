# MemoQ 工单系统管理员手册

## 目录

1. [系统概述](#系统概述)
2. [管理员角色与权限](#管理员角色与权限)
3. [系统部署](#系统部署)
   - [环境要求](#环境要求)
   - [使用Docker部署](#使用docker部署)
   - [手动部署](#手动部署)
4. [数据库迁移与验证](#数据库迁移与验证)
   - [从SQLite迁移到PostgreSQL](#从sqlite迁移到postgresql)
   - [验证数据库连接](#验证数据库连接)
5. [系统配置](#系统配置)
   - [环境变量配置](#环境变量配置)
   - [邮件系统配置](#邮件系统配置)
   - [Webhook配置](#webhook配置)
6. [用户管理](#用户管理)
   - [创建系统管理员](#创建系统管理员)
   - [管理技术支持账号](#管理技术支持账号)
   - [管理公司账号](#管理公司账号)
7. [工单管理](#工单管理)
   - [工单分配](#工单分配)
   - [工单状态管理](#工单状态管理)
   - [SLA监控](#sla监控)
8. [系统维护](#系统维护)
   - [日志管理](#日志管理)
   - [数据备份与恢复](#数据备份与恢复)
   - [系统升级](#系统升级)
9. [常见问题与解决方案](#常见问题与解决方案)

## 系统概述

MemoQ工单系统是一个专为本地化技术支持团队设计的工单管理平台，支持多角色权限管理、工单生命周期管理、SLA监控、公司专属登录等功能。系统采用前后端分离架构，后端使用Django REST Framework，前端使用Vue.js和Vuetify组件库。

### 主要功能

- 多角色权限管理：系统管理员、技术支持管理员、技术支持、公司用户
- 工单生命周期管理：创建、分配、处理、关闭等
- SLA监控：首次响应时间、解决时间等
- 公司专属登录：每个公司拥有独立的登录入口和工单URL
- 工单标签系统：支持多级工单类型和标签管理
- 邮件通知：支持邮件发送和接收
- Webhook集成：支持与第三方系统集成

## 管理员角色与权限

系统包含以下角色：

1. **系统管理员(system_admin)**：
   - 拥有系统的全部权限
   - 可以创建和管理所有类型的用户
   - 可以配置系统参数和全局设置

2. **技术支持管理员(technical_support_admin)**：
   - 可以创建和管理公司
   - 可以创建和管理技术支持账号
   - 可以分配工单给技术支持
   - 可以查看所有工单和SLA监控

3. **技术支持(support)**：
   - 可以处理分配给自己的工单
   - 可以创建工单并指定公司
   - 可以转移工单给其他技术支持

4. **公司用户(company_user)**：
   - 可以创建和查看本公司的工单
   - 可以回复和关注工单

## 系统部署

### 环境要求

- Docker和Docker Compose（推荐）
- 或Python 3.8+和Node.js 16+（手动部署）
- PostgreSQL 12+
- Redis 6+

### 使用Docker部署

1. 克隆代码仓库：
   ```bash
   git clone <repository-url>
   cd memoq-ticket-system
   ```

2. 配置环境变量：
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/memoq-ticket-frontend/.env.example frontend/memoq-ticket-frontend/.env
   ```
   
   编辑这两个文件，设置必要的环境变量。

3. 启动服务：
   ```bash
   docker-compose up -d
   ```

4. 创建超级用户：
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

5. 访问系统：
   - 前端：http://localhost:3000
   - 后端API：http://localhost:8000/api/
   - Django管理后台：http://localhost:8000/admin/

### 手动部署

#### 后端部署

1. 创建并激活虚拟环境：
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量：
   ```bash
   cp .env.example .env
   ```
   
   编辑.env文件，设置必要的环境变量。

4. 执行数据库迁移：
   ```bash
   python manage.py migrate
   ```

5. 创建超级用户：
   ```bash
   python manage.py createsuperuser
   ```

6. 启动开发服务器：
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

#### 前端部署

1. 安装依赖：
   ```bash
   cd frontend/memoq-ticket-frontend
   npm install
   ```

2. 配置环境变量：
   ```bash
   cp .env.example .env.local
   ```
   
   编辑.env.local文件，设置必要的环境变量。

3. 启动开发服务器：
   ```bash
   npm run dev
   ```

4. 构建生产版本：
   ```bash
   npm run build
   ```

## 数据库迁移与验证

### 从SQLite迁移到PostgreSQL

系统默认使用PostgreSQL数据库，如果您之前使用的是SQLite，可以按照以下步骤迁移数据：

1. 确保已安装必要的工具：
   ```bash
   pip install psycopg2-binary dj-database-url
   ```

2. 导出SQLite数据：
   ```bash
   python manage.py dumpdata --exclude auth.permission --exclude contenttypes > data.json
   ```

3. 修改settings.py中的数据库配置为PostgreSQL：
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'memoq_ticket_system',
           'USER': 'postgres',
           'PASSWORD': 'postgres',
           'HOST': 'db',
           'PORT': '5432',
       }
   }
   ```

4. 执行数据库迁移：
   ```bash
   python manage.py migrate
   ```

5. 导入之前导出的数据：
   ```bash
   python manage.py loaddata data.json
   ```

### 验证数据库连接

您可以通过以下方法验证系统是否已成功连接到PostgreSQL数据库：

1. **使用Django Shell**：
   ```bash
   # 进入Django Shell
   docker-compose exec backend python manage.py shell
   
   # 在Shell中执行以下代码
   from django.db import connection
   print(connection.vendor)  # 应输出 'postgresql'
   ```

2. **查看数据库日志**：
   ```bash
   docker-compose logs db
   ```
   
   查看日志中是否有成功连接的记录。

3. **通过Django管理后台**：
   访问http://localhost:8000/admin/，登录后查看是否能正常访问数据。

4. **直接连接数据库**：
   ```bash
   docker-compose exec db psql -U postgres -d memoq_ticket_system
   
   # 在PostgreSQL命令行中执行
   \dt  # 列出所有表
   ```
   
   如果能看到系统的所有表，说明数据库连接正常。

## 系统配置

### 环境变量配置

#### 后端环境变量(.env)

```
# 基本设置
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# 数据库设置
DATABASE_URL=postgres://postgres:postgres@db:5432/memoq_ticket_system

# Redis设置
REDIS_URL=redis://redis:6379/0

# 邮件设置
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=your-email@example.com

# 文件存储设置
MEDIA_ROOT=/app/media
STATIC_ROOT=/app/static

# 前端URL
FRONTEND_URL=http://localhost:3000
```

#### 前端环境变量(.env)

```
# API设置
VITE_API_BASE_URL=http://localhost:8000/api

# 应用设置
VITE_APP_TITLE=MemoQ工单系统
```

### 邮件系统配置

1. 在Django管理后台配置邮件模板：
   - 访问http://localhost:8000/admin/
   - 导航到"邮件模板"部分
   - 创建不同事件类型的邮件模板（工单创建、状态变更等）

2. 在技术支持管理员仪表盘中配置公司邮件设置：
   - 为每个公司配置是否启用邮件通知
   - 设置接收通知的邮箱地址

### Webhook配置

1. 在Django管理后台配置Webhook模板：
   - 访问http://localhost:8000/admin/
   - 导航到"Webhook模板"部分
   - 创建不同事件类型的Webhook模板

2. 在技术支持管理员仪表盘中配置公司Webhook：
   - 为每个公司配置Webhook URL
   - 设置需要触发的事件类型
   - 使用测试功能验证Webhook是否正常工作

## 用户管理

### 创建系统管理员

1. 使用Django命令行创建：
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```
   
   按照提示输入用户名、邮箱和密码。

2. 或在Django管理后台创建：
   - 访问http://localhost:8000/admin/
   - 导航到"用户"部分
   - 点击"添加用户"
   - 填写用户信息，并将角色设置为"system_admin"

### 管理技术支持账号

1. 在技术支持管理页面创建技术支持账号：
   - 登录系统（系统管理员或技术支持管理员）
   - 导航到"技术支持管理"页面
   - 点击"创建技术支持账号"
   - 填写用户信息，选择角色（技术支持或技术支持管理员）

2. 管理现有技术支持账号：
   - 编辑账号信息
   - 重置密码
   - 启用/禁用账号

### 管理公司账号

1. 创建公司：
   - 登录系统（系统管理员或技术支持管理员）
   - 导航到"公司管理"页面
   - 点击"创建公司"
   - 填写公司信息，上传公司Logo
   - 配置允许的登录方式（账号密码、SSO等）

2. 生成公司专属URL：
   - 系统会自动为每个公司生成唯一的URL
   - 可以手动修改URL标识符
   - 复制URL分享给公司用户

3. 管理公司用户：
   - 创建公司管理员账号
   - 查看公司用户列表
   - 启用/禁用用户账号

## 工单管理

### 工单分配

1. 在管理员仪表盘分配工单：
   - 查看"待分配工单"表格
   - 为每个工单选择合适的技术支持
   - 点击"分配"按钮

2. 工单转移：
   - 技术支持可以将工单转移给其他技术支持
   - 需要提供转移理由
   - 系统会记录转移历史

### 工单状态管理

工单状态流转：
- 待处理(open)：新创建的工单
- 处理中(in_progress)：技术支持已接手处理
- 待回复(pending)：等待公司用户提供更多信息
- 已解决(resolved)：问题已解决，等待确认
- 已关闭(closed)：工单已完成
- 已暂停(paused)：工单暂时搁置，不计入SLA和idle时间

### SLA监控

1. 首次响应SLA：
   - 从工单创建时开始计时
   - 到技术支持首次回复时结束
   - 在管理员仪表盘的"即将miss IR和已miss IR"表格中监控

2. 工单闲置监控：
   - 从最后一次活动时间开始计时
   - 在管理员仪表盘的"即将idle和已idle"表格中监控

## 系统维护

### 日志管理

1. 查看系统日志：
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   ```

2. 日志文件位置：
   - 后端日志：`backend/logs/`
   - 数据库日志：`docker-compose logs db`

### 数据备份与恢复

1. 备份数据库：
   ```bash
   docker-compose exec db pg_dump -U postgres memoq_ticket_system > backup.sql
   ```

2. 恢复数据库：
   ```bash
   cat backup.sql | docker-compose exec -T db psql -U postgres -d memoq_ticket_system
   ```

3. 备份媒体文件：
   ```bash
   docker cp $(docker-compose ps -q backend):/app/media ./media_backup
   ```

### 系统升级

1. 拉取最新代码：
   ```bash
   git pull origin main
   ```

2. 重新构建容器：
   ```bash
   docker-compose build
   ```

3. 执行数据库迁移：
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

4. 重启服务：
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## 常见问题与解决方案

### 登录问题

**问题**：用户无法登录系统
**解决方案**：
1. 检查用户账号是否处于活跃状态
2. 重置用户密码
3. 检查用户角色权限是否正确
4. 检查公司SSO配置是否正确

### 数据库连接问题

**问题**：系统无法连接到数据库
**解决方案**：
1. 检查数据库服务是否运行：`docker-compose ps db`
2. 检查数据库连接配置是否正确
3. 检查数据库用户权限
4. 重启数据库服务：`docker-compose restart db`

### 邮件发送问题

**问题**：系统无法发送邮件
**解决方案**：
1. 检查邮件服务器配置是否正确
2. 检查邮件模板是否存在
3. 检查发送邮箱是否有权限发送邮件
4. 查看邮件发送日志

### 工单分配问题

**问题**：无法分配工单给技术支持
**解决方案**：
1. 检查技术支持账号是否处于活跃状态
2. 检查当前用户是否有分配工单的权限
3. 检查工单状态是否允许分配

### 性能问题

**问题**：系统响应缓慢
**解决方案**：
1. 检查服务器资源使用情况
2. 优化数据库查询
3. 增加服务器资源
4. 启用缓存机制
