# Stage 1: Build frontend app
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:latest

# Sao chép thư mục dist vào Nginx
COPY dist /usr/share/nginx/html

# Sao chép file cấu hình nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Mở cổng 80
EXPOSE 80
