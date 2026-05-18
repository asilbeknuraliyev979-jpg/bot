from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="↩️ Ortga qaytish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="↩️ Ortga qaytish")]
        ],
        resize_keyboard=True
    )

def get_class_keyboard():
    # Buttons for 1-sinf to 11-sinf
    buttons = []
    row = []
    for i in range(1, 12):
        row.append(KeyboardButton(text=f"{i}-sinf"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    # Add Back button at the bottom
    buttons.append([KeyboardButton(text="↩️ Ortga qaytish")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)


def get_main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Test ishlash"), KeyboardButton(text="🎁 Sovg'ali testlar")],
            [KeyboardButton(text="📊 Natijam"), KeyboardButton(text="🏆 Umumiy reyting"), KeyboardButton(text="👤 Profilim")],
            [KeyboardButton(text="📢 Reklama berish"), KeyboardButton(text="ℹ️ Yordam"), KeyboardButton(text="🤝 Hamkorlik")]
        ],
        resize_keyboard=True
    )

def get_solving_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏁 Ishlab bo'ldim")]
        ],
        resize_keyboard=True
    )


def get_admin_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Test qo'shish"), KeyboardButton(text="🎁 Sovg'ali test qo'shish")],
            [KeyboardButton(text="❌ Testni o'chirish"), KeyboardButton(text="✏️ Testni tahrirlash")],
            [KeyboardButton(text="📊 Statistikalar"), KeyboardButton(text="📥 Natijalarni yuklab olish")],
            [KeyboardButton(text="👥 Foydalanuvchilar"), KeyboardButton(text="📢 Xabar yuborish")],
            [KeyboardButton(text="⚙️ Majburiy kanallar"), KeyboardButton(text="🔐 Adminlar")],
            [KeyboardButton(text="🏠 Bosh menuga qaytish")]
        ],
        resize_keyboard=True
    )
