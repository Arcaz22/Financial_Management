import re
import logging
from datetime import datetime
from app.utils.conversation import ConversationState, get_user_session
from app.service.summary import SummaryGenerator

logger = logging.getLogger(__name__)

summary_generator = SummaryGenerator()

async def handle_summary(text=None, chat_id=None):

    try:
        session = None
        if chat_id:
            session = get_user_session(chat_id)

        if text == "/summary":
            if session:
                session.set_state(ConversationState.SUMMARY_INPUT)
            return "📊 Apa ringkasan keuangan yang kamu butuhkan?", None

        elif session and session.state == ConversationState.SUMMARY_INPUT:
            query = text.lower()

            month = datetime.now().month
            year = datetime.now().year

            month_names = {
                "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
                "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
                "jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "jun": 6,
                "jul": 7, "agu": 8, "agus": 8, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12
            }

            for name, num in month_names.items():
                if name in query:
                    month = num
                    break

            year_match = re.search(r'\b(20[2-3][0-9])\b', query)
            if year_match:
                year = int(year_match.group(1))

            if "bulan ini" in query or "bulan sekarang" in query:
                month = datetime.now().month
                year = datetime.now().year
            elif "bulan lalu" in query or "bulan kemarin" in query:
                if datetime.now().month == 1:
                    month = 12
                    year = datetime.now().year - 1
                else:
                    month = datetime.now().month - 1
                    year = datetime.now().year

            session.reset()

            month_names_id = {
                1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
                7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
            }
            month_name = month_names_id.get(month, "Unknown")

            result = await summary_generator.get_monthly_summary(year, month)

            if result["status"] == "success":
                month_name = result.get("month_name", month_names_id.get(month, "Unknown"))
                response = f"📊 *RINGKASAN KEUANGAN - {month_name.upper()} {year}*\n\n{result['analysis']}"
                return response, None
            elif result["status"] == "empty":
                return f"{result['message']}", None
            else:
                logger.error(f"Error in summary generation: {result['message']}")
                return f"❌ Maaf, terjadi kesalahan saat membuat ringkasan: {result['message']}", None

        return "Maaf, saya tidak dapat memproses permintaan ringkasan Anda. Silakan coba lagi dengan mengetik /summary", None

    except Exception as e:
        logger.error(f"Error handling summary: {str(e)}")
        return f"❌ Terjadi kesalahan saat membuat ringkasan keuangan: {str(e)}. Silakan coba lagi nanti.", None
