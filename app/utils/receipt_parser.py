import re
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ReceiptParser:
    def __init__(self):
        logger.info("ReceiptParser initialized")

    def parse_receipt_text(self, text: str) -> dict:
        transaction_data = {
            "tanggal": self._extract_date(text),
            "nama": self._extract_store_name(text),
            "jenis": "Pengeluaran",  # Default untuk nota adalah pengeluaran
            "sumber": "Cash",  # Default sumber dana
            "kategori": self._extract_category(text),
            "jumlah": self._extract_total_amount(text),
            "deskripsi": self._extract_items_description(text),
            "items": self._extract_items(text),
            "tax": self._extract_tax(text),
            "discount": self._extract_discount(text),
            "raw_text": text,  # Simpan teks asli untuk referensi
        }

        if transaction_data["tanggal"]:
            try:
                date_obj = datetime.strptime(transaction_data["tanggal"], "%d/%m/%Y")
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
                transaction_data["tanggal"] = (
                    f"{date_obj.day} {month_names[date_obj.month-1]} {date_obj.year} {datetime.now().hour:02d}:{datetime.now().minute:02d}"
                )
            except:
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
                transaction_data["tanggal"] = (
                    f"{now.day} {month_names[now.month-1]} {now.year} {now.hour:02d}:{now.minute:02d}"
                )
        else:
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
            transaction_data["tanggal"] = (
                f"{now.day} {month_names[now.month-1]} {now.year} {now.hour:02d}:{now.minute:02d}"
            )

        return transaction_data

    def _extract_date(self, text: str) -> str:
        date_patterns = [
            r"(\d{1,2})[/-](\d{1,2})[/-](20\d{2})",
            r"(\d{1,2})\s+([A-Za-z]+)\s+(20\d{2})",
            r"Date\s*:\s*(\d{1,2})[/-](\d{1,2})[/-](20\d{2})",
            r"Tanggal\s*:\s*(\d{1,2})[/-](\d{1,2})[/-](20\d{2})",
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 3:
                    day, month, year = match.groups()
                    if re.match(r"[A-Za-z]+", month):
                        month_names = {
                            "jan": 1,
                            "feb": 2,
                            "mar": 3,
                            "apr": 4,
                            "may": 5,
                            "jun": 6,
                            "jul": 7,
                            "aug": 8,
                            "sep": 9,
                            "oct": 10,
                            "nov": 11,
                            "dec": 12,
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
                        month_lower = month.lower()
                        for key, value in month_names.items():
                            if month_lower.startswith(key):
                                month = str(value)
                                break
                    return f"{day}/{month}/{year}"

        return ""

    def _extract_store_name(self, text: str) -> str:
        lines = text.split("\n")
        for i in range(min(3, len(lines))):
            if lines[i] and not any(
                keyword in lines[i].lower()
                for keyword in ["receipt", "invoice", "struk", "nota"]
            ):
                return lines[i].strip()

        store_patterns = [
            r"Store\s*:\s*(.*)",
            r"Merchant\s*:\s*(.*)",
            r"Toko\s*:\s*(.*)",
        ]

        for pattern in store_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return "Toko/Merchant"

    def _extract_category(self, text: str) -> str:
        text_lower = text.lower()

        if any(
            keyword in text_lower
            for keyword in ["restaurant", "resto", "cafe", "food", "makanan", "minuman"]
        ):
            return "Makanan"
        elif any(
            keyword in text_lower
            for keyword in [
                "transport",
                "transportasi",
                "grab",
                "gojek",
                "taxi",
                "taksi",
                "bus",
                "train",
                "kereta",
            ]
        ):
            return "Transportasi"
        elif any(
            keyword in text_lower
            for keyword in ["invest", "investasi", "saham", "reksadana", "obligasi"]
        ):
            return "Investasi"
        elif any(
            keyword in text_lower
            for keyword in [
                "belanja",
                "supermarket",
                "mart",
                "market",
                "toko",
                "retail",
            ]
        ):
            return "Belanja"
        elif any(
            keyword in text_lower
            for keyword in ["pulsa", "data", "internet", "telepon", "phone"]
        ):
            return "Telekomunikasi"

        # Default
        return "Lainnya"

    def _extract_total_amount(self, text: str) -> str:
        total_patterns = [
            r"Total\s*:?\s*(?:Rp\.?|IDR)?\s*([\d.,]+)",
            r"TOTAL\s*:?\s*(?:Rp\.?|IDR)?\s*([\d.,]+)",
            r"Grand Total\s*:?\s*(?:Rp\.?|IDR)?\s*([\d.,]+)",
            r"Jumlah\s*:?\s*(?:Rp\.?|IDR)?\s*([\d.,]+)",
            r"Amount\s*:?\s*(?:Rp\.?|IDR)?\s*([\d.,]+)",
        ]

        for pattern in total_patterns:
            match = re.search(pattern, text)
            if match:
                # Bersihkan format angka
                amount = match.group(1).replace(".", "").replace(",", "")
                return amount

        amounts = re.findall(r"(?:Rp\.?|IDR)?\s*([\d.,]+)", text)
        if amounts:
            cleaned_amounts = []
            for amount in amounts:
                try:
                    cleaned = amount.replace(".", "").replace(",", "")
                    if cleaned.isdigit():
                        cleaned_amounts.append(int(cleaned))
                except ValueError:
                    continue

            if cleaned_amounts:
                return str(max(cleaned_amounts))

        return "0"

    def _extract_items_description(self, text: str) -> str:
        items = self._extract_items(text)
        if items:
            item_names = [item.get("name", "") for item in items]
            return ", ".join(item_names[:3]) + ("..." if len(item_names) > 3 else "")

        lines = text.split("\n")
        for i in range(len(lines)):
            if "item" in lines[i].lower() or "barang" in lines[i].lower():
                if i + 1 < len(lines) and lines[i + 1].strip():
                    return lines[i + 1].strip()

        return "Pembelian barang"

    def _extract_items(self, text: str) -> list:
        items = []
        lines = text.split("\n")

        for i in range(len(lines)):
            price_match = re.search(
                r"(.*?)(?:Rp\.?|IDR)?\s*([\d.,]+)(?:\s*(?:x|×)\s*(\d+))?\s*$", lines[i]
            )
            if price_match:
                name = price_match.group(1).strip()
                price = price_match.group(2).replace(".", "").replace(",", "")
                quantity = price_match.group(3) if price_match.group(3) else "1"

                if name and not any(
                    keyword in name.lower()
                    for keyword in [
                        "total",
                        "subtotal",
                        "tax",
                        "pajak",
                        "diskon",
                        "discount",
                    ]
                ):
                    items.append({"name": name, "price": price, "quantity": quantity})

        return items

    def _extract_tax(self, text: str) -> dict:
        tax_patterns = [
            r"PPN\s*:?\s*(?:Rp\.?|IDR)?\s*([\d.,]+)",
            r"Tax\s*:?\s*(?:Rp\.?|IDR)?\s*([\d.,]+)",
            r"Pajak\s*:?\s*(?:Rp\.?|IDR)?\s*([\d.,]+)",
            r"VAT\s*:?\s*(?:Rp\.?|IDR)?\s*([\d.,]+)",
            r"PPN\s*(\d+)%",
            r"Tax\s*(\d+)%",
            r"Pajak\s*(\d+)%",
            r"VAT\s*(\d+)%",
        ]

        for pattern in tax_patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1)
                if "." in value or "," in value:  # Nilai absolut
                    tax_amount = value.replace(".", "").replace(",", "")
                    return {"type": "amount", "value": tax_amount}
                else:  # Persentase
                    return {"type": "percentage", "value": value}

        return {"type": "none", "value": "0"}

    def _extract_discount(self, text: str) -> dict:
        discount_patterns = [
            r"Diskon\s*:?\s*(?:Rp\.?|IDR)?\s*([\d.,]+)",
            r"Discount\s*:?\s*(?:Rp\.?|IDR)?\s*([\d.,]+)",
            r"Potongan\s*:?\s*(?:Rp\.?|IDR)?\s*([\d.,]+)",
            r"Diskon\s*(\d+)%",
            r"Discount\s*(\d+)%",
            r"Potongan\s*(\d+)%",
        ]

        for pattern in discount_patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1)
                if "." in value or "," in value:  # Nilai absolut
                    discount_amount = value.replace(".", "").replace(",", "")
                    return {"type": "amount", "value": discount_amount}
                else:  # Persentase
                    return {"type": "percentage", "value": value}

        return {"type": "none", "value": "0"}
