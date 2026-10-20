with open('bot/handlers/start.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('*Qo\'llab-quvvatlash xizmati*\n\n"\n        "Bizga savol', '*Qo\'llab-quvvatlash xizmati*\\n\\n"\n        "Bizga savol')

with open('bot/handlers/start.py', 'w', encoding='utf-8') as f:
    f.write(text)
