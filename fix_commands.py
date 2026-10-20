with open('bot/handlers/customer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add import Command if not exists
if 'from aiogram.filters import Command' not in text:
    text = text.replace('from aiogram import Router, F, types, Bot', 'from aiogram import Router, F, types, Bot\nfrom aiogram.filters import Command')

text = text.replace('@router.message(F.text == "🚕 Taksi chaqirish")', '@router.message(Command("buyurtma"))\n@router.message(F.text == "🚕 Taksi chaqirish")')
text = text.replace('@router.message(F.text == "📋 Buyurtmalarim")', '@router.message(Command("buyurtmalarim"))\n@router.message(F.text == "📋 Buyurtmalarim")')

with open('bot/handlers/customer.py', 'w', encoding='utf-8') as f:
    f.write(text)

with open('bot/handlers/driver.py', 'r', encoding='utf-8') as f:
    text2 = f.read()

if 'from aiogram.filters import Command' not in text2:
    text2 = text2.replace('from aiogram import Router, F, types, Bot', 'from aiogram import Router, F, types, Bot\nfrom aiogram.filters import Command')

text2 = text2.replace('@router.message(F.text == "🚕 Haydovchi bo\'lish")', '@router.message(Command("haydovchi"))\n@router.message(F.text == "🚕 Haydovchi bo\'lish")')

with open('bot/handlers/driver.py', 'w', encoding='utf-8') as f:
    f.write(text2)

with open('bot/handlers/start.py', 'r', encoding='utf-8') as f:
    text3 = f.read()

text3 = text3.replace('@router.message(Command("help"))\n@router.message(F.text == "ℹ️ Yordam")', '@router.message(Command("help"))\n@router.message(Command("yordam"))\n@router.message(F.text == "ℹ️ Yordam")')

with open('bot/handlers/start.py', 'w', encoding='utf-8') as f:
    f.write(text3)

