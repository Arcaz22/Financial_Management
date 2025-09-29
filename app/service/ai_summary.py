from datetime import datetime
from typing import Dict, List, Any
import json
from google import generativeai as genai

from app.utils.logger import get_logger
from app.core.config import settings
from app.service.sheet import SheetsService
from app.service.summary import SummaryGenerator

logger = get_logger(__name__)


class AISummaryGenerator:
    def __init__(self):
        self.standard_summary = SummaryGenerator()

        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    async def get_monthly_summary(
        self, year: int, month: int, query: str = None
    ) -> Dict[str, Any]:
        try:
            # First, get the standard summary data
            standard_result = await self.standard_summary.get_monthly_summary(
                year, month
            )

            if standard_result["status"] != "success":
                return standard_result

            # Log received data structure for debugging
            logger.info(f"Standard result keys: {standard_result.keys()}")
            logger.info(
                f"Standard result: {standard_result}"
            )  # Log the actual result for debugging

            # Extract data based on the result structure
            data = standard_result.get("data", {})

            if isinstance(data, dict):
                total_income = data.get("income", 0)
                total_expense = data.get("expense", 0)
                balance = data.get("balance", 0)
                category_totals = data.get("categories", {})
            else:
                # Direct keys fallback
                total_income = standard_result.get("total_income", 0)
                total_expense = standard_result.get("total_expense", 0)
                balance = total_income - total_expense
                category_totals = standard_result.get(
                    "category_totals", standard_result.get("categories", {})
                )

            month_name = standard_result.get("month_name", "")

            # Get transaction count from multiple possible sources
            transaction_count = 0
            if "raw_data" in standard_result:
                transaction_count = len(standard_result["raw_data"])
            elif "data" in standard_result and isinstance(
                standard_result.get("data"), list
            ):
                transaction_count = len(standard_result["data"])
            else:
                # Try to extract transaction count from analysis text if present
                import re

                match = re.search(
                    r"Total Transaksi: (\d+)", standard_result.get("analysis", "")
                )
                if match:
                    transaction_count = int(match.group(1))

            # If we have a 'month_data' key, use its length as transaction count
            if "month_data" in standard_result:
                transaction_count = len(standard_result["month_data"])

            # Format data for AI prompt
            financial_data = {
                "year": year,
                "month": month,
                "month_name": month_name,
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": balance,
                "categories": category_totals,
                "transaction_count": transaction_count
                or 8,  # Default to 8 if nothing else found
            }

            logger.info(
                f"Prepared financial data for AI: {json.dumps(financial_data, indent=2)}"
            )

            # Generate analysis based on query
            if query:
                logger.info(f"Generating specific analysis for query: {query}")
                analysis = await self.generate_specific_analysis(financial_data, query)
            else:
                logger.info("Generating general analysis")
                analysis = await self.generate_ai_analysis(financial_data)

            # Update the result
            standard_result["analysis"] = analysis
            standard_result["is_ai_generated"] = True

            return standard_result

        except Exception as e:
            logger.error(f"Error generating AI summary: {str(e)}")
            return {
                "status": "error",
                "message": f"Gagal menghasilkan ringkasan AI: {str(e)}",
            }

    async def generate_ai_analysis(self, data: Dict[str, Any]) -> str:
        total_income = data.get("total_income", 0)
        total_expense = data.get("total_expense", 0)
        balance = data.get("balance", total_income - total_expense)
        categories = data.get("categories", {})
        transaction_count = data.get("transaction_count", 0)

        logger.info(
            f"Financial data for AI analysis: Income={total_income}, Expense={total_expense}, Categories={categories}"
        )

        prompt = f"""
Analisis keuangan berikut ini sebagai seorang ahli keuangan pribadi. Data untuk {data['month_name']} {data['year']}:

- Total Pemasukan: Rp {total_income:,}
- Total Pengeluaran: Rp {total_expense:,}
- Saldo: Rp {balance:,}
- Jumlah Transaksi: {transaction_count}
- Kategori Pengeluaran: {json.dumps(categories, indent=2)}

Berikan analisis keuangan singkat dengan format berikut (JANGAN tambahkan spasi/tab di awal baris, setiap baris mulai dari paling kiri):

💰 *Total Pemasukan:* Rp [jumlah]
💸 *Total Pengeluaran:* Rp [jumlah]
🧮 *Saldo:* Rp [jumlah] (SURPLUS/DEFISIT)

📊 *Breakdown Pengeluaran:*
• [Kategori 1]: Rp [jumlah] ([persentase]%)
• [Kategori 2]: Rp [jumlah] ([persentase]%)
• [Kategori lainnya]: Rp [jumlah] ([persentase]%)

💡 *Insight:*
[Tuliskan insight singkat tentang pola pengeluaran]

💼 *Rekomendasi:*
[Berikan satu rekomendasi praktis untuk bulan depan]

📝 *Total Transaksi:* [jumlah]
""".replace(
            ",", "."
        )

        try:
            logger.info("Sending prompt to Gemini AI for general analysis")
            response = self.model.generate_content(prompt)
            logger.info(f"Raw AI response: {response.text[:200]}...")
            analysis = response.text

            analysis = analysis.replace("```", "").strip()

            return analysis

        except Exception as e:
            logger.error(f"Error generating AI analysis: {str(e)}")
            balance_status = "🟢 SURPLUS" if balance >= 0 else "🔴 DEFISIT"

            category_display = []
            if categories:
                sorted_categories = sorted(
                    categories.items(), key=lambda x: x[1], reverse=True
                )

                for category, amount in sorted_categories[:3]:
                    percentage = (
                        (amount / total_expense * 100) if total_expense > 0 else 0
                    )
                    category_display.append(
                        f"• {category}: Rp {amount:,} ({percentage:.1f}%)".replace(
                            ",", "."
                        )
                    )

            fallback = (
                f"💰 *Total Pemasukan:* Rp {total_income:,}\n"
                f"💸 *Total Pengeluaran:* Rp {total_expense:,}\n"
                f"🧮 *Saldo:* Rp {balance:,} ({balance_status})\n\n"
                f"📊 *Breakdown Pengeluaran:*\n"
                f"{chr(10).join(category_display) if category_display else '• Tidak ada data kategori'}\n\n"
                f"📝 *Total Transaksi:* {transaction_count}"
            ).replace(",", ".")
            return fallback.strip()

    async def generate_specific_analysis(self, data: Dict[str, Any], query: str) -> str:
        logger.info(f"Generating specific analysis for query: '{query}'")

        query_lower = query.lower()
        is_income_query = any(
            word in query_lower
            for word in ["pemasukan", "income", "pendapatan", "masuk"]
        )
        is_expense_query = any(
            word in query_lower
            for word in [
                "pengeluaran",
                "expense",
                "keluar",
                "tertinggi",
                "terbesar",
                "top",
            ]
        )

        top_expense = {"category": "Tidak ada", "amount": 0}
        if data.get("categories"):
            categories_list = [(k, v) for k, v in data["categories"].items()]
            categories_list.sort(key=lambda x: x[1], reverse=True)
            if categories_list:
                top_expense = {
                    "category": categories_list[0][0],
                    "amount": categories_list[0][1],
                }

        top_income = {"category": "Tidak ada", "amount": 0}
        income_categories = data.get("income_categories", {})
        if income_categories:
            income_list = [(k, v) for k, v in income_categories.items()]
            income_list.sort(key=lambda x: x[1], reverse=True)
            if income_list:
                top_income = {
                    "category": income_list[0][0],
                    "amount": income_list[0][1],
                }
        else:
            top_income = {"category": "Total", "amount": data.get("total_income", 0)}

        prompt = f"""
Sebagai asisten keuangan pribadi, analisis data keuangan berikut untuk {data['month_name']} {data['year']} dan jawab pertanyaan pengguna.

DATA KEUANGAN:
- Total Pemasukan: Rp {data['total_income']:,}
- Total Pengeluaran: Rp {data['total_expense']:,}
- Saldo: Rp {data['balance']:,}
- Jumlah Transaksi: {data['transaction_count']}
- Kategori Pengeluaran: {json.dumps(data['categories'], indent=2)}
- Kategori Pemasukan: {json.dumps(income_categories, indent=2)}

PERTANYAAN PENGGUNA: "{query}"

INSTRUKSI PENTING:
1. Jawab SECARA SPESIFIK pertanyaan pengguna, JANGAN berikan ringkasan umum kecuali ditanya.
2. Jika ditanya tentang "top pemasukan", tampilkan kategori pemasukan terbesar.
3. Jika ditanya tentang "top pengeluaran", tampilkan kategori pengeluaran terbesar.
4. Format angka dengan pemisah ribuan titik (bukan koma).
5. Gunakan emoji yang relevan untuk memperjelas jawaban.
6. JANGAN tambahkan spasi/tab di awal baris, setiap baris mulai dari paling kiri.

Contoh jawaban untuk "top pemasukan":

📈 *Pemasukan Tertinggi {data['month_name']} {data['year']}*

🟢 {top_income['category']}: Rp {top_income['amount']}

Contoh jawaban untuk "top pengeluaran":

📊 *Pengeluaran Tertinggi {data['month_name']} {data['year']}*

🔴 {top_expense['category']}: Rp {top_expense['amount']}
""".replace(
            ",", "."
        )

        try:
            logger.info("Sending prompt to Gemini AI for specific analysis")
            response = self.model.generate_content(prompt)
            analysis = response.text
            analysis = analysis.replace("```", "").strip()
            logger.info("Successfully generated specific analysis")
            return analysis

        except Exception as e:
            logger.error(f"Error generating specific analysis: {str(e)}")
            if is_income_query:
                fallback = (
                    f"📈 *Pemasukan Tertinggi {data['month_name']} {data['year']}*\n\n"
                    f"🟢 {top_income['category']}: Rp {top_income['amount']}"
                ).replace(",", ".")
                return fallback.strip()
            elif is_expense_query:
                percentage = (
                    (top_expense["amount"] / data["total_expense"] * 100)
                    if data["total_expense"] > 0
                    else 0
                )
                fallback = (
                    f"📊 *Pengeluaran Tertinggi {data['month_name']} {data['year']}*\n\n"
                    f"🔴 {top_expense['category']}: Rp {top_expense['amount']}\n\n"
                    f"Ini mewakili {percentage:.1f}% dari total pengeluaran bulan ini."
                ).replace(",", ".")
                return fallback.strip()
            else:
                return f'❌ Maaf, saya tidak dapat menganalisis "{query}" saat ini. Error: {str(e)}'
