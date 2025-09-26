from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.service.ocr import OCRService

router = APIRouter(prefix="/ocr")


def get_ocr_service():
    return OCRService()


@router.post("/test")
async def scan_nota_ocr(
    file: UploadFile = File(...), ocr_service: OCRService = Depends(get_ocr_service)
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail="File yang diunggah harus berupa gambar."
        )

    try:
        contents = await file.read()

        extracted_text = await ocr_service.process_image_for_ocr(contents)

        return {
            "filename": file.filename,
            "extracted_text": extracted_text,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses OCR: {e}")
