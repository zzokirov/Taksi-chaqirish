import re

with open('bot/handlers/customer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove the line containing "Telefon: {user.phone}"
new_text = re.sub(r'[ \t]*f\"[^\"]+Telefon: \{user\.phone\}\\n\"', '', text)

# Add reply_markup to the group send_message
new_text = new_text.replace(
'''            await bot.send_message(
                chat_id=group.telegram_group_id,
                text=order_text,
                parse_mode="Markdown"
            )''',
'''            await bot.send_message(
                chat_id=group.telegram_group_id,
                text=order_text,
                parse_mode="Markdown",
                reply_markup=order_action_kb(order.id)
            )'''
)

# Add reply_markup to the fallback safe_send_message
new_text = new_text.replace(
'''await safe_send_message(bot, drv.user.telegram_id, order_text, parse_mode="Markdown")''',
'''await safe_send_message(bot, drv.user.telegram_id, order_text, parse_mode="Markdown", reply_markup=order_action_kb(order.id))'''
)

with open('bot/handlers/customer.py', 'w', encoding='utf-8') as f:
    f.write(new_text)
