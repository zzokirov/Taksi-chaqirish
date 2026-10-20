with open('bot/handlers/orders.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('qabul qildi.\n\n"\n        f"📞', 'qabul qildi.\\n\\n"\n        f"📞')
text = text.replace('*Haydovchi topildi!*\n\n"\n        f"👤', '*Haydovchi topildi!*\\n\\n"\n        f"👤')
text = text.replace('{driver.full_name}\n"\n        f"🚕', '{driver.full_name}\\n"\n        f"🚕')
text = text.replace('{driver.car_model}\n"\n        f"🔢', '{driver.car_model}\\n"\n        f"🔢')
text = text.replace('{driver.car_number}\n\n"\n        "Haydovchi', '{driver.car_number}\\n\\n"\n        "Haydovchi')

text = text.replace('(Qaytarilgan)\n\n"\n        f"🏠', '(Qaytarilgan)\\n\\n"\n        f"🏠')
text = text.replace('{order.from_address}\n"\n        f"🏁', '{order.from_address}\\n"\n        f"🏁')
text = text.replace('{order.to_address}\n"\n        f"👥', '{order.to_address}\\n"\n        f"👥')
text = text.replace('{order.passengers}\n"\n        f"💰', '{order.passengers}\\n"\n        f"💰')
text = text.replace("'Kelishiladi'}\n\"\n        f\"🕒", "'Kelishiladi'}\\n\"\n        f\"🕒")


with open('bot/handlers/orders.py', 'w', encoding='utf-8') as f:
    f.write(text)
