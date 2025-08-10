from app.utils.logger import get_logger
from app.core.config import settings
from google import generativeai as genai
import json
from app.service.ocr import OCRService

logger = get_logger(__name__)

class GeminiReceiptProcessor:
    def __init__(self):
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        self.ocr_service = OCRService()
        logger.info("Gemini Receipt Processor initialized")

    async def process_receipt(self, image_bytes: bytes) -> dict:
        try:
            ocr_text = await self.ocr_service.process_image_for_ocr(image_bytes)

            result = await self.extract_data_from_ocr(ocr_text)

            result["jenis"] = "Pengeluaran"
            result["sumber"] = "Cash"

            result["raw_ocr_text"] = ocr_text

            logger.info(f"Gemini receipt processing successful")
            return result

        except Exception as e:
            logger.error(f"Error in Gemini receipt processing: {str(e)}")
            return {
                "tanggal": "",
                "nama": "Error processing receipt",
                "jenis": "Pengeluaran",
                "sumber": "Cash",
                "kategori": "Lainnya",
                "jumlah": "0",
                "deskripsi": f"Error: {str(e)}",
                "items": [],
                "tax": {"type": "none", "value": "0"},
                "discount": {"type": "none", "value": "0"},
                "raw_ocr_text": ""
            }

    async def extract_data_from_ocr(self, ocr_text: str) -> dict:
        prompt = f"""
        I have a receipt that was processed with OCR. Please extract the key information and format it as JSON.

        OCR TEXT:
        {ocr_text}

        Extract and return ONLY the following information in JSON format:
        1. Store/merchant name
        2. Date of transaction (in DD Month YYYY format if possible)
        3. Total amount (in Indonesian Rupiah, with no thousands separator)
        4. Individual items if present (name, quantity, price per unit)
        5. Category based on the merchant (use one of: Makanan, Transportasi, Invest, Tagihan, Belanja, or Lainnya)

        For amounts:
        - Find the TOTAL or GRAND TOTAL amount
        - Look for "RP" or "Rp" followed by numbers
        - Ignore bank account numbers
        - For amounts, keep only digits, no separators

        Return ONLY a valid JSON object with these fields:
        {{
          "tanggal": "date of transaction",
          "nama": "merchant name",
          "kategori": "expense category",
          "jumlah": "total amount as digits only",
          "deskripsi": "brief description of purchase",
          "items": [
            {{"name": "item name", "quantity": "quantity", "price": "unit price"}}
          ],
          "tax": {{"type": "percentage/fixed/none", "value": "tax amount"}},
          "discount": {{"type": "percentage/fixed/none", "value": "discount amount"}}
        }}

        If you can't determine some fields, use empty strings or default values.
        """

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text

            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'```json\n(.*?)\n```', result_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                else:
                    json_str = re.search(r'(\{.*\})', result_text, re.DOTALL)
                    if json_str:
                        return json.loads(json_str.group(0))
                    else:
                        raise ValueError("Could not parse JSON from API response")

        except Exception as e:
            logger.error(f"Error extracting data with Gemini: {str(e)}")
            return {
                "tanggal": "",
                "nama": "Error processing receipt",
                "kategori": "Lainnya",
                "jumlah": "0",
                "deskripsi": "",
                "items": [],
                "tax": {"type": "none", "value": "0"},
                "discount": {"type": "none", "value": "0"}
            }
