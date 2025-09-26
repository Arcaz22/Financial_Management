from datetime import datetime
from app.service.gemini import GeminiReceiptProcessor
from app.utils.conversation import ConversationState
from app.service.ocr import OCRService
from app.utils.constant import get_back_keyboard, get_confirmation_keyboard
from app.utils.logger import get_logger
import re

logger = get_logger(__name__)

ocr_service = OCRService()
gemini_processor = GeminiReceiptProcessor()


def _format_ocr_result(transaction_data: dict) -> str:
    def format_currency(amount_str):
        try:
            amount = int(amount_str)
            return f"{amount:,}".replace(",", ".")
        except (ValueError, TypeError):
            return "0"

    merchant = transaction_data.get("nama", "Toko/Merchant")
    date = transaction_data.get("tanggal", "")
    category = transaction_data.get("kategori", "Lainnya")
    amount = format_currency(transaction_data.get("jumlah", "0"))

    items_text = ""
    if "items" in transaction_data and transaction_data["items"]:
        items_text = "\n\n📋 Detail Item:"
        for idx, item in enumerate(
            transaction_data["items"][:5], 1
        ):  # Limit to first 5 items
            name = item.get("name", "Item")
            qty = item.get("quantity", "1")
            price = format_currency(item.get("price", "0"))
            items_text += f"\n{idx}. {name} ({qty}x) @ Rp{price}"

        if len(transaction_data["items"]) > 5:
            items_text += f"\n... dan {len(transaction_data['items']) - 5} item lainnya"

    tax_text = ""
    if "tax" in transaction_data and transaction_data["tax"].get("value", "0") != "0":
        tax_type = transaction_data["tax"].get("type", "fixed")
        tax_value = transaction_data["tax"].get("value", "0")
        if tax_type == "percentage":
            tax_text = f"\n💰 Pajak: {tax_value}%"
        else:
            tax_text = f"\n💰 Pajak: Rp{format_currency(tax_value)}"

    discount_text = ""
    if (
        "discount" in transaction_data
        and transaction_data["discount"].get("value", "0") != "0"
    ):
        disc_type = transaction_data["discount"].get("type", "fixed")
        disc_value = transaction_data["discount"].get("value", "0")
        if disc_type == "percentage":
            discount_text = f"\n🏷️ Diskon: {disc_value}%"
        else:
            discount_text = f"\n🏷️ Diskon: Rp{format_currency(disc_value)}"

    message = (
        f"✅ Hasil Scan Nota\n\n"
        f"📆 Tanggal: {date}\n"
        f"🏢 Merchant: {merchant}\n"
        f"📝 Kategori: {category}\n"
        f"💵 Total: Rp{amount}"
        f"{tax_text}"
        f"{discount_text}"
        f"{items_text}\n\n"
        f"Apakah data di atas sudah benar?"
    )

    return message


async def handle_scan_add(session, text=None, photo=None):
    if session.state == ConversationState.ADD_AI_PROCESSING:
        if text and (text.lower() == "back" or text.lower() == "« kembali"):
            session.go_back()
            return "Silakan pilih metode input transaksi:", get_back_keyboard()

        if photo:
            try:
                session.set_state(ConversationState.ADD_AI_PROCESSING_WAIT)

                transaction_data = await gemini_processor.process_receipt(photo)
                receipt_date = transaction_data.get("tanggal", "")
                session.set_current_datetime()
                transaction_data["tanggal"] = receipt_date
                session.temp_data = transaction_data
                formatted_message = _format_ocr_result(transaction_data)
                session.set_state(ConversationState.ADD_AI_CONFIRM)

                return formatted_message, get_confirmation_keyboard()
            except Exception as e:
                logger.error(f"Error processing receipt: {str(e)}")
                session.set_state(ConversationState.ADD_AI_PROCESSING)
                return (
                    "❌ Terjadi kesalahan saat memproses foto. Silakan coba lagi atau gunakan input manual.",
                    get_back_keyboard(),
                )

        return "📷 Silakan kirim foto nota/struk untuk diproses.", get_back_keyboard()

    elif session.state == ConversationState.ADD_AI_CONFIRM:
        if text and text.lower() == "ya":
            session.transaction_data = session.temp_data.copy()
            session.temp_data = None

            if "jumlah" in session.transaction_data:
                try:
                    raw_jumlah = str(session.transaction_data["jumlah"]).lstrip("'")
                    amount_str = re.sub(r"[^\d]", "", raw_jumlah)
                    amount = int(amount_str) if amount_str else 0
                    formatted_amount = f"{amount:,}".replace(",", ".")
                    session.transaction_data["jumlah"] = (
                        formatted_amount if amount > 0 else "0"
                    )
                except (ValueError, TypeError):
                    logger.warning(
                        f"Failed to format amount: {session.transaction_data['jumlah']}"
                    )

            # Format tanggal ke DD/MM/YYYY
            if "tanggal" in session.transaction_data:
                try:
                    raw_tanggal = str(session.transaction_data["tanggal"]).lstrip("'")
                    date_obj = datetime.strptime(raw_tanggal, "%Y-%m-%d")
                    session.transaction_data["tanggal"] = date_obj.strftime("%d/%m/%Y")
                except Exception:
                    pass

            try:
                from app.service.sheet import SheetsService

                sheets_service = SheetsService()
                sheets_service.add_transaction(session.transaction_data)

                logger.info(f"Transaction saved successfully to spreadsheet")
                session.reset()
                return "✅ Transaksi berhasil disimpan!", None
            except Exception as e:
                logger.error(f"Error saving transaction: {str(e)}")
                session.reset()
                return f"❌ Terjadi kesalahan saat menyimpan transaksi: {str(e)}", None

        elif text and text.lower() == "edit":
            session.transaction_data = session.temp_data.copy()
            session.temp_data = None

            session.reset()
            return "🔄 Fitur edit akan segera tersedia. Transaksi dibatalkan.", None

        elif text and text.lower() == "batal":
            session.reset()
            return "❌ Transaksi dibatalkan.", None

        else:
            return "Silakan konfirmasi hasil scan:", get_confirmation_keyboard()

    return None, None
