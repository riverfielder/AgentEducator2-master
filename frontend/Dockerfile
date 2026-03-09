# ---- Build Stage ----
FROM node:18-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm npm install
COPY . .
RUN NODE_OPTIONS=--max_old_space_size=2560 npm run build

# ---- Production Stage ----
FROM nginx:alpine AS production-stage
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
