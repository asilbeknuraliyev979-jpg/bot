import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from loader import bot, db
from config.config import Config
from states.states import RegistrationStates
from keyboards.reply.keyboards import get_contact_keyboard, get_class_keyboard, get_main_menu_keyboard
from keyboards.inline.keyboards import get_subscription_keyboard
from utils.subscription import is_subscribed

router = Router()
logger = logging.getLogger("EduMasterBot.handlers.start")

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    
    # 1. Check mandatory channel subscription first
    channels = db.get_all_channels()
    not_subscribed = []
    if channels:
        for ch in channels:
            if not await is_subscribed(bot, ch['channel_id'], telegram_id):
                not_subscribed.append(ch)

    if not_subscribed:
        await message.answer(
            f"👋 <b>Edu Master Botga xush kelibsiz!</b>\n\n"
            f"🔒 Botdan foydalanish uchun hamkor kanallarimizga a'zo bo'lishingiz majburiy.\n\n"
            f"<i>A'zo bo'lgandan so'ng, pastdagi '✅ Tekshirish' tugmasini bosing!</i>",
            reply_markup=get_subscription_keyboard(not_subscribed)
        )
        return

    # 2. Check if user already exists
    user = db.get_user(telegram_id)
    if not user:
        await message.answer(
            "👋 <b>Edu Master Botga xush kelibsiz!</b>\n\n"
            "Tizimdan foydalanish uchun ro'yxatdan o'tishingiz kerak.\n\n"
            "📝 <b>Ism va familiyangizni kiriting:</b>\n"
            "<i>(Masalan: Bahodir Boliqulov)</i>",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegistrationStates.waiting_for_name)
    else:
        await message.answer(
            f"👋 <b>Qaytganingizdan xursandmiz, {user['full_name']}!</b>\n\n"
            "📚 Kerakli bo'limni tanlang:",
            reply_markup=get_main_menu_keyboard()
        )

# Registration FSM: 1. Full name
@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name.split()) < 2:
        await message.answer(
            "⚠️ <b>Xatolik!</b>\n\n"
            "Iltimos, ism va familiyangizni to'liq kiriting (kamida 2 ta so'z):\n"
            "<i>(Masalan: Bahodir Boliqulov)</i>"
        )
        return
        
    await state.update_data(full_name=name)
    await message.answer(
        "📞 <b>Telefon raqamingizni yuboring:</b>\n\n"
        "Quyidagi <b>'📞 Telefon raqamni yuborish'</b> tugmasini bosing:",
        reply_markup=get_contact_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)

# Registration FSM: 2. Phone number
@router.message(RegistrationStates.waiting_for_phone, F.contact)
@router.message(RegistrationStates.waiting_for_phone, F.text)
async def process_phone(message: Message, state: FSMContext):
    phone = ""
    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = f"+{phone}"
    elif message.text:
        text = message.text.strip()
        # Basic validation
        if not text.startswith("+") and not text.isdigit():
            await message.answer(
                "⚠️ <b>Telefon raqami formati noto'g'ri!</b>\n\n"
                "Iltimos, pastdagi tugmani bosing yoki raqamni quyidagi formatda yozib yuboring:\n"
                "<i>+998901234567</i>"
            )
            return
        phone = text

    await state.update_data(phone=phone)
    await message.answer(
        "🏫 <b>Sinfingizni tanlang:</b>\n\n"
        "Quyidagi ro'yxatdan o'zingiz o'qiydigan sinfni tanlang:",
        reply_markup=get_class_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_class)

# Registration FSM: 3. Class
@router.message(RegistrationStates.waiting_for_class, F.text)
async def process_class(message: Message, state: FSMContext):
    class_name = message.text.strip()
    # Simple check if class is one of the choices
    valid_classes = [f"{i}-sinf" for i in range(1, 12)]
    if class_name not in valid_classes:
        await message.answer(
            "⚠️ <b>Sinf noto'g'ri tanlandi!</b>\n\n"
            "Iltimos, klaviaturadagi sinflardan birini tanlang:",
            reply_markup=get_class_keyboard()
        )
        return
        
    user_data = await state.get_data()
    telegram_id = message.from_user.id
    
    # Save to Database
    db.add_user(
        telegram_id=telegram_id,
        full_name=user_data["full_name"],
        phone=user_data["phone"],
        class_name=class_name
    )
    
    await state.clear()
    
    await message.answer(
        "🎉 <b>Muvaffaqiyatli ro'yxatdan o'tdingiz!</b>",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Check subscription
    channels = db.get_all_channels()
    not_subscribed = []
    if channels:
        for ch in channels:
            if not await is_subscribed(bot, ch['channel_id'], telegram_id):
                not_subscribed.append(ch)

    if not not_subscribed:
        await message.answer(
            f"✨ <b>Xush kelibsiz, {user_data['full_name']}!</b>\n\n"
            "Botdan foydalanishga tayyorsiz. Quyidagi menyudan foydalaning:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(
            f"🔒 <b>Ro'yxatdan o'tish muvaffaqiyatli yakunlandi.</b>\n\n"
            f"Biroq, botdan foydalanishni boshlash uchun kanallarimizga a'zo bo'lishingiz shart:",
            reply_markup=get_subscription_keyboard(not_subscribed)
        )

# Callback handler for subscription checking
@router.callback_query(F.data == "check_subscription")
async def process_check_subscription(callback: CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    
    channels = db.get_all_channels()
    not_subscribed = []
    if channels:
        for ch in channels:
            if not await is_subscribed(bot, ch['channel_id'], telegram_id):
                not_subscribed.append(ch)

    if not_subscribed:
        await callback.answer(
            "❌ Siz hali hamma kanallarga a'zo bo'lmadingiz! Iltimos, a'zo bo'lib qayta tekshirib ko'ring.",
            show_alert=True
        )
        return
        
    user = db.get_user(telegram_id)
    await callback.message.delete()
    if not user:
        # Start FSM registration
        await callback.message.answer(
            "✅ <b>Rahmat! A'zolik tasdiqlandi.</b>\n\n"
            "Tizimdan foydalanish uchun ro'yxatdan o'tishingiz kerak.\n\n"
            "📝 <b>Ism va familiyangizni kiriting:</b>\n"
            "<i>(Masalan: Bahodir Boliqulov)</i>",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegistrationStates.waiting_for_name)
    else:
        await callback.message.answer(
            f"✅ <b>Rahmat! Kanaldan a'zolik tekshirildi.</b>\n\n"
            f"✨ Xush kelibsiz, {user['full_name']}!\n"
            f"Kerakli bo'limni tanlang:",
            reply_markup=get_main_menu_keyboard()
        )
    await callback.answer()
