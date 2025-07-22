from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
from app.schema.webhook import Update, WebhookResponse
from app.service.webhook import TelegramService
from app.core.config import settings

router = APIRouter(prefix="/telegram")
logger = logging.getLogger(__name__)

telegram_service = TelegramService()

@router.post("/webhook", response_model=WebhookResponse)
async def telegram_webhook(update: Update, background_tasks: BackgroundTasks):
    try:
        # Process update in background to avoid timeout
        background_tasks.add_task(telegram_service.process_update, update)

        return WebhookResponse(
            status="success",
            message="Update processed"
        )

    except Exception as e:
        logger.error(f"Error in webhook endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/set")
async def set_webhook():
    try:
        webhook_url = f"{settings.base_webhook_url}/telegram/webhook"
        success = await telegram_service.set_webhook(webhook_url)

        if success:
            return {"status": "success", "webhook_url": webhook_url}
        else:
            raise HTTPException(status_code=400, detail="Failed to set webhook")

    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/info")
async def get_webhook_info():
    try:
        info = await telegram_service.get_webhook_info()
        return info

    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
