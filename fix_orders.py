import re

with open('bot/handlers/orders.py', 'r', encoding='utf-8') as f:
    text = f.read()

accept_block = '''@router.callback_query(F.data.startswith("accept_order:"))
async def process_accept_order(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    order_id = int(callback.data.split(":")[1])
    driver = await DriverService.get_driver_by_telegram_id(session, callback.from_user.id)
    
    if not driver:
        await callback.answer("Haydovchi topilmadi.", show_alert=True)
        return

    active_order = await OrderService.get_driver_active_order(session, driver.id)
    if active_order:
        await callback.answer("Sizda ayni vaqtda faol buyurtma bor. Avval uni tugating.", show_alert=True)
        return

    success = await OrderService.accept_order(session, order_id, driver.id)
    if not success:
        await callback.message.edit_text("❌ Ushbu buyurtma boshqa haydovchi tomonidan qabul qilindi yoki bekor qilindi.")
        await callback.answer()
        return

    order = await OrderService.get_order(session, order_id)
    
    from bot.keyboards.driver_kb import order_return_kb
    await callback.message.edit_text(
        f"✅ Buyurtmani *{driver.full_name}* qabul qildi.\\n\\n"
        f"📞 Mijoz raqami: {order.customer.phone}",
        reply_markup=order_return_kb(order.id),
        parse_mode="Markdown"
    )
    await callback.answer("Buyurtma qabul qilindi!")

    customer_text = (
        "✅ *Haydovchi topildi!*\\n\\n"
        f"👤 Ism: {driver.full_name}\\n"
        f"🚕 Mashina: {driver.car_model}\\n"
        f"🔢 Davlat raqami: {driver.car_number}\\n\\n"
        "Haydovchi tez orada siz bilan bog'lanadi."
    )
    await safe_send_message(bot, order.customer.telegram_id, customer_text, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())

@router.callback_query(F.data.startswith("return_order:"))
async def process_return_order(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    order_id = int(callback.data.split(":")[1])
    driver = await DriverService.get_driver_by_telegram_id(session, callback.from_user.id)
    
    order = await OrderService.get_order(session, order_id)
    if not order or not driver or order.driver_id != driver.id:
        await callback.answer("Bu buyurtmani qaytara olmaysiz.", show_alert=True)
        return

    order.status = "SEARCHING_DRIVER"
    order.driver_id = None
    order.accepted_at = None
    await session.commit()
    
    from bot.keyboards.driver_kb import order_action_kb
    order_text = (
        "🚕 *YANGI BUYURTMA* (Qaytarilgan)\\n\\n"
        f"🏠 Qayerdan: {order.from_address}\\n"
        f"🏁 Qayerga: {order.to_address}\\n"
        f"👥 Yo'lovchilar: {order.passengers}\\n"
        f"💰 Taklif qilingan narx: {order.price or 'Kelishiladi'}\\n"
        f"🕒 Vaqt: {order.created_at.strftime('%H:%M') if order.created_at else ''}"
    )
    await callback.message.edit_text(order_text, reply_markup=order_action_kb(order.id), parse_mode="Markdown")
    await callback.answer("Buyurtma guruhga qaytarildi!")
    
    await safe_send_message(bot, order.customer.telegram_id, "⚠️ Haydovchi buyurtmani bekor qildi. Boshqa haydovchi qidirilmoqda...", parse_mode="Markdown")
'''

text = re.sub(
    r'@router\.callback_query\(F\.data\.startswith\("accept_order:"\)\).*?(?=@router\.callback_query\(F\.data\.startswith\("reject_order:"\)\))',
    accept_block + '\n\n',
    text,
    flags=re.DOTALL
)

with open('bot/handlers/orders.py', 'w', encoding='utf-8') as f:
    f.write(text)
