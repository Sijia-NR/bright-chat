# 构建阶段
FROM node:20-alpine as builder

WORKDIR /build

# 接收构建参数
ARG VITE_API_BASE_URL=/api/v1
ENV NODE_ENV=development
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# 复制 package 文件并安装依赖
COPY package*.json ./
RUN npm ci && npm cache clean --force

# 复制源代码并构建
COPY . .
RUN npm run build

# 生产阶段
FROM nginx:1.25-alpine

LABEL maintainer="BrightChat Team" \
      version="1.0.0" \
      description="BrightChat Frontend"

# 安装 curl 用于健康检查
RUN apk add --no-cache curl

# 删除默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /build/dist /usr/share/nginx/html

# 创建必要的目录
RUN mkdir -p /var/log/nginx /var/cache/nginx /tmp

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
