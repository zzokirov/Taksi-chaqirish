"""Buyurtma qabul qilish va safar jarayoni."""
import logging
from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.driver_kb import (
    trip_contact_kb, trip_on_way_kb, trip_arrived_kb, trip_started_kb, back_to_main_kb
)
from bot.keyboards.customer_kb import cancel_reasons_kb
from bot.services.order_service import OrderService
from bot.services.driver_service import DriverService
from bot.services.customer_service import CustomerService
from bot.utils.helpers import safe_send_message

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data.startswith("accept_order:"))
async def process_accept_order(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    order_id = int(callback.data.split(":")[1])
    driver = await DriverService.get_driver_by_telegram_id(session, callback.from_user.id)
    
    if not driver:
        await callback.answer("Haydovchi topilmadi.", show_alert=True)
        return

    success = await OrderService.accept_order(session, order_id, driver.id)
    if not success:
        await callback.answer("❌ Ushbu buyurtma allaqachon boshqa haydovchi tomonidan qabul qilingan yoki bekor qilingan!", show_alert=True)
        return

    order = await OrderService.get_order(session, order_id)
    
    # Guruh chat_id va message_id saqlaymiz
    if callback.message:
        order.group_chat_id = callback.message.chat.id
        order.group_message_id = callback.message.message_id
        await session.commit()

    group_text = (
        "🚖 *BUYURTMA BAND QILINDI*\n\n"
        f"🏠 Qayerdan: {order.from_address}\n"
        f"🏁 Qayerga: {order.to_address}\n"
        f"👥 Yo'lovchilar: {order.passengers}\n"
        f"💰 Narx: {order.price or 'Kelishiladi'}\n"
        f"👤 Qabul qildi: *{driver.full_name}*\n"
        f"🚗 Mashina: {driver.car_model} ({driver.car_number})\n\n"
        "✅ *Buyurtma haydovchi tomonidan qabul qilindi.*"
    )
    try:
        await callback.message.edit_text(
            group_text,
            reply_markup=None,  # Guruhda boshqa hech qanday knopka va raqam ko'rinmaydi!
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"edit group message error: {e}")

    await callback.answer("✅ Buyurtmani qabul qildingiz! Barcha ma'lumotlar bot lichkangizga yuborildi.", show_alert=False)

    # Faqat buyurtmani olgan haydovchining shaxsiy botiga (lichkasiga) raqam va tugmalarni yuboramiz
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    driver_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Telegram orqali bog'lanish", url=f"tg://user?id={order.customer.telegram_id}")],
        [InlineKeyboardButton(text="❌ Olmadim (Qaytarish)", callback_data=f"return_order:{order.id}")]
    ])
    driver_text = (
        "🎉 *Siz buyurtmani qabul qildingiz!*\n\n"
        f"👤 *Mijoz:* {order.customer.full_name}\n"
        f"📞 *Telefon raqami:* {order.customer.phone}\n"
        f"(Nusxa olish uchun: `{order.customer.phone}`)\n\n"
        f"🏠 *Qayerdan:* {order.from_address}\n"
        f"🏁 *Qayerga:* {order.to_address}\n"
        f"👥 *Yo'lovchilar:* {order.passengers}\n"
        f"💰 *Narx:* {order.price or 'Kelishiladi'}\n\n"
        "👇 *Qo'ng'iroq qilish uchun pastdagi kontaktni bosing:*"
    )
    await safe_send_message(bot, driver.user.telegram_id, driver_text, parse_mode="Markdown", reply_markup=driver_kb)

    # 1 ta bosishda telefon qilish uchun Telegram kontakt kartochkasini ham yuboramiz
    try:
        await bot.send_contact(
            chat_id=driver.user.telegram_id,
            phone_number=order.customer.phone,
            first_name=order.customer.full_name or "Mijoz"
        )
    except Exception as e:
        logger.warning(f"send_contact error: {e}")

    customer_text = (
        "✅ *Haydovchi topildi!*\n\n"
        f"👤 Ism: {driver.full_name}\n"
        f"🚕 Mashina: {driver.car_model}\n"
        f"🔢 Davlat raqami: {driver.car_number}\n\n"
        "Haydovchi tez orada siz bilan bog'lanadi."
    )
    await safe_send_message(bot, order.customer.telegram_id, customer_text, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())

@router.callback_query(F.data.startswith("show_phone:"))
async def process_show_phone(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    order_id = int(callback.data.split(":")[1])
    order = await OrderService.get_order(session, order_id)
    if not order:
        await callback.answer("Buyurtma topilmadi.", show_alert=True)
        return
        
    driver = await DriverService.get_driver_by_telegram_id(session, callback.from_user.id)
    if not driver or order.driver_id != driver.id:
        await callback.answer("❌ Bu buyurtmani siz olmagansiz! Raqam faqat buyurtmani olgan haydovchiga ko'rinadi.", show_alert=True)
        return

    await callback.answer(f"📞 Mijoz telefoni:\n{order.customer.phone}", show_alert=True)

@router.callback_query(F.data.startswith("return_order:"))
async def process_return_order(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    order_id = int(callback.data.split(":")[1])
    driver = await DriverService.get_driver_by_telegram_id(session, callback.from_user.id)
    
    order = await OrderService.get_order(session, order_id)
    if not order:
        await callback.answer("Buyurtma topilmadi.", show_alert=True)
        return

    if not driver or order.driver_id != driver.id:
        await callback.answer("❌ Siz bu buyurtmani olmagansiz, uni qaytara olmaysiz.", show_alert=True)
        return

    order.status = "SEARCHING_DRIVER"
    order.driver_id = None
    order.accepted_at = None
    await session.commit()
    
    from bot.keyboards.driver_kb import order_action_kb
    order_text = (
        "🚕 *YANGI BUYURTMA* (Qaytarilgan)\n\n"
        f"🏠 Qayerdan: {order.from_address}\n"
        f"🏁 Qayerga: {order.to_address}\n"
        f"👥 Yo'lovchilar: {order.passengers}\n"
        f"💰 Taklif qilingan narx: {order.price or 'Kelishiladi'}\n"
        f"🕒 Vaqt: {order.created_at.strftime('%H:%M') if order.created_at else ''}"
    )

    # 1. Haydovchining shaxsiy chatidagi xabarni yangilaymiz (agar shaxsiy chatdan bosgan bo'lsa)
    if callback.message.chat.type == "private":
        try:
            await callback.message.edit_text("❌ *Siz buyurtmani qaytardingiz.* Buyurtma yana umumiy guruhga yuborildi.", parse_mode="Markdown")
        except Exception:
            pass

    # 2. Guruhdagi xabarni qayta tiklaymiz: "🙋‍♂️ Olaman" tugmasi bilan!
    if order.group_chat_id and order.group_message_id:
        try:
            await bot.edit_message_text(
                chat_id=order.group_chat_id,
                message_id=order.group_message_id,
                text=order_text,
                reply_markup=order_action_kb(order.id),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"edit group message on return error: {e}")
    elif callback.message.chat.type != "private":
        try:
            await callback.message.edit_text(order_text, reply_markup=order_action_kb(order.id), parse_mode="Markdown")
        except Exception:
            pass
            
    await callback.answer("Buyurtma guruhga qaytarildi!", show_alert=True)
    await safe_send_message(bot, order.customer.telegram_id, "⚠️ Haydovchi buyurtmani bekor qildi. Boshqa haydovchi qidirilmoqda...", parse_mode="Markdown")


@router.callback_query(F.data.startswith("reject_order:"))
async def process_reject_order(callback: types.CallbackQuery):
    await callback.message.edit_text("❌ Siz buyurtmani rad etdingiz.")
    await callback.answer()


@router.callback_query(F.data.startswith("trip_noop:"))
async def trip_noop(callback: types.CallbackQuery):
    await callback.answer("Bu tugma orqali mijozning telefon raqamini ko'rishingiz mumkin.", show_alert=True)


@router.callback_query(F.data.startswith("trip_status:"))
async def change_trip_status(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    data = callback.data.split(":")
    order_id = int(data[1])
    action = data[2]
    
    order = await OrderService.get_order(session, order_id)
    if not order:
        await callback.answer("Buyurtma topilmadi.", show_alert=True)
        return
        
    if action == "on_way":
        await OrderService.update_status(session, order_id, "DRIVER_ON_WAY")
        await callback.message.edit_reply_markup(reply_markup=trip_on_way_kb(order_id))
        await safe_send_message(bot, order.customer.telegram_id, "🚗 Haydovchi siz tomonga yo'lga chiqdi.")
        
    elif action == "arrived":
        await OrderService.update_status(session, order_id, "DRIVER_ARRIVED")
        await callback.message.edit_reply_markup(reply_markup=trip_arrived_kb(order_id))
        await safe_send_message(bot, order.customer.telegram_id, "📍 Haydovchi yetib keldi. Iltimos, chiqing.")
        
    elif action == "started":
        await OrderService.update_status(session, order_id, "TRIP_STARTED")
        await callback.message.edit_reply_markup(reply_markup=trip_started_kb(order_id))
        await safe_send_message(bot, order.customer.telegram_id, "▶️ Safar boshlandi. Oq yo'l!")
        
    elif action == "completed":
        await OrderService.update_status(session, order_id, "COMPLETED")
        await callback.message.edit_text("✅ Safar muvaffaqiyatli yakunlandi.")
        await safe_send_message(bot, order.customer.telegram_id, "✅ Safar yakunlandi. Xizmatimizdan foydalanganingiz uchun rahmat!")
        
    await callback.answer()


@router.callback_query(F.data.startswith("customer_cancel:"))
async def customer_cancel_request(callback: types.CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "Bekor qilish sababini tanlang:",
        reply_markup=cancel_reasons_kb(order_id, "customer")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("driver_cancel:"))
async def driver_cancel_request(callback: types.CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "Bekor qilish sababini tanlang:",
        reply_markup=cancel_reasons_kb(order_id, "driver")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_reason_"))
async def process_cancel_reason(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    parts = callback.data.split(":")
    role_part = parts[0]
    order_id = int(parts[1])
    reason_code = parts[2]
    
    reason_map = {
        "driver_no_show": "Haydovchi kelmadi",
        "customer_no_show": "Mijoz kelmadi",
        "driver_cant_come": "Haydovchi kela olmaydi",
        "wrong_address": "Manzil noto'g'ri",
        "other": "Boshqa sabab"
    }
    reason_text = reason_map.get(reason_code, "Noma'lum sabab")
    
    order = await OrderService.get_order(session, order_id)
    if not order or order.status in ["COMPLETED", "CANCELLED"]:
        await callback.answer("Buyurtma allaqachon yakunlangan yoki bekor qilingan.", show_alert=True)
        return
        
    await OrderService.cancel_order(session, order_id, reason_text)
    await callback.message.edit_text(f"❌ Buyurtma bekor qilindi.\nSabab: {reason_text}")
    
    if role_part == "cancel_reason_customer":
        if order.driver:
            await safe_send_message(bot, order.driver.user.telegram_id, f"❌ Buyurtma mijoz tomonidan bekor qilindi.\nSabab: {reason_text}")
    else:
        await safe_send_message(bot, order.customer.telegram_id, f"❌ Buyurtma haydovchi tomonidan bekor qilindi.\nSabab: {reason_text}")
        
    await callback.answer()
