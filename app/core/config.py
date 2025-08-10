import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN")
    base_webhook_url: str = os.getenv("BASE_WEBHOOK_URL")
    spreadsheet_id: str = os.getenv("SPREADSHEET_ID")
    credentials_path: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    google_api_key = os.getenv("GOOGLE_API_KEY")

settings = Settings()
