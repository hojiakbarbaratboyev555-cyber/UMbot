# Mahsulotlar shu yerda belgilanadi. Bot ishga tushganda avtomatik bazaga qo'shiladi/yangilanadi.
#
# MUHIM: "name", "description", "price", "photo_file_id" — bular kodning ICHKI
# nomlari (kalitlari), ularni O'ZGARTIRMANG! Faqat qavs ichidagi matnni (qiymatni)
# o'zgartiring.
#
#   name        - mahsulot nomi
#   description - tavsif
#   price       - narxi SO'MDA (qat'iy). Foydalanuvchidan yechiladigan ⌁𝗛𝗕⌁
#                 miqdori qat'iy kursga (1 ⌁𝗛𝗕⌁ = 30 000 so'm) qarab hisoblanadi.
#   photo_file_id - rasm file_id (bo'lmasa None qoldiring)

PRODUCTS = [
    {
        "name": "1 oylik telegram premium",
        "description": "1 oy telegram premium funksiyalaridan erkin foydalanasiz. Akkauntga kirib olib beriladi",
        "price": 30_000,  # so'mda — narxni o'zingiz to'g'rilang
        "photo_file_id": None,
    },
]