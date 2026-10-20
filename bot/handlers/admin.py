"""Admin panel amallari."""
import logging
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.admin_states import AdminState
from bot.keyboards.admin_kb import (
    admin_menu_kb, drivers_filter_kb, payments_filter_kb, 
    districts_manage_kb, district_actions_kb, groups_manage_kb, 
    group_actions_kb, group_district_select_kb, broadcast_target_kb, 
    broadcast_district_kb, payment_settings_kb, driver_manage_kb
)
from bot.services.admin_service import AdminService
from bot.services.driver_service import DriverService
from bot.services.support_service import SupportService
from bot.services.payment_service import PaymentService
from bot.services.customer_service import CustomerService
from bot.services.order_service import OrderService
from bot.utils.helpers import is_admin, format_driver_status, format_payment_status, safe_send_message
from config import settings

logger = logging.getLogger(__name__)
router = Router()

async def build_admin_menu(session: AsyncSession):
    from bot.keyboards.admin_kb import admin_menu_kb
    pending_drivers = await DriverService.get_drivers_by_status(session, "PENDING")
    support_count = await SupportService.get_new_messages_count(session)
    return admin_menu_kb(len(pending_drivers), support_count)


def check_admin(message: types.Message) -> bool:
    return is_admin(message.from_user.id) and message.chat.type == "private"

@router.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext, session: AsyncSession):
    if not check_admin(message):
        return
    await state.clear()
    pending_drivers = await DriverService.get_drivers_by_status(session, "PENDING")
    await message.answer("⚙️ Admin paneliga xush kelibsiz.", reply_markup=await build_admin_menu(session))

@router.message(F.text == "👥 Foydalanuvchilar")
async def admin_users_menu(message: types.Message, session: AsyncSession):
    if not check_admin(message): return
    users_count = await CustomerService.get_all_users_count(session)
    text = (
        "👥 *FOYDALANUVCHILAR STATISTIKASI*\n\n"
        f"Botdan foydalanayotgan jami mijozlar (oddiy foydalanuvchilar) soni: *{users_count}* ta."
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "💰 To'lovlar")
async def admin_payments_menu(message: types.Message, session: AsyncSession):
    if not check_admin(message): return
    
    import datetime
    from sqlalchemy import select
    from bot.database.models import Payment
    
    res = await session.execute(select(Payment))
    all_payments = res.scalars().all()
    
    now_uzt = datetime.datetime.utcnow() + datetime.timedelta(hours=5)
    current_month = now_uzt.month
    current_year = now_uzt.year
    
    total_sum = 0
    month_sum = 0
    month_count = 0
    pending_count = 0
    
    for p in all_payments:
        if p.status == "APPROVED":
            total_sum += int(p.amount)
            
            p_uzt = p.created_at + datetime.timedelta(hours=5)
            if p_uzt.month == current_month and p_uzt.year == current_year:
                month_sum += int(p.amount)
                month_count += 1
                
        elif p.status in ["PENDING", "PENDING_RENEWAL"]:
            pending_count += 1
            
    months = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"]
    month_name = months[current_month - 1]
    
    text = (
        "💰 *TO'LOVLAR STATISTIKASI*\n\n"
        f"📅 *Shu oy ({month_name}, {current_year}):*\n"
        f"👥 Tasdiqlangan to'lovlar soni: *{month_count} ta*\n"
        f"💵 Shu oydagi tushum: *{month_sum:,} so'm*\n\n"
        f"📊 *Umumiy statistika (Bot ochilgandan beri):*\n"
        f"🏦 Jami tushum: *{total_sum:,} so'm*\n"
        f"⏳ Tasdiqlashni kutayotgan arizalar: *{pending_count} ta*\n"
    )
    
    text = text.replace(",", " ")
    
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "🚕 Haydovchilar")
async def admin_drivers_menu(message: types.Message, session: AsyncSession):
    if not check_admin(message): return
    
    from sqlalchemy import select
    from bot.database.models import Driver
    result = await session.execute(select(Driver))
    drivers = result.scalars().all()
    
    total = len(drivers)
    active = sum(1 for d in drivers if d.status == "APPROVED")
    pending = sum(1 for d in drivers if d.status == "PENDING")
    blocked = sum(1 for d in drivers if d.status == "BLOCKED")
    
    text = (
        "📊 *HAYDOVCHILAR STATISTIKASI*\n\n"
        f"👥 Jami ro'yxatdan o'tganlar: {total} ta\n"
        f"✅ Faol haydovchilar: {active} ta\n"
        f"⏳ Tasdiq kutayotganlar: {pending} ta\n"
        f"🚫 Bloklanganlar: {blocked} ta\n\n"
    )
    
    if active > 0:
        text += "🟢 *Faol haydovchilar ro'yxati:*\n"
        # Only show up to 30 active drivers to avoid message length limits
        active_drivers = [d for d in drivers if d.status == "APPROVED"][:30]
        for d in active_drivers:
            text += f"🆔 `{d.id}` | {d.full_name} | {d.phone}\n"
    
    text += "\n⚙️ To'liq boshqarish uchun `/driver_info <id>` buyrug'idan foydalaning (Masalan: `/driver_info 1`)."
    
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("driver_info"))
async def cmd_driver_info(message: types.Message, session: AsyncSession):
    if not check_admin(message): return
    try:
        drv_id = int(message.text.split(" ")[1])
        driver = await DriverService.get_driver_by_id(session, drv_id)
        if not driver:
            await message.answer("Topilmadi.")
            return
            
        text = (
            f"🚕 *HAYDOVCHI MA'LUMOTI*\n\n"
            f"ID: {driver.id}\n"
            f"Ism: {driver.full_name}\n"
            f"Tel: {driver.phone}\n"
            f"Mashina: {driver.car_model} ({driver.car_number})\n"
            f"Tuman: {driver.district.name}\n"
            f"Holat: {format_driver_status(driver.status)}\n"
            f"To'lov: {format_payment_status(driver.payment_status)}"
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=driver_manage_kb(driver.id, driver.status))
    except (IndexError, ValueError):
        await message.answer("Notog'ri format. Misol: /driver_info 123")


async def show_next_pending_application(message: types.Message, session: AsyncSession):
    pending_drivers = await DriverService.get_drivers_by_status(session, "PENDING")
    if not pending_drivers:
        from bot.keyboards.admin_kb import admin_menu_kb
        await message.answer("✅ Barcha arizalar ko'rib chiqildi. Yangi arizalar yo'q.", reply_markup=await build_admin_menu(session))
        return
        
    driver = pending_drivers[0]
    
    from bot.services.payment_service import PaymentService
    payments = await PaymentService.get_driver_payments(session, driver.id, limit=1)
    amount = payments[0].amount if payments else "Noma'lum"
    
    admin_text = (
        f"🆕 *{'OBUNANI UZAYTIRISH' if driver.payment_status == 'PENDING_RENEWAL' else 'YANGI HAYDOVCHI ARIZASI'}* ({len(pending_drivers)} ta dan 1-chisi)\n\n"
        f"👤 Ism familiya: {driver.full_name}\n"
        f"📱 Telefon: {driver.phone}\n"
        f"🚗 Mashina: {driver.car_model}\n"
        f"📍 Tuman: {driver.district.name}\n"
        f"💰 To'lov miqdori: {amount} so'm"
    )
    
    from bot.keyboards.admin_kb import driver_approval_kb
    kb = driver_approval_kb(driver.id)
    
    if payments and payments[0].receipt_file_id:
        if payments[0].receipt_type == "jpg":
            await message.answer_photo(photo=payments[0].receipt_file_id, caption=admin_text, parse_mode="Markdown", reply_markup=kb)
        else:
            await message.answer_document(document=payments[0].receipt_file_id, caption=admin_text, parse_mode="Markdown", reply_markup=kb)
    else:
        await message.answer(admin_text, parse_mode="Markdown", reply_markup=kb)

@router.message(F.text.startswith("🆕 Yangi arizalar"))
async def cmd_new_applications(message: types.Message, session: AsyncSession):
    if not check_admin(message): return
    await show_next_pending_application(message, session)


@router.callback_query(F.data.startswith("admin_driver:"))
@router.callback_query(F.data.startswith("approve_driver:"))
@router.callback_query(F.data.startswith("reject_driver:"))
async def process_admin_driver_action(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    parts = callback.data.split(":")
    if callback.data.startswith("approve_driver:"):
        action = "approve"
        driver_id = int(parts[1])
    elif callback.data.startswith("reject_driver:"):
        action = "reject"
        driver_id = int(parts[1])
    else:
        action = parts[1]
        driver_id = int(parts[2])
    admin_id = callback.from_user.id
    
    driver = await DriverService.get_driver_by_id(session, driver_id)
    if not driver:
        await callback.answer("Haydovchi topilmadi.")
        return
        
    try:
        await callback.message.delete()
    except:
        pass

    if action == "approve":
        await DriverService.approve_driver(session, driver_id, admin_id)
        await callback.message.answer(f"✅ Haydovchi {driver.full_name} tasdiqlandi.")

        # Guruh havolasini topib haydovchiga yuborish
        group = await DriverService.get_group_for_driver(session, driver.district_id)
        
        if group and not group.invite_link and group.telegram_group_id:
            try:
                invite_link = await bot.export_chat_invite_link(group.telegram_group_id)
                await AdminService.update_group(session, group.id, invite_link=invite_link)
                group.invite_link = invite_link
            except Exception:
                pass

        if group and group.invite_link:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            invite_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Guruhga qo'shilish", url=group.invite_link)]
            ])
            await safe_send_message(
                bot,
                driver.user.telegram_id,
                f"🎉 *Tabriklaymiz, {driver.full_name}!*\n\n"
                f"Sizning haydovchilik arizangiz tasdiqlandi.\n"
                f"Hudud: {driver.district.name}\n\n"
                f"Guruhga qo'shilish uchun quyidagi tugmani bosing 👇",
                parse_mode="Markdown",
                reply_markup=invite_kb
            )
        else:
            await safe_send_message(
                bot,
                driver.user.telegram_id,
                f"🎉 *Tabriklaymiz, {driver.full_name}!*\n\n"
                f"Sizning haydovchilik arizangiz tasdiqlandi.\n"
                f"Guruh havolasi tez orada yuboriladi. Admin bilan bog'laning.",
                parse_mode="Markdown"
            )
        
        await show_next_pending_application(callback.message, session)

    elif action == "reject":
        await DriverService.reject_driver(session, driver_id)
        await callback.message.answer(f"❌ Haydovchi {driver.full_name} rad etildi.")
        await safe_send_message(
            bot,
            driver.user.telegram_id,
            "❌ Afsuski, sizning haydovchilik arizangiz rad etildi.\nQo'shimcha ma'lumot uchun adminga murojaat qiling."
        )
        
        await show_next_pending_application(callback.message, session)

    elif action == "block":
        await DriverService.block_driver(session, driver_id)
        await callback.message.answer(f"🚫 Haydovchi {driver.full_name} bloklandi.")

    elif action == "unblock":
        await DriverService.unblock_driver(session, driver_id)
        await callback.message.answer(f"🔓 Haydovchi {driver.full_name} blokdan chiqarildi.")

    await callback.answer()


@router.callback_query(F.data.startswith("admin_payment:"))
async def process_admin_payment_action(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    parts = callback.data.split(":")
    action = parts[1]
    payment_id = int(parts[2])
    admin_id = callback.from_user.id
    
    payment = await PaymentService.get_payment(session, payment_id)
    if not payment:
        await callback.answer("To'lov topilmadi.")
        return
        
    if action == "approve":
        await PaymentService.approve_payment(session, payment_id, admin_id)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"✅ To'lov tasdiqlandi (ID: {payment_id}).")
        
    elif action == "reject":
        await PaymentService.reject_payment(session, payment_id, admin_id)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"❌ To'lov rad etildi (ID: {payment_id}).")
        
    await callback.answer()


@router.message(F.text == "📍 Tumanlar")
async def admin_districts(message: types.Message, session: AsyncSession):
    if not check_admin(message): return
    districts = await AdminService.get_all_districts(session, include_inactive=True)
    await message.answer("Tumanlarni boshqarish:", reply_markup=districts_manage_kb(districts))

@router.callback_query(F.data == "admin_district:add")
async def admin_district_add(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Yangi tuman nomini kiriting:")
    await state.set_state(AdminState.adding_district)
    await callback.answer()

@router.message(AdminState.adding_district)
async def process_adding_district(message: types.Message, session: AsyncSession, state: FSMContext):
    res = await AdminService.add_district(session, message.text)
    if res:
        await message.answer(f"✅ '{message.text}' tumani qo'shildi.")
    else:
        await message.answer("❌ Bu tuman allaqachon mavjud.")
    await state.clear()
    
@router.message(F.text == "📊 Statistika")
async def admin_stats(message: types.Message, session: AsyncSession):
    if not check_admin(message): return
    
    users_count = await CustomerService.get_all_users_count(session)
    drivers_total = await DriverService.count_drivers(session)
    drivers_active = await DriverService.count_drivers(session, "APPROVED")
    drivers_pending = await DriverService.count_drivers(session, "PENDING")
    
    payments_sum = await PaymentService.get_total_payments_amount(session)
    orders_total = await OrderService.count_orders(session)
    orders_completed = await OrderService.count_orders(session, "COMPLETED")
    orders_cancelled = await OrderService.count_orders(session, "CANCELLED")
    
    today_stats = await OrderService.get_today_stats(session)
    
    text = (
        "📊 *UMUMIY STATISTIKA*\n\n"
        f"👥 Jami foydalanuvchilar: {users_count}\n"
        f"🚕 Jami haydovchilar: {drivers_total}\n"
        f"🟢 Faol haydovchilar: {drivers_active}\n"
        f"🟡 Kutilayotganlar: {drivers_pending}\n\n"
        f"💰 Jami to'lovlar summasi: {payments_sum} so'm\n\n"
        f"📋 Jami buyurtmalar: {orders_total}\n"
        f"✅ Tugallangan: {orders_completed}\n"
        f"❌ Bekor qilingan: {orders_cancelled}\n\n"
        "📅 *BUGUNGI STATISTIKA*\n"
        f"Buyurtmalar: {today_stats['total']}\n"
        f"Tugallangan: {today_stats['completed']}\n"
        f"Bekor qilingan: {today_stats['cancelled']}\n"
    )
    
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "💳 To'lov sozlamalari")
async def admin_payment_settings(message: types.Message, session: AsyncSession):
    if not check_admin(message): return
    p = await AdminService.get_payment_settings(session)
    text = (
        "💳 *To'lov sozlamalari*\n\n"
        f"Karta raqami: `{p['card']}`\n"
        f"Karta egasi: {p['owner']}\n"
        f"To'lov summasi: {p['amount']}\n\n"
    )
    from bot.keyboards.admin_kb import payment_settings_kb
    await message.answer(text, parse_mode="Markdown", reply_markup=payment_settings_kb())

@router.message(F.text == "🔙 Bosh menyuga qaytish")
async def cancel_admin_action(message: types.Message, state: FSMContext, session: AsyncSession):
    if not check_admin(message): return
    await state.clear()
    from bot.keyboards.admin_kb import admin_menu_kb
    pending_drivers = await DriverService.get_drivers_by_status(session, "PENDING")
    await message.answer("Bosh menyuga qaytdingiz.", reply_markup=await build_admin_menu(session))

@router.callback_query(F.data.startswith("settings:"))
async def process_payment_settings_action(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    from bot.keyboards.admin_kb import cancel_admin_action_kb
    
    if action == "card":
        await callback.message.answer("Yangi karta raqamini kiriting:", reply_markup=cancel_admin_action_kb())
        await state.set_state(AdminState.editing_card)
    elif action == "card_owner":
        await callback.message.answer("Karta egasining ism-familiyasini kiriting:", reply_markup=cancel_admin_action_kb())
        await state.set_state(AdminState.editing_card_owner)
    elif action == "amount":
        await callback.message.answer("Yangi to'lov summasini kiriting (faqat raqamlar, masalan: 50000):", reply_markup=cancel_admin_action_kb())
        await state.set_state(AdminState.editing_amount)
        
    await callback.answer()

@router.message(AdminState.editing_card)
async def process_editing_card(message: types.Message, session: AsyncSession, state: FSMContext):
    await AdminService.update_payment_settings(session, card=message.text)
    from bot.keyboards.admin_kb import admin_menu_kb
    pending_drivers = await DriverService.get_drivers_by_status(session, "PENDING")
    await message.answer("✅ Karta raqami muvaffaqiyatli o'zgartirildi.", reply_markup=await build_admin_menu(session))
    await state.clear()

@router.message(AdminState.editing_card_owner)
async def process_editing_card_owner(message: types.Message, session: AsyncSession, state: FSMContext):
    await AdminService.update_payment_settings(session, owner=message.text)
    from bot.keyboards.admin_kb import admin_menu_kb
    pending_drivers = await DriverService.get_drivers_by_status(session, "PENDING")
    await message.answer("✅ Karta egasi muvaffaqiyatli o'zgartirildi.", reply_markup=await build_admin_menu(session))
    await state.clear()

@router.message(AdminState.editing_amount)
async def process_editing_amount(message: types.Message, session: AsyncSession, state: FSMContext):
    await AdminService.update_payment_settings(session, amount=message.text)
    from bot.keyboards.admin_kb import admin_menu_kb
    pending_drivers = await DriverService.get_drivers_by_status(session, "PENDING")
    await message.answer("✅ To'lov summasi muvaffaqiyatli o'zgartirildi.", reply_markup=await build_admin_menu(session))
    await state.clear()
@router.message(F.text == "📨 Xabar yuborish")
async def cmd_broadcast_menu(message: types.Message):
    if not check_admin(message): return
    from bot.keyboards.admin_kb import broadcast_target_kb
    await message.answer("Xabarni kimlarga yuboramiz? Tanlang:", reply_markup=broadcast_target_kb())

@router.callback_query(F.data.startswith("broadcast:"))
async def process_broadcast_target(callback: types.CallbackQuery, state: FSMContext):
    target = callback.data.split(":")[1]
    await state.update_data(broadcast_target=target)
    from bot.keyboards.admin_kb import cancel_admin_action_kb
    await callback.message.answer(
        "Yubormoqchi bo'lgan xabaringizni (matn, rasm yoki video bilan) kiriting:",
        reply_markup=cancel_admin_action_kb()
    )
    await state.set_state(AdminState.broadcasting)
    await callback.answer()

@router.message(AdminState.broadcasting)
async def catch_broadcast_message(message: types.Message, state: FSMContext):
    await state.update_data(msg_id=message.message_id, from_chat_id=message.chat.id)
    from bot.keyboards.admin_kb import confirm_broadcast_kb
    await message.copy_to(message.chat.id, reply_markup=confirm_broadcast_kb())

@router.callback_query(F.data.startswith("broadcast_confirm:"))
async def confirm_broadcast_action(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    choice = callback.data.split(":")[1]
    from bot.keyboards.admin_kb import admin_menu_kb
    pending_drivers = await DriverService.get_drivers_by_status(session, "PENDING")
    
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
        
    if choice == "no":
        await callback.message.answer("❌ Xabar yuborish bekor qilindi.")
        await callback.message.answer("Bosh menyuga qaytdingiz.", reply_markup=await build_admin_menu(session))
        await state.clear()
        return
        
    data = await state.get_data()
    target = data.get("broadcast_target")
    msg_id = data.get("msg_id")
    from_chat_id = data.get("from_chat_id")
    
    if not target or not msg_id or not from_chat_id:
        await callback.message.answer("Ma'lumot topilmadi, qaytadan urinib ko'ring.")
        await callback.message.answer("Bosh menyuga qaytdingiz.", reply_markup=await build_admin_menu(session))
        await state.clear()
        return
        
    status_msg = await callback.message.answer("⏳ Xabar yuborilmoqda, kuting...")
    
    sent_count = 0
    if target == "groups":
        groups = await AdminService.get_all_groups(session)
        for g in groups:
            try:
                await bot.copy_message(g.telegram_group_id, from_chat_id, msg_id)
                sent_count += 1
            except Exception:
                pass
    elif target == "users":
        user_ids = await CustomerService.get_all_user_ids(session)
        for uid in user_ids:
            try:
                await bot.copy_message(uid, from_chat_id, msg_id)
                sent_count += 1
            except Exception:
                pass
                
    await status_msg.edit_text(f"✅ Xabar muvaffaqiyatli {sent_count} ta manzilga yuborildi.")
    await callback.message.answer("Bosh menyuga qaytdingiz.", reply_markup=await build_admin_menu(session))
    await state.clear()

TASHKENT_DISTRICTS = [
    "Bektemir tumani", "Chilonzor tumani", "Mirobod tumani", "Mirzo Ulug'bek tumani",
    "Olmazor tumani", "Sergeli tumani", "Shayxontohur tumani", "Uchtepa tumani",
    "Yakkasaroy tumani", "Yashnobod tumani", "Yunusobod tumani", "Yangihayot tumani"
]

@router.message(F.text == "📢 Guruhlar")
async def admin_groups(message: types.Message, session: AsyncSession):
    if not check_admin(message): return
    groups = await AdminService.get_all_groups(session)
    text = "📢 *Ulangan guruhlar:*\n\n"
    if not groups:
        text += "Hozircha hech qanday guruh ulanmagan.\n\n"
    else:
        for g in groups:
            text += f"▪️ {g.group_name} ({g.district.name})\nID: `{g.telegram_group_id}`\n\n"
            
    text += (
        "Yangi guruh ulash uchun:\n"
        "1. Telegramda yangi guruh oching\n"
        "2. Botni shu guruhga qo'shib Admin qiling\n"
        "3. Guruh ichida /setgroup deb yozing."
    )
    await message.answer(text, parse_mode="Markdown")
    

@router.message(Command("setgroup"))
async def cmd_setgroup(message: types.Message, session: AsyncSession):
    if message.chat.type == "private":
        await message.answer("Bu buyruqni faqat guruh ichida yozish kerak.")
        return
        
    districts = await AdminService.get_all_districts(session)
    fergana_districts = [d for d in districts if d.name not in TASHKENT_DISTRICTS]
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for d in fergana_districts:
        builder.button(text=d.name, callback_data=f"bindgrp:{message.chat.id}:{d.id}")
    builder.adjust(2)
    
    await message.answer(
        f"Guruh ID: {message.chat.id}\nBu guruhni qaysi tumanga biriktiramiz?", 
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("bindgrp:"))
async def process_bind_group(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    from bot.utils.helpers import is_admin
    if not is_admin(callback.from_user.id): 
        await callback.answer("Sizda ruxsat yo'q!", show_alert=True)
        return
        
    _, chat_id_str, district_id_str = callback.data.split(":")
    chat_id = int(chat_id_str)
    district_id = int(district_id_str)
    
    district = await AdminService.get_district(session, district_id)
    group = await DriverService.get_group_for_driver(session, district_id)
    
    chat_title = callback.message.chat.title or "Haydovchilar"
    
    invite_link = None
    try:
        invite_link = await bot.export_chat_invite_link(chat_id)
    except Exception as e:
        pass
        
    if group:
        await AdminService.update_group(session, group.id, telegram_group_id=chat_id, group_name=chat_title, invite_link=invite_link)
    else:
        await AdminService.add_group(session, district_id, chat_title, chat_id, invite_link)
        
    text = f"✅ Ushbu guruh muvaffaqiyatli **{district.name}** tumaniga biriktirildi!"
    if invite_link:
        text += "\n🔗 Havola avtomatik saqlandi."
    else:
        text += "\n⚠️ Havolani saqlab bo'lmadi. Botni guruhda to'liq admin qiling."
        
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@router.message(F.text.startswith("📩 Yordam"))
async def cmd_admin_support(message: types.Message, session: AsyncSession, bot: Bot):
    if not check_admin(message): return
    
    msg = await SupportService.get_oldest_new_message(session)
    if not msg:
        await message.answer("Yangi xabarlar yo'q.", reply_markup=await build_admin_menu(session))
        return
        
    user = msg.user
    text = f"📩 *Yangi xabar ({msg.message_type})*\n\n"
    text += f"👤 Yuboruvchi: {user.full_name}\n"
    text += f"📞 Telefon: {user.phone or 'Mavjud emas'}\n"
    text += f"📅 Vaqt: {msg.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    if msg.text_content:
        text += f"📝 Matn: {msg.text_content}\n"
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Shaxsiy profiliga yozish", url=f"tg://user?id={user.telegram_id}")],
        [InlineKeyboardButton(text="✅ Ko'rib chiqildi (Keyingisi)", callback_data=f"support_read:{msg.id}")]
    ])
    
    if msg.message_type == "text":
        await message.answer(text, parse_mode="Markdown", reply_markup=kb)
    elif msg.message_type == "photo":
        await message.answer_photo(msg.file_id, caption=text, parse_mode="Markdown", reply_markup=kb)
    elif msg.message_type == "voice":
        await message.answer_voice(msg.file_id, caption=text, parse_mode="Markdown", reply_markup=kb)
    elif msg.message_type == "video":
        await message.answer_video(msg.file_id, caption=text, parse_mode="Markdown", reply_markup=kb)

@router.callback_query(F.data.startswith("support_read:"))
async def process_support_read(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    msg_id = int(callback.data.split(":")[1])
    await SupportService.mark_as_read(session, msg_id)
    
    await callback.message.delete()
    
    # Try fetching the next one
    msg = await SupportService.get_oldest_new_message(session)
    if not msg:
        await callback.message.answer("✅ Barcha xabarlar ko'rib chiqildi.", reply_markup=await build_admin_menu(session))
        return
        
    user = msg.user
    text = f"📩 *Yangi xabar ({msg.message_type})*\n\n"
    text += f"👤 Yuboruvchi: {user.full_name}\n"
    text += f"📞 Telefon: {user.phone or 'Mavjud emas'}\n"
    text += f"📅 Vaqt: {msg.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    if msg.text_content:
        text += f"📝 Matn: {msg.text_content}\n"
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Shaxsiy profiliga yozish", url=f"tg://user?id={user.telegram_id}")],
        [InlineKeyboardButton(text="✅ Ko'rib chiqildi (Keyingisi)", callback_data=f"support_read:{msg.id}")]
    ])
    
    if msg.message_type == "text":
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    elif msg.message_type == "photo":
        await callback.message.answer_photo(msg.file_id, caption=text, parse_mode="Markdown", reply_markup=kb)
    elif msg.message_type == "voice":
        await callback.message.answer_voice(msg.file_id, caption=text, parse_mode="Markdown", reply_markup=kb)
    elif msg.message_type == "video":
        await callback.message.answer_video(msg.file_id, caption=text, parse_mode="Markdown", reply_markup=kb)
