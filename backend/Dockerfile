# # Dockerfile cho backend
# FROM openjdk:17-jdk-slim
#
# # Đặt thư mục làm việc
# WORKDIR /app
#
# # Thêm đối số để chỉ định file JAR
# ARG JAR_FILE=target/qlkh-0.0.1-SNAPSHOT.jar
#
# # Sao chép file JAR vào container
# COPY ${JAR_FILE} app.jar
#
# # Cập nhật và cài đặt curl (nếu thực sự cần thiết)
# RUN apt-get update && apt-get install -y --no-install-recommends curl && \
#     apt-get clean && rm -rf /var/lib/apt/lists/*
#
# # Khai báo cổng mà ứng dụng sẽ sử dụng
# EXPOSE 8080
#
# # Lệnh chạy ứng dụng
# ENTRYPOINT ["java", "-jar", "app.jar"]

# Stage 1: Build application
FROM maven:3.9-eclipse-temurin-17-alpine AS builder
WORKDIR /app

# Sao chép pom.xml trước để tận dụng cache của dependencies
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Sao chép mã nguồn vào container
COPY src ./src

# Build ứng dụng
RUN mvn clean package -DskipTests

# Stage 2: Runtime
FROM openjdk:17-jdk-slim
WORKDIR /app

# Sao chép file JAR từ giai đoạn build
COPY --from=builder /app/target/*.jar app.jar

# Khai báo cổng
EXPOSE 8080

# Lệnh chạy ứng dụng
ENTRYPOINT ["java", "-jar", "app.jar"]
