FROM python:3.10

WORKDIR /app
# 安装 uv

# 安装 uv
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install uv

ENV PATH="/root/.local/bin:$PATH"

# 复制依赖文件和uv配置文件
COPY requirements.txt .
# 确保uv可以读取镜像配置
COPY pyproject.toml .

# 创建虚拟环境并安装依赖
RUN uv venv --seed && \
    . .venv/bin/activate && \
    uv pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 激活虚拟环境并收集静态文件
RUN . .venv/bin/activate && \
    python manage.py collectstatic --noinput

# 创建媒体文件夹
RUN mkdir -p /app/media/attachments

# 设置权限
RUN chmod -R 755 /app/media

# 暴露端口
EXPOSE 8000

# 运行应用 (确保在虚拟环境中运行)
CMD ["sh", "-c", ". .venv/bin/activate && gunicorn memoq_ticket_system.wsgi:application --bind 0.0.0.0:8000"]

