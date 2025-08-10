from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import io
import numpy as np
import cv2
from app.utils.logger import get_logger
from app.utils.receipt_parser import ReceiptParser

logger = get_logger(__name__)

class OCRService:
    def __init__(self):
        logger.info("Enhanced OCRService initialized.")
        self.custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1 -c page_separator=""'
        self.receipt_parser = ReceiptParser()

    async def process_image_for_ocr(self, image_bytes: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(image_bytes))

            if image.mode != 'RGB':
                image = image.convert('RGB')

            width, height = image.size
            if width < 1000 or height < 1000:
                scale_factor = 2
                image = image.resize((width * scale_factor, height * scale_factor), Image.LANCZOS)

            img_cv = np.array(image)
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

            blur = cv2.GaussianBlur(gray, (3, 3), 0)

            thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)

            kernel = np.ones((1, 1), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

            enhanced_image = Image.fromarray(opening)

            enhancer = ImageEnhance.Contrast(enhanced_image)
            enhanced_image = enhancer.enhance(2.0)

            enhanced_image = enhanced_image.filter(ImageFilter.SHARPEN)

            text1 = pytesseract.image_to_string(enhanced_image, lang='eng+ind', config=self.custom_config)

            custom_config2 = r'--oem 3 --psm 4 -c preserve_interword_spaces=1'
            text2 = pytesseract.image_to_string(enhanced_image, lang='eng+ind', config=custom_config2)

            inverted_image = Image.fromarray(cv2.bitwise_not(opening))
            text3 = pytesseract.image_to_string(inverted_image, lang='eng+ind', config=self.custom_config)

            texts = [text1, text2, text3]
            extracted_text = max(texts, key=len)

            extracted_text = self._clean_ocr_text(extracted_text)

            logger.info("Enhanced OCR successful with multiple processing steps.")
            return extracted_text
        except Exception as e:
            logger.error(f"Error during OCR processing: {type(e).__name__}: {e}")
            raise

    def _clean_ocr_text(self, text: str) -> str:
        import re
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)

        text = re.sub(r'\s+', ' ', text)

        text = text.replace('|', 'I').replace('l', 'I')

        text = re.sub(r'\n\s*\n', '\n', text)

        return text.strip()

    async def extract_transaction_data(self, image_bytes: bytes) -> dict:
        try:
            text = await self.process_image_for_ocr(image_bytes)
            logger.info(f"Extracted OCR text: {text[:100]}...")

            transaction_data = self.receipt_parser.parse_receipt_text(text)
            logger.info(f"Parsed transaction data: {transaction_data}")

            return transaction_data
        except Exception as e:
            logger.error(f"Error extracting transaction data: {type(e).__name__}: {e}")
            raise
