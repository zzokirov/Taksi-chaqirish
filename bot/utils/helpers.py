"""Yordamchi funksiyalar."""
import logging
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)


def is_admin(telegram_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish."""
    return telegram_id in settings.ADMIN_IDS


def format_phone(phone: str) -> str:
    """Telefon raqamni formatlash."""
    if phone and not phone.startswith("+"):
        phone = "+" + phone
    return phone


def format_datetime(dt: datetime | None) -> str:
    """Sana va vaqtni formatlash."""
    if dt is None:
        return "—"
    return dt.strftime("%d.%m.%Y %H:%M")


def format_order_status(status: str) -> str:
    """Buyurtma statusini o'zbek tilida formatlash."""
    statuses = {
        "NEW": "🆕 Yangi",
        "SEARCHING_DRIVER": "🔍 Haydovchi qidirilmoqda",
        "DRIVER_ACCEPTED": "✅ Haydovchi qabul qildi",
        "DRIVER_ON_WAY": "🚗 Haydovchi yo'lda",
        "DRIVER_ARRIVED": "📍 Haydovchi yetib keldi",
        "TRIP_STARTED": "▶️ Safar boshlandi",
        "COMPLETED": "✅ Tugallandi",
        "CANCELLED": "❌ Bekor qilindi",
    }
    return statuses.get(status, status)


def format_driver_status(status: str) -> str:
    """Haydovchi statusini o'zbek tilida formatlash."""
    statuses = {
        "PENDING": "🟡 Kutilmoqda",
        "APPROVED": "🟢 Tasdiqlangan",
        "REJECTED": "🔴 Rad etilgan",
        "BLOCKED": "🚫 Bloklangan",
    }
    return statuses.get(status, status)


def format_payment_status(status: str) -> str:
    """To'lov statusini o'zbek tilida formatlash."""
    statuses = {
        "NONE": "⚪ Hali to'lanmagan",
        "PENDING": "🟡 Kutilmoqda",
        "APPROVED": "🟢 Tasdiqlangan",
        "REJECTED": "🔴 Rad etilgan",
    }
    return statuses.get(status, status)


async def safe_send_message(bot, chat_id: int, text: str, **kwargs) -> bool:
    """Xabar yuborishda xatolik bo'lsa log yozish."""
    try:
        await bot.send_message(chat_id=chat_id, text=text, **kwargs)
        return True
    except Exception as e:
        logger.error(f"Xabar yuborib bo'lmadi (chat_id={chat_id}): {e}")
        return False
