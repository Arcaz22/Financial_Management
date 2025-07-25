import gspread
from datetime import datetime
from app.utils.logger import get_logger
from google.oauth2.service_account import Credentials
from app.core.config import settings

logger = get_logger(__name__)

class SheetsService:
    def __init__(self):
        self._init_connection()

    def _init_connection(self):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_file(
            settings.credentials_path,
            scopes=scopes
        )
        self.gc = gspread.authorize(credentials)
        try:
            self.spreadsheet = self.gc.open_by_key(settings.spreadsheet_id)
            logger.info(f"Connected to spreadsheet: {self.spreadsheet.title}")
        except Exception as e:
            logger.error(f"Google Sheets connection error: {type(e).__name__}: {e}")
            raise e

    def ensure_year_sheet_exists(self, year=None):
        if year is None:
            year = datetime.now().year

        sheet_name = f"Transaksi {year}"

        try:
            self.spreadsheet.worksheet(sheet_name)
            return sheet_name
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title=sheet_name,
                rows=1000,
                cols=10
            )

            headers = [
                "Tanggal", "Nama", "Jenis", "Sumber",
                "Kategori", "Jumlah", "Deskripsi"
            ]
            worksheet.update('A1:G1', [headers])

            worksheet.format('A1:G1', {
                'textFormat': {'bold': True},
                'horizontalAlignment': 'CENTER'
            })

            logger.info(f"Created new sheet: {sheet_name}")
            return sheet_name

    def add_transaction(self, transaction_data):
        date_str = transaction_data["tanggal"]
        try:
            date_obj = datetime.strptime(date_str, "%d %B %Y %H:%M")
            year = date_obj.year
        except ValueError:
            year = datetime.now().year

        sheet_name = self.ensure_year_sheet_exists(year)
        worksheet = self.spreadsheet.worksheet(sheet_name)

        row_data = [
            transaction_data["tanggal"],
            transaction_data["nama"],
            transaction_data["jenis"],
            transaction_data["sumber"],
            transaction_data["kategori"],
            transaction_data["jumlah"],
            transaction_data["deskripsi"]
        ]

        worksheet.append_row(row_data)
        logger.info(f"Added new transaction for {transaction_data['nama']}")

        return True
