package com.example.qlkh.Controller;

import com.example.qlkh.Service.OCRService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@RestController
@RequestMapping("/api/ocr")
public class OCRController {

    @Autowired
    private OCRService ocrService;

    @PostMapping("/upload")
    public ResponseEntity<?> uploadImage(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "ground_truth", required = false) String groundTruth) {

        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body("No file uploaded");
        }

        if (!file.getContentType().equals("application/pdf") && !file.getContentType().startsWith("image")) {
            return ResponseEntity.badRequest().body("Invalid file type. Please upload an image or PDF.");
        }

        try {
            Map<String, Object> result = ocrService.processOCR(file, groundTruth);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error processing file: " + e.getMessage());
        }
    }
}

