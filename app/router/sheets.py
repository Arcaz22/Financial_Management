from fastapi import APIRouter
from app.utils.sheets import test_google_sheet_connection

router = APIRouter(prefix="/sheet")


@router.get("/test")
async def test_sheet():
    success, message = test_google_sheet_connection()
    return {"success": success, "message": message}
