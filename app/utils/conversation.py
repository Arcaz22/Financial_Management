from enum import Enum
from datetime import datetime
from typing import Dict, Optional


class ConversationState(Enum):
    IDLE = "idle"
    ADD_METHOD_SELECTION = "add_method_selection"
    ADD_MANUAL_NAME = "add_manual_name"
    ADD_MANUAL_JENIS = "add_manual_jenis"
    ADD_MANUAL_SUMBER = "add_manual_sumber"
    ADD_MANUAL_KATEGORI = "add_manual_kategori"
    ADD_MANUAL_KATEGORI_LAINNYA = "add_manual_kategori_lainnya"
    ADD_MANUAL_JUMLAH = "add_manual_jumlah"
    ADD_MANUAL_DESKRIPSI = "add_manual_deskripsi"
    ADD_MANUAL_CONFIRM = "add_manual_confirm"
    ADD_AI_PROCESSING = "add_ai_processing"
    ADD_AI_PROCESSING_WAIT = "add_ai_processing_wait"
    ADD_AI_CONFIRM = "add_ai_confirm"
    ADD_AI_EDIT = "add_ai_edit"
    SUMMARY_INPUT = "SUMMARY_INPUT"


class UserSession:
    def __init__(self):
        self.state = ConversationState.IDLE
        self.transaction_data = {
            "tanggal": "",
            "nama": "",
            "jenis": "",
            "sumber": "",
            "kategori": "",
            "jumlah": "",
            "deskripsi": "",
        }
        self.prev_states = []
        self.temp_data = None

    def set_state(self, new_state: ConversationState):
        self.prev_states.append(self.state)
        self.state = new_state

    def go_back(self) -> Optional[ConversationState]:
        if not self.prev_states:
            return None

        self.state = self.prev_states.pop()
        return self.state

    def reset(self):
        self.state = ConversationState.IDLE
        self.prev_states = []
        self.transaction_data = {
            "tanggal": "",
            "nama": "",
            "jenis": "",
            "sumber": "",
            "kategori": "",
            "jumlah": "",
            "deskripsi": "",
        }

    def set_current_datetime(self):
        now = datetime.now()
        month_names = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "November",
            "Desember",
        ]
        formatted_date = f"{now.day} {month_names[now.month-1]} {now.year} {now.hour:02d}:{now.minute:02d}"
        self.transaction_data["tanggal"] = formatted_date


user_sessions: Dict[int, UserSession] = {}


def get_user_session(chat_id: int) -> UserSession:
    if chat_id not in user_sessions:
        user_sessions[chat_id] = UserSession()
    return user_sessions[chat_id]
