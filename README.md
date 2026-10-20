# 🚕 Farg'ona Viloyati Taksi Bot

Ushbu loyiha Farg'ona viloyati uchun maxsus ishlab chiqilgan professional Telegram taksi botidir.

## 📌 Asosiy xususiyatlar
- Mijozlar uchun oson buyurtma berish.
- Haydovchilarni ro'yxatdan o'tkazish (faqat Farg'ona tumanlari).
- Haydovchilar to'lov chekini yuborishi va admin tasdiqlashi.
- Tasdiqlangan haydovchilarni o'zlari tanlagan tuman guruhiga yo'naltirish.
- Buyurtmalarni faqat mos tuman va ONLINE haydovchilarga yuborish.
- Admin panel (statistika, to'lovlar, guruhlar va tumanlar boshqaruvi).

---

## 🛠 1. BotFather Sozlamalari (Telegram)

1. Telegramda **@BotFather** ga kiring va `/newbot` buyrug'ini yozing.
2. Botga ism va username bering.
3. BotFather bergan **HTTP API Token** ni nusxalab oling.
4. Bot tavsifini o'rnatish: `/setdescription` -> Botni tanlang -> Matnni kiriting.
5. Bot haqida ma'lumot: `/setabouttext` -> Botni tanlang -> Matnni kiriting.
6. Buyruqlarni o'rnatish: `/setcommands` -> Botni tanlang -> Quyidagini yuboring:
```text
start - Botni ishga tushirish
help - Yordam va qoidalar
admin - Admin panel (faqat adminlar uchun)
```

---

## 💻 2. Windows uchun o'rnatish (Qadam-ba-qadam)

### 1-qadam: Python o'rnatish
Agar kompyuteringizda Python yo'q bo'lsa, [python.org](https://www.python.org/downloads/) saytidan oxirgi versiyani yuklab oling va o'rnating. O'rnatish vaqtida **"Add Python to PATH"** tugmasini belgilashni unutmang.

### 2-qadam: PostgreSQL o'rnatish
[PostgreSQL.org](https://www.postgresql.org/download/windows/) saytidan Windows uchun PostgreSQL ni yuklab oling va o'rnating.
PgAdmin orqali kirib yangi database yarating, nomi: `taxi_bot` bo'lsin.

### 3-qadam: Loyihani sozlash
Terminalni (Command Prompt yoki PowerShell) oching va loyiha papkasiga kiring:
```powershell
cd "C:\Users\Sizning_Ismingiz\Desktop\shafyor bot"
```

Virtual environment (izolyatsiya qilingan muhit) yarating:
```powershell
python -m venv venv
```

Virtual environmentni ishga tushiring:
```powershell
.\venv\Scripts\activate
```

Kerakli kutubxonalarni o'rnating:
```powershell
pip install -r requirements.txt
```

### 4-qadam: .env faylini yaratish
Loyiha papkasida `.env` nomli fayl yarating va ichiga quyidagilarni yozing:
```env
BOT_TOKEN=Sizning_Bot_Tokeningiz
ADMIN_IDS=Sizning_Telegram_ID_Raqamingiz
DATABASE_URL=postgresql+asyncpg://postgres:parolingiz@localhost:5432/taxi_bot
PAYMENT_CARD=8600 0000 0000 0000
PAYMENT_CARD_OWNER=Ism Familiya
PAYMENT_AMOUNT=50000
ADMIN_USERNAME=@sizning_useringiz
LOG_LEVEL=INFO
```
*(Telegram ID ni @userinfobot orqali bilib olishingiz mumkin)*

### 5-qadam: Baza (Database) migratsiyasi
Database jadvallarini yaratish uchun Alembic ishlatamiz:
```powershell
alembic revision --autogenerate -m "Init tables"
alembic upgrade head
```
*(Bu buyruq barcha 8 ta jadvalni sizning PostgreSQL bazangizda yaratib beradi)*

### 6-qadam: Tumanlar va Guruhlarni sozlash
1. Botni ishga tushiring: `python main.py`
2. Botga kirib `/admin` deb yozing.
3. **📍 Tumanlar** bo'limiga kirib Farg'ona tumanlarini qo'shing (masalan: Farg'ona shahri, Qo'qon shahri, Rishton va hokazo).
4. Telegramda har bir tuman uchun alohida guruh oching (masalan, "Rishton Haydovchilari").
5. Guruh sozlamalaridan Invite Link (taklif havolasi) oling.
6. Admin panelda **📢 Guruhlar** bo'limiga kirib, yaratilgan tumanlarni shu guruhlar bilan bog'lab chiqing va havolani saqlang.

### 7-qadam: Botni ishga tushirish
Hammasi tayyor! Botni ishlatish uchun:
```powershell
python main.py
```

---

## 🚀 3. VPS / Ubuntu Server uchun Deploy (Production)

### Variant A: Docker orqali o'rnatish (Tavsiya etiladi)

1. Serverga kiring va loyihani yuklang.
2. `.env` faylini to'ldiring (Bunda `DATABASE_URL=postgresql+asyncpg://postgres:postgres_password@db:5432/taxi_bot` qiling, chunki db docker konteyner nomi).
3. Docker Compose orqali ishga tushiring:
```bash
docker-compose up -d --build
```
4. Migratsiya qilish uchun konteyner ichiga kirib bajaring:
```bash
docker exec -it taxi_bot alembic upgrade head
```

### Variant B: Systemd orqali o'rnatish (Dockersiz)

1. Serverga Python va PostgreSQL o'rnating:
```bash
sudo apt update
sudo apt install python3.12-venv python3.12-dev postgresql postgresql-contrib
```
2. Database yarating:
```bash
sudo -u postgres psql -c "CREATE DATABASE taxi_bot;"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'parolingiz';"
```
3. Loyihani `/opt/taxi-bot` papkasiga joylang.
4. Virtual environment yarating:
```bash
cd /opt/taxi-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
5. `.env` yarating va `alembic upgrade head` ni bajaring.
6. Systemd service yaratish:
```bash
sudo cp systemd/taxi-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable taxi-bot
sudo systemctl start taxi-bot
```
Bot holatini tekshirish: `sudo systemctl status taxi-bot`

---

## 📝 Muhim Eslatmalar
- Mijoz buyurtma berganda faqat uning hududidagi (`district_id`) va **ONLINE** holatdagi haydovchilarga xabar boradi.
- Haydovchi ro'yxatdan o'tganda avtomatik guruhga kiritilmaydi. U to'lov qilishi va ADMIN uni tasdiqlashi **SHART**.
- Haydovchi guruhga kirish linkini faqat Admin tasdiqlaganidan keyin "📢 Guruhim" tugmasi orqali ola biladi.
- Aloqa qoidasi: Mijoz aslo haydovchiga birinchi qo'ng'iroq qilmaydi (unga raqam berilmaydi), **haydovchi mijozga qo'ng'iroq qiladi.**
