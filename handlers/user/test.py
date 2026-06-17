import os
import logging
import time
import asyncio

from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from loader import bot, db
from config.config import Config
from states.states import TestStates
from keyboards.reply.keyboards import get_main_menu_keyboard, get_back_keyboard, get_solving_keyboard
from keyboards.inline.keyboards import get_test_start_keyboard, get_result_keyboard
from utils.subscription import is_subscribed
from utils.certificate import create_certificate
import re

def parse_user_answers(input_text: str) -> str:
    if not input_text:
        return ""
    input_text = input_text.upper().strip()
    # Matches patterns like 1.A, 1-A, 1 A, 1A
    matches = re.findall(r"(\d+)[\s\.\-]*([A-Z])", input_text)
    if matches:
        # Sort by the question number to ensure exact sequence order
        sorted_matches = sorted(matches, key=lambda x: int(x[0]))
        return "".join(val for num, val in sorted_matches)
    else:
        # Fallback to extracting all alphabetic characters directly
        return "".join(c for c in input_text if c.isalpha())

router = Router()
logger = logging.getLogger("EduMasterBot.handlers.test")

# Active timer tasks to cancel them if user submits early
active_timers = {}

async def test_timer_countdown(user_id: int, test_code: str, duration_seconds: int, state: FSMContext):
    """
    Background timer task. Sleeps for the duration of the test, 
    and automatically stops it if not already completed.
    """
    try:
        await asyncio.sleep(duration_seconds)
        
        # Check if the user is still taking this test
        current_state = await state.get_state()
        if current_state in [TestStates.solving, TestStates.waiting_for_answers]:
            state_data = await state.get_data()
            if state_data.get("active_test_code") == test_code:
                # Retrieve test details
                test = db.get_test(test_code)
                correct_answers = test["correct_answers"]
                total_q = len(correct_answers)
                
                # Auto submit with 0 correct answers
                user = db.get_user(user_id)
                db.add_result(
                    telegram_id=user_id,
                    test_code=test_code,
                    correct_count=0,
                    wrong_count=total_q,
                    percentage=0.0,
                    duration_spent=duration_seconds
                )
                
                await state.clear()
                
                # Notify User
                await bot.send_message(
                    user_id,
                    "⌛ <b>Vaqt tugadi!</b>\n\n"
                    f"Siz '{test['subject']}' testini topshirishga berilgan vaqtdan kechikdingiz. "
                    "Javoblaringiz qabul qilinmadi, natijangiz: 0%.",
                    reply_markup=get_main_menu_keyboard()
                )
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Error in test timer for user {user_id}: {e}")

# Check subscription middleware helper
async def check_user_access(message: Message) -> bool:
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("⚠️ Tizimdan foydalanish uchun /start buyrug'ini bosing va ro'yxatdan o'ting.")
        return False
        
    subscribed = await is_subscribed(bot, Config.CHANNEL_USERNAME, telegram_id)
    if not subscribed:
        from keyboards.inline.keyboards import get_subscription_keyboard
        await message.answer(
            f"🔒 <b>Botdan foydalanish uchun hamkor kanalimizga a'zo bo'lishingiz majburiy:</b>\n"
            f"👉 {Config.CHANNEL_USERNAME}",
            reply_markup=get_subscription_keyboard(Config.CHANNEL_USERNAME)
        )
        return False
    return True

# --- 📚 TEST ISHLASH SECTION ---
@router.message(F.text == "📚 Test ishlash")
async def enter_test_menu(message: Message, state: FSMContext):
    if not await check_user_access(message):
        return
        
    await message.answer(
        "📚 <b>Test topshirish bo'limi</b>\n\n"
        "Iltimos, topshirmoqchi bo'lgan <b>test kodini</b> yuboring:\n"
        "<i>(Masalan: <code>PM-21</code>)</i>",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(TestStates.waiting_for_code)


async def start_solving_test_for_user(user_id: int, test_code: str, state: FSMContext, message: Message):
    # 1. Fetch test
    test = db.get_test(test_code)
    if not test:
        await message.answer(
            "❌ <b>Bunday kodli test topilmadi!</b>\n\n"
            "Iltimos, test kodini to'g'ri kiritganingizga ishonch hosil qiling va qayta yuboring:\n"
            "<i>(Ortga qaytish uchun: '↩️ Ortga qaytish' tugmasini bosing)</i>",
            reply_markup=get_back_keyboard()
        )
        return
        
    # 2. Check if already participated
    if db.has_participated(user_id, test_code):
        await message.answer(
            "⚠️ <b>Ziddiyat!</b>\n\n"
            "Siz ushbu testni topshirib bo'lgansiz. Qoida tariqasida har bir testda faqat bir marta ishtirok etish mumkin."
        )
        await state.clear()
        return

    # 3. Check if test active
    if not test["is_active"]:
        await message.answer("⚠️ <b>Ushbu test hozirda faol emas!</b>")
        await state.clear()
        return

    # 4. Check dates/times
    try:
        now = datetime.now()
        start_dt = datetime.strptime(test["start_time"], "%d.%m.%Y %H:%M")
        end_dt = datetime.strptime(test["end_time"], "%d.%m.%Y %H:%M")
        
        if now < start_dt:
            await message.answer(
                "⏳ <b>Ushbu test hali boshlanmadi!</b>\n\n"
                f"📅 Boshlanish vaqti: <b>{test['start_time']}</b>\n"
                f"🕒 Hozirgi vaqt: <b>{now.strftime('%d.%m.%Y %H:%M')}</b>"
            )
            await state.clear()
            return
            
        if now > end_dt:
            await message.answer(
                "❌ <b>Ushbu test muddati tugagan!</b>\n\n"
                f"📅 Tugash vaqti: <b>{test['end_time']}</b>\n"
                f"🕒 Hozirgi vaqt: <b>{now.strftime('%d.%m.%Y %H:%M')}</b>"
            )
            await state.clear()
            return
    except Exception as e:
        logger.error(f"Error parsing test times: {e}")
        await message.answer("⚠️ Test vaqtlarini tekshirishda xatolik yuz berdi. Admin bilan bog'laning.")
        await state.clear()
        return

    # 5. Show test details and start test immediately
    gift_tag = "🎁 SOVG'ALI " if test.get("is_gift", 0) else ""
    test_info = (
        f"🚀 <b>{gift_tag}TEST BOSHLANDI!</b>\n\n"
        f"📚 Fan: <b>{test['subject']}</b>\n"
        f"📄 Test kodi: <b>{test_code}</b>\n"
        f"⏳ Ishlash vaqti: <b>{test['duration']} daqiqa</b>\n"
        f"📅 Boshlanish: {test['start_time']}\n"
        f"📅 Tugash: {test['end_time']}\n\n"
        "Savollarni yeching. Ishlab bo'lganingizdan so'ng pastdagi <b>'🏁 Ishlab bo'ldim'</b> tugmasini bosing va javoblaringizni yuboring!"
    )
    
    start_timestamp = time.time()
    duration_seconds = test["duration"] * 60
    
    await state.update_data(
        active_test_code=test_code,
        start_time=start_timestamp,
        duration_seconds=duration_seconds
    )
    await state.set_state(TestStates.solving)
    
    # Send PDF first
    if test["pdf_path"] and os.path.exists(test["pdf_path"]):
        pdf_file = FSInputFile(test["pdf_path"])
        await message.answer_document(pdf_file, caption=f"📄 {test['subject']} savollari.pdf")
        
    await message.answer(test_info, reply_markup=get_solving_keyboard())
    
    # Create background task for auto submission
    timer_task = asyncio.create_task(
        test_timer_countdown(user_id, test_code, duration_seconds, state)
    )
    active_timers[f"{user_id}_{test_code}"] = timer_task

@router.message(TestStates.waiting_for_code)
async def process_test_code(message: Message, state: FSMContext):
    input_text = message.text.strip()
    
    # Check for back action
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_main_menu_keyboard())
        return
        
    test_code = input_text.upper()
    telegram_id = message.from_user.id
    
    await start_solving_test_for_user(telegram_id, test_code, state, message)

# Handle gift test start from callback button
@router.callback_query(F.data.startswith("start_gift_test:"))
async def process_callback_gift_test_start(callback: CallbackQuery, state: FSMContext):
    test_code = callback.data.split(":")[1]
    telegram_id = callback.from_user.id
    
    await callback.message.delete()
    await start_solving_test_for_user(telegram_id, test_code, state, callback.message)
    await callback.answer()

# User sends random text while solving
@router.message(TestStates.solving, F.text != "🏁 Ishlab bo'ldim")
async def solving_reminder(message: Message):
    await message.answer(
        "⏳ <b>Siz hozir test yechish jarayonidasiz!</b>\n\n"
        "Savollarni yechib bo'lgach, iltimos pastdagi <b>'🏁 Ishlab bo'ldim'</b> tugmasini bosing.",
        reply_markup=get_solving_keyboard()
    )

# When they click finished solving
@router.message(TestStates.solving, F.text == "🏁 Ishlab bo'ldim")
async def user_finished_solving(message: Message, state: FSMContext):
    await state.set_state(TestStates.waiting_for_answers)
    await message.answer(
        "✍️ <b>Javoblaringizni quyidagi to'g'ri formatlardan birida yuboring:</b>\n\n"
        "👉 Ketma-ket: <code>ABCDABCD</code>\n"
        "👉 Vergul bilan: <code>1.a, 2.b, 3.c</code>\n"
        "👉 Tire bilan: <code>1-a 2-b 3-c</code>",
        reply_markup=get_back_keyboard()
    )

# Receive and process answers under waiting_for_answers
@router.message(TestStates.waiting_for_answers)
async def process_answers(message: Message, state: FSMContext):
    input_text = message.text.strip() if message.text else ""
    telegram_id = message.from_user.id
    
    state_data = await state.get_data()
    test_code = state_data["active_test_code"]
    start_time = state_data["start_time"]
    
    if input_text == "↩️ Ortga qaytish":
        # Cancel active timer
        timer_key = f"{telegram_id}_{test_code}"
        if timer_key in active_timers:
            active_timers[timer_key].cancel()
            del active_timers[timer_key]
        await state.clear()
        await message.answer("🏠 Test bekor qilindi va bosh menyuga qaytildi.", reply_markup=get_main_menu_keyboard())
        return
        
    answers = parse_user_answers(input_text)
    test = db.get_test(test_code)
    correct_answers = test["correct_answers"]
    total_q = len(correct_answers)
    
    # Validate input length and chars
    if not answers:
        await message.answer(
            "⚠️ <b>Javoblaringiz aniqlanmadi!</b>\n\n"
            "Iltimos, quyidagi to'g'ri formatlardan birida yuboring:\n"
            "👉 Ketma-ket: <code>ABCDABCD</code>\n"
            "👉 Vergul bilan: <code>1.a, 2.b, 3.c</code>\n"
            "👉 Tire bilan: <code>1-a 2-b 3-c</code>"
        )
        return
        
    if len(answers) != total_q:
        await message.answer(
            f"⚠️ <b>Javoblar soni mos kelmadi!</b>\n\n"
            f"Ushbu testda jami <b>{total_q} ta</b> savol bor. Siz esa <b>{len(answers)} ta</b> javob yubordingiz.\n"
            f"Iltimos, qaytadan tekshirib, to'liq yuboring:"
        )
        return
        
    # Cancel active timer now that validation is passed
    timer_key = f"{telegram_id}_{test_code}"
    if timer_key in active_timers:
        active_timers[timer_key].cancel()
        del active_timers[timer_key]
        
    duration_spent = int(time.time() - start_time)
    
    # Check answers
    correct_count = 0
    wrong_count = 0
    wrong_details = []
    
    for idx in range(total_q):
        user_ans = answers[idx]
        correct_ans = correct_answers[idx]
        if user_ans == correct_ans:
            correct_count += 1
        else:
            wrong_count += 1
            wrong_details.append(
                f"❓ <b>{idx+1}-savol:</b> Siz yuborgan javob: '<code>{user_ans}</code>', to'g'ri javob: '<code>{correct_ans}</code>'.\n"
                f"⚠️ <i>(Ushbu savolni yaxshilab ko'rib chiqing!)</i>"
            )
            
    percentage = round((correct_count / total_q) * 100, 1)
    
    # Save results
    db.add_result(
        telegram_id=telegram_id,
        test_code=test_code,
        correct_count=correct_count,
        wrong_count=wrong_count,
        percentage=percentage,
        duration_spent=duration_spent
    )
    
    user = db.get_user(telegram_id)
    rank, total_p = db.get_user_rank(telegram_id, test_code)
    
    # Clear FSM State
    await state.clear()
    
    # Result Summary Page
    result_text = (
        "🎯 <b>TEST NATIJASI</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {user['full_name']}\n"
        f"🏫 <b>Sinf:</b> {user['class_name']}\n"
        f"📚 <b>Fan:</b> {test['subject']}\n"
        f"📄 <b>Test kodi:</b> <code>{test_code}</code>\n\n"
        f"✅ <b>To'g'ri javoblar:</b> {correct_count} ta\n"
        f"❌ <b>Noto'g'ri javoblar:</b> {wrong_count} ta\n"
        f"📊 <b>Natija:</b> {percentage}%\n"
        f"🏆 <b>Reyting:</b> {rank}-o'rin (jami {total_p} ta o'quvchidan)\n\n"
        f"⏱ <b>Sarflangan vaqt:</b> {duration_spent // 60} daqiqa {duration_spent % 60} soniya"
    )
    
    await message.answer(
        result_text, 
        reply_markup=get_result_keyboard(test_code)
    )
    
    # Send wrong answers feedback
    if wrong_details:
        feedback_text = "❌ <b>XATO ISHLANGAN SAVOLLAR TAHLILI:</b>\n"
        feedback_text += "<i>Xatolaringiz ustida ishlab, ushbu savollarni yaxshilab ko'rib chiqing:</i>\n\n"
        feedback_text += "\n\n".join(wrong_details)
        await message.answer(feedback_text)




@router.callback_query(F.data.startswith("view_rating:"))
async def view_test_leaderboard(callback: CallbackQuery):
    test_code = callback.data.split(":")[1]
    telegram_id = callback.from_user.id
    
    test = db.get_test(test_code)
    results = db.get_test_results(test_code)
    
    if not results:
        await callback.answer("⚠️ Bu test bo'yicha ma'lumot topilmadi!", show_alert=True)
        return
        
    msg_text = f"🏆 <b>'{test['subject']}' BO'YICHA REYTING (TOP 10)</b>\n"
    msg_text += f"📄 Test kodi: <code>{test_code}</code>\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    for idx, r in enumerate(results[:10], 1):
        icon = medals[idx-1] if idx <= 3 else f"<b>{idx}.</b>"
        name = r["full_name"]
        sinf = r["class_name"]
        score = r["percentage"]
        
        row_text = f"{icon} {name} ({sinf}) — <b>{score}%</b>\n"
        if r["telegram_id"] == telegram_id:
            row_text = f"👤 <b>{row_text.strip()} (Siz)</b>\n"
        msg_text += row_text
        
    await callback.message.answer(msg_text)
    await callback.answer()

@router.callback_query(F.data == "new_test")
async def start_new_test(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await enter_test_menu(callback.message, state)
    await callback.answer()
