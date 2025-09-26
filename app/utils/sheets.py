import gspread
from app.utils.logger import get_logger
from google.oauth2.service_account import Credentials
from app.core.config import settings
import traceback  # Tambahkan import ini

logger = get_logger(__name__)


def test_google_sheet_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_file(
        settings.credentials_path, scopes=scopes
    )
    gc = gspread.authorize(credentials)
    try:
        sh = gc.open_by_key(settings.spreadsheet_id)
        return True, f"Connected to spreadsheet: {sh.title}"
    except Exception as e:
        logger.error(
            f"Google Sheets connection error: {type(e).__name__}: {e}\n{traceback.format_exc()}"
        )
        return False, f"{type(e).__name__}: {e}"
