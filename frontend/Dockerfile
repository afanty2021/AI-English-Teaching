# ===========================================
# AI英语教学系统 - 前端 Dockerfile
# ===========================================
# 多阶段构建：减小最终镜像体积

# Stage 1: 构建阶段
FROM docker.m.daocloud.io/library/node:20-alpine AS builder

WORKDIR /app

# 安装依赖（利用缓存）
COPY package*.json ./
RUN npm install --prefer-offline --no-audit || npm ci

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# Stage 2: 生产阶段
FROM docker.m.daocloud.io/library/nginx:alpine AS production

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1/ || exit 1

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
