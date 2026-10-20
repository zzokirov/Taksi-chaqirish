"""Haydovchi uchun klaviaturalar."""
from typing import List

from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
)

from bot.database.models import District


def driver_panel_kb() -> ReplyKeyboardMarkup:
    """Haydovchi asosiy paneli."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🟢 Ishni boshlash"),
                KeyboardButton(text="🔴 Ishni to'xtatish"),
            ],
            [
                KeyboardButton(text="📋 Buyurtmalar"),
                KeyboardButton(text="👤 Profilim"),
            ],
            [
                KeyboardButton(text="💰 To'lovlarim"),
                KeyboardButton(text="💳 Obunani uzaytirish"),
            ],
            [
                KeyboardButton(text="📢 Guruhim"),
            ],
            [KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True,
    )


def driver_districts_kb(districts: List[District]) -> InlineKeyboardMarkup:
    """Haydovchi uchun tuman/shahar tanlash."""
    buttons = []
    for d in districts:
        buttons.append([
            InlineKeyboardButton(text=f"📍 {d.name}", callback_data=f"drv_district:{d.id}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def transport_type_kb() -> InlineKeyboardMarkup:
    """Transport turi tanlash."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Yengil avto (sedan)", callback_data="transport:sedan")],
        [InlineKeyboardButton(text="🚙 Minivan / Mikro", callback_data="transport:minivan")],
        [InlineKeyboardButton(text="🚌 Avtobus", callback_data="transport:avtobus")],
        [InlineKeyboardButton(text="🚐 Yo'l avtobus (marshrutka)", callback_data="transport:marshrutka")],
    ])


def driver_confirm_kb() -> InlineKeyboardMarkup:
    """Haydovchi ma'lumotlarini tasdiqlash."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Adminga yuborish", callback_data="drv_reg:confirm")],
        [InlineKeyboardButton(text="✏️ O'zgartirish", callback_data="drv_reg:restart")],
    ])


def payment_done_kb() -> InlineKeyboardMarkup:
    """To'lov amalga oshirildi tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 To'lov qildim", callback_data="payment:done")],
    ])


def order_action_kb(order_id: int) -> InlineKeyboardMarkup:
    """Haydovchi buyurtmani qabul qilish."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🙋‍♂️ Olaman",
            callback_data=f"accept_order:{order_id}"
        )]
    ])

def order_return_kb(order_id: int) -> InlineKeyboardMarkup:
    """Haydovchi buyurtmani qaytarishi uchun tugma."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="❌ Olmadim (Qaytarish)",
                callback_data=f"return_order:{order_id}"
            )
        ]
    ])


def trip_contact_kb(order_id: int, phone: str) -> InlineKeyboardMarkup:
    """Mijoz bilan bog'lanish tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"📞 Mijoz bilan bog'lanish: {phone}",
            callback_data=f"trip_noop:{order_id}"
        )],
        [InlineKeyboardButton(
            text="🚗 Yo'lga chiqdim",
            callback_data=f"trip_status:{order_id}:on_way"
        )],
    ])


def trip_on_way_kb(order_id: int) -> InlineKeyboardMarkup:
    """Yo'lda — keyingi qadam tugmalari."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📍 Manzilga yetib keldim",
            callback_data=f"trip_status:{order_id}:arrived"
        )],
        [InlineKeyboardButton(
            text="❌ Buyurtmani bekor qilish",
            callback_data=f"driver_cancel:{order_id}"
        )],
    ])


def trip_arrived_kb(order_id: int) -> InlineKeyboardMarkup:
    """Manzilga yetib keldi — safarni boshlash."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="▶️ Safarni boshlash",
            callback_data=f"trip_status:{order_id}:started"
        )],
        [InlineKeyboardButton(
            text="❌ Buyurtmani bekor qilish",
            callback_data=f"driver_cancel:{order_id}"
        )],
    ])


def trip_started_kb(order_id: int) -> InlineKeyboardMarkup:
    """Safar boshlandi — yakunlash."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Safarni yakunlash",
            callback_data=f"trip_status:{order_id}:completed"
        )],
    ])


def group_link_kb(invite_link: str) -> InlineKeyboardMarkup:
    """Guruhga qo'shilish linki."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Guruhga qo'shilish", url=invite_link)],
    ])


def back_to_main_kb() -> ReplyKeyboardMarkup:
    """Asosiy menyuga qaytish."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Asosiy menyu")],
        ],
        resize_keyboard=True,
    )
