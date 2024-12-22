from flask import Flask, request, jsonify
from utils.image_processing import (
    process_image_conditionally,  # Thay thế preprocess_image
    recognize_text_with_tesseract,
    recognize_text_with_easyocr,
    recognize_text_with_google_vision,
    convert_pdf_to_images,
    recognize_text_with_textract
)
import os
import uuid

app = Flask(__name__)

def calculate_cer(ground_truth, ocr_result):
    total_characters = len(ground_truth)
    errors = sum(1 for gt, ocr in zip(ground_truth, ocr_result) if gt != ocr)
    errors += abs(len(ground_truth) - len(ocr_result))
    cer = errors / total_characters if total_characters > 0 else 1
    accuracy = (1 - cer) * 100 if total_characters > 0 else 0
    return round(accuracy, 2), round(cer, 4)

def calculate_wer(ground_truth, ocr_result):
    gt_words = ground_truth.split()
    ocr_words = ocr_result.split()

    substitutions = sum(1 for gt, ocr in zip(gt_words, ocr_words) if gt != ocr)
    deletions = abs(len(gt_words) - len(ocr_words))
    total_words = len(gt_words)

    wer = (substitutions + deletions) / total_words if total_words > 0 else 1
    accuracy = (1 - wer) * 100 if total_words > 0 else 0
    return round(accuracy, 2), round(wer, 4)

@app.route('/ocr/upload', methods=['POST'])
def ocr_service():
    file_path = None
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        ground_truth = request.form.get('ground_truth', '').strip()

        # Lưu file tạm
        file_path = f"temp_{uuid.uuid4().hex}{os.path.splitext(file.filename)[1]}"
        file.save(file_path)

        results = []

        if file.filename.endswith('.pdf'):
            # Xử lý PDF
            image_paths = convert_pdf_to_images(file_path)
            for image_path in image_paths:
                processed_image_path = process_image_conditionally(image_path)

                tesseract_result = recognize_text_with_tesseract(processed_image_path)
                easyocr_result = recognize_text_with_easyocr(processed_image_path)
                google_vision_result = recognize_text_with_google_vision(processed_image_path)
                textract_result = recognize_text_with_textract(processed_image_path)

                # Tính CER và WER nếu có ground truth
                for result in [tesseract_result, easyocr_result, google_vision_result, textract_result]:
                    if ground_truth:
                        cer_accuracy, cer = calculate_cer(ground_truth, result['text'])
                        wer_accuracy, wer = calculate_wer(ground_truth, result['text'])
                        result['cer_accuracy'] = f"{cer_accuracy}%"
                        result['cer'] = f"{cer}"
                        result['wer_accuracy'] = f"{wer_accuracy}%"
                        result['wer'] = f"{wer}"

                results.append({
                    "page": os.path.basename(image_path),
                    "tesseract": tesseract_result,
                    "easyocr": easyocr_result,
                    "google_vision": google_vision_result,
                    "aws_textract": textract_result,
                })
        else:
            # Xử lý ảnh đơn
            processed_image_path = process_image_conditionally(file_path)

            tesseract_result = recognize_text_with_tesseract(processed_image_path)
            easyocr_result = recognize_text_with_easyocr(processed_image_path)
            google_vision_result = recognize_text_with_google_vision(processed_image_path)
            textract_result = recognize_text_with_textract(processed_image_path)

            for result in [tesseract_result, easyocr_result, google_vision_result, textract_result]:
                if ground_truth:
                    cer_accuracy, cer = calculate_cer(ground_truth, result['text'])
                    wer_accuracy, wer = calculate_wer(ground_truth, result['text'])
                    result['cer_accuracy'] = f"{cer_accuracy}%"
                    result['cer'] = f"{cer}"
                    result['wer_accuracy'] = f"{wer_accuracy}%"
                    result['wer'] = f"{wer}"

            results.append({
                "tesseract": tesseract_result,
                "easyocr": easyocr_result,
                "google_vision": google_vision_result,
                "aws_textract": textract_result,
            })

        return jsonify({"results": results}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        if 'image_paths' in locals():
            for image_path in image_paths:
                if os.path.exists(image_path):
                    os.remove(image_path)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
