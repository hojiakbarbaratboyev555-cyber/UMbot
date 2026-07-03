# UM Wallet Bot

Telegram orqali ishlaydigan virtual hamyon boti. Foydalanuvchilar UM (ichki valyuta)
sotib olishi, boshqa foydalanuvchiga **UM karta raqami** orqali o'tkazma qilishi va
do'kondagi mahsulotlarni UM evaziga xarid qilishi mumkin.

Bot **webhook** orqali ishlaydi va Render.com **Web Service**'da 24/7 ishlashga mo'ljallangan.

---

## Loyiha tuzilishi

```
um_bot_pro/
├── main.py              # bot handlerlari + webhook server
├── database.py          # SQLite bilan ishlash (aiosqlite)
├── keyboards.py          # tugmalar
├── states.py             # FSM holatlari
├── config.py             # environment o'zgaruvchilari
├── utils.py               # formatlash / validatsiya
├── requirements.txt
├── runtime.txt
├── Procfile
├── render.yaml
├── .env.example
└── .gitignore
```

---

## 1. Botni yaratish

1. Telegramda **@BotFather** ga yozing → `/newbot`
2. Bot nomi va username kiriting (username `bot` bilan tugashi kerak)
3. Sizga berilgan **tokenni** saqlab qo'ying

## 2. O'z Telegram ID'ingizni bilib olish

**@userinfobot** ga `/start` yuboring — ID raqamingizni ko'rsatadi. Bu ID admin
huquqi (mahsulot qo'shish, to'ldirish so'rovlarini tasdiqlash) uchun kerak.

---

## 3. Lokal test qilish

```bash
git clone https://github.com/FOYDALANUVCHI/um-wallet-bot.git
cd um-wallet-bot
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` faylini oching va `BOT_TOKEN`, `ADMIN_ID` ni to'ldiring. `WEBHOOK_URL` ni
bo'sh qoldiring — bu holda bot avtomatik **polling** rejimida ishlaydi (lokal
test uchun eng qulay usul).

```bash
python main.py
```

Telegram'da botga `/start` yozing — 4 ta tugmali menyu chiqadi.

---

## 4. GitHub'ga yuklash

**Sayt orqali (eng oson):**
1. github.com → **New repository** → nomi kiriting → Create
2. **Add file → Upload files** → yuqoridagi barcha fayllarni tashlang
3. **Commit changes**

**Terminal orqali:**
```bash
git init
git add .
git commit -m "UM Wallet Bot - production versiya"
git branch -M main
git remote add origin https://github.com/FOYDALANUVCHI/um-wallet-bot.git
git push -u origin main
```

⚠️ `.env` faylni hech qachon yuklamang — u `.gitignore` orqali avtomatik chetlab
o'tiladi.

---

## 5. Render.com'da deploy qilish

1. render.com → **New +** → **Web Service**
2. GitHub repongizni tanlang (avval GitHub'ni Render'ga ulashingiz kerak bo'ladi)
3. Sozlamalar (agar `render.yaml` avtomatik aniqlanmasa, qo'lda kiriting):

   | Maydon | Qiymat |
   |---|---|
   | Environment | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `python main.py` |
   | Instance Type | Free |

4. **Environment Variables** bo'limida qo'shing:
   ```
   BOT_TOKEN = sizning haqiqiy tokeningiz
   ADMIN_ID  = sizning telegram ID raqamingiz
   ```
   (`WEBHOOK_URL` va `PORT` ni qo'lda kiritish shart emas — Render buni avtomatik
   ta'minlaydi orqali `RENDER_EXTERNAL_URL` va `PORT`.)

5. **Create Web Service** tugmasini bosing.

Deploy tugagach, loglarda quyidagi yozuv chiqishi kerak:
```
Webhook ishga tushdi: https://um-wallet-bot.onrender.com/webhook (port 10000)
```

Brauzerda `https://sizning-service.onrender.com/` manzilini ochsangiz `Bot running`
deb yozilgan bo'ladi — bu health-check endpoint.

---

## Admin buyruqlari

| Buyruq | Format | Tavsif |
|---|---|---|
| `/addproduct` | `Nomi; Narxi; Tavsifi` | Do'konga yangi mahsulot qo'shish |
| `/editproduct` | `ID; Nomi; Narxi; Tavsifi` | Mahsulotni tahrirlash |
| `/deleteproduct` | `ID` | Mahsulotni butunlay o'chirish |
| `/setprice` | `ID; YangiNarx` | Faqat narxni o'zgartirish |
| `/enableproduct` | `ID` | Mahsulotni faollashtirish |
| `/disableproduct` | `ID` | Mahsulotni vaqtincha o'chirish |
| `/addbalance` | `TelegramID; Miqdor` | Foydalanuvchiga qo'lda UM qo'shish |
| `/removebalance` | `TelegramID; Miqdor` | Foydalanuvchidan UM yechish |
| `/users` | — | Barcha foydalanuvchilar ro'yxati |
| `/stats` | — | Umumiy statistika |
| `/broadcast` | keyingi xabar sifatida matn | Barcha foydalanuvchilarga xabar yuborish |

**Misol:** `/addproduct Premium obuna; 15000; 1 oylik premium status`

UM to'ldirish so'rovlari (foydalanuvchi screenshot yuborgach) sizga (adminga)
rasm va ✅/❌ tugmalari bilan avtomatik keladi.

---

## ⚠️ Ma'lumotlar bazasi haqida muhim eslatma

SQLite fayli (`um_bot.db`) Render'ning **free** tarifida vaqtinchalik diskda
saqlanadi. Har safar qayta deploy qilinganda (kod push qilinganda yoki server
qayta ishga tushganda) baza **tozalanishi mumkin** — ya'ni barcha balanslar,
karta raqamlari va tarix yo'qoladi.

Ishonchli production uchun ikkita variant bor:
- **Persistent Disk** qo'shish (Render → servis → Disks, ~$0.25/GB/oy)
- **PostgreSQL**ga o'tish (Render bepul PostgreSQL beradi, disk muammosi bo'lmaydi)

Agar buni hal qilishni xohlasangiz, ayting — kodni PostgreSQL'ga moslashtirib
beraman.

---

## Xavfsizlik choralari

- Barcha SQL so'rovlar parametrlashtirilgan (`?` placeholder) — SQL Injection'dan himoyalangan
- Karta raqamlari `UNIQUE` cheklov bilan generatsiya qilinadi — dublikat bo'lishi mumkin emas
- Balans hech qachon manfiy bo'lishiga yo'l qo'yilmaydi — har bir tranzaksiyadan oldin tekshiriladi
- Barcha foydalanuvchi kiritgan raqamlar validatsiya qilinadi
- Global xatolik ushlagich (`error_handler`) botni kutilmagan xatoliklardan crash bo'lishdan saqlaydi
