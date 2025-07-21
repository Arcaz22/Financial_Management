def handle_command(text: str, user_name: str) -> str:
    if text.startswith("/start"):
        return f"Hai, {user_name}! 👋 Selamat datang di bot pencatat keuanganmu. Siap bantu keuanganmu terkontrol! Ketik /menu untuk mulai ya"
    elif text.startswith("/menu"):
        return (
            "📚 *Menu Utama:*\n\n"
            "✨ /add - Yuk, catat pengeluaran atau pemasukan barumu! \n"
            "📈 /summary - Intip ringkasan keuanganmu \n"
            "🆘 /help - Butuh panduan lebih lanjut?  \n\n"
            "Pilih salah satu menu di atas untuk mulai berinteraksi! 👇"
        )
    elif text.startswith("/add"):
        return "✍️ Siap mencatat!"
    elif text.startswith("/summary"):
        return "📊 Sedang menyiapkan ringkasan keuanganmu... Mohon tunggu sebentar ya! Fitur ini akan segera hadir ✨"
    elif text.startswith("/help"):
        return "🤔 Bingung? Jangan khawatir! Gunakan /menu untuk melihat semua perintah yang tersedia dan bagaimana cara menggunakannya."
    else:
        return "🤷‍♀️ Maaf, perintah yang kamu masukkan tidak aku kenali. Coba ketik /menu untuk melihat daftar perintah yang bisa kamu gunakan ya! 😉"
