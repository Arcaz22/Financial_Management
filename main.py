import uvicorn
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router.webhook import router as webhook
from app.router.sheets import router as sheets
from app.router.ocr import router as ocr
from app.router.gemini import router as scan

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="Bot Telegram",
    description="Bot Telegram Financial Management Api",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook, tags=["telegram"])
app.include_router(sheets, tags=["sheets"])
app.include_router(ocr, tags=["ocr"])
app.include_router(scan, tags=["ocr"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Financial Management API",
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
