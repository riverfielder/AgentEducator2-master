# ---- Build Stage ----
FROM node:18-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm npm install
COPY . .
# 增加 NODE_OPTIONS 提高编译内存上限，配合你升级后的服务器内存
RUN NODE_OPTIONS=--max_old_space_size=4096 npm run build

# ---- Production Stage ----
FROM nginx:alpine AS production-stage
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
