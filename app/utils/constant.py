INCOME_CATEGORIES = [
    ("💼 Gaji", "gaji"),
    ("🎁 Bonus", "bonus"),
    ("♾️ Lainnya", "other_category"),
]

EXPENSE_CATEGORIES = [
    ("🍔 Makanan", "makanan"),
    ("🚗 Transportasi", "transportasi"),
    ("💸 Invest", "invest"),
    ("📱 Tagihan", "tagihan"),
    ("♾️ Lainnya", "other_category"),
]

SOURCE_MAP = {
    "cash": "Cash",
    "bca": "BCA",
}

CATEGORY_MAP = {
    "makanan": "Makanan",
    "transportasi": "Transportasi",
    "invest": "Invest",
    "tagihan": "Tagihan",
    "gaji": "Gaji",
    "bonus": "Bonus",
}

VALID_JENIS = ["pemasukan", "pengeluaran"]
VALID_SUMBER = list(SOURCE_MAP.keys()) + ["other_source"]
VALID_KATEGORI = [cat[1] for cat in INCOME_CATEGORIES + EXPENSE_CATEGORIES]
VALID_CONFIRM = ["save_transaction", "cancel_transaction"]

def build_keyboard(options, row=2):
    keyboard = []
    for i in range(0, len(options), row):
        keyboard.append([
            {"text": text, "callback_data": data}
            for text, data in options[i:i+row]
        ])
    keyboard.append([{"text": "« Kembali", "callback_data": "back"}])
    return {"inline_keyboard": keyboard}
