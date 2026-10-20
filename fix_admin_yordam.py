import re

with open('bot/handlers/admin.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add import SupportService
if 'from bot.services.support_service import SupportService' not in text:
    text = text.replace('from bot.services.driver_service import DriverService', 'from bot.services.driver_service import DriverService\nfrom bot.services.support_service import SupportService')

helper_func = '''
async def build_admin_menu(session: AsyncSession):
    from bot.keyboards.admin_kb import admin_menu_kb
    pending_drivers = await DriverService.get_drivers_by_status(session, "PENDING")
    support_count = await SupportService.get_new_messages_count(session)
    return admin_menu_kb(len(pending_drivers), support_count)
'''

# Insert helper function at the top after imports
text = re.sub(r'router = Router\(\)', 'router = Router()\n' + helper_func, text)

# Replace all usages of admin_menu_kb(...)
# Be careful with await build_admin_menu(session)
text = re.sub(r'admin_menu_kb\(len\(pending_drivers\)\)', 'await build_admin_menu(session)', text)
text = re.sub(r'admin_menu_kb\(0\)', 'await build_admin_menu(session)', text)

# Now add Yordam handler
yordam_handler = '''
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@router.message(F.text.startswith("📩 Yordam"))
async def cmd_admin_support(message: types.Message, session: AsyncSession, bot: Bot):
    if not check_admin(message): return
    
    msg = await SupportService.get_oldest_new_message(session)
    if not msg:
        await message.answer("Yangi xabarlar yo'q.", reply_markup=await build_admin_menu(session))
        return
        
    user = msg.user
    text = f"📩 *Yangi xabar ({msg.message_type})*\\n\\n"
    text += f"👤 Yuboruvchi: {user.full_name}\\n"
    text += f"📞 Telefon: {user.phone or 'Mavjud emas'}\\n"
    text += f"📅 Vaqt: {msg.created_at.strftime('%d.%m.%Y %H:%M')}\\n\\n"
    
    if msg.text_content:
        text += f"📝 Matn: {msg.text_content}\\n"
        
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
    text = f"📩 *Yangi xabar ({msg.message_type})*\\n\\n"
    text += f"👤 Yuboruvchi: {user.full_name}\\n"
    text += f"📞 Telefon: {user.phone or 'Mavjud emas'}\\n"
    text += f"📅 Vaqt: {msg.created_at.strftime('%d.%m.%Y %H:%M')}\\n\\n"
    
    if msg.text_content:
        text += f"📝 Matn: {msg.text_content}\\n"
        
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
'''

text = text + '\n' + yordam_handler

with open('bot/handlers/admin.py', 'w', encoding='utf-8') as f:
    f.write(text)
