FROM node:18-alpine as build-stage

WORKDIR /app

# 复制 package.json 和 package-lock.json 以及 .npmrc
COPY package*.json ./
# 确保npm可以读取国内镜像配置
COPY .npmrc .

# 安装依赖
RUN npm install

# 复制项目文件
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:stable-alpine as production-stage

# 从构建阶段复制构建结果到 nginx 目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制自定义 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]