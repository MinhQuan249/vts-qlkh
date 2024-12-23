import pytesseract
import easyocr
import time
from PIL import Image
import cv2
import os
import numpy as np
import uuid
from pdf2image import convert_from_path
from google.cloud import vision
import logging
import boto3
import json

# Cấu hình logging
logging.basicConfig(level=logging.INFO)

# Khởi tạo EasyOCR Reader một lần duy nhất
reader = easyocr.Reader(['vi', 'en'], gpu=False)

def load_aws_credentials():
    """
    Load AWS credentials từ file JSON trong thư mục secrets.
    """
    try:
        with open("secrets/aws_credentials.json", "r") as file:
            credentials = json.load(file)
        return credentials
    except Exception as e:
        logging.error(f"Could not load AWS credentials: {e}")
        return None

def convert_pdf_to_images(pdf_path):
    """
    Chuyển đổi PDF thành danh sách ảnh.
    """
    try:
        images = convert_from_path(pdf_path)
        image_paths = []
        for i, image in enumerate(images):
            output_path = f"page_{i}_{uuid.uuid4().hex}.png"
            image.save(output_path, "PNG")
            image_paths.append(output_path)
        return image_paths
    except Exception as e:
        logging.error(f"Error converting PDF to images: {str(e)}")
        return []

def cleanup_temp_files(file_paths):
    """
    Xóa các file tạm.
    """
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)

def preprocess_image(image_path):
    """
    Tiền xử lý ảnh:
    - Chuyển ảnh thành đen trắng (adaptive threshold).
    - Làm sạch nhiễu nhỏ (morphology).
    - Làm sắc nét nhẹ và lưu kết quả với tên file tạm thời.
    """
    try:
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        img_adaptive_thresh = cv2.adaptiveThreshold(
            img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 10
        )

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        img_cleaned = cv2.morphologyEx(img_adaptive_thresh, cv2.MORPH_OPEN, kernel)

        kernel_sharpen = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        img_sharpen = cv2.filter2D(img_cleaned, -1, kernel_sharpen)

        output_path = f"processed_{uuid.uuid4().hex}.png"
        cv2.imwrite(output_path, img_sharpen)
        return output_path
    except Exception as e:
        logging.error(f"Error preprocessing image: {str(e)}")
        return None

def is_image_quality_good(image_path, threshold=150):
    """
    Kiểm tra chất lượng ảnh bằng cách đánh giá độ tương phản trung bình.
    """
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        contrast = img.std()  # Độ lệch chuẩn biểu thị độ tương phản
        logging.info(f"Image contrast: {contrast}")
        return contrast > threshold
    except Exception as e:
        logging.error(f"Error checking image quality: {str(e)}")
        return True  # Mặc định không tiền xử lý nếu kiểm tra thất bại

def process_image_conditionally(image_path):
    """
    Tiền xử lý ảnh nếu chất lượng thấp.
    """
    if not is_image_quality_good(image_path):
        logging.info(f"Image {image_path} is being preprocessed.")
        return preprocess_image(image_path)
    logging.info(f"Image {image_path} is of good quality. Skipping preprocessing.")
    return image_path

def recognize_text_with_tesseract(image_path):
    """
    Nhận diện văn bản sử dụng Tesseract OCR.
    """
    try:
        start_time = time.time()
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang="vie")
        processing_time = round((time.time() - start_time) * 1000)

        return {
            "library": "Tesseract OCR",
            "text": text.strip(),
            "time": f"{processing_time} ms",
            "cer_accuracy": None,
            "wer_accuracy": None,
            "handwritingSupport": "Hạn chế",
            "vietnameseSupport": "Có"
        }
    except Exception as e:
        logging.error(f"Error in Tesseract OCR: {str(e)}")
        return {"library": "Tesseract OCR", "text": f"Error: {str(e)}"}

def recognize_text_with_easyocr(image_path):
    """
    Nhận diện văn bản sử dụng EasyOCR.
    """
    try:
        start_time = time.time()
        results = reader.readtext(image_path)
        extracted_text = "\n".join([text for _, text, _ in results])
        processing_time = round((time.time() - start_time) * 1000)

        return {
            "library": "EasyOCR",
            "text": extracted_text.strip(),
            "time": f"{processing_time} ms",
            "cer_accuracy": None,
            "wer_accuracy": None,
            "handwritingSupport": "Tốt",
            "vietnameseSupport": "Có"
        }
    except Exception as e:
        logging.error(f"Error in EasyOCR: {str(e)}")
        return {"library": "EasyOCR", "text": f"Error: {str(e)}"}

def recognize_text_with_google_vision(image_path):
    """
    Nhận diện văn bản sử dụng Google Vision API.
    """
    try:
        start_time = time.time()
        client = vision.ImageAnnotatorClient()

        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations

        extracted_text = texts[0].description if texts else ""
        confidence = texts[0].score if texts and hasattr(texts[0], "score") else 0
        processing_time = round((time.time() - start_time) * 1000)

        return {
            "library": "Google Vision API",
            "text": extracted_text.strip(),
            "confidence": f"{confidence * 100:.2f}%",
            "time": f"{processing_time} ms",
            "handwritingSupport": "Tốt",
            "vietnameseSupport": "Có"
        }
    except Exception as e:
        logging.error(f"Error in Google Vision API: {str(e)}")
        return {"library": "Google Vision API", "text": f"Error: {str(e)}"}

def recognize_text_with_textract(image_path):
    """
    Nhận diện văn bản sử dụng AWS Textract.
    """
    credentials = load_aws_credentials()
    if not credentials:
        return {"library": "AWS Textract", "text": "Error: Missing AWS credentials"}

    try:
        textract_client = boto3.client(
            'textract',
            aws_access_key_id=credentials['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=credentials['AWS_SECRET_ACCESS_KEY'],
            region_name=credentials['AWS_REGION']
        )

        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        start_time = time.time()
        response = textract_client.detect_document_text(Document={'Bytes': image_bytes})
        processing_time = round((time.time() - start_time) * 1000)

        detected_text = []
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                detected_text.append(block['Text'])

        return {
            "library": "AWS Textract",
            "text": "\n".join(detected_text).strip(),
            "time": f"{processing_time} ms",
            "cer_accuracy": None,
            "wer_accuracy": None,
            "handwritingSupport": "Hạn chế",
            "vietnameseSupport": "Hạn chế"
        }
    except Exception as e:
        logging.error(f"Error in AWS Textract: {e}")
        return {"library": "AWS Textract", "text": f"Error: {str(e)}"}
