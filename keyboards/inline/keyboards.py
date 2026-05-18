from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_subscription_keyboard(channels: list):
    inline_keyboard = []
    for idx, channel in enumerate(channels, 1):
        inline_keyboard.append([InlineKeyboardButton(text=f"📢 {idx}-kanalga o'tish", url=channel['url'])])
    
    inline_keyboard.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def get_test_start_keyboard(test_code: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Testni boshlash", callback_data=f"start_test:{test_code}")]
        ]
    )

def get_result_keyboard(test_code: str):
    buttons = []
    buttons.append([InlineKeyboardButton(text="🏆 Reytingni ko'rish", callback_data=f"view_rating:{test_code}")])
    buttons.append([InlineKeyboardButton(text="📚 Yangi test", callback_data="new_test")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_profile_edit_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Profilni tahrirlash", callback_data="edit_profile"),
                InlineKeyboardButton(text="📞 Telefonni yangilash", callback_data="update_phone")
            ]
        ]
    )

def get_admin_test_keyboard(test_code: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ O'chirish", callback_data=f"del_test:{test_code}")]
        ]
    )
