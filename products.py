# Mahsulotlar shu yerda belgilanadi. Bot ishga tushganda avtomatik bazaga qo'shiladi/yangilanadi.
#
# Har bir mahsulot uchun:
#   name        - mahsulot nomi
#   description - tavsif
#   price       - narxi SO'MDA (qat'iy, o'zgarmaydi). Foydalanuvchidan yechiladigan
#                 ⌁𝗛𝗕⌁ miqdori TON kursiga qarab har safar avtomatik qayta hisoblanadi:
#                 TON qimmatlashsa -> kamroq HB kerak, TON arzonlashsa -> ko'proq HB kerak.
#   photo_file_id - rasm file_id (Telegram'ga rasm yuborib, botdan file_id oling; bo'lmasa None qoldiring)
#
# Mahsulotni o'chirish uchun shu ro'yxatdan qatorni olib tashlang va qayta deploy qiling.

PRODUCTS = [
    {
        "name": "Namuna mahsulot 1",
        "description": "Bu yerga mahsulot haqida qisqacha ma'lumot yozing.",
        "price": 30_000,  # so'mda
        "photo_file_id": None,
    },
    {
        "name": "Namuna mahsulot 2",
        "description": "Ikkinchi mahsulot tavsifi.",
        "price": 75_000,  # so'mda
        "photo_file_id": None,
    },
]