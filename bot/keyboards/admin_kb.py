"""Admin uchun klaviaturalar."""
from typing import List

from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
)

from bot.database.models import District


def admin_menu_kb(pending_count: int = 0, support_count: int = 0) -> ReplyKeyboardMarkup:
    """Admin asosiy menyusi."""
    new_apps_text = f"🆕 Yangi arizalar ({pending_count})" if pending_count > 0 else "🆕 Yangi arizalar"
    support_text = f"📩 Yordam ({support_count})" if support_count > 0 else "📩 Yordam"
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=new_apps_text),
                KeyboardButton(text=support_text),
            ],
            [
                KeyboardButton(text="👥 Foydalanuvchilar"),
                KeyboardButton(text="🚕 Haydovchilar"),
            ],
            [
                KeyboardButton(text="💰 To'lovlar"),
                KeyboardButton(text="💳 To'lov sozlamalari"),
            ],
            [
                KeyboardButton(text="📨 Xabar yuborish"),
            ]
        ],
        resize_keyboard=True
    )

def driver_approval_kb(driver_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"admin_driver:approve:{driver_id}")],
        [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"admin_driver:reject:{driver_id}")]
    ])

def payment_settings_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Karta raqamini o'zgartirish", callback_data="payment_setting:card")],
        [InlineKeyboardButton(text="👤 Karta egasini o'zgartirish", callback_data="payment_setting:owner")],
        [InlineKeyboardButton(text="💰 To'lov summasini o'zgartirish", callback_data="payment_setting:amount")]
    ])

def cancel_admin_action_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Bekor qilish")]],
        resize_keyboard=True
    )

def broadcast_target_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Barcha foydalanuvchilarga")],
            [KeyboardButton(text="🚕 Barcha haydovchilarga")],
            [KeyboardButton(text="🔙 Bekor qilish")]
        ],
        resize_keyboard=True
    )

def confirm_broadcast_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast:confirm"), InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast:cancel")]
    ])

def driver_manage_kb(driver_id: int, status: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ O'chirish (Bloklash)", callback_data=f"admin_driver:reject:{driver_id}")]
    ])

def districts_manage_kb(districts: List[District]) -> InlineKeyboardMarkup:
    buttons = []
    for d in districts:
        buttons.append([InlineKeyboardButton(text=d.name, callback_data=f"district_act:{d.id}")])
    buttons.append([InlineKeyboardButton(text="➕ Yangi tuman qo'shish", callback_data="add_district")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Stubs for things that might be in import
def drivers_filter_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[])

def payments_filter_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[])

def district_actions_kb(*args, **kwargs) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[])

def groups_manage_kb(*args, **kwargs) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[])

def group_actions_kb(*args, **kwargs) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[])

def group_district_select_kb(*args, **kwargs) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[])

def broadcast_district_kb(*args, **kwargs) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[])
