import os
import time
import json
import base64
import requests

class OCRService:
    @staticmethod
    def extract_text(file) -> str:
        """Sends image to OCR.space and extracts text with retries."""
        ocr_key = os.environ.get("OCR_SPACE_API_KEY", "helloworld")
        
        for attempt in range(3):
            try:
                # Reset file pointer for each retry attempt
                file.seek(0)
                file_data = file.read()
                base64_image = base64.b64encode(file_data).decode('utf-8')
                
                if len(file_data) < 100:
                    print("ERROR: File data too small.")
                    return ""

                payload = {
                    "apikey": ocr_key,
                    "base64Image": f"data:{file.content_type};base64,{base64_image}",
                    "language": "eng",
                    "OCREngine": 2,      # Engine 2 is usually better for small/blurry text
                    "scale": True,
                    "isOverlayRequired": True # Forces more detailed analysis
                }
                
                res = requests.post(
                    "https://api.ocr.space/parse/image",
                    data=payload,
                    timeout=30
                )
                res.raise_for_status()
                ocr_data = res.json()
                
                if ocr_data.get("IsErroredOnProcessing"):
                    err_msg = ocr_data.get("ErrorMessage") or "Unknown OCR Engine error"
                    print(f"OCR Attempt {attempt+1} Engine Error: {err_msg}")
                elif ocr_data.get("ParsedResults"):
                    text = ocr_data["ParsedResults"][0]["ParsedText"]
                    if text and text.strip():
                        return text.strip()
                
                if attempt < 2: time.sleep(1)
            except Exception as e:
                print(f"OCR Attempt {attempt+1} Error: {str(e)}")
                if attempt < 2: time.sleep(1.5)
        
        return ""
