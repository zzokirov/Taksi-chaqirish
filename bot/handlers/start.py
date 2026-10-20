"""Start handler."""
import logging
from aiogram import Router, F, types, Bot
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.customer_kb import main_menu_kb, phone_kb
from bot.keyboards.driver_kb import driver_panel_kb
from bot.keyboards.admin_kb import admin_menu_kb
from bot.services.customer_service import CustomerService
from bot.services.driver_service import DriverService
from bot.utils.helpers import is_admin
from config import settings

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession, state: FSMContext):
    """Foydalanuvchini kutib olish."""
    await state.clear()
    user_id = message.from_user.id
    
    # Userni DB ga yozamiz/olamiz
    user = await CustomerService.get_or_create_user(
        session=session,
        telegram_id=user_id,
        full_name=message.from_user.full_name
    )

    # Agar telefon raqami yo'q bo'lsa, so'raymiz
    if not user.phone:
        text = (
            "🚕 Assalomu alaykum!\n\n"
            "Farg'ona Taxi botiga xush kelibsiz.\n\n"
            "Taksi buyurtma qilish uchun telefon raqamingizni yuboring."
        )
        await message.answer(text, reply_markup=phone_kb())
        return

    # Agar haydovchi bo'lsa va tasdiqlangan bo'lsa, driver panel beramiz
    driver = await DriverService.get_driver_by_user_id(session, user.id)
    if driver and driver.status == "APPROVED" and driver.payment_status == "APPROVED":
        text = f"🚕 Assalomu alaykum, {driver.full_name}!\nHaydovchi paneliga xush kelibsiz."
        await message.answer(text, reply_markup=driver_panel_kb())
        return

    # Mijoz menyusi
    text = "🚕 Asosiy menyu"
    await message.answer(text, reply_markup=main_menu_kb())


@router.message(F.contact, StateFilter(None))
async def handle_contact(message: types.Message, session: AsyncSession):
    """Telefon raqamni saqlash (faqat state bo'lmaganda)."""
    if not message.contact:
        return
        
    phone = message.contact.phone_number
    if not phone.startswith('+'):
        phone = '+' + phone
        
    await CustomerService.update_phone(session, message.from_user.id, phone)
    
    text = "✅ Telefon raqamingiz saqlandi.\nAsosiy menyuga o'tdingiz."
    await message.answer(text, reply_markup=main_menu_kb())


@router.message(Command("help"))
@router.message(Command("yordam"))
@router.message(F.text == "ℹ️ Yordam")
async def cmd_help(message: types.Message, state: FSMContext):
    """Yordam xabari."""
    text = (
        "ℹ️ *Qo'llab-quvvatlash xizmati*\n\n"
        "Bizga savol, taklif yoki shikoyatingiz bo'lsa yozib qoldiring. "
        "Matn, rasm yoki ovozli xabar yuborishingiz mumkin:"
    )
    from bot.keyboards.admin_kb import cancel_admin_action_kb
    await message.answer(text, parse_mode="Markdown", reply_markup=cancel_admin_action_kb())
    
    from bot.states.customer_states import CustomerOrderState
    await state.set_state(CustomerOrderState.waiting_for_support_message)


@router.message(F.text == "🏠 Asosiy menyu")
async def btn_main_menu(message: types.Message, session: AsyncSession, state: FSMContext):
    """Asosiy menyuga qaytish."""
    await state.clear()
    await cmd_start(message, session, state)
