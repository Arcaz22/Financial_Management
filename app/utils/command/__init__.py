from app.utils.command.menu import handle_menu
from app.utils.command.help import handle_help
from app.utils.command.summary import handle_summary
from app.utils.command.add.manual import handle_manual_add
from app.utils.command.add.scan import handle_scan_add
from app.utils.conversation import ConversationState, get_user_session
from app.service.sheet import SheetsService

sheets_service = SheetsService()


async def handle_command(text, user_name, chat_id, photo=None):
    session = get_user_session(chat_id)

    if text.startswith("/start"):
        session.reset()
        return (
            f"Hai, {user_name}! 👋 Selamat datang di bot pencatat keuanganmu. Siap bantu keuanganmu terkontrol! Ketik /menu untuk mulai ya",
            None,
        )

    elif text.startswith("/menu"):
        session.reset()
        return handle_menu(user_name)

    elif text.startswith("/help"):
        return handle_help()

    elif text.startswith("/summary"):
        return await handle_summary(text, chat_id)

    elif session.state == ConversationState.SUMMARY_INPUT:
        return await handle_summary(text, chat_id)

    elif text.startswith("/add"):
        session.reset()
        session.set_state(ConversationState.ADD_METHOD_SELECTION)
        keyboard = {
            "inline_keyboard": [
                [{"text": "✏️ Input Manual", "callback_data": "add_manual"}],
                [{"text": "📷 Scan Nota", "callback_data": "add_scan"}],
            ]
        }
        return "Pilih metode untuk menambahkan transaksi:", keyboard

    # Routing ke handler add manual/qr
    if session.state in [
        ConversationState.ADD_METHOD_SELECTION,
        ConversationState.ADD_MANUAL_NAME,
        ConversationState.ADD_MANUAL_JENIS,
        ConversationState.ADD_MANUAL_SUMBER,
        ConversationState.ADD_MANUAL_KATEGORI,
        ConversationState.ADD_MANUAL_KATEGORI_LAINNYA,
        ConversationState.ADD_MANUAL_JUMLAH,
        ConversationState.ADD_MANUAL_DESKRIPSI,
        ConversationState.ADD_MANUAL_CONFIRM,
    ]:
        return handle_manual_add(session, text, user_name)

    if session.state in [
        ConversationState.ADD_AI_PROCESSING,
        ConversationState.ADD_AI_PROCESSING_WAIT,
        ConversationState.ADD_AI_CONFIRM,
        ConversationState.ADD_AI_EDIT,
    ]:
        return await handle_scan_add(session, text, photo)

    return (
        "🤷‍♀️ Maaf, perintah yang kamu masukkan tidak aku kenali. Coba ketik /menu untuk melihat daftar perintah yang bisa kamu gunakan ya! 😉",
        None,
    )
