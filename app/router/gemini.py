from fastapi import APIRouter, UploadFile, File, HTTPException
from app.service.gemini import GeminiReceiptProcessor
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/gemini")

processor = GeminiReceiptProcessor()

@router.post("/test")
async def scan(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        result = await processor.process_receipt(contents)

        return {
            "filename": file.filename,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error processing file with Gemini: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing receipt: {str(e)}")
