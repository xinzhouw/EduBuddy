FROM node:20-slim AS builder

WORKDIR /app
COPY package*.json ./
RUN npm config set registry https://registry.npmmirror.com && npm ci
# 先复制源码（每次源码变化都会触发重新构建）
COPY . .
# 清理可能存在的旧构建产物
RUN rm -rf dist
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
