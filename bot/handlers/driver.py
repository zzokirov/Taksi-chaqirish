"""Haydovchi ro'yxatdan o'tishi va profili."""
import logging
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.driver_states import DriverRegistrationState, PaymentState
from bot.keyboards.driver_kb import (
    driver_confirm_kb, driver_panel_kb,
    driver_districts_kb, group_link_kb
)
from bot.keyboards.customer_kb import main_menu_kb
from bot.services.driver_service import DriverService
from bot.services.customer_service import CustomerService
from bot.services.payment_service import PaymentService
from bot.services.admin_service import AdminService
from bot.utils.helpers import format_payment_status
from config import settings

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(F.chat.type == "private")

TASHKENT_DISTRICTS = [
    "Bektemir tumani", "Chilonzor tumani", "Mirobod tumani", "Mirzo Ulug'bek tumani",
    "Olmazor tumani", "Sergeli tumani", "Shayxontohur tumani", "Uchtepa tumani",
    "Yakkasaroy tumani", "Yashnobod tumani", "Yunusobod tumani", "Yangihayot tumani"
]

PAYMENT_CARD = "9860350142624583"


# ============================================================
# RO'YXATDAN O'TISH
# ============================================================

@router.message(Command("haydovchi"))
@router.message(F.text == "🚕 Haydovchi bo'lish")
async def start_driver_reg(message: types.Message, session: AsyncSession, state: FSMContext):
    user = await CustomerService.get_user(session, message.from_user.id)
    if not user:
        return

    driver = await DriverService.get_driver_by_user_id(session, user.id)
    if driver:
        if driver.status == "APPROVED":
            await message.answer("✅ Siz allaqachon tasdiqlangan haydovchisiz.", reply_markup=driver_panel_kb())
            return
        elif driver.status == "BLOCKED":
            await message.answer("🚫 Sizning haydovchi profilingiz bloklangan. Adminga murojaat qiling.")
            return
        else:
            # Agar PENDING yoki REJECTED bo'lsa, o'chirib yangidan boshlaymiz
            await DriverService.delete_driver(session, driver.id)

    await message.answer(
        "👤 *RO'YXATDAN O'TISH*\n\nBoshlash uchun ism va familiyangizni kiriting:",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(DriverRegistrationState.full_name)


@router.message(DriverRegistrationState.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("Iltimos, to'liq ism familiyangizni kiriting:")
        return
    await state.update_data(full_name=message.text.strip())
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("📱 Telefon raqamingizni yuboring:", reply_markup=kb)
    await state.set_state(DriverRegistrationState.phone)


@router.message(DriverRegistrationState.phone, F.contact | F.text)
async def process_phone(message: types.Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith('+'):
            phone = '+' + phone
    else:
        phone = message.text.strip()

    await state.update_data(phone=phone)
    await message.answer(
        "🚗 Mashinangiz rusumini yozing (masalan: Cobalt):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(DriverRegistrationState.car_model)


@router.message(DriverRegistrationState.car_model)
async def process_car_model(message: types.Message, state: FSMContext, session: AsyncSession):
    if not message.text:
        await message.answer("Iltimos, mashina rusumini yozing:")
        return
        
    await state.update_data(car_model=message.text.strip())

    districts = await AdminService.get_all_districts(session)
    fergana_districts = [d for d in districts if d.name not in TASHKENT_DISTRICTS]

    if not fergana_districts:
        await message.answer("Tizimda xatolik. Farg'ona tumanlari topilmadi. Adminga murojaat qiling.")
        await state.clear()
        return

    await message.answer("📍 Farg'onaning qaysi tumanidansiz?", reply_markup=types.ReplyKeyboardRemove())
    await message.answer("👇 Tumanni tanlang:", reply_markup=driver_districts_kb(fergana_districts))
    await state.set_state(DriverRegistrationState.district)


@router.callback_query(DriverRegistrationState.district, F.data.startswith("drv_district:"))
async def process_drv_district(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    district_id = int(callback.data.split(":")[1])
    district = await AdminService.get_district(session, district_id)

    await state.update_data(district_id=district_id, district_name=district.name)
    
    payment_settings = await AdminService.get_payment_settings(session)
    card = payment_settings.get('card') or PAYMENT_CARD
    amount = payment_settings.get('amount') or "Belgilanmagan"
    owner = payment_settings.get('owner') or "Admin"
    await state.update_data(amount=amount)

    text = (
        "💳 *OYLIK TO'LOV*\n\n"
        f"Guruhga qo'shilish uchun oylik to'lovni amalga oshiring.\n\n"
        f"💰 To'lov summasi: *{amount} so'm*\n"
        f"💳 Karta raqami:\n`{card}`\n"
        f"👤 Karta egasi: *{owner}*\n\n"
        "📎 Karta raqamiga to'lovni o'tkazib, *to'lov chekini (rasm yoki PDF formatida) shu yerga yuboring*."
    )

    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(DriverRegistrationState.waiting_receipt)
    await callback.answer()


@router.message(DriverRegistrationState.waiting_receipt, F.photo | F.document)
async def process_receipt(message: types.Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        receipt_type = "jpg"
    else:
        file_id = message.document.file_id
        receipt_type = "pdf"
        
    await state.update_data(receipt_file_id=file_id, receipt_type=receipt_type)
    
    data = await state.get_data()

    text = (
        "📋 *UMUMIY ARIZA*\n\n"
        f"👤 Ism familiya: {data['full_name']}\n"
        f"📱 Telefon: {data['phone']}\n"
        f"🚗 Mashina: {data['car_model']}\n"
        f"📍 Ishlash tumani: {data['district_name']}\n"
        f"💰 To'lov miqdori: {data['amount']} so'm\n\n"
        "Hamma ma'lumotlar to'g'ri bo'lsa, adminga yuboring."
    )

    # Chek bilan birga arizani ko'rsatish
    if receipt_type == "jpg":
        await message.answer_photo(
            photo=file_id, 
            caption=text, 
            parse_mode="Markdown", 
            reply_markup=driver_confirm_kb()
        )
    else:
        await message.answer_document(
            document=file_id, 
            caption=text, 
            parse_mode="Markdown", 
            reply_markup=driver_confirm_kb()
        )
        
    await state.set_state(DriverRegistrationState.confirmation)


@router.callback_query(DriverRegistrationState.confirmation, F.data == "drv_reg:restart")
async def restart_drv_reg(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "👤 Boshlash uchun ism va familiyangizni kiriting:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(DriverRegistrationState.full_name)
    await callback.answer()


@router.callback_query(DriverRegistrationState.confirmation, F.data == "drv_reg:confirm")
async def confirm_drv_reg(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    user = await CustomerService.get_user(session, callback.from_user.id)

    # 1. Haydovchini DB ga saqlash
    driver = await DriverService.create_driver(
        session=session,
        user_id=user.id,
        full_name=data['full_name'],
        phone=data['phone'],
        car_model=data['car_model'],
        car_number="-",
        district_id=data['district_id']
    )

    # 2. To'lovni DB ga saqlash
    payment_settings = await AdminService.get_payment_settings(session)
    card = payment_settings.get('card') or PAYMENT_CARD
    amount = payment_settings.get('amount') or 0

    await PaymentService.create_payment(
        session=session,
        driver_id=driver.id,
        amount=amount,
        card_number=card,
        receipt_file_id=data['receipt_file_id'],
        receipt_type=data['receipt_type']
    )

    await callback.message.edit_caption(
        caption="✅ Arizangiz va to'lov chekingiz adminga yuborildi!\n\n⏳ Tasdiqlanishini kuting.",
        reply_markup=None
    )
    await callback.message.answer("Asosiy menyuga qaytdingiz.", reply_markup=main_menu_kb())
    await state.clear()

    # 3. Adminga bildirishnoma (majburiy emas, lekin arizalar paneliga o'tishini aytish mumkin)
    # Hozircha admin panelidan o'zi kirib ko'radi.
    await callback.answer()


# ============================================================
# HAYDOVCHI PANELI
# ============================================================

@router.message(F.text == "🟢 Ishni boshlash")
async def driver_go_online(message: types.Message, session: AsyncSession):
    driver = await DriverService.get_driver_by_telegram_id(session, message.from_user.id)
    if not driver or driver.status != "APPROVED":
        return
    await DriverService.set_online(session, driver.id)
    await message.answer("🟢 Siz faol holatdasiz. Buyurtmalar guruhda ko'rinadi.")


@router.message(F.text == "🔴 Ishni to'xtatish")
async def driver_go_offline(message: types.Message, session: AsyncSession):
    driver = await DriverService.get_driver_by_telegram_id(session, message.from_user.id)
    if not driver or driver.status != "APPROVED":
        return
    await DriverService.set_offline(session, driver.id)
    await message.answer("🔴 Ish to'xtatildi.")


@router.message(F.text == "📢 Guruhim")
async def driver_group(message: types.Message, session: AsyncSession):
    driver = await DriverService.get_driver_by_telegram_id(session, message.from_user.id)
    if not driver or driver.status != "APPROVED" or driver.payment_status != "APPROVED":
        await message.answer("Guruhga kirish uchun siz tasdiqlangan bo'lishingiz kerak.")
        return

    group = await DriverService.get_group_for_driver(session, driver.district_id)
    if not group or not group.invite_link:
        await message.answer("Sizning tumaningizga biriktirilgan guruh hali mavjud emas. Adminga murojaat qiling.")
        return

    await message.answer(
        f"📢 *Guruh havolasi*\n\n"
        f"Hudud: {driver.district.name}\n"
        f"Guruh: {group.group_name}\n\n"
        "Quyidagi tugma orqali guruhga qo'shiling:",
        parse_mode="Markdown",
        reply_markup=group_link_kb(group.invite_link)
    )


@router.message(F.text == "💰 To'lovlarim")
async def driver_payments(message: types.Message, session: AsyncSession):
    driver = await DriverService.get_driver_by_telegram_id(session, message.from_user.id)
    if not driver:
        return

    # Fetch all payments to calculate total
    all_payments = await PaymentService.get_driver_payments(session, driver.id, limit=100)
    
    text = "📊 *OBUNA VA TO'LOVLAR*\n\n"
    
    import datetime
    now = datetime.datetime.utcnow()
    # Check status
    if driver.payment_status == "APPROVED" and driver.subscription_end and driver.subscription_end > now:
        end_date = (driver.subscription_end + datetime.timedelta(hours=5)).strftime("%d.%m.%Y %H:%M")
        text += f"Holati: ✅ *Aktiv (Tasdiqlangan)*\n"
        text += f"Obuna muddati: *{end_date}* gacha\n\n"
    else:
        text += f"Holati: ❌ *Faol emas* (To'lov talab etiladi yoki tasdiqlanmagan)\n\n"

    if not all_payments:
        text += "Sizda hali to'lovlar mavjud emas."
        await message.answer(text, parse_mode="Markdown")
        return

    text += "📝 *To'lovlar tarixi (oxirgi 10 ta):*\n"
    
    total_paid = 0
    recent_payments = all_payments[:10]
    
    for p in recent_payments:
        # adjust timezone for display
        dt = (p.created_at + datetime.timedelta(hours=5)).strftime("%d.%m.%Y")
        if p.status == "APPROVED":
            status_text = "✅ Tasdiqlangan"
        elif p.status == "PENDING" or p.status == "PENDING_RENEWAL":
            status_text = "⏳ Kutilmoqda"
        else:
            status_text = "❌ Rad etilgan"
            
        text += f"▪️ {dt} | {int(p.amount)} so'm | {status_text}\n"
        
    for p in all_payments:
        if p.status == "APPROVED":
            total_paid += int(p.amount)

    text += f"\n💰 *Jami to'langan summa: {total_paid} so'm*"
    
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "💳 Obunani uzaytirish")
async def driver_renewal_start(message: types.Message, session: AsyncSession, state: FSMContext):
    driver = await DriverService.get_driver_by_telegram_id(session, message.from_user.id)
    if not driver or driver.status != "APPROVED":
        await message.answer("Siz tasdiqlanmagansiz.")
        return

    payment_settings = await AdminService.get_payment_settings(session)
    card = payment_settings.get('card') or PAYMENT_CARD
    amount = payment_settings.get('amount') or "Belgilanmagan"
    owner = payment_settings.get('owner') or "Admin"
    await state.update_data(amount=amount)

    text = (
        "💳 *OBUNANI UZAYTIRISH*\n\n"
        f"Guruhda ishlashni davom ettirish uchun oylik to'lovni amalga oshiring.\n\n"
        f"💰 To'lov summasi: *{amount} so'm*\n"
        f"💳 Karta raqami:\n`{card}`\n"
        f"👤 Karta egasi: *{owner}*\n\n"
        "📎 Karta raqamiga to'lovni o'tkazib, *to'lov chekini (rasm yoki PDF formatida) shu yerga yuboring*."
    )

    await message.answer(text, parse_mode="Markdown")
    await state.set_state(DriverRegistrationState.waiting_renewal_receipt)


@router.message(DriverRegistrationState.waiting_renewal_receipt, F.photo | F.document)
async def process_renewal_receipt(message: types.Message, state: FSMContext, session: AsyncSession):
    driver = await DriverService.get_driver_by_telegram_id(session, message.from_user.id)
    if not driver:
        return

    if message.photo:
        file_id = message.photo[-1].file_id
        receipt_type = "jpg"
    else:
        file_id = message.document.file_id
        receipt_type = "pdf"
        
    data = await state.get_data()
    amount = data.get('amount', 0)
    
    payment_settings = await AdminService.get_payment_settings(session)
    card = payment_settings.get('card') or PAYMENT_CARD

    # Update driver payment status
    driver.payment_status = "PENDING_RENEWAL"
    
    await PaymentService.create_payment(
        session=session,
        driver_id=driver.id,
        amount=amount,
        card_number=card,
        receipt_file_id=file_id,
        receipt_type=receipt_type
    )

    await message.answer("✅ To'lov chekingiz adminga yuborildi!\n⏳ Tasdiqlanishini kuting.", reply_markup=driver_panel_kb())
    await state.clear()
