import re

with open('bot/handlers/start.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_cmd_help = '''@router.message(Command("help"))
@router.message(Command("yordam"))
@router.message(F.text == "ℹ️ Yordam")
async def cmd_help(message: types.Message, state: FSMContext):
    """Yordam xabari."""
    text = (
        "ℹ️ *Qo'llab-quvvatlash xizmati*\\n\\n"
        "Bizga savol, taklif yoki shikoyatingiz bo'lsa yozib qoldiring. "
        "Matn, rasm yoki ovozli xabar yuborishingiz mumkin:"
    )
    from bot.keyboards.admin_kb import cancel_admin_action_kb
    await message.answer(text, parse_mode="Markdown", reply_markup=cancel_admin_action_kb())
    
    from bot.states.customer_states import CustomerOrderState
    await state.set_state(CustomerOrderState.waiting_for_support_message)'''

text = re.sub(r'@router\.message\(Command\(\"help\"\)\).*?await message\.answer\(text, parse_mode=\"Markdown\"\)', new_cmd_help, text, flags=re.DOTALL)

with open('bot/handlers/start.py', 'w', encoding='utf-8') as f:
    f.write(text)
