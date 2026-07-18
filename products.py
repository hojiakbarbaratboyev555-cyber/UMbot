# Mahsulotlar shu yerda belgilanadi. Bot ishga tushganda avtomatik bazaga qo'shiladi/yangilanadi.
#
# Har bir mahsulot uchun:
#   name        - mahsulot nomi
#   description - tavsif
#   price       - narxi (⌁𝗛𝗕⌁ da)
#   photo_file_id - rasm file_id (Telegram'ga rasm yuborib, botdan file_id oling; bo'lmasa None qoldiring)
#
# Mahsulotni o'chirish uchun shu ro'yxatdan qatorni olib tashlang va qayta deploy qiling.

PRODUCTS = [
    {
        "name": "Namuna mahsulot 1",
        "description": "Bu yerga mahsulot haqida qisqacha ma'lumot yozing.",
        "price": 1.0,
        "photo_file_id": None,
    },
    {
        "name": "Namuna mahsulot 2",
        "description": "Ikkinchi mahsulot tavsifi.",
        "price": 2.5,
        "photo_file_id": None,
    },
]
