import gspread
import calendar
import locale
from datetime import datetime
from typing import Dict, List, Any
from app.utils.logger import get_logger
from app.core.config import settings
from app.service.sheet import SheetsService

logger = get_logger(__name__)


class SummaryGenerator:
    def __init__(self):
        self.sheets_service = SheetsService()
        logger.info("Summary Generator initialized")

        # Kamus untuk menerjemahkan nama bulan bahasa Indonesia ke angka
        self.month_id_to_number = {
            "januari": 1,
            "februari": 2,
            "maret": 3,
            "april": 4,
            "mei": 5,
            "juni": 6,
            "juli": 7,
            "agustus": 8,
            "september": 9,
            "oktober": 10,
            "november": 11,
            "desember": 12,
        }

    def parse_indonesian_date(self, date_str):
        """Parse tanggal dengan format Indonesia seperti 'Agustus 31, 2025'"""
        try:
            parts = date_str.replace(",", "").split()
            if len(parts) != 3:
                return None

            month_name, day, year = parts
            month_number = self.month_id_to_number.get(month_name.lower())
            if not month_number:
                return None

            day = int(day)
            year = int(year)

            return datetime(year, month_number, day)
        except Exception as e:
            logger.debug(f"Error parsing Indonesian date: {e}")
            return None

    async def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """
        Generate financial summary for a specific month and year.

        Args:
            year (int): Year for the summary
            month (int): Month for the summary (1-12)

        Returns:
            Dict with status and analysis results
        """
        try:
            # Log parameter yang diterima fungsi
            logger.info(f"Generating summary for year: {year}, month: {month}")

            # Get all worksheets to find the appropriate transaction sheet
            all_sheets = self.sheets_service.spreadsheet.worksheets()
            sheet_name = f"Transaksi {year}"
            logger.info(f"Looking for sheet: '{sheet_name}'")

            # Log semua sheet yang tersedia
            available_sheets = [sheet.title for sheet in all_sheets]
            logger.info(f"Available sheets: {available_sheets}")

            # Check if there's a sheet for the requested year
            worksheet = None
            for sheet in all_sheets:
                if sheet.title == sheet_name:
                    worksheet = sheet
                    logger.info(f"Found matching sheet: {sheet.title}")
                    break

            if not worksheet:
                # If year-specific sheet doesn't exist, try finding the most recent available sheet
                transaction_sheets = [
                    sheet for sheet in all_sheets if sheet.title.startswith("Transaksi")
                ]
                if not transaction_sheets:
                    logger.warning("No transaction sheets found")
                    return {
                        "status": "empty",
                        "message": f"Tidak ditemukan sheet transaksi untuk {year} atau tahun lainnya.",
                    }

                # Sort by year (descending) and use the most recent available
                transaction_sheets.sort(
                    key=lambda s: (
                        int(s.title.split()[-1]) if s.title.split()[-1].isdigit() else 0
                    ),
                    reverse=True,
                )
                worksheet = transaction_sheets[0]
                year = (
                    int(worksheet.title.split()[-1])
                    if worksheet.title.split()[-1].isdigit()
                    else year
                )
                logger.info(
                    f"Using alternative sheet: {worksheet.title} for requested year {year}"
                )

            # Get all data
            all_data = worksheet.get_all_values()
            logger.info(
                f"Retrieved {len(all_data) - 1 if len(all_data) > 0 else 0} data rows"
            )

            if len(all_data) <= 1:  # Only headers, no data
                logger.info("Sheet is empty (only contains headers)")
                return {
                    "status": "empty",
                    "message": f"Belum ada transaksi yang tercatat.",
                }

            headers = all_data[0]
            data = all_data[1:]
            logger.info(f"Headers: {headers}")
            logger.info(f"Total rows of data: {len(data)}")

            # Find column indices
            date_idx = headers.index("Tanggal") if "Tanggal" in headers else 0
            amount_idx = headers.index("Jumlah") if "Jumlah" in headers else 5
            type_idx = headers.index("Jenis") if "Jenis" in headers else 2
            category_idx = headers.index("Kategori") if "Kategori" in headers else 4
            logger.info(
                f"Column indices - Date: {date_idx}, Amount: {amount_idx}, Type: {type_idx}, Category: {category_idx}"
            )

            # Tampilkan sampel data untuk debugging
            if data:
                logger.info(f"Sample data row: {data[0]}")

            # Filter data for the specific month
            month_data = []
            for row_idx, row in enumerate(data):
                if len(row) <= max(date_idx, amount_idx, type_idx, category_idx):
                    logger.warning(
                        f"Row {row_idx + 2} skipped: not enough columns. Row data: {row}"
                    )
                    continue  # Skip rows that don't have enough columns

                date_str = row[date_idx].strip()
                logger.info(f"Processing row {row_idx + 2}, date: '{date_str}'")

                # Handle various date formats
                try:
                    date_obj = None

                    # Coba parse tanggal dengan format Indonesia terlebih dahulu
                    date_obj = self.parse_indonesian_date(date_str)
                    if date_obj:
                        logger.info(
                            f"Date '{date_str}' parsed with Indonesian format => {date_obj}"
                        )
                    else:
                        formats_tried = []
                        # Coba parse berbagai format tanggal standar
                        formats_to_try = [
                            "%d/%m/%Y",  # DD/MM/YYYY
                            "%Y-%m-%d",  # YYYY-MM-DD
                            "%d-%m-%Y",  # DD-MM-YYYY
                            "%d %B %Y",  # DD Month YYYY
                            "%d %b %Y",  # DD Mon YYYY
                            "%Y/%m/%d",  # YYYY/MM/DD
                        ]

                        for date_format in formats_to_try:
                            try:
                                formats_tried.append(date_format)
                                date_obj = datetime.strptime(date_str, date_format)
                                logger.info(
                                    f"Date '{date_str}' parsed with format '{date_format}' => {date_obj}"
                                )
                                break
                            except ValueError:
                                continue

                    if not date_obj:
                        logger.warning(
                            f"Couldn't parse date: '{date_str}'. Tried formats: {formats_tried}"
                        )
                        continue

                    row_month = date_obj.month
                    row_year = date_obj.year
                    logger.info(
                        f"Date info - month: {row_month}, year: {row_year} (looking for month: {month}, year: {year})"
                    )

                    if row_month == month and row_year == year:
                        logger.info(f"Match found! Adding row to month data: {row}")
                        month_data.append(row)
                    else:
                        logger.info(f"Not a match for requested month/year")

                except Exception as e:
                    # Skip rows with unparseable dates
                    logger.error(f"Error with date '{date_str}': {e}")
                    continue

            logger.info(
                f"Filtered data: found {len(month_data)} transactions for {month}/{year}"
            )

            if not month_data:
                # Get month name in Indonesian
                month_names_id = {
                    1: "Januari",
                    2: "Februari",
                    3: "Maret",
                    4: "April",
                    5: "Mei",
                    6: "Juni",
                    7: "Juli",
                    8: "Agustus",
                    9: "September",
                    10: "Oktober",
                    11: "November",
                    12: "Desember",
                }
                month_name = month_names_id.get(month, "Unknown")

                logger.info(f"No transactions found for {month_name} {year}")
                return {
                    "status": "empty",
                    "message": f"Belum ada transaksi yang tercatat untuk {month_name} {year}. Gunakan /add untuk menambahkan transaksi baru!",
                }

            # Calculate summary statistics
            total_income = 0
            total_expense = 0
            category_totals = {}

            for row_idx, row in enumerate(month_data):
                try:
                    amount_str = (
                        row[amount_idx].replace(".", "").replace(",", "").strip()
                    )
                    amount = int(amount_str) if amount_str.isdigit() else 0
                    logger.info(
                        f"Processing amount for row {row_idx + 1}: '{amount_str}' => {amount}"
                    )

                    transaction_type = row[type_idx].lower()
                    logger.info(f"Transaction type: '{transaction_type}'")

                    if transaction_type == "pemasukan":
                        total_income += amount
                        logger.info(
                            f"Added to income: {amount} (total: {total_income})"
                        )
                    else:  # Pengeluaran
                        total_expense += amount
                        logger.info(
                            f"Added to expense: {amount} (total: {total_expense})"
                        )

                        # Track category totals for expenses
                        category = row[category_idx]
                        if category not in category_totals:
                            category_totals[category] = 0
                        category_totals[category] += amount
                        logger.info(
                            f"Updated category '{category}': {category_totals[category]}"
                        )

                except (ValueError, IndexError) as e:
                    logger.error(
                        f"Error processing amount or category in row {row_idx + 1}: {e}"
                    )
                    continue

            # Sort categories by amount (descending)
            sorted_categories = sorted(
                category_totals.items(), key=lambda x: x[1], reverse=True
            )

            # Generate analysis text
            analysis = []

            # Add income and expense totals
            analysis.append(
                f"💰 *Total Pemasukan:* Rp {total_income:,}".replace(",", ".")
            )
            analysis.append(
                f"💸 *Total Pengeluaran:* Rp {total_expense:,}".replace(",", ".")
            )

            # Calculate balance
            balance = total_income - total_expense
            balance_status = "🟢 SURPLUS" if balance >= 0 else "🔴 DEFISIT"
            analysis.append(
                f"🧮 *Saldo:* Rp {balance:,} ({balance_status})".replace(",", ".")
            )

            # Add expense breakdown by category
            if sorted_categories:
                analysis.append("\n📊 *Breakdown Pengeluaran:*")
                for category, amount in sorted_categories[:5]:  # Show top 5 categories
                    percentage = (
                        (amount / total_expense * 100) if total_expense > 0 else 0
                    )
                    analysis.append(
                        f"• {category}: Rp {amount:,} ({percentage:.1f}%)".replace(
                            ",", "."
                        )
                    )

                if len(sorted_categories) > 5:
                    other_total = sum(amount for _, amount in sorted_categories[5:])
                    other_percentage = (
                        (other_total / total_expense * 100) if total_expense > 0 else 0
                    )
                    analysis.append(
                        f"• Lainnya: Rp {other_total:,} ({other_percentage:.1f}%)".replace(
                            ",", "."
                        )
                    )

            # Add transaction count
            analysis.append(f"\n📝 *Total Transaksi:* {len(month_data)}")

            # Get month name in Indonesian
            month_names_id = {
                1: "Januari",
                2: "Februari",
                3: "Maret",
                4: "April",
                5: "Mei",
                6: "Juni",
                7: "Juli",
                8: "Agustus",
                9: "September",
                10: "Oktober",
                11: "November",
                12: "Desember",
            }
            month_name = month_names_id.get(month, "Unknown")

            logger.info(
                f"Summary generated successfully - Income: {total_income}, Expense: {total_expense}"
            )

            return {
                "status": "success",
                "analysis": "\n".join(analysis),
                "month_name": month_name,
                "data": {
                    "income": total_income,
                    "expense": total_expense,
                    "balance": balance,
                    "categories": dict(sorted_categories),
                },
            }

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return {"status": "error", "message": str(e)}
