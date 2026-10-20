with open('bot/handlers/customer.py', 'a', encoding='utf-8') as f:
    f.write('''
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
''')
