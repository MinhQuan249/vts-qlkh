# Stage 1: Build frontend app
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Nginx container
FROM nginx:latest

# Sao chép thư mục dist vào Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Sao chép file cấu hình nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Mở cổng 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
