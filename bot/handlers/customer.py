"""Mijoz xatti-harakatlari va buyurtma berish jarayoni."""
import logging
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.customer_states import CustomerOrderState
from bot.keyboards.customer_kb import (
    main_menu_kb, districts_kb, passengers_kb, order_confirm_kb, cancel_order_kb, direction_kb
)
from bot.keyboards.driver_kb import order_action_kb
from bot.services.customer_service import CustomerService
from bot.services.driver_service import DriverService
from bot.services.order_service import OrderService
from bot.services.admin_service import AdminService
from bot.utils.helpers import format_order_status, safe_send_message

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(F.chat.type == "private")

TASHKENT_DISTRICTS = [
    "Bektemir tumani", "Chilonzor tumani", "Mirobod tumani", "Mirzo Ulug'bek tumani",
    "Olmazor tumani", "Sergeli tumani", "Shayxontohur tumani", "Uchtepa tumani",
    "Yakkasaroy tumani", "Yashnobod tumani", "Yunusobod tumani", "Yangihayot tumani"
]

@router.message(F.text == "👤 Profilim")
async def customer_profile(message: types.Message, session: AsyncSession):
    user = await CustomerService.get_user(session, message.from_user.id)
    if not user:
        return
    stats = await CustomerService.get_user_stats(session, user.id)
    text = (
        "👤 *Profilim*\n\n"
        f"Ism: {user.full_name}\n"
        f"Telefon: {user.phone}\n\n"
        f"📋 Barcha buyurtmalar: {stats['total']}\n"
        f"✅ Tugallangan safarlar: {stats['completed']}\n"
        f"❌ Bekor qilingan safarlar: {stats['cancelled']}"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("buyurtmalarim"))
@router.message(F.text == "📋 Buyurtmalarim")
async def customer_orders(message: types.Message, session: AsyncSession):
    user = await CustomerService.get_user(session, message.from_user.id)
    if not user:
        return
    orders = await CustomerService.get_user_orders(session, user.id, limit=5)
    if not orders:
        await message.answer("Sizda hozircha buyurtmalar yo'q.")
        return
    text = "📋 *Oxirgi buyurtmalaringiz:*\n\n"
    for o in orders:
        dt = o.created_at.strftime("%d.%m.%Y %H:%M")
        status = format_order_status(o.status)
        text += (
            f"🆔 ID: {o.id}\n"
            f"📍 {o.from_address} ➡️ {o.to_address}\n"
            f"📅 {dt} | {status}\n\n"
        )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("buyurtma"))
@router.message(F.text == "🚕 Taksi chaqirish")
async def start_order(message: types.Message, session: AsyncSession, state: FSMContext):
    user = await CustomerService.get_user(session, message.from_user.id)
    if not user or not user.phone:
        await message.answer("Iltimos, avval /start ni bosib telefon raqamingizni yuboring.")
        return

    await message.answer("🛣 Qaysi yo'nalishda ketmoqchisiz?", reply_markup=direction_kb())
    await state.set_state(CustomerOrderState.choosing_direction)


@router.callback_query(CustomerOrderState.choosing_direction, F.data.startswith("direction:"))
async def process_direction(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    direction = callback.data.split(":")[1]
    await state.update_data(direction=direction)
    
    all_districts = await AdminService.get_all_districts(session)
    
    if direction == "tosh_far":
        filtered = [d for d in all_districts if d.name in TASHKENT_DISTRICTS]
        text = "📍 Toshkentning qaysi hududidan kelasiz?"
    else:
        filtered = [d for d in all_districts if d.name not in TASHKENT_DISTRICTS]
        text = "📍 Farg'onaning qaysi hududidan kelasiz?"
        
    if not filtered:
        await callback.message.edit_text("Kechirasiz, ushbu yo'nalish bo'yicha tumanlar topilmadi.")
        return
        
    await callback.message.edit_text(text, reply_markup=districts_kb(filtered))
    await state.set_state(CustomerOrderState.choosing_district)
    await callback.answer()


@router.callback_query(CustomerOrderState.choosing_district, F.data.startswith("district:"))
async def process_district(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    district_id = int(callback.data.split(":")[1])
    district = await AdminService.get_district(session, district_id)
    
    await state.update_data(district_id=district_id, district_name=district.name, from_address=district.name)
    
    data = await state.get_data()
    all_districts = await AdminService.get_all_districts(session)
    
    if data.get("direction") == "tosh_far":
        filtered = [d for d in all_districts if d.name not in TASHKENT_DISTRICTS]
        text = "🏁 Farg'onaning qaysi tumaniga borasiz?"
    else:
        # Farg'onadan Toshkentga, demak jo'nab ketayotgan tuman Farg'ona tumani. Shu tumanni saqlaymiz.
        await state.update_data(fergana_district_id=district_id)
        filtered = [d for d in all_districts if d.name in TASHKENT_DISTRICTS]
        text = "🏁 Toshkentning qaysi tumaniga borasiz?"
        
    await callback.message.edit_text(text, reply_markup=districts_kb(filtered))
    await state.set_state(CustomerOrderState.choosing_destination_district)
    await callback.answer()


@router.callback_query(CustomerOrderState.choosing_destination_district, F.data.startswith("district:"))
async def process_destination_district(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    district_id = int(callback.data.split(":")[1])
    district = await AdminService.get_district(session, district_id)
    
    await state.update_data(to_address=district.name)
    
    data = await state.get_data()
    if data.get("direction") == "tosh_far":
        # Toshkentdan Farg'onaga, demak borayotgan tuman Farg'ona tumani. Shu tumanni saqlaymiz.
        await state.update_data(fergana_district_id=district_id)
    
    await callback.message.edit_text("👥 Necha kishi bor?", reply_markup=passengers_kb())
    await state.set_state(CustomerOrderState.choosing_passengers)
    await callback.answer()


@router.callback_query(CustomerOrderState.choosing_passengers, F.data.startswith("passengers:"))
async def process_passengers(callback: types.CallbackQuery, state: FSMContext):
    passengers = callback.data.split(":")[1]
    await state.update_data(passengers=passengers)
    
    await callback.message.edit_text("💰 Kishi boshiga taklif qiladigan narxingizni yozing:\n(Masalan: 50000 so'm yoki 100 ming)")
    await state.set_state(CustomerOrderState.entering_price)
    await callback.answer()


@router.message(CustomerOrderState.entering_price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    
    data = await state.get_data()
    
    if data.get("direction") == "tosh_far":
        dir_text = "Toshkent ➡️ Farg'ona"
    else:
        dir_text = "Farg'ona ➡️ Toshkent"
        
    text = (
        "🚕 *BUYURTMA XULOSASI*\n\n"
        f"🛣 Yo'nalish: {dir_text}\n"
        f"📍 Qayerdan: {data['from_address']} ({data['district_name']})\n"
        f"🏁 Qayerga: {data['to_address']}\n"
        f"👥 Yo'lovchilar: {data['passengers']}\n"
        f"💰 Taklif narx: {data['price']}"
    )
    
    await message.answer(text, parse_mode="Markdown", reply_markup=order_confirm_kb())
    await state.set_state(CustomerOrderState.confirmation)


@router.callback_query(CustomerOrderState.confirmation, F.data == "order:edit")
async def edit_order(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.message.edit_text("🛣 Qaysi yo'nalishda ketmoqchisiz?", reply_markup=direction_kb())
    await state.set_state(CustomerOrderState.choosing_direction)
    await callback.answer()

@router.callback_query(CustomerOrderState.confirmation, F.data == "order:cancel")
async def cancel_order_draft(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Buyurtma bekor qilindi.")
    await callback.answer()

@router.callback_query(CustomerOrderState.confirmation, F.data == "order:confirm")
async def confirm_order(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    user = await CustomerService.get_user(session, callback.from_user.id)
    
    if not user:
        await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return
        
    fergana_id = data.get('fergana_district_id')
    
    order = await OrderService.create_order(
        session=session,
        customer_id=user.id,
        district_id=fergana_id,
        from_address=data['from_address'],
        to_address=data['to_address'],
        passengers=int(data['passengers'].replace("+", "") if isinstance(data['passengers'], str) else data['passengers']),
        price=data.get('price')
    )
    
    await OrderService.update_status(session, order.id, "SEARCHING_DRIVER")
    await state.clear()
    
    await callback.message.edit_text(
        "✅ Buyurtmangiz qabul qilindi.\n📞 Tez orada shafyorimiz aloqaga chiqadi."
    )
    await callback.answer()

    import datetime
    if data.get("direction") == "tosh_far":
        dir_text = "Toshkent ➡️ Farg'ona"
    else:
        dir_text = "Farg'ona ➡️ Toshkent"
        
    order_text = (
        "🚕 *YANGI BUYURTMA*\n\n"
        f"🛣 Yo'nalish: {dir_text}\n"
        f"📍 Qayerdan: {data['from_address']}\n"
        f"🏁 Qayerga: {data['to_address']}\n"
        f"👥 Yo'lovchilar: {data['passengers']}\n"
        f"💰 Taklif qilingan narx: {data.get('price', 'Kelishiladi')}\n"

        f"🕐 Vaqt: {datetime.datetime.utcnow().strftime('%H:%M')}"
    )
    
    group = await DriverService.get_group_for_driver(session, fergana_id)
    if group and group.telegram_group_id:
        try:
            sent_msg = await bot.send_message(
                chat_id=group.telegram_group_id,
                text=order_text,
                parse_mode="Markdown",
                reply_markup=order_action_kb(order.id)
            )
            order.group_chat_id = group.telegram_group_id
            order.group_message_id = sent_msg.message_id
            await session.commit()
            return
        except Exception as e:
            logger.error(f"Guruhga yuborishda xatolik: {e}")
            
    # Agar guruh ulanmagan bo'lsa yoki xato beraversa lchkaga yuboramiz (zaxira)
    drivers = await DriverService.get_online_drivers_by_district(session, fergana_id)
    if drivers:
        for drv in drivers:
            await safe_send_message(bot, drv.user.telegram_id, order_text, parse_mode="Markdown", reply_markup=order_action_kb(order.id))
    else:
        await safe_send_message(bot, callback.from_user.id, "Kechirasiz, ushbu hududda ayni vaqtda guruh yoki faol haydovchilar topilmadi.")
        await OrderService.update_status(session, order.id, "CANCELLED")


from bot.services.support_service import SupportService

@router.message(CustomerOrderState.waiting_for_support_message)
async def process_support_message(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == "🔙 Bosh menyuga qaytish":
        return

    user = await CustomerService.get_user(session, message.from_user.id)
    if not user:
        return
        
    msg_type = "text"
    text_content = message.text
    file_id = None
    
    if message.photo:
        msg_type = "photo"
        text_content = message.caption
        file_id = message.photo[-1].file_id
    elif message.voice:
        msg_type = "voice"
        file_id = message.voice.file_id
    elif message.video:
        msg_type = "video"
        text_content = message.caption
        file_id = message.video.file_id
    
    await SupportService.create_support_message(
        session=session,
        user_id=user.id,
        message_type=msg_type,
        text_content=text_content,
        file_id=file_id
    )
    
    await message.answer("✅ Xabaringiz administratorga yuborildi. Tez orada javob beramiz.")
    from bot.handlers.start import cmd_start
    await cmd_start(message, session, state)
