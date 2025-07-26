from app.utils.conversation import ConversationState

def handle_qr_add(session, text):
    if session.state == ConversationState.ADD_AI_PROCESSING:
        if text == "back" or text == "« Kembali":
            return None, None
        return "📷 Fitur Scan Nota akan segera hadir! Untuk sementara, silahkan gunakan input manual dengan /add", None
    return None, None
