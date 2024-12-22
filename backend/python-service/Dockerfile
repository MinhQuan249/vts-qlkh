# Sử dụng Python 3.12
FROM python:3.12-slim

# Đặt biến môi trường
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Cài đặt các gói phụ thuộc và Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    imagemagick \
    python3-pip \
    libleptonica-dev \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y poppler-utils

# Cài đặt file ngôn ngữ Tiếng Việt (tessdata_fast)
RUN mkdir -p /usr/share/tesseract-ocr/5/tessdata/ && \
    wget -O /usr/share/tesseract-ocr/5/tessdata/vie.traineddata \
    https://github.com/tesseract-ocr/tessdata_fast/raw/main/vie.traineddata

# Tạo thư mục làm việc
WORKDIR /app

# Sao chép requirements và cài đặt thư viện trước
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn cuối cùng
COPY . .

# Expose port Flask
EXPOSE 5000

# Chạy ứng dụng Flask
CMD ["python", "ocr_service.py"]
