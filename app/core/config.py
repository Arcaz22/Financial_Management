import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN")
    base_webhook_url: str = os.getenv("BASE_WEBHOOK_URL")

settings = Settings()
