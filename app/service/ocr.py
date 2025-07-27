from PIL import Image
import pytesseract
import io
from app.utils.logger import get_logger

logger = get_logger(__name__)

class OCRService:
    def __init__(self):
        logger.info("OCRService initialized.")

    async def process_image_for_ocr(self, image_bytes: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(image_bytes))

            # Anda bisa menambahkan pra-pemrosesan gambar di sini jika diperlukan,
            # seperti resizing, grayscale, thresholding untuk akurasi Tesseract
            # Contoh: image = image.convert('L') # Mengubah ke grayscale

            # Lakukan OCR menggunakan Tesseract
            # lang='ind' untuk bahasa Indonesia, 'eng' untuk Inggris, atau kombinasikan 'eng+ind'
            extracted_text = pytesseract.image_to_string(image, lang='eng+ind')

            logger.info("OCR successful.")
            return extracted_text
        except Exception as e:
            logger.error(f"Error during OCR processing: {type(e).__name__}: {e}")
            raise
