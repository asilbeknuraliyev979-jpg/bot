import os
import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from loader import bot, db
from config.config import Config
from states.states import ProfileStates, RatingStates

from keyboards.reply.keyboards import get_main_menu_keyboard, get_class_keyboard, get_contact_keyboard, get_back_keyboard, get_admin_menu_keyboard
from keyboards.inline.keyboards import get_profile_edit_keyboard
from utils.subscription import is_subscribed

router = Router()
logger = logging.getLogger("EduMasterBot.handlers.menu")

from aiogram.filters import StateFilter

@router.message(F.text.in_(["↩️ Ortga qaytish", "↩️ Ortga", "🏠 Bosh menuga qaytish"]), StateFilter("*"))
async def global_back_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_main_menu_keyboard())

# Middleware check function to ensure subscription
async def check_user_access(message: Message) -> bool:
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("⚠️ Botdan foydalanish uchun iltimos /start buyrug'ini bosing va ro'yxatdan o'ting.")
        return False
        
    channels = db.get_all_channels()
    not_subscribed = []
    if channels:
        for ch in channels:
            if not await is_subscribed(bot, ch['channel_id'], telegram_id):
                not_subscribed.append(ch)

    if not_subscribed:
        from keyboards.inline.keyboards import get_subscription_keyboard
        await message.answer(
            f"🔒 <b>Botdan foydalanish uchun hamkor kanallarimizga a'zo bo'lishingiz majburiy:</b>\n",
            reply_markup=get_subscription_keyboard(not_subscribed)
        )
        return False
    return True

# --- 👤 PROFILIM SECTION ---
@router.message(F.text == "👤 Profilim")
async def show_profile(message: Message):
    if not await check_user_access(message):
        return
        
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    results = db.get_user_results(telegram_id)
    
    msg_text = (
        "👤 <b>PROFIL MA'LUMOTLARI</b>\n\n"
        f"📝 <b>Ism va Familiya:</b> {user['full_name']}\n"
        f"📞 <b>Telefon raqam:</b> {user['phone']}\n"
        f"🏫 <b>Sinf:</b> {user['class_name']}\n"
        f"🆔 <b>Telegram ID:</b> <code>{user['telegram_id']}</code>\n"
        f"📅 <b>Ro'yxatdan o'tgan sana:</b> {user['registration_date']}\n"
        f"📚 <b>Topshirilgan testlar:</b> {len(results)} ta"
    )
    
    await message.answer(msg_text, reply_markup=get_profile_edit_keyboard())

# Profile edit callback
@router.callback_query(F.data == "edit_profile")
async def edit_profile_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "📝 <b>Yangi ism va familiyangizni kiriting:</b>",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(ProfileStates.waiting_for_new_name)
    await callback.answer()

@router.message(ProfileStates.waiting_for_new_name)
async def process_new_name(message: Message, state: FSMContext):
    name = message.text.strip()
    
    if name == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_main_menu_keyboard())
        return
        
    if len(name.split()) < 2:
        await message.answer(
            "⚠️ Iltimos, ism va familiyani to'liq kiriting (masalan: Ali Hasanov):",
            reply_markup=get_back_keyboard()
        )
        return
        
    await state.update_data(new_name=name)
    await message.answer(

        "🏫 <b>Yangi sinfingizni tanlang:</b>",
        reply_markup=get_class_keyboard()
    )
    await state.set_state(ProfileStates.waiting_for_new_class)

@router.message(ProfileStates.waiting_for_new_class)
async def process_new_class(message: Message, state: FSMContext):
    class_name = message.text.strip()
    
    if class_name == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_main_menu_keyboard())
        return
        
    valid_classes = [f"{i}-sinf" for i in range(1, 12)]
    if class_name not in valid_classes:
        await message.answer("⚠️ Iltimos, klaviaturadagi sinflardan birini tanlang:", reply_markup=get_class_keyboard())
        return
        
    user_data = await state.get_data()
    db.update_user(message.from_user.id, full_name=user_data["new_name"], class_name=class_name)
    await state.clear()
    
    await message.answer(
        "✅ <b>Profil ma'lumotlaringiz muvaffaqiyatli yangilandi!</b>",
        reply_markup=get_main_menu_keyboard()
    )

# Phone update callback
@router.callback_query(F.data == "update_phone")
async def update_phone_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📞 <b>Yangi telefon raqamingizni yuboring:</b>\n"
        "Quyidagi tugmani bosing yoki raqamni quyidagi formatda kiriting: <i>+998901234567</i>",
        reply_markup=get_contact_keyboard()
    )
    await state.set_state(ProfileStates.waiting_for_new_phone)
    await callback.answer()

@router.message(ProfileStates.waiting_for_new_phone)
async def process_new_phone(message: Message, state: FSMContext):
    input_text = message.text.strip() if message.text else ""
    
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_main_menu_keyboard())
        return
        
    phone = ""
    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = f"+{phone}"
    elif message.text:
        text = input_text
        if not text.startswith("+") and not text.isdigit():
            await message.answer(
                "⚠️ Noto'g'ri format. Telefon raqamingizni kiriting (+998901234567):",
                reply_markup=get_contact_keyboard()
            )
            return
        phone = text
        
    db.update_user(message.from_user.id, phone=phone)
    await state.clear()
    
    await message.answer(
        "✅ <b>Telefon raqamingiz muvaffaqiyatli yangilandi!</b>",
        reply_markup=get_main_menu_keyboard()
    )


# --- 📊 NATIJAM SECTION ---
@router.message(F.text == "📊 Natijam")
async def show_my_results(message: Message):
    if not await check_user_access(message):
        return
        
    telegram_id = message.from_user.id
    results = db.get_user_results(telegram_id)
    results = db.get_user_results(telegram_id)
    
    if not results:
        await message.answer(
            "📊 <b>Siz hali hech qanday test topshirmagansiz!</b>\n\n"
            "Test topshirish uchun <b>📚 Test ishlash</b> bo'limidan foydalaning."
        )
        return
        
    percentages = [r["percentage"] for r in results]
    avg_percentage = sum(percentages) / len(percentages)
    best_result = max(percentages)
    last_result = results[0]
    
    msg_text = (
        "🎯 <b>TEST NATIJALARINGIZ TAHLILI</b>\n\n"
        f"📊 <b>Umumiy topshirilgan testlar:</b> {len(results)} ta\n"
        f"🥇 <b>Eng yuqori natija:</b> {best_result:.1f}%\n"
        f"📈 <b>O'rtacha ko'rsatkich:</b> {avg_percentage:.1f}%\n\n"
        "📝 <b>Oxirgi topshirilgan test:</b>\n"
        f"▪️ Fan: {last_result['subject']}\n"
        f"▪️ Test kodi: <code>{last_result['test_code']}</code>\n"
        f"▪️ To'g'ri javoblar: {last_result['correct_count']} ta\n"
        f"▪️ Natija: {last_result['percentage']}%\n"
        f"▪️ Vaqt: {last_result['submission_time']}"
    )
    
    await message.answer(msg_text)

# --- 🏆 REYTING SECTION ---
@router.message(F.text == "🏆 Umumiy reyting")
async def show_rating_prompt(message: Message, state: FSMContext):
    if not await check_user_access(message):
        return
        
    telegram_id = message.from_user.id
    
    # Get overall global leaderboard (Top 10)
    leaderboard = db.get_global_leaderboard(limit=10)
    
    msg_text = "🏆 <b>EDU MASTER BOT GLOBAL REYTINGI (TOP 10)</b>\n"
    msg_text += "<i>Hamma foydalanuvchilarning ishlagan testlari va o'rtacha ballariga ko'ra:</i>\n\n"
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    if not leaderboard:
        msg_text += "ℹ️ Hozircha reytingda hech kim yo'q.\n\n"
    else:
        for idx, r in enumerate(leaderboard):
            icon = medals[idx] if idx < len(medals) else f"{idx+1}."
            name = r["full_name"]
            sinf = r["class_name"]
            avg_score = r["avg_score"]
            count = r["tests_count"]
            msg_text += f"{icon} <b>{name}</b> ({sinf}) — <b>{avg_score}%</b> <i>({count} ta test topshirgan)</i>\n"
            
    # Show user's own global rank
    u_rank, total_u = db.get_user_global_rank(telegram_id)
    msg_text += "\n-----------------------------------------\n"
    if u_rank:
        msg_text += f"👤 <b>Sizning o'rningiz: {u_rank}-o'rin</b> (jami {total_u} ta o'quvchidan)\n\n"
    else:
        msg_text += "👤 <b>Siz hali biror test topshirmadingiz.</b>\n\n"
        
    msg_text += (
        "🔍 <b>Muayyan test bo'yicha natijalar reytingini ko'rishni istaysizmi?</b>\n"
        "Unda test kodini kiriting (masalan: <code>PM-21</code>):\n"
        "<i>(Bekor qilish uchun: '↩️ Ortga qaytish' tugmasini bosing)</i>"
    )
    
    await message.answer(msg_text, reply_markup=get_back_keyboard())
    await state.set_state(RatingStates.waiting_for_test_code)

@router.message(RatingStates.waiting_for_test_code)
async def process_rating_test_code(message: Message, state: FSMContext):
    if not await check_user_access(message):
        await state.clear()
        return
        
    input_text = message.text.strip()
    
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_main_menu_keyboard())
        return
        
    test_code = input_text.upper()
    telegram_id = message.from_user.id
    
    # Check test existence
    test = db.get_test(test_code)
    if not test:
        await message.answer(
            "❌ <b>Bunday kodli test topilmadi!</b>\n\n"
            "Iltimos, test kodini to'g'ri kiritganingizga ishonch hosil qiling va qayta yuboring:\n"
            "<i>(Ortga qaytish uchun: '↩️ Ortga qaytish' tugmasini bosing)</i>",
            reply_markup=get_back_keyboard()
        )
        return

        
    # Get test results sorted by percentage desc, duration spent asc
    results = db.get_test_results(test_code)
    
    # Clear state since input is processed
    await state.clear()
    
    if not results:
        await message.answer(
            f"🏆 <b>'{test['subject']}' ({test_code}) bo'yicha hali natijalar mavjud emas.</b>\n\n"
            "Ushbu test bo'yicha birinchi bo'lib ishtirok eting!",
            reply_markup=get_main_menu_keyboard()
        )
        return
        
    msg_text = f"🏆 <b>'{test['subject']}' BO'YICHA REYTING (TOP 3)</b>\n"
    msg_text += f"📄 Test kodi: <code>{test_code}</code>\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    for idx, r in enumerate(results[:3], 1):
        icon = medals[idx-1]
        name = r["full_name"]
        sinf = r["class_name"]
        score = r["percentage"]
        
        row_text = f"{icon} {name} ({sinf}) — <b>{score}%</b>\n"
        msg_text += row_text
        
    msg_text += "\n-----------------------------------------\n"
    
    # Get current user rank in this test
    rank, total_p = db.get_user_rank(telegram_id, test_code)
    if rank is not None:
        user_result = None
        for r in results:
            if r["telegram_id"] == telegram_id:
                user_result = r
                break
        score_str = f" ({user_result['percentage']}%)" if user_result else ""
        msg_text += f"👤 <b>Sizning o'rningiz: {rank}-o'rin{score_str}</b> (jami {total_p} ta o'quvchidan)\n"
    else:
        msg_text += "👤 <b>Siz ushbu testda hali ishtirok etmadingiz.</b>\n"
        
    await message.answer(msg_text, reply_markup=get_main_menu_keyboard())


# --- ℹ️ YORDAM SECTION ---
@router.message(F.text == "ℹ️ Yordam")
async def show_help(message: Message):
    help_text = (
        "✨ <b>EDU MASTER — PROFESSIONAL YORDAM TIZIMI</b> ✨\n\n"
        "🤖 <b>Botdan to'g'ri va samarali foydalanish yo'riqnomasi:</b>\n\n"
        "1️⃣ <b>📚 Test ishlash bo'limi:</b>\n"
        "Asosiy menyudagi <b>📚 Test ishlash</b> tugmasini bosing va o'zingiz topshirmoqchi bo'lgan maxsus test kodini (masalan: <code>PM-21</code>) yozib yuboring.\n\n"
        "2️⃣ <b>📄 Savollar va topshiriqlar:</b>\n"
        "Test faol bo'lgan taqdirda, tizim sizga PDF formatdagi savollar faylini yuboradi. Vaqt darhol ketishni boshlaydi.\n\n"
        "3️⃣ <b>🚀 Testni yakunlash va javob topshirish:</b>\n"
        "Savollarni yechib bo'lgandan so'ng, pastdagi <b>'🏁 Ishlab bo'ldim'</b> tugmasini bosing va javoblaringizni quyidagi to'g'ri formatlardan birida yozib yuboring:\n"
        "👉 Ketma-ket: <code>ABCDABCD</code>\n"
        "👉 Vergul bilan: <code>1.a, 2.b, 3.c</code>\n"
        "👉 Tire bilan: <code>1-a 2-b 3-c</code>\n\n"
        "🏆 <b>Reyting tizimi:</b>\n"
        "O'z bilimingizni sinab ko'ring va do'stlaringiz orasida nechanchi o'rinda ekanligingizni <b>🏆 Umumiy reyting</b> bo'limi orqali doimiy kuzatib boring.\n\n"
        "🤝 <b>Texnik qo'llab-quvvatlash va takliflar:</b>\n"
        "Agar sizda biron bir savol, taklif yoki texnik muammolar yuzaga kelsa, loyiha rahbariga murojaat qilishingiz mumkin:\n"
        "📞 <b>Murojaat uchun administrator:</b> @xolikulovic7"
    )
    await message.answer(help_text)


# --- 🤝 HAMKORLIK SECTION ---
@router.message(F.text == "🤝 Hamkorlik")
async def show_partnership(message: Message):
    partnership_text = (
        "🤝 <b>HAMKORLIK VA REKLAMA BO'LIMI</b>\n\n"
        "📢 Hurmatli hamkorlar va tadbirkorlar!\n"
        "Agar siz <b>Edu Master Bot</b> auditoriyasiga o'zingizning reklama xabaringizni joylamoqchi bo'lsangiz yoki hamkorlik loyihalarini taklif qilmoqchi bo'lsangiz, biz hamkorlikka doim tayyormiz.\n\n"
        "📩 <b>Reklama va tijoriy hamkorlik bo'yicha bog'lanish:</b>\n"
        "👉 Administrator: @xolikulovic7\n\n"
        "<i>Iltimos, murojaatingizda taklifingiz haqida to'liq va aniq ma'lumot qoldiring. Tez orada siz bilan bog'lanamiz!</i>"
    )
    await message.answer(partnership_text)

# --- 📢 REKLAMA BERISH SECTION ---
@router.message(F.text == "📢 Reklama berish")
async def show_advertisement(message: Message):
    ad_text = (
        "📢 <b>REKLAMA BERISH</b>\n\n"
        "Siz o'z mahsulotlaringiz, xizmatlaringiz yoki kanallaringizni botimizdagi minglab o'quvchilarga reklama qilishingiz mumkin!\n\n"
        "Bizda quyidagi reklama turlari mavjud:\n"
        "1️⃣ <b>Majburiy a'zolik</b> — Botga kiruvchi har bir yangi foydalanuvchi sizning kanalingizga a'zo bo'ladi.\n"
        "2️⃣ <b>Xabar tarqatish (Broadcast)</b> — Barcha bot a'zolariga sizning reklama xabaringiz yuboriladi.\n"
        "3️⃣ <b>Homiylik (Sovg'ali testlar)</b> — Haftalik testlarga homiylik qilib, brendingizni tanitishingiz mumkin.\n\n"
        "💰 <b>Narxlar va shartlar bo'yicha ma'lumot olish uchun admin bilan bog'laning:</b>\n"
        "👉 Administrator: @xolikulovic7"
    )
    await message.answer(ad_text)

# Go back to main menu
@router.message(F.text == "🏠 Bosh menuga qaytish")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 <b>Bosh menyu:</b>", reply_markup=get_main_menu_keyboard())

# --- 🎁 SOVG'ALI TESTLAR SECTION ---
@router.message(F.text == "🎁 Sovg'ali testlar")
async def show_gift_tests(message: Message):
    if not await check_user_access(message):
        return
        
    gifts = db.get_gift_tests()
    
    if not gifts:
        await message.answer(
            "🎁 <b>Hozirda faol sovg'ali testlar mavjud emas!</b>\n\n"
            "<i>Har haftada bir marta yangi sovg'ali testlar qo'shiladi. Kanalimizni va botni muntazam kuzatib boring!</i>",
            reply_markup=get_main_menu_keyboard()
        )
        return
        
    msg_text = (
        "🎁 <b>HAFTALIK SOVG'ALI TESTLAR RO'YXATI</b>\n"
        "<i>Quyidagi faol sovg'ali testlarda ishtirok eting va o'z bilimingizni sinab ko'ring!</i>\n\n"
    )
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    
    for g in gifts:
        msg_text += f"⭐ <b>Fan:</b> {g['subject']} | <b>Kod:</b> <code>{g['code']}</code>\n"
        msg_text += f"⏳ Ishlash vaqti: {g['duration']} daqiqa\n"
        msg_text += f"📅 Muddati: {g['start_time']} dan {g['end_time']} gacha\n\n"
        
        # Button to instantly start this specific gift test
        kb.button(text=f"🚀 {g['subject']} ({g['code']}) ni boshlash", callback_data=f"start_gift_test:{g['code']}")
        
    kb.adjust(1)
    
    await message.answer(msg_text, reply_markup=kb.as_markup())
