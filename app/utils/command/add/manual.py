from app.utils.conversation import ConversationState
from app.utils.constant import (
    INCOME_CATEGORIES,
    EXPENSE_CATEGORIES,
    build_keyboard,
    SOURCE_MAP,
    CATEGORY_MAP,
    VALID_JENIS,
    VALID_SUMBER,
    VALID_KATEGORI,
    VALID_CONFIRM,
)

def handle_manual_add(session, text, user_name):
    if session.state == ConversationState.ADD_METHOD_SELECTION:
        if text == "add_manual":
            session.set_state(ConversationState.ADD_MANUAL_NAME)
            session.set_current_datetime()
            keyboard = {"inline_keyboard": [[{"text": "« Kembali", "callback_data": "back"}]]}
            return "Silahkan masukkan nama transaksi:", keyboard
        elif text == "add_qr":
            session.set_state(ConversationState.ADD_AI_PROCESSING)
            keyboard = {"inline_keyboard": [[{"text": "« Kembali", "callback_data": "back"}]]}
            return "Silahkan jelaskan transaksi dengan bahasa natural'", keyboard

    # Nama transaksi
    if session.state == ConversationState.ADD_MANUAL_NAME:
        if text in ["back", "« Kembali"]:
            session.go_back()
            keyboard = {
                "inline_keyboard": [
                    [{"text": "✏️ Input Manual", "callback_data": "add_manual"}],
                    [{"text": "📷 Scan Nota", "callback_data": "add_qr"}]
                ]
            }
            return "Silahkan pilih metode input transaksi:", keyboard
        session.transaction_data["nama"] = text
        session.set_state(ConversationState.ADD_MANUAL_JENIS)
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "💰 Pemasukan", "callback_data": "pemasukan"},
                    {"text": "💸 Pengeluaran", "callback_data": "pengeluaran"}
                ],
                [{"text": "« Kembali", "callback_data": "back"}]
            ]
        }
        return "Pilih jenis transaksi:", keyboard

    # Jenis transaksi
    if session.state == ConversationState.ADD_MANUAL_JENIS:
        if text in ["back", "« Kembali"]:
            session.go_back()
            keyboard = {"inline_keyboard": [[{"text": "« Kembali", "callback_data": "back"}]]}
            return "Silahkan masukkan nama transaksi:", keyboard
        if text not in VALID_JENIS:
            return "Silahkan pilih jenis transaksi menggunakan tombol yang tersedia.", None
        if text == "pemasukan":
            session.transaction_data["jenis"] = "Pemasukan"
        elif text == "pengeluaran":
            session.transaction_data["jenis"] = "Pengeluaran"
        session.set_state(ConversationState.ADD_MANUAL_SUMBER)
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "💵 Cash", "callback_data": "cash"},
                    {"text": "🏦 BCA", "callback_data": "bca"},
                    {"text": "♾️ Lainnya", "callback_data": "other_source"}
                ],
                [{"text": "« Kembali", "callback_data": "back"}]
            ]
        }
        return "Pilih sumber dana transaksi:", keyboard

    # Sumber dana
    if session.state == ConversationState.ADD_MANUAL_SUMBER:
        if text in ["back", "« Kembali"]:
            session.go_back()
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "💰 Pemasukan", "callback_data": "pemasukan"},
                        {"text": "💸 Pengeluaran", "callback_data": "pengeluaran"}
                    ],
                    [{"text": "« Kembali", "callback_data": "back"}]
                ]
            }
            return "Pilih jenis transaksi:", keyboard
        if text in SOURCE_MAP:
            session.transaction_data["sumber"] = SOURCE_MAP[text]
        else:
            session.transaction_data["sumber"] = text
        session.set_state(ConversationState.ADD_MANUAL_KATEGORI)
        if session.transaction_data["jenis"] == "Pemasukan":
            keyboard = build_keyboard(INCOME_CATEGORIES)
        else:
            keyboard = build_keyboard(EXPENSE_CATEGORIES)
        return "Pilih kategori transaksi:", keyboard

    # Kategori
    if session.state == ConversationState.ADD_MANUAL_KATEGORI:
        if text in ["back", "« Kembali"]:
            session.go_back()
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "💵 Cash", "callback_data": "cash"},
                        {"text": "🏦 BCA", "callback_data": "bca"},
                        {"text": "♾️ Lainnya", "callback_data": "other_source"}
                    ],
                    [{"text": "« Kembali", "callback_data": "back"}]
                ]
            }
            return "Pilih sumber dana transaksi:", keyboard
        session.transaction_data["kategori"] = CATEGORY_MAP.get(text, text)
        session.set_state(ConversationState.ADD_MANUAL_JUMLAH)
        keyboard = {"inline_keyboard": [[{"text": "« Kembali", "callback_data": "back"}]]}
        return "Masukkan jumlah transaksi (dalam angka, contoh: 50000):", keyboard

    # Jumlah
    if session.state == ConversationState.ADD_MANUAL_JUMLAH:
        if text in ["back", "« Kembali"]:
            session.go_back()
            if session.transaction_data["jenis"] == "Pemasukan":
                keyboard = build_keyboard(INCOME_CATEGORIES)
            else:
                keyboard = build_keyboard(EXPENSE_CATEGORIES)
            return "Pilih kategori transaksi:", keyboard
        clean_amount = text.replace(".", "").replace(",", "").strip()
        if not clean_amount.isdigit() or int(clean_amount) <= 0:
            return "Jumlah harus berupa angka positif. Silahkan masukkan kembali:", None
        amount = int(clean_amount)
        formatted_amount = f"{amount:,}".replace(",", ".")
        session.transaction_data["jumlah"] = formatted_amount
        session.set_state(ConversationState.ADD_MANUAL_DESKRIPSI)
        keyboard = {"inline_keyboard": [[{"text": "« Kembali", "callback_data": "back"}]]}
        return "Masukkan deskripsi transaksi (opsional, ketik '-' jika tidak ada):", keyboard

    # Deskripsi
    if session.state == ConversationState.ADD_MANUAL_DESKRIPSI:
        if text in ["back", "« Kembali"]:
            session.go_back()
            keyboard = {"inline_keyboard": [[{"text": "« Kembali", "callback_data": "back"}]]}
            return "Masukkan jumlah transaksi (dalam angka, contoh: 50000):", keyboard
        session.transaction_data["deskripsi"] = text if text != "-" else ""
        session.set_state(ConversationState.ADD_MANUAL_CONFIRM)
        confirmation = "📝 *Detail Transaksi:*\n\n"
        confirmation += f"📅 Tanggal: {session.transaction_data['tanggal']}\n"
        confirmation += f"🏷️ Nama: {session.transaction_data['nama']}\n"
        confirmation += f"📊 Jenis: {session.transaction_data['jenis']}\n"
        confirmation += f"💰 Sumber: {session.transaction_data['sumber']}\n"
        confirmation += f"🏷️ Kategori: {session.transaction_data['kategori']}\n"
        confirmation += f"💵 Jumlah: Rp {session.transaction_data['jumlah']}\n"
        if session.transaction_data['deskripsi']:
            confirmation += f"📝 Deskripsi: {session.transaction_data['deskripsi']}\n"
        confirmation += "\nApakah data di atas sudah benar?"
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Simpan", "callback_data": "save_transaction"},
                    {"text": "❌ Batal", "callback_data": "cancel_transaction"}
                ],
                [{"text": "« Kembali", "callback_data": "back"}]
            ]
        }
        return confirmation, keyboard

    # Konfirmasi
    if session.state == ConversationState.ADD_MANUAL_CONFIRM:
        if text in ["back", "« Kembali"]:
            session.go_back()
            keyboard = {"inline_keyboard": [[{"text": "« Kembali", "callback_data": "back"}]]}
            return "Masukkan deskripsi transaksi (opsional, ketik '-' jika tidak ada):", keyboard
        if text not in VALID_CONFIRM:
            return "Silahkan pilih aksi menggunakan tombol yang tersedia.", None
        if text == "save_transaction":
            # Simpan ke sheets
            try:
                from app.service.sheet import SheetsService
                sheets_service = SheetsService()
                sheets_service.add_transaction(session.transaction_data)
                session.reset()
                return "✅ Transaksi berhasil disimpan! Gunakan /add untuk menambahkan transaksi baru atau /menu untuk kembali ke menu utama.", None
            except Exception as e:
                return f"❌ Terjadi kesalahan saat menyimpan transaksi: {str(e)}", None
        elif text == "cancel_transaction":
            session.reset()
            return "❌ Transaksi dibatalkan. Gunakan /menu untuk kembali ke menu utama.", None

    return None, None
