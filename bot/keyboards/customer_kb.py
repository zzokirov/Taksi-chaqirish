"""Mijoz uchun klaviaturalar."""
from typing import List

from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
)

from bot.database.models import District


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Mijoz asosiy menyusi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚕 Taksi chaqirish")],
            [KeyboardButton(text="👤 Profilim"), KeyboardButton(text="📋 Buyurtmalarim")],
            [KeyboardButton(text="🚕 Haydovchi bo'lish"), KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True,
    )


def phone_kb() -> ReplyKeyboardMarkup:
    """Telefon raqam yuborish tugmasi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


from aiogram.utils.keyboard import InlineKeyboardBuilder

def direction_kb() -> InlineKeyboardMarkup:
    """Yo'nalish tanlash tugmalari."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Toshkent ➡️ Farg'ona", callback_data="direction:tosh_far")
    builder.button(text="Farg'ona ➡️ Toshkent", callback_data="direction:far_tosh")
    builder.adjust(1)
    return builder.as_markup()

def districts_kb(districts: List[District]) -> InlineKeyboardMarkup:
    """Tuman/shahar tanlash tugmalari."""
    buttons = []
    for d in districts:
        buttons.append([
            InlineKeyboardButton(text=f"📍 {d.name}", callback_data=f"district:{d.id}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def passengers_kb() -> InlineKeyboardMarkup:
    """Yo'lovchilar soni."""
    buttons = [
        [
            InlineKeyboardButton(text="1 kishi", callback_data="passengers:1"),
            InlineKeyboardButton(text="2 kishi", callback_data="passengers:2"),
        ],
        [
            InlineKeyboardButton(text="3 kishi", callback_data="passengers:3"),
            InlineKeyboardButton(text="4 kishi", callback_data="passengers:4"),
        ],
        [
            InlineKeyboardButton(text="5+ kishi", callback_data="passengers:5"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def order_confirm_kb() -> InlineKeyboardMarkup:
    """Buyurtmani tasdiqlash."""
    buttons = [
        [InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="order:confirm")],
        [InlineKeyboardButton(text="✏️ O'zgartirish", callback_data="order:edit")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="order:cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_order_kb(order_id: int) -> InlineKeyboardMarkup:
    """Mijoz buyurtmani bekor qilish."""
    buttons = [
        [InlineKeyboardButton(
            text="❌ Buyurtmani bekor qilish",
            callback_data=f"customer_cancel:{order_id}"
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_reasons_kb(order_id: int, role: str = "customer") -> InlineKeyboardMarkup:
    """Bekor qilish sabablari."""
    prefix = f"cancel_reason_{role}"
    reasons = [
        ("❌ Haydovchi kelmadi", "driver_no_show"),
        ("❌ Manzil noto'g'ri", "wrong_address"),
        ("❌ Boshqa sabab", "other"),
    ]
    if role == "driver":
        reasons = [
            ("❌ Mijoz kelmadi", "customer_no_show"),
            ("❌ Haydovchi kela olmaydi", "driver_cant_come"),
            ("❌ Manzil noto'g'ri", "wrong_address"),
            ("❌ Boshqa sabab", "other"),
        ]
    buttons = []
    for text, reason in reasons:
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"{prefix}:{order_id}:{reason}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
