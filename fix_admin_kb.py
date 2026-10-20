with open('bot/keyboards/admin_kb.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_kb = '''def admin_menu_kb(pending_count: int = 0, support_count: int = 0) -> ReplyKeyboardMarkup:
    """Admin asosiy menyusi."""
    new_apps_text = f"🆕 Yangi arizalar ({pending_count})" if pending_count > 0 else "🆕 Yangi arizalar"
    support_text = f"📩 Yordam ({support_count})" if support_count > 0 else "📩 Yordam"
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=new_apps_text),
                KeyboardButton(text=support_text),
            ],
            [
                KeyboardButton(text="👥 Foydalanuvchilar"),
                KeyboardButton(text="🚕 Haydovchilar"),
            ],
            [
                KeyboardButton(text="💰 To'lovlar"),
                KeyboardButton(text="💳 To'lov sozlamalari"),
            ],
            [
                KeyboardButton(text="📨 Xabar yuborish"),
            ]
        ],
        resize_keyboard=True
    )'''

import re
text = re.sub(r'def admin_menu_kb\(pending_count: int = 0\) -> ReplyKeyboardMarkup:.*?resize_keyboard=True\n    \)', new_kb, text, flags=re.DOTALL)

with open('bot/keyboards/admin_kb.py', 'w', encoding='utf-8') as f:
    f.write(text)
